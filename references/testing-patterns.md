# Patrones de testing — meal-to-cart

Patrones reutilizables aprendidos durante el desarrollo de los tests.

## Mock de clientes async sin warnings de coroutine

### Problema

Al testear `mercadona_client.py`, que usa `asyncio.run(run(args))` en su
`main()`, mockear `asyncio.run` directamente produce el warning:

```
RuntimeWarning: coroutine 'run' was never awaited
```

Esto ocurre porque `run(args)` crea una coroutine que se pasa al mock,
pero el mock lanza una excepción sin consumirla — la coroutine queda
huérfana y el garbage collector avisa.

### Solución

**NO mockear `asyncio.run`.** En su lugar, mockear la clase cliente para
que falle dentro del flujo async real. La coroutine se crea, se espera
correctamente, y la excepción se captura en el `except Exception` de
`main()`.

```python
# ❌ MAL — produce warning
def test_main_error(monkeypatch):
    monkeypatch.setattr(mc.asyncio, "run", lambda *a: exec('raise RuntimeError("foo")'))
    rc = mc.main(["--search", "x"])
    assert rc == 1

# ✅ BIEN — sin warning
def test_main_error(monkeypatch):
    class FailingClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None
        async def open(self): raise RuntimeError("foo")
        async def add_many(self, items, dry_run=True): return []

    monkeypatch.setattr(mc, "MercadonaClient", lambda **kw: FailingClient())
    rc = mc.main(["--search", "x"])
    assert rc == 1
```

### Aplica a

Cualquier CLI async que use `asyncio.run()` como entry point:
- `mercadona_client.py`
- `cookidough_client.py` (si se le añade CLI)
- Cualquier script con patrón `def main(): return asyncio.run(...)`
