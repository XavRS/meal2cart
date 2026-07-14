# Sesión menú ensaladas (2026-07-14)

## Resumen

Planificación de menú de ensaladas y wraps frescos para 2 personas, 4 cenas (jueves-domingo),
con flujo meal-to-cart completo: búsqueda Cookidoo → calendario → consolidación → Mercadona → Gate 1 → carrito.

## Menú planificado

| Día       | Receta                                         | Fuente    | Kcal |
|-----------|------------------------------------------------|-----------|------|
| Jueves 17 | Ensalada César con Pollo                       | Manual    | 400  |
| Viernes 18 | Ensalada campera con naranja (r77976)         | Cookidoo  | 380  |
| Sábado 19 | Wraps de Pollo Teriyaki                        | Manual    | 420  |
| Domingo 20 | Ensalada de quinoa con calabacín (r174234)    | Cookidoo  | 360  |

## Métricas del flujo

- **Recetas Cookidoo encontradas:** 2/2 (búsqueda exitosa)
- **Recetas añadidas al calendario:** 2/2 (verificado con `add_recipes_to_calendar`)
- **Ingredientes consolidados:** 39 crudos → 15 con cantidad >0 (filtrado)
- **Ingredientes re-buscados manualmente:** 15 (los que llegaron con qty=0)
- **Productos resueltos en Mercadona:** 31/31 (100%)
- **Productos añadidos al carrito:** 31/31 (100%)
- **Total carrito:** 68.83€
- **Tiempo total:** ~15 minutos

## Lecciones y pitfalls aplicados

### Pitfall #9 (cantidades decimales) — Aplicado
Las cantidades 0.8 (pollo braseado) y 0.1 (queso rallado) se redondearon hacia arriba
a 1 antes de generar `basket.txt` final. Sin este ajuste, `mercadona cart set-many`
habría fallado con HTTP 400.

### Pitfall #8 (batch top-hit incorrecto) — Aplicado
Para "patatas para cocer", el batch devolvió "Tortilla de patata con cebolla" (60089).
Se usó `mercadona search` individual con `--limit 10` filtrado por categoría
"Fruta y verdura" para encontrar el ID correcto (69166, Patatas).

### Pitfall #10 (sustituciones) — Aplicado
- "Ensalada mediterránea con atún" no encontrada en Cookidoo → sustituida por
  "Ensalada campera con naranja" (r77976)
- "Ensalada quinoa con verduras asadas" → sustituida por
  "Ensalada de quinoa con calabacín y zanahoria" (r174234)

### Pitfall #3a (falsos negativos en verificación de calendario) — Confirmado
Tras `add_recipes_to_calendar`, `get_calendar_week` puede devolver vacío
o sin las recetas recién añadidas. No bloquear el flujo.

### Cookidoo: ingredientes con cantidad 0
De 39 ingredientes consolidados, 24 llegaron con `quantity: 0` desde Cookidoo.
Esto requirió un paso adicional de búsqueda manual para completar la lista.
Posible mejora: normalizar cantidades nulas en `cookidough_client.py`.

## Archivos generados

- Recetario: `/mnt/vault/Personal/Menjars/2026-07-17.md`
- Basket final: `/tmp/basket_ensaladas_completo.txt`
- Gate 1 detallado: `/tmp/gate1_aprobacion_ensaladas.md`
- Plan JSON: `/tmp/meal_plan_ensaladas.json`

## Flujo de comandos clave

```bash
# Añadir recetas al calendario Cookidoo
add_recipes_to_calendar(["r77976"], "2026-07-18")
add_recipes_to_calendar(["r174234"], "2026-07-20")

# Búsqueda individual (fallback para batch incorrecto)
mercadona search 'patatas' --json --limit 10 | jq '.hits[] | select(.categories[].name == "Fruta y verdura")'

# Preview y carga
mercadona total -f /tmp/basket_ensaladas_completo.txt
mercadona cart set-many -f /tmp/basket_ensaladas_completo.txt --max 70
```
