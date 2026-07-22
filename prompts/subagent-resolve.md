# Subagente B: resolve — Mercadona Product Resolution

## Tu tarea

Recibes una shopping list JSON y debes resolver cada ingrediente a productos concretos
de Mercadona, generar un basket, y calcular el preview total.

## Input

El orquestador te pasará:
- `shopping_list`: JSON array de ingredientes
- `skill_dir`: ruta base de la skill (para encontrar scripts)
- `warehouse`: "4182" (fijo para Xavi)

## Pasos

### 1. Cargar el wrapper

```python
import sys
sys.path.insert(0, '{skill_dir}/scripts')
from mercadona_cli_wrapper import MercadonaCLI
import json

cli = MercadonaCLI(warehouse="4182")
shopping_list = json.loads('''{shopping_list_json}''')
```

### 2. Resolver productos

```python
result = cli.resolve_shopping_list(shopping_list)
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 3. Revisar mismatches

El `batch --fresh` puede devolver productos incorrectos para ciertos términos.
Revisa los top hits y corrige si es necesario:

**Mismatches conocidos** (buscar individualmente con `mercadona search`):
| Término | Batch devuelve (INCORRECTO) | Buscar individual |
|---------|---------------------------|-------------------|
| patata | Patatas fritas clásicas (snack) | `mercadona search 'patata' --json --limit 5` |
| piña fresca | Queso rulo con piña | `mercadona search 'piña' --json --limit 5` |
| albahaca fresca | Salsa Pesto | `mercadona search 'albahaca' --json --limit 5` |
| tomate frito | Pasta rellena de tomate | `mercadona search 'tomate frito' --json --limit 5` |

Si el top hit es incorrecto, usa:
```bash
mercadona search '<query>' --json --limit 5 --wh 4182
```
Y selecciona manualmente el producto correcto.

### 4. Ajustar cantidades a enteros

**REGLA DURA**: el basket solo acepta cantidades ENTERAS. Productos que en `product info`
muestran `ref=kg` pueden ser rechazados con decimales (contramuslos pollo, filetes pechuga
se venden por bandeja → qty=1 = 1 bandeja).

```python
import math
for item in resolved['resolved']:
    qty = item['quantity']
    if qty != int(qty):
        item['quantity'] = math.ceil(qty)
        item['notes'] = f"Ajustado de {qty} → {item['quantity']} (entero requerido)"
```

### 5. Generar basket

```python
basket_path = cli.generate_basket_file(resolved['resolved'], '/tmp/basket.txt')
```

### 6. Preview total

```python
preview = cli.preview_total(basket_path)
```

## Output

Devuelve un informe con esta estructura exacta:

```
## Resultados Subagente B

### Basket generado
- Ruta: /tmp/basket.txt
- Total: {total}€
- Productos: {count}

### Preview detallado
| Producto | ID | Qty | Precio ud. | Subtotal |
|----------|-----|------|-----------|----------|
| {name} | {id} | {qty} | {unit_price}€ | {subtotal}€ |

### No resueltos
- {query}: {reason}

### Ajustes de cantidad (decimal → entero)
- {product}: {old_qty} → {new_qty}
- Si el ajuste cambia el total >10€, MARCAR para re-aprobación en Gate 1.

### Sustituciones sospechosas
- {query} → batch devolvió {wrong}, corregido a {correct} vía search individual
```

## Pitfalls

- **batch --fresh miente**: si el top hit es claramente incorrecto, usa `mercadona search` individual.
- **Cantidades enteras**: redondear hacia arriba con `math.ceil`. Reportar cambios >10€.
- **Productos por bandeja**: contramuslos (2789), filetes pechuga (3400) → qty=1 bandeja, no peso.
- **Warehouse siempre 4182**.
