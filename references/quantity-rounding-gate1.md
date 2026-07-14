# Quantity Rounding & Gate 1 Validation Pattern

**Session:** 2026-07-15 (menú semanal ensaladas, 7 días, 36 productos)  
**Issue:** Decimal quantities in `basket.txt` caused HTTP 400 AFTER Gate 1 approval  
**Root cause:** Ingredient consolidation produced fractional quantities that Mercadona API rejects for unit-sold products

---

## Problem Description

### Timeline

1. **Gate 1 (Preview):** User approved shopping list with estimated total **73.62€**
2. **Cart addition attempt:** `mercadona cart set-many -f basket.txt --max 80` → HTTP 400
3. **Error message:** `"Invalid quantity 0.2 for a product sold by unit"`
4. **Manual correction:** Edited `basket.txt` to round decimals → retry with `--max 85` → HTTP 400 again
5. **Second correction:** Found MORE decimals (0.5, 1.5) → fixed all → retry with `--max 90` → **SUCCESS** (82.38€)

### Problematic Lines in basket.txt

```
69975 1.5  # Tomates pera          → should be 2
69990 0.5  # Tomates cherry        → should be 1
56652 0.8  # Pechuga pollo         → should be 1
53444 0.2  # Salmón ahumado        → should be 1
51110 0.2  # Queso mozzarella      → should be 1
51197 0.2  # Queso feta            → should be 1
```

### Why Gate 1 Didn't Catch This

Gate 1 used `mercadona total -f basket.txt`, which **estimates** totals without validating quantity constraints. The actual cart API (`cart set-many`) enforces stricter rules:

- Products sold by **unit** (selling_method=0, unit_selector=true) require **integer** quantities
- Fractional quantities work for **weight-based** products (tomates by kg) BUT Mercadona may have minimum increments

The preview passed because `mercadona total` doesn't call the cart API — it just multiplies unit_price × quantity.

---

## Root Cause Analysis

### Consolidation Phase

`ingredient_consolidation.md` prompt produced:

```json
{
  "name": "queso rallado mozzarella",
  "quantity": 0.2,
  "unit": "kg",
  "fresh": true
}
```

This maps to the **recipe's exact need** (200g), not the **vendible unit** (1 paquete de 200g).

### Wrapper Phase

`mercadona_cli_wrapper.py` → `generate_basket_file()` writes quantities as-is:

```python
f.write(f"{product_id} {item['quantity']}  # {name}\n")
```

No rounding or validation against `unit_size` or `selling_method`.

### API Phase

Mercadona cart API rejects:
- `51110` (queso mozzarella, unit_size=0.2kg, sold by unit) with qty=0.2 → wants qty=1 (1 package)
- `69990` (tomates cherry, unit_size=0.5kg, sold by unit) with qty=0.5 → wants qty=1 (1 bandeja)

---

## Solution: Three-Tier Defense

### 1. Consolidation (Preventive)

Update `prompts/ingredient_consolidation.md` to round quantities **UP** to the nearest vendible unit:

**Current (problematic):**
```json
{"name": "queso mozzarella", "quantity": 0.2, "unit": "kg"}
```

**Correct:**
```json
{"name": "queso mozzarella", "quantity": 1, "unit": "ud"}
```

**Heuristic:**
- Cheese, deli meats, packaged items → `unit: "ud"`, qty rounded up to nearest integer
- Fresh produce sold by weight (tomates, peppers) → `unit: "kg"`, qty rounded to 0.5kg or 1kg increments
- Query Mercadona API for `unit_size` if available and round accordingly

### 2. Basket Generation (Defensive)

Add validation in `mercadona_cli_wrapper.py` → `generate_basket_file()`:

```python
def generate_basket_file(self, resolved_items, output_path="/tmp/basket.txt"):
    with open(output_path, 'w') as f:
        f.write("# Basket generado por meal-to-cart\n\n")
        for item in resolved_items:
            product_id = item["id"]
            quantity = item["quantity"]
            
            # Validate: if product is sold by unit, quantity must be integer
            product_info = item.get("product_info", {})
            price_instructions = product_info.get("price_instructions", {})
            unit_selector = price_instructions.get("unit_selector", False)
            selling_method = price_instructions.get("selling_method", 0)
            
            if unit_selector and selling_method == 0:
                # Sold by discrete units
                if quantity != int(quantity):
                    original = quantity
                    quantity = max(1, int(math.ceil(quantity)))
                    print(f"⚠️ Rounded {item['name']} from {original} to {quantity} units")
            
            f.write(f"{product_id} {quantity}  # {item['name']}\n")
    return output_path
```

### 3. Pre-Cart Validation (Last Resort)

Before `fill_cart()`, scan `basket.txt` for decimal quantities:

```python
def validate_basket_quantities(basket_file):
    """Returns True if all quantities are integers, False otherwise."""
    with open(basket_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(None, 2)
            if len(parts) >= 2:
                try:
                    qty = float(parts[1])
                    if qty != int(qty):
                        return False
                except ValueError:
                    pass  # Skip malformed lines
    return True

# Usage in workflow:
basket_file = cli.generate_basket_file(resolved, "/tmp/basket.txt")
preview = cli.preview_total(basket_file)
print(f"Gate 1 preview: {preview['total']}€")

# → USER APPROVES

if not validate_basket_quantities(basket_file):
    print("⚠️ Ajustando cantidades decimales a paquetes completos...")
    basket_file = fix_decimal_quantities(basket_file)  # Round up
    preview_adjusted = cli.preview_total(basket_file)
    print(f"Total ajustado: {preview_adjusted['total']}€")
    
    # If total changed significantly, re-request approval
    if abs(float(preview['total']) - float(preview_adjusted['total'])) > 5.0:
        print("⚠️ El ajuste cambió el total en más de 5€. Solicitar re-aprobación.")
        # → Notify user via Telegram, wait for confirmation

result = cli.fill_cart(basket_file, max_eur=90, dry_run=False)
```

---

## Improved Gate 1 Pattern

Gate 1 should present:

1. **Exact basket.txt contents** (with quantities that will be sent to API)
2. **Preview total** from `mercadona total`
3. **Validation status**: "✅ All quantities valid" or "⚠️ Adjusted N items to whole packages"
4. **List of adjustments** if any (e.g., "Queso mozzarella: 0.2kg → 1 paquete (+0.8kg)")

**Template:**

```
📋 Gate 1 Preview — Mercadona Shopping List

🛒 36 productos — Total estimado: 73.62€

⚠️ Ajustes realizados:
• Queso mozzarella: 200g → 1 paquete (ajuste +0g, mismo precio)
• Salmón ahumado: 200g → 1 paquete 100g (ajuste -100g, -X.XX€)
• Tomates pera: 1.5kg → 2kg (ajuste +0.5kg, +X.XX€)
• Tomates cherry: 0.5kg → 1kg (ajuste +0.5kg, +X.XX€)

💰 Total ajustado: 82.38€

¿Aprobar y añadir al carrito?
```

If the user approved 73.62€ but the adjusted total is 82.38€ (+8.76€, >5€ threshold), require **re-approval**.

---

## Lessons

1. **Gate 1 ≠ API-ready.** `mercadona total` is an estimate; only `cart set-many` validates constraints.
2. **Decimal quantities are common** when consolidating recipes (0.2kg cheese, 1.5kg tomatoes).
3. **Rounding must happen BEFORE Gate 1**, not after user approval.
4. **Significant price changes** (>5€) after rounding warrant re-approval.
5. **Wrapper should enforce constraints** that the API will reject, so errors surface early.

---

## Code Changes Required

### File: `scripts/mercadona_cli_wrapper.py`

Add method:

```python
import math

def generate_basket_file(self, resolved_items, output_path="/tmp/basket.txt"):
    """Generate basket.txt with validated integer quantities for unit-sold products."""
    adjustments = []
    
    with open(output_path, 'w') as f:
        f.write("# Basket generado por meal-to-cart\n\n")
        for item in resolved_items:
            product_id = item["id"]
            quantity = item["quantity"]
            name = item.get("name", "Unknown")
            
            # Check if product requires integer quantity
            product_info = item.get("product_info", {})
            price_instructions = product_info.get("price_instructions", {})
            unit_selector = price_instructions.get("unit_selector", False)
            selling_method = price_instructions.get("selling_method", 0)
            
            if unit_selector and selling_method == 0:
                # Sold by discrete units — must be integer
                if quantity != int(quantity):
                    original = quantity
                    quantity = max(1, int(math.ceil(quantity)))
                    adjustments.append({
                        "name": name,
                        "original": original,
                        "adjusted": quantity
                    })
            
            f.write(f"{product_id} {quantity}  # {name}\n")
    
    if adjustments:
        print("⚠️ Cantidades ajustadas a paquetes completos:")
        for adj in adjustments:
            print(f"  • {adj['name']}: {adj['original']} → {adj['adjusted']}")
    
    return output_path, adjustments
```

Usage:

```python
basket_file, adjustments = cli.generate_basket_file(resolved["resolved"], "/tmp/basket.txt")

if adjustments:
    # Regenerate preview with adjusted quantities
    preview = cli.preview_total(basket_file)
    print(f"Total con ajustes: {preview['total']}€")
else:
    preview = cli.preview_total(basket_file)
    print(f"Total: {preview['total']}€")

# → Show preview to user (Gate 1)
```

---

## Testing

### Reproduce the Issue

```bash
# Create a basket with decimal quantities
cat > /tmp/test_basket.txt <<EOF
69975 1.5  # Tomates pera
51110 0.2  # Queso mozzarella
EOF

# Attempt to add to cart
mercadona cart set-many -f /tmp/test_basket.txt --max 10
# → HTTP 400: Invalid quantity 1.5 for a product sold by unit
```

### Verify the Fix

```python
from scripts.mercadona_cli_wrapper import MercadonaCLI

cli = MercadonaCLI()

# Shopping list with fractional quantities
shopping_list = [
    {"name": "tomates pera", "quantity": 1.5, "unit": "kg", "fresh": True},
    {"name": "queso mozzarella", "quantity": 0.2, "unit": "kg", "fresh": True}
]

resolved = cli.resolve_shopping_list(shopping_list)
basket_file, adjustments = cli.generate_basket_file(resolved["resolved"], "/tmp/basket_fixed.txt")

# Check adjustments
print(f"Adjustments made: {len(adjustments)}")
for adj in adjustments:
    print(f"  {adj['name']}: {adj['original']} → {adj['adjusted']}")

# Verify basket.txt has only integers
with open(basket_file, 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            parts = line.split(None, 2)
            qty = float(parts[1])
            assert qty == int(qty), f"Decimal quantity found: {line}"

print("✅ All quantities are integers")

# Add to cart (should succeed)
result = cli.fill_cart(basket_file, max_eur=20, dry_run=False)
print(f"✅ Cart updated: {result['products_count']} products, {result['summary']['total']}€")
```

---

## Related

- **Pitfall #2:** Productos unitarios requieren cantidad entera (original discovery)
- **Pitfall #6:** Bug conversión g→unidades (related but different — that was about unit conversion logic, this is about rounding)
- **Test 2 session (2026-07-15):** First occurrence of this issue in a multi-day menu workflow
- **Gate 1 approval pattern:** See `references/gate1-approval-pattern.md` for user-facing template

---

**Status:** Documented 2026-07-15  
**Next steps:** Implement rounding logic in `mercadona_cli_wrapper.py` → `generate_basket_file()`  
**Priority:** High (blocks automation, requires manual intervention post-approval)
