"""Labelled directed graphs for the paint studio, built with `ast`: one graph per function,
over every family renderer `art_registry.py` maps a slug to plus every studio helper those
reach transitively.  Nodes are calls (callee name and a coarse arity bucket, `cos/1`), SVG-tag
emissions found by regex in a string template (`<path>`), and the control constructs `for` and
`if`.  Edges are `next` (sequence), `in` (containment in a loop or branch body) and `arg` (a
value feeding a call or a template).  Deterministic: source order, sets sorted on the way out."""
from __future__ import annotations
import ast, os, re
STUDIO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "consumers", "discstudio-card")
STUDIO_FILES = ("art_registry.py", "paint_components.py", "paint_families.py",
                "_families_botanical.py", "_families_cartography.py",
                "_families_foundry.py", "_families_signal.py")
MODULES = tuple(name[:-3] for name in STUDIO_FILES)
TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)")
def read_source(module):
    """Read one studio module; refuses anything else, so the miner stays inside."""
    if module + ".py" not in STUDIO_FILES:  raise ValueError("not a studio source")
    with open(os.path.join(STUDIO, module + ".py"), encoding="utf-8") as handle:
        return handle.read()
class Graph:
    """Node labels, (src, dst, kind) edges, and (module, func, line) per node."""
    def __init__(self):
        self.labels, self.edges, self.where = [], [], []
    def add(self, label, module, func, lineno):
        self.labels.append(label); self.where.append((module, func, lineno))
        return len(self.labels) - 1
    def link(self, src, dst, kind):
        if src is not None and dst is not None and src != dst:
            self.edges.append((src, dst, kind))   # None means "nothing was emitted here"
class Builder:
    """Turns one function body into the nodes and edges of `self.g`."""
    def __init__(self, module, func, modnames):
        self.g, self.module, self.func, self.mods = Graph(), module, func, modnames
        self.calls, self.nested = [], []
    def node(self, label, lineno):
        return self.g.add(label, self.module, self.func, lineno)
    def body(self, stmts, container):
        prev = None
        for stmt in stmts:
            entry = self.stmt(stmt)
            if entry is not None:
                self.g.link(container, entry, "in"); self.g.link(prev, entry, "next")
                prev = entry
    def stmt(self, stmt):
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.nested.append(stmt); return None    # built as a graph of its own
        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While, ast.If)):
            nid = self.node("if" if isinstance(stmt, ast.If) else "for", stmt.lineno)
            self.expr(getattr(stmt, "test", None) or getattr(stmt, "iter", None), nid)
            self.body(stmt.body, nid); self.body(stmt.orelse, nid)
            return nid
        first = None
        for child in ast.iter_child_nodes(stmt):
            got = (self.expr(child, None) if isinstance(child, ast.expr) else
                   self.stmt(child) if isinstance(child, ast.stmt) else None)
            first = got if first is None else first
        return first
    def expr(self, node, parent):
        """Create nodes for `node`, wire them to `parent`, return its entry node."""
        if isinstance(node, ast.Call):
            nid = self.node(self.label(node), node.lineno)
            self.calls.append(self.callee(node))
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                self.expr(arg, nid)
            if isinstance(node.func, ast.Attribute):
                self.expr(node.func.value, nid)
            self.g.link(nid, parent, "arg")
            return nid
        if isinstance(node, ast.JoinedStr):
            text = "".join(p.value for p in node.values
                           if isinstance(p, ast.Constant) and isinstance(p.value, str))
            first = self.emit(text, node.lineno, parent)
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    self.expr(part.value, first if first is not None else parent)
            return first
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return self.emit(node.value, node.lineno, parent)
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            nid = self.node("for", node.lineno)
            for gen in node.generators:
                self.expr(gen.iter, nid)
                for cond in gen.ifs:
                    self.expr(cond, nid)
            for part in ([node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]):
                self.g.link(nid, self.expr(part, None), "in")
            self.g.link(nid, parent, "arg")
            return nid
        first = None
        for child in ast.iter_child_nodes(node) if node is not None else ():
            if isinstance(child, ast.expr):
                got = self.expr(child, parent)
                first = got if first is None else first
        return first
    def emit(self, text, lineno, parent):
        """One node per SVG tag the literal opens, chained in source order."""
        first = prev = None
        for match in TAG.finditer(text):
            nid = self.node("<%s>" % match.group(1), lineno)
            self.g.link(nid, parent, "arg") if prev is None else self.g.link(prev, nid, "next")
            first, prev = (nid if first is None else first), nid
        return first
    def callee(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):        # module-qualified, or a local's method
            if isinstance(func.value, ast.Name) and func.value.id in self.mods:
                return func.value.id + "." + func.attr
            return func.attr
        return "<expr>"
    def label(self, node):
        count = len(node.args) + len(node.keywords)
        return "%s/%s" % (self.callee(node), count if count < 3 else "3+")
