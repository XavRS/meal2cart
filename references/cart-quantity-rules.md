# Reglas de cantidades para Mercadona cart set-many

El comando `mercadona cart set-many` es más estricto que `mercadona total` con las cantidades.
Productos que parecen venderse por peso (`ref=kg`) pueden ser rechazados con decimales.

## Productos que requieren cantidades enteras

**Regla general: usar SIEMPRE cantidades enteras en el basket.** El ahorro de ajustar
0.4 kg vs 1 bandeja no compensa el riesgo de HTTP 400.

### Carnes (bandeja, no peso)

| Producto | ID | ref en product info | Realidad cart API |
|----------|----|--------------------|--------------------|
| Contramuslos pollo deshuesados | 2789 | kg | vendido por bandeja (qty=1) |
| Filetes pechuga pollo corte fino | 3400 | kg | vendido por bandeja (qty=1) |

> **Regla:** para carnes frescas en Mercadona, qty=1 representa una bandeja (~400-500g).
> No intentar qty=0.4 para "400 gramos".

### Productos que SÍ aceptan decimales

Solo se ha verificado que estos funcionan (pueden aceptar decimales pero no se recomienda):
- Productos con `ref=kg` y `bulk_price` muy inferior a `unit_price` (indica venta por peso real)
- La mayoría de frutas y verduras a granel

### Productos que necesitan verificación

| Producto | ID | ref | ¿Acepta decimal? |
|----------|----|-----|-------------------|
| Pimiento rojo | 69310 | kg | ❓ No verificado |
| Tomates cherry | 69990 | kg | ❓ No verificado |
| Cebollas | 69089 | kg | ❓ No verificado |
| Zanahorias | 69586 | kg | ❓ No verificado |
| Limón | 3210 | kg | ❓ No verificado |

## Workflow seguro

1. **Construir basket siempre con qty enteras** para todos los productos.
2. Para productos por peso (carne), qty=1 = 1 bandeja/pack, no 1 kg.
3. Ejecutar `mercadona total -f basket.txt --json` para estimar.
4. Si `total` devuelve `complete: true`, proceder con `cart set-many`.
5. Si `cart set-many` falla con "Invalid quantity", el producto ofensor está en el mensaje
   de error (no dice cuál) — probar quitando productos uno a uno o usar `mercadona product <id>`
   para inspeccionar.

## Comando de diagnóstico

```bash
# Inspeccionar un producto para ver ref, bulk_price, is_pack
mercadona product <id> --json --wh 4182 | python3 -c "
import sys, json
d = json.load(sys.stdin)
pi = d['price_instructions']
print(f'{d[\"display_name\"]}')
print(f'  ref={pi[\"reference_format\"]}  pack={pi.get(\"is_pack\")}  bulk={pi.get(\"is_bulk\")}')
print(f'  unit_price={pi[\"unit_price\"]}  bulk_price={pi.get(\"bulk_price\")}')
"
```

> **Actualizado:** 2026-07-14 — sesión menú cenas verano (20-26 julio)
