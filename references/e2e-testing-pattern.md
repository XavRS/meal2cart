# End-to-End Testing Pattern — meal-to-cart

**Patrón validado:** 2026-07-14  
**Contexto:** Test completo Cookidoo → Mercadona carrito REAL

---

## Por qué E2E es crítico aquí

Los tests unitarios con mocks NO detectan:
- Categorías incorrectas (`"Verdura"` vs `"Fruta y verdura"`)
- Bugs de conversión unidades (150g → 150 unidades → 285€)
- Sustituciones inesperadas por matching ambiguo (albahaca → pesto)
- Desajustes entre estimación y precio real

**Lección 2026-07-14:** El test e2e con carrito REAL es el gate definitivo para validar integraciones. Reveló 2 bugs críticos que tests unitarios habrían pasado.

---

## Patrón de ejecución

### 1. Buscar receta real (Cookidoo o Spoonacular)

```python
from cookidough_client import CookidoughClient

client = CookidoughClient()
recipes = client.search("ensalada", limit=5)
recipe = client.get_recipe(recipes[0]['id'])
```

### 2. Extraer ingredientes → shopping list

Manual o vía LLM (ingredient_consolidation.md):

```python
shopping_list = [
    {"name": "tomate", "quantity": 6, "unit": "ud", "fresh": True, "category": None},
    # ... más items
]
```

⚠️ **Lección:** Usar `unit: "ud"` para productos pack (aceite, conservas, pasta) evita bugs de conversión.

### 3. Resolver productos en Mercadona

```python
from mercadona_cli_wrapper import MercadonaCLI

cli = MercadonaCLI()
result = cli.resolve_shopping_list(shopping_list)

print(f"Resueltos: {len(result['resolved'])}/{len(shopping_list)}")
print(f"Total: {result['total']}€")
```

**Verificar:**
- ✅ 100% productos resueltos (o identificar no-encontrados)
- ✅ Total razonable (no 285€ por una lata de aceitunas)

### 4. Preview (Gate 1)

```python
basket_file = cli.generate_basket_file(result['resolved'], '/tmp/basket.txt')
preview = cli.preview_total(basket_file)
print(f"Preview: {preview['total']}€ ({preview['count']} productos)")
```

**CRÍTICO:** Revisar manualmente productos antes de añadir al carrito. Detectar:
- Sustituciones inesperadas (albahaca fresca → salsa pesto)
- Productos incorrectos (tomate frito en vez de tomate fresco)
- Cantidades absurdas

### 5. Añadir al carrito REAL (Gate 2)

Tras aprobación manual:

```python
result = cli.fill_cart(basket_file, max_eur=100.0, dry_run=False)
print(f"✓ Añadidos: {result['products_count']} productos")
print(f"Total real: {result['summary']['total']}€")
```

### 6. Verificar coincidencia

```python
cart = cli.get_cart()
assert cart['summary']['total'] == preview['total'], "Desajuste estimación vs real"
```

**Lección 2026-07-14:** mercadona-cli preview coincide 100% con total real. Fiable para presupuestos.

### 7. Limpiar

```python
cli.clear_cart()
```

---

## Métricas esperadas (baseline 2026-07-14)

**Test:** Ensalada italiana pasta pesto (Cookidoo r221200, 9 ingredientes)

| Métrica | Valor | Estado |
|---------|-------|--------|
| Productos resueltos | 9/9 (100%) | ✅ |
| Total estimado | 20.95€ | ✅ |
| Total real | 20.95€ | ✅ Coincidencia 100% |
| Tiempo | ~2 min | ✅ |
| Errores | 0 | ✅ |

**Umbral de calidad:** 
- ≥ 90% productos resueltos
- Coincidencia estimado/real ≥ 95%
- Tiempo < 5 min

---

## Señales de regresión

❌ **Falla el test si:**
- Productos resueltos < 90%
- Subtotal absurdo (> 10× precio esperado producto individual)
- Desajuste estimado/real > 5%
- Crash durante fill_cart

🟡 **Advertencia si:**
- Sustituciones > 2 (ej: albahaca → pesto)
- Productos no-encontrados > 1
- Tiempo > 3 min

---

## Cuándo ejecutar

**Obligatorio:**
- Tras cambios en `mercadona_cli_wrapper.py`
- Tras updates en `ingredient_consolidation.md`
- Antes de release nueva versión skill

**Recomendado:**
- Semanalmente (detectar cambios API Mercadona)
- Tras updates mercadona-cli (npm)

---

## Automatización (futuro)

```bash
# Cron job semanal con reporte Telegram
0 9 * * 1 cd ~/.hermes/skills/meal-to-cart && \
  PYTHONPATH=scripts python3 tests/test_e2e_mercadona_cli.py && \
  hermes notify "✅ E2E test meal-to-cart: PASS" || \
  hermes notify "❌ E2E test meal-to-cart: FAIL - revisar logs"
```

---

## Lecciones clave

1. **Gate 1 (preview) es crítico** — detecta sustituciones/errores antes de commit
2. **Flag `--fresh` suficiente** — no usar `--category` (evita errores ID numérico)
3. **Conversión g→ud evita bugs** — productos pack (conservas, aceite) usar unidades
4. **Preview = Real** — mercadona-cli 100% fiable para estimaciones presupuesto

---

**Patrón validado con carrito REAL:** 2026-07-14  
**Test de referencia:** `/mnt/vault/Personal/Hermes/meal-to-cart/2026-07-14_TEST_ENSALADA_COMPLETADO.md`
