# Subagente C: fill — Ejecutar fill_cart en Mercadona

## Tu tarea

Recibes un basket file ya validado (Gate 1 aprobado) y debes ejecutar `fill_cart`
para añadir los productos al carrito real de Mercadona.

## Input

El orquestador te pasará:
- `basket_path`: ruta del archivo basket.txt (ej. `/tmp/basket.txt`)
- `max_eur`: presupuesto máximo aprobado en Gate 1
- `skill_dir`: ruta base de la skill

## Pasos

### 1. Cargar wrapper y ejecutar

```python
import sys
sys.path.insert(0, '{skill_dir}/scripts')
from mercadona_cli_wrapper import MercadonaCLI

cli = MercadonaCLI(warehouse="4182")
result = cli.fill_cart('{basket_path}', max_eur={max_eur})
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 2. Verificar carrito

```python
cart = cli.get_cart()
print(f"Productos en carrito: {cart['products_count']}")
print(f"Total carrito: {cart['summary']['total']}€")
```

## Output

```
## Resultados Subagente C

### fill_cart ejecutado
- Éxito: {yes/no}
- Productos añadidos: {count}
- Total carrito: {total}€
- ID carrito: {cart_id}

### Verificación post-fill
- Products count: {n}
- Summary total: {total}€
```

## Pitfalls

- **No ejecutar sin Gate 1 aprobado**. Este subagente solo se invoca tras OK explícito de Xavi.
- **max_eur actúa como spending guard**. Si el total real supera max_eur, Mercadona CLI rechaza.
- **Si fill_cart falla**, reportar el error exacto. NO reintentar sin consultar.
- **Warehouse siempre 4182**.
