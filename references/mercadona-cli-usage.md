# mercadona-cli — Uso en meal-to-cart

Ejemplos prácticos del CLI para cada paso del flujo.

---

## Flujo completo

```bash
# 1. Búsqueda batch (ingredientes → productos)
printf 'tomate\ncebolla\narroz redondo\nsalmón\n' | \
  mercadona batch -f - --fresh --json > resolved.json

# 2. Generar basket.txt (con Python wrapper)
python3 scripts/mercadona_cli_wrapper.py --test-resolve resolved.json > basket.txt

# 3. Preview total (Gate 1 - mostrar a Xavier)
mercadona total -f basket.txt
# → total: 65.40€ (32 líneas)

# 4. Añadir al carrito (Gate 2 - tras confirmación)
mercadona cart set-many -f basket.txt --max 80
# → ✓ set-many: 32 cambios | carrito: 32 productos, total 65.40€

# 5. Verificar
mercadona cart get --json | jq '{count: .products_count, total: .summary.total}'
```

---

## Comandos clave

### Búsqueda batch

```bash
# Básico
printf 'tomate\ncebolla\npan\n' | mercadona batch -f -

# Con flag --fresh (excluye congelados/conservas)
printf 'salmón\ngambas\nmejillón\n' | mercadona batch -f - --fresh

# Con categoría específica
mercadona search "salmón" --category "Marisco y pescado" --limit 3

# JSON output (para scripting)
printf 'tomate\n' | mercadona batch -f - --fresh --json | \
  jq '.[0].hits[0] | {id, name: .display_name, price: .price_instructions.unit_price}'
```

**Output:**
```json
{
  "id": "69975",
  "name": "Tomates pera",
  "price": "2.11"
}
```

---

### Preview total

```bash
# Desde archivo basket.txt
mercadona total -f basket.txt

# Con JSON
mercadona total -f basket.txt --json | jq '{total, count}'
```

**Formato basket.txt:**
```text
# Comentarios permitidos
69975 2    # Tomates pera
69089 1    # Cebollas
5044  1    # Arroz redondo Hacendado
4740  1    # Aceite oliva (⚠️ cantidad entera, no 0.5)
```

---

### Añadir al carrito

```bash
# set-many: añade todo en 1 PUT
mercadona cart set-many -f basket.txt --max 80

# Spending guard: rechaza si total > max
mercadona cart set-many -f basket.txt --max 50
# → error: BUDGET EXCEEDED ... refusing (exit 1)
```

**Output:**
```
✓ set-many: 32 cambios  |  carrito: 32 productos, total 65.40€
```

---

### Leer/limpiar carrito

```bash
# Leer
mercadona cart get
mercadona cart get --json  # Para parsing

# Limpiar
mercadona cart clear
# → ✓ carrito vaciado (32 productos eliminados)
```

---

## Flags importantes

| Flag | Uso | Efecto |
|------|-----|--------|
| `--fresh` | `batch`, `search` | Excluye congelados (id 17) y conservas (id 14) |
| `--category <name\|id>` | `batch`, `search` | Filtra por sección (ej. "Marisco y pescado") |
| `--limit N` | `search` | Máximo N resultados (default 50) |
| `--max EUR` | `cart *`, `checkout *` | Spending guard (rechaza si total > límite) |
| `--json` | Todos | Output en JSON (para scripting) |
| `--wh <id>` | Todos | Override warehouse (default: config.toml) |

---

## Ejemplos por caso de uso

### 1. Buscar salmón FRESCO (no ahumado/congelado)

```bash
# Sin --fresh: devuelve ahumado
mercadona search "salmón" --limit 1
# → [53444] Salmón ahumado Hacendado

# Con --fresh + categoría: devuelve fresco
mercadona search "salmón" --fresh --category "Marisco y pescado" --limit 1
# → [81649.5] Salmón media pieza abierto en libro
```

### 2. Productos Hacendado (marca blanca)

```bash
# Buscar arroz Hacendado específicamente
mercadona search "arroz redondo hacendado" --limit 1
# → [5044] Arroz redondo Hacendado — 1.20€
```

### 3. Convertir gramos a cantidad de producto

```bash
# "400g salmón" en receta
# Salmón se vende por peso (€/kg)
# → cantidad = 400g / 1000 = 0.4
# basket.txt: "81649.5 0.4  # Salmón"

# "500ml aceite" en receta
# ⚠️ Aceite se vende por UNIDAD (botella)
# → cantidad = 1 (no 0.5)
# basket.txt: "4740 1  # Aceite oliva"
```

### 4. Batch de 50+ productos

```bash
# El CLI no tiene límite (a diferencia de Playwright que crashea a los 20)
# Puede procesar 100+ items en un solo batch
cat shopping_list_50items.txt | mercadona batch -f - --fresh --json
```

---

## Troubleshooting

### Producto no encontrado

```bash
# ❌ Muy genérico
mercadona search "carne"
# → [34157] Carne de pimiento (¡no es carne!)

# ✅ Más específico
mercadona search "pechuga pollo" --fresh
# → [10250] Pechuga de pollo fileteada
```

### Cantidad 0.5 no permitida

```bash
# Error: "Invalid quantity 0.5 for a product sold by unit"
# Causa: El producto es unitario (botella, pack)
# Solución: Usar cantidad entera (1, 2, ...)
```

### Total no coincide entre `total` y `cart get`

```bash
# Normal: el carrito backend es eventually consistent
# Reads pueden tardar 1-2s en reflejar writes

# Solución: Esperar 2s y releer
sleep 2 && mercadona cart get
```

Ver `mercadona-cli-setup.md` para más troubleshooting.
