"""Spike: does pyto 0.1.0 express a grouped-feature ablation? Records each constraint hit."""
from __future__ import annotations
import dataclasses, json, random, time, hashlib, itertools
from pyto import Calculation, Part, PCR, PQL, PxC

random.seed(7)

# ---- constraint probes -------------------------------------------------------
print('== constraint probes ==')
pcr = PCR('probe')
ident = Calculation('fn.ident', lambda a: a['x'])
pcr.calc('T', ident, id='v1', x=Part('px.in'), into='scratch.out')
try:
    pcr.calc('T', ident, id='v2', x=Part('px.in'), into='scratch.out')
except ValueError as e:
    print('P1 two variants -> same into address:', e)

pxc = PxC()
pxc.register(Calculation('fn.fit', lambda a: 1))
try:
    pxc.register(Calculation('fn.fit', lambda a: 2))
except ValueError as e:
    print('P2 same fn address, different closure:', e)

w1 = pxc.set('px.x', 1); w2 = pxc.set('px.x', 2)
print('P3 PxC.set twice ->', w1.kind, '/', w2.kind, '(no error, no version, no hash)')

pcr = PCR('args')
pcr.calc('T', Calculation('fn.f', lambda a: a['k']), id='c', args={'k': [1, 2]})
run = pcr.run(PxC())
t = run.ticks[0].calculations[0]
print('P4 testimony fields:', [f.name for f in dataclasses.fields(t)], '-> args recorded:', t.args)
print('P5 PcrRun fields:', [f.name for f in dataclasses.fields(run)], '(no timing, no result digest)')

# shared intermediate across two PCRs through one PxC
pxc = PxC(); pxc.set('px.raw', [1, 2, 3])
a = PCR('A'); a.calc('T', Calculation('fn.prep', lambda x: [v * 2 for v in x['raw']]), id='prep', raw=Part('px.raw'), into='px.prepared'); a.run(pxc)
b = PCR('B'); b.calc('T', Calculation('fn.sum', lambda x: sum(x['p'])), id='s', p=Part('px.prepared')); rb = b.run(pxc)
print('P6 second PCR sees shared Part as', rb.ticks[0].calculations[0].inputs, '(px:, not fn: -- provenance link to producer is lost across PCRs)')

# ---- the actual grouped ablation on synthetic data ----------------------------
print('\n== grouped feature ablation (15 features, 5 groups, leave-one-group-out) ==')
FEATURES = [f'f{i:02d}' for i in range(15)]
GROUPS = {f'g{k}': FEATURES[3 * k:3 * k + 3] for k in range(5)}   # 5 groups x 3 features
TRUE_W = [1.5, 0, 0, 0.8, 0, 0, 0, 0, 0, 2.0, 0, 0, 0, 0, 0]       # only g0, g1, g3 matter

def make_data(n=400):
    rows = []
    for _ in range(n):
        x = [random.gauss(0, 1) for _ in FEATURES]
        y = sum(w * v for w, v in zip(TRUE_W, x)) + random.gauss(0, 0.3)
        rows.append((x, y))
    return rows

def solve(A, b):  # Gauss-Jordan on small dense system
    n = len(A); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        piv = M[c][c] or 1e-12; M[c] = [v / piv for v in M[c]]
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c]; M[r] = [rv - f * cv for rv, cv in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]

def ols(args):  # ridge-ish OLS restricted to args['columns']
    cols = args['columns']; X, y = args['train']
    idx = [FEATURES.index(c) for c in cols]
    Xs = [[r[i] for i in idx] for r in X]
    d = len(idx); lam = 1e-3
    A = [[sum(Xs[k][i] * Xs[k][j] for k in range(len(Xs))) + (lam if i == j else 0) for j in range(d)] for i in range(d)]
    b = [sum(Xs[k][i] * y[k] for k in range(len(Xs))) for i in range(d)]
    return {'columns': cols, 'w': solve(A, b)}

def rmse(args):
    cols, w = args['model']['columns'], args['model']['w']; X, y = args['test']
    idx = [FEATURES.index(c) for c in cols]
    err = [(sum(wi * r[i] for wi, i in zip(w, idx)) - yi) ** 2 for r, yi in zip(X, y)]
    return {'rmse': (sum(err) / len(err)) ** 0.5, 'n': len(err)}

