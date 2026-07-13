# Prompt — Consolidación de la lista de la compra

> **Rol**: recibe las 7 recetas del menú semanal y produce UNA lista de la compra consolidada, normalizada para Mercadona Online, agrupada por categoría y con estimación de coste.

## Inputs

- `meals`: diccionario como el producido por `prompts/menu_planning.md` (7 días, clave `cena`).
- `stock_known`: (opcional) lista de ingredientes que el usuario ya tiene (ej. `["aceite", "sal", "pimienta"]`).

## Objetivos

1. **Unificar duplicados**: si "cebolla" aparece en 3 recetas, SUMA cantidades.
2. **Normalizar nombres** a la nomenclatura de Mercadona:
   - "salmón fresco" → "salmón fresco lomo"
   - "calabacín" → "calabacín"
   - "tomates cherry" → "tomate cherry"
   - "ajo" → "ajo" (o "ajos morados" si Mercadona lo lista así)
   - "leche de coco" → "leche de coco"
3. **Agrupar** por categoría siguiendo este orden:
   - 🥩 **Proteínas** (carnes, pescados, huevos, jamón)
   - 🥬 **Verduras y frutas**
   - 🥫 **Despensa** (legumbres, arroces, caldos, conservas)
   - 🧂 **Condimentos y básicos** (aceite, sal, especias)
4. **Marcar stock**: ingredientes en `stock_known` → columna "Cantidad" = `— (comprobar stock)`.
5. **Convertir unidades** para comprar paquetes realistas:
   - 400 g salmón → "400g (2 lomos)"
   - 5 uds patata → "1 kg (aprox.)"
   - 700 ml caldo → "2 bricks de 500 ml"
6. **Estimar coste total** sumando precios orientativos (ej. salmón 25€/kg, pollo 8€/kg, calabacín 1,5€/ud). Indica `€ orientativo` por línea y TOTAL.
7. **Mapear a query Mercadona**: para cada ingrediente, genera `mercadona_query` (lo que se pasará a `mercadona_client.py --list`).

## Formato de salida

Devuelve un JSON:

```json
{
  "shopping_list": [
    {"name": "salmón fresco lomo", "category": "proteinas", "quantity": "400g (2 lomos)", "mercadona_query": "salmón fresco", "estimated_price_eur": 10.0, "needs_stock_check": false}
  ],
  "total_estimated_eur": 45.7,
  "raw_queries_for_mercadona": ["salmón fresco", "calabacín", "cebolla", ...]
}
```

## Heurísticas de conversión

| Input | Output Mercadona |
|-------|------------------|
| 1 ajo (diente) | "ajo" (compra 1 cabeza) |
| 7 dientes de ajo | "ajo molido" o "1 cabeza" |
| 200 ml caldo | "caldo verduras brick 500 ml" |
| 1 trozo jengibre 2 cm | "jengibre fresco" (raíz ~80g) |
| "quesito" | "quesito porciones" |
| "pimiento asado" | "pimiento asado bote" |

## Pseudocódigo del razonamiento (sigue estos pasos)

```
1. ingredients = []
2. for day in ["Lunes"..."Domingo"]:
3.   for slot in ["comida", "cena"]:
4.     for ing in meals[day][slot].ingredients:
5.       key = normalize(ing.name)
6.       if key not in consolidated:
7.          consolidated[key] = {amount: 0, unit, used_in: []}
8.       if consolidated[key].unit == ing.unit:
9.          consolidated[key].amount += ing.amount
10.      consolidated[key].used_in.append(day[0])
11. for ing in consolidated.values():
12.    if ing.name in stock_known: mark stock
13.    ing.mercadona_query = map_to_mercadona(ing.name)
14. total = sum(estimate_price(ing))
15. return {shopping_list, total_estimated_eur, raw_queries_for_mercadona}
```

## Output para el script

El campo `raw_queries_for_mercadona` se pasa directamente a:

```bash
python3 scripts/mercadona_client.py --add-from-file shopping_list.json
```

donde `shopping_list.json` se escribe como `{"shopping_list": ["query1", "query2", ...]}`.