"""Isolated DOM harness for own local source when Chrome URL navigation is disabled.
Uses real JS modules, actual SVG rendering and browser image/canvas APIs.
LocalStorage is a disclosed in-memory test double; CI runs the normal HTTP mode.
No external requests or browser policy changes.
"""
from pathlib import Path
import re,base64,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
cache={}
def module(path):
 path=path.resolve()
 if path in cache: return cache[path]
 source=path.read_text()
 def sub(m):
  start,rel,end=m.groups()
  if not rel.startswith('.'):return m.group(0)
  return start+module(path.parent/rel)+end
 # Only real import lines are rewritten (single-line imports, and the closing `} from '...'` of a
 # multi-line one): a comment or string that merely mentions an import must not be inlined, and a
 # module that mentions itself must not recurse.
 def line_sub(line):
  head=line.lstrip()
  if not (head.startswith('import ') or head.startswith('export ') or head.startswith('} from ')):return line
  return re.sub(r"(from\s*['\"]|import\s*['\"])([^'\"]+)(['\"])",sub,line)
 source='\n'.join(line_sub(l) for l in source.split('\n'))
 source=source.replace("new URL('../build-info.json', import.meta.url)",json.dumps('data:application/json,'+json.dumps({'commit':'local-DOM-check','fingerprint':'local-DOM-check'})))
 uri='data:text/javascript;base64,'+base64.b64encode(source.encode()).decode()
 cache[path]=uri
 return uri

def mount(page,storage=None):
 html=(ROOT/'index.html').read_text()
 html=re.sub(r'<link[^>]+>','',html)
 html=re.sub(r'<script[^>]*>.*?</script>','',html)
 page.set_content(html)
 page.add_style_tag(content=(ROOT/'src/style.css').read_text())
 page.evaluate('''initial=>{const store=new Map(Object.entries(initial));Object.defineProperty(window,'localStorage',{value:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k),clear:()=>store.clear()}});window.testStorage=store;}''',storage or {})
 page.evaluate('(url)=>import(url)',module(ROOT/'src/app.js'))
 page.wait_for_selector('.app-header')
 return page

