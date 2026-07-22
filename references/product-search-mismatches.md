# Búsquedas problemáticas en Mercadona: casos documentados

`mercadona batch --fresh` prioriza productos empaquetados sobre frescos a granel.
Esta página documenta casos donde el top hit de batch es incorrecto y qué búsqueda
individual lo corrige.

## Casos documentados (sesión 2026-07-14, menú verano)

| Búsqueda original | Top hit (incorrecto) | Búsqueda corregida | Resultado correcto | ID |
|-------------------|---------------------|-------------------|-------------------|-----|
| `piña fresca` | Queso rulo con piña y almendra Liptana | `piña` (sin --fresh) | Piña natural a rodajas | 3024 |
| `patatas` / `patata` | Patatas fritas clásicas Hacendado | `mercadona search patata` (individual) | Patata (a granel) | 69066 |
| `albahaca fresca` | Salsa fresca Pesto con albahaca | `mercadona search albahaca` (individual) | Albahaca (hierba fresca) | 69287 |
| `queso parmesano` | Queso rallado mozzarella pizza-Roma | `grana padano` (sin --fresh) | Grana padano Zanetti | 50008 |
| `tomate frito` | Pasta fresca rellena de tomate frito | `salsa tomate frito` (sin --fresh) | Tomate frito Hacendado | 17132 |
| `aceitunas kalamata` | Aceitunas verdes rellenas de anchoa ⚠️ | No disponible en Mercadona | Aceitunas negras en rodajas | 8309 |

## Patrón

`batch --fresh` es bueno para verduras comunes (cebolla, pepino, lechuga) pero falla con:
- Productos que tienen nombre similar a procesados (patata→fritas, albahaca→pesto)
- Ingredientes con nombre en inglés o extranjero (kalamata)
- Quesos específicos (parmesano busca cualquier queso rallado)

## Workflow de corrección

1. Ejecutar `batch --fresh` con todas las queries.
2. Revisar resultados manualmente — buscar nombres claramente incorrectos.
3. Para cada mismatch, ejecutar `mercadona search '<query corregida>' --json --limit 5`.
4. Seleccionar el hit correcto y sustituir en el basket.
5. Si no hay resultado en Mercadona, consultar `references/mercadona-product-substitutions.md`.

## Comando útil

```bash
# Búsqueda individual (más resultados que batch)
mercadona search '<producto>' --json --limit 5 --wh 4182 | \
  python3 -c "import sys,json; [print(f'{h[\"id\"]}: {h[\"display_name\"]}') for h in json.load(sys.stdin)['hits'][:5]]"
```

> **Actualizado:** 2026-07-14 — sesión menú cenas verano (20-26 julio)
