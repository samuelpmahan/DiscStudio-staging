"""the backend vertical: one facade, many engines.

`fn.brain.backend.<op>` takes `args["backend"]` - `"py"` (pure python, the
reference), `"np"` (numpy), `"sp"` (scipy) - and every engine answers the same
question the same way, within tolerance. a backend that changes semantics is a
failed backend, and its oracle part says so.
"""
