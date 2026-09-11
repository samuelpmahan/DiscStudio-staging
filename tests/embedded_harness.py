"""Isolated DOM harness for own local source when Chrome URL navigation is disabled.
Uses real JS modules, actual SVG rendering and browser image/canvas APIs.
LocalStorage is a disclosed in-memory test double; CI runs the normal HTTP mode.
No external requests or browser policy changes.

Every module is mounted ONCE, as its own data: URL, and its relative imports are
rewritten to `mod:<path-from-the-repository-root>` specifiers that an import map
in the page resolves. Inlining each child's data URL into its parent instead --
what this did until 2026-09-11 -- re-encodes a module once per import edge, so a
diamond like src/domain.js is carried dozens of times and the payload grows with
the depth of the graph: 48 modules totalling ~1 MB of source were mounted as a
single 32 MB data URL, and one import added to domain.js crashed the renderer
(Playwright reports it as "Target crashed" on the next interaction).
"""
from pathlib import Path
import re,base64,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def specifier(path):
 """A stable bare specifier for a module: its path from the repository root."""
 return 'mod:'+path.resolve().relative_to(ROOT).as_posix()
def collect(path,modules):
 """path and everything it imports, each source once, imports rewritten to bare specifiers."""
 path=path.resolve()
 if path in modules: return specifier(path)
 modules[path]=''  # claimed before reading, so a cycle resolves to the specifier instead of recursing
 source=path.read_text()
 def sub(m):
  start,rel,end=m.groups()
  if not rel.startswith('.'):return m.group(0)
  return start+collect(path.parent/rel,modules)+end
 # Only real import lines are rewritten (single-line imports, and the closing `} from '...'` of a
 # multi-line one): a comment or string that merely mentions an import must not be rewritten.
 def line_sub(line):
  head=line.lstrip()
  if not (head.startswith('import ') or head.startswith('export ') or head.startswith('} from ')):return line
  return re.sub(r"(from\s*['\"]|import\s*['\"])([^'\"]+)(['\"])",sub,line)
 source='\n'.join(line_sub(l) for l in source.split('\n'))
 source=source.replace("new URL('../build-info.json', import.meta.url)",json.dumps('data:application/json,'+json.dumps({'commit':'local-DOM-check','fingerprint':'local-DOM-check'})))
 modules[path]=source
 return specifier(path)
def graph(entry):
 """(entry specifier, import map) for one entry module."""
 modules={}
 spec=collect(entry,modules)
 return spec,{specifier(p):'data:text/javascript;base64,'+base64.b64encode(s.encode()).decode() for p,s in modules.items()}
def module(path):
 """The entry specifier and its import map, for a caller that mounts the page itself."""
 return graph(Path(path))

def mount(page,storage=None):
 html=(ROOT/'index.html').read_text()
 html=re.sub(r'<link[^>]+>','',html)
 html=re.sub(r'<script[^>]*>.*?</script>','',html)
 page.set_content(html)
 entry,imports=graph(ROOT/'src/app.js')
 page.add_script_tag(content=json.dumps({'imports':imports}),type='importmap')
 page.add_style_tag(content=(ROOT/'src/style.css').read_text())
 page.evaluate('''initial=>{const store=new Map(Object.entries(initial));Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k),clear:()=>store.clear()}});window.testStorage=store;}''',storage or {})
 page.evaluate('(specifier)=>import(specifier)',entry)
 page.wait_for_selector('.app-header')
 return page