def parse_studio():
    """module -> (ast, top-level defs, imported module names)."""
    trees, funcs, mods = {}, {}, {}
    for module in MODULES:
        trees[module] = ast.parse(read_source(module), filename=module + ".py")
        funcs[module] = {n.name: n for n in trees[module].body if isinstance(n, ast.FunctionDef)}
        mods[module] = sorted({a.name.split(".")[0] for n in trees[module].body
                               if isinstance(n, ast.Import) for a in n.names})
    return trees, funcs, mods
def _renderers(tree):
    """The `RENDERERS = {slug: function}` table of one studio module."""
    for stmt in tree.body:
        if (isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == "RENDERERS"):
            return {k.value: v.id for k, v in zip(stmt.value.keys, stmt.value.values)}
    return {}
def roots(trees, funcs):
    """Every slug `art_registry.ALL_FAMILIES` maps to, with the function it maps to."""
    found = []
    for stmt in trees["art_registry"].body:
        if not isinstance(stmt, ast.For) or not any(
                isinstance(s, ast.Subscript) and getattr(s.value, "id", "") == "ALL_FAMILIES"
                for s in ast.walk(stmt)):
            continue
        table = ""      # a loop body may look its renderer up in a slug table instead
        for sub in ast.walk(stmt):
            if (isinstance(sub, ast.Subscript) and isinstance(sub.value, ast.Attribute)
                    and sub.value.attr == "RENDERERS"):
                table = sub.value.value.id
        for elt in stmt.iter.elts:
            parts = elt.elts if isinstance(elt, ast.Tuple) else [elt]
            slug, target = parts[0].value, None
            for part in parts[1:]:
                if isinstance(part, ast.Name) and part.id in funcs["art_registry"]:
                    target = ("art_registry", part.id)
                elif (isinstance(part, ast.Attribute) and isinstance(part.value, ast.Name)
                      and part.value.id in funcs and part.attr in funcs[part.value.id]):
                    target = (part.value.id, part.attr)
            if target is None and table:  target = (table, _renderers(trees[table])[slug])
            if target is None:  raise ValueError("no renderer for slug %r" % slug)
            found.append((slug, target))
    return found
def _resolve(raw, module, qual, funcs, nested):
    """A callee name seen in `module.qual` -> the studio function it names, or None."""
    if "." in raw:
        mod, name = raw.split(".", 1)
        return (mod, name, funcs[mod][name]) if mod in funcs and name in funcs[mod] else None
    if raw in nested:
        return (module, qual + "." + raw, nested[raw])
    return (module, raw, funcs[module][raw]) if raw in funcs[module] else None
def build_studio():
    """(order, graphs, slugs): one graph per reachable function, discovery order."""
    trees, funcs, mods = parse_studio()
    graphs, built, slugs, order = {}, {}, {}, []
    for slug, (module, name) in roots(trees, funcs):
        queue, seen = [(module, name, funcs[module][name])], set()
        while queue:
            mod, qual, node = queue.pop(0)
            key = (mod, qual)
            if key in seen:  continue
            seen.add(key)
            slugs.setdefault(key, set()).add(slug)
            if key not in graphs:
                builder = Builder(mod, qual, mods[mod])
                builder.body(node.body, None); graphs[key] = builder.g
                built[key] = (builder.calls, {d.name: d for d in builder.nested})
                order.append(key)
            calls, nested = built[key]
            queue.extend(x for x in (_resolve(r, mod, qual, funcs, nested) for r in calls)
                         if x is not None)
    return order, graphs, {k: tuple(sorted(v)) for k, v in slugs.items()}
def union(order, graphs):
    """One graph over every function graph, disconnected, in `order`."""
    whole = Graph()
    for key in order:
        sub, base = graphs[key], len(whole.labels)
        whole.labels.extend(sub.labels); whole.where.extend(sub.where)
        whole.edges.extend((a + base, b + base, kind) for a, b, kind in sub.edges)
    return whole