def split(args):
    rows = args['rows']; k = int(len(rows) * 0.75)
    return {'train': ([r[0] for r in rows[:k]], [r[1] for r in rows[:k]]),
            'test': ([r[0] for r in rows[k:]], [r[1] for r in rows[k:]])}

def selector(args):  # leave-one-group-out + full baseline; a Calculation, so testimony records it
    groups = args['groups']
    variants = [{'key': 'all', 'drop': [], 'columns': [f for g in groups.values() for f in g]}]
    for g in groups:
        variants.append({'key': f'drop-{g}', 'drop': [g], 'columns': [f for h, fs in groups.items() if h != g for f in fs]})
    return variants

pxc = PxC()
pxc.set('input.ablation.rows', make_data())
pxc.set('input.ablation.groups', GROUPS)
pcr = PCR('ablation.grouped')
pcr.calc('Plan', Calculation('fn.ablation.selectVariants', selector), id='select', groups=Part('input.ablation.groups'), into='scratch.ablation.variants')
pcr.calc('Prepare', Calculation('fn.ablation.split', split), id='split', rows=Part('input.ablation.rows'), into='scratch.ablation.split')

# The variant family cannot be expressed inside the PCR from the selector's *result*:
# PCR.calc needs the variant list at authoring time, so we compute it outside and unroll.
variants = selector({'groups': GROUPS})
fit = Calculation('fn.ablation.fitOls', lambda a: ols({'columns': a['columns'], 'train': a['split']['train']}))
score = Calculation('fn.ablation.rmse', lambda a: rmse({'model': a['model'], 'test': a['split']['test']}))
timings = {}
for v in variants:
    fid = f"fit:{v['key']}"; sid = f"score:{v['key']}"
    pcr.calc('Fit', fit, id=fid, split=Part('scratch.ablation.split'), args={'columns': v['columns'], 'variant': v['key']}, into=f"scratch.ablation.model.{v['key']}")
    pcr.calc('Score', score, id=sid, split=Part('scratch.ablation.split'), model=Part(f"scratch.ablation.model.{v['key']}"), into=f"scratch.ablation.score.{v['key']}")

def compare(args):
    base = args['scores']['all']['rmse']
    return sorted(({'variant': k, 'rmse': round(s['rmse'], 4), 'delta_vs_all': round(s['rmse'] - base, 4)} for k, s in args['scores'].items()), key=lambda r: -r['delta_vs_all'])

# comparison consumes every variant score: only expressible by unrolling the bindings by hand
pcr.calc('Compare', Calculation('fn.ablation.compare', lambda a: compare({'scores': {k[len('s_'):]: v for k, v in a.items()}})),
         id='compare', into='scratch.ablation.comparison', **{f"s_{v['key']}": Part(f"scratch.ablation.score.{v['key']}") for v in variants})

t0 = time.perf_counter(); run = pcr.run(pxc); wall = time.perf_counter() - t0
print('ticks:', [tk.name for tk in run.ticks], '| calcs:', sum(len(tk.calculations) for tk in run.ticks), f'| wall {wall*1000:.1f} ms (measured OUTSIDE pyto)')
for row in PQL.part('scratch.ablation.comparison').one(pxc):
    print('  ', row)
print('fit testimony example:', dataclasses.asdict(run.ticks[2].calculations[1]))
print('compare inputs are fn: refs ->', run.ticks[4].calculations[0].inputs)
print('score Parts via PQL prefix ->', [m.address for m in PQL.prefix('scratch.ablation.score.').matches(pxc)])

# what a content key would have to be built from, by hand:
key = hashlib.sha256(json.dumps({'fn': 'fn.ablation.fitOls', 'args': variants[1]['columns'], 'split': hashlib.sha256(json.dumps(pxc.get('scratch.ablation.split')).encode()).hexdigest()}, sort_keys=True).encode()).hexdigest()[:12]
print('hand-built content key for fit:drop-g0 ->', key, '(pyto has no such key; Part identity is the address string only)')
print('rerun with same PxC: PxC.set kinds ->', pcr.run(pxc) and pxc.set('scratch.ablation.split', pxc.get('scratch.ablation.split')).kind)
