---
name: meal-to-cart
description: "Planifica menús semanales con Cookidoo (Thermomix) y Spoonacular (tradicional), genera recetario .md con foto y kcal por plato, y automatiza la compra en Mercadona Online."
version: 2.2.0
author: Hermes Agent
license: MIT
---

# Skill: Hermes Meal-to-Cart

Planifica menú semanal → sincroniza Cookidoo → genera recetario Markdown → llena carrito Mercadona.

---

## 🔴 Reglas obligatorias (no negociables)

### 1. Recetas Cookidoo → SIEMPRE al calendario "Mi semana"

Cada vez que uses una receta de Cookidoo en el menú, DEBES añadirla al calendario "Mi semana" del día planificado **ANTES** de procesar la shopping list de Mercadona. Sin esto, la receta no aparece en la Thermomix tras sincronizar.

```python
from scripts.cookidough_client import CookidoughClient
client = CookidoughClient()
recipe = client.get_recipe("r221200")
client.add_to_calendar([recipe["id"]], day="2026-07-20")  # ⚠️ OBLIGATORIO
# → sólo AHORA continuar con Mercadona
```

**Orden del flujo:**
1. Buscar/obtener receta Cookidoo
2. **Añadir al calendario** (`add_to_calendar`)
3. Extraer ingredientes → consolidar shopping list
4. Resolver Mercadona → Gate 1 preview → Gate 2 fill_cart

**Nota:** La verificación posterior con `get_calendar_week()` puede dar falso vacío (delay de API). Si `add_to_calendar()` no devuelve error, asumir éxito y continuar.

Detalle: `references/cookidoo-calendar-sync.md`.

### 2. Formato del recetario Markdown (spec v2.2)

El .md tiene **dos secciones únicamente**:

**Arriba** — cabecera + tabla resumen semanal (Día | Receta | Tiempo | kcal) + leyenda con media kcal/plato.

**Abajo** — recetas detalladas, una tras otra, cada una con:
- `### {emoji_fuente} {Día} {n} · {slot}: {título}`
- ![foto del plato](image_url) ← **siempre que haya `image_url`**
- Meta en una línea: `⏱️ **N min** · 👥 **N personas** · 🔥 **N kcal/ración** · ⭐ **N** · 🔗 [Fuente](url)`
- Blockquote con descripción breve (`> ...`)
- `### 🛒 Ingredientes` (lista)
- `### 👨‍🍳 Preparación (Thermomix)` si Cookidoo, sino `### 👨‍🍳 Preparación` (numerada)

**NO incluir en el .md:** lista de la compra consolidada, resumen del carrito Mercadona, notas de sustituciones, resúmenes nutricionales. Esas viven en el flujo Gate 1/Gate 2 de Telegram.

**Campos JSON obligatorios por receta:** `title`, `source`, `url`, `image_url`, `time_minutes`, `servings`, `calories_per_serving`, `ingredients[{name,amount,unit}]`, `steps[]` (sin numerar — el generador los enumera).

**Imagen `image_url`:**
- Cookidoo: `https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/{recipe_id}.jpg` (recipe_id sin `r`)
- Spoonacular: campo `image` de la API directamente

Spec completa: `prompts/recipe_format.md`. Ejemplos de imágenes: `references/recipe-image-urls.md`.

---

## Flujo end-to-end

```
1. Planificar menú (prompts/menu_planning.md) → JSON semanal
2. Añadir recetas Cookidoo al calendario "Mi semana"  ← Regla #1
3. Generar recetario .md (recipe_md_generator.py)      ← Regla #2
4. Consolidar shopping list (prompts/ingredient_consolidation.md)
   - Filtrar items con quantity ≤ 0 (despensa)
   - Redondear cantidades decimales a enteros
5. Resolver productos en Mercadona (mercadona_cli_wrapper)
6. Gate 1: preview total → mostrar a Xavi → esperar aprobación
7. Gate 2: fill_cart con --max presupuesto
```

---

## Setup

**Variables de entorno** (`~/.hermes/.env`):
```bash
COOKIDOUGH_EMAIL="…"
COOKIDOUGH_PASSWORD="…"
COOKIDOUGH_COUNTRY="es"        # ⚠️ default es "de"
COOKIDOUGH_LANGUAGE="es"       # ⚠️ default es "de"
SPOONACULAR_API_KEY="…"
RECIPE_OUTPUT_PATH="/mnt/vault/Personal/Menjars"
RECIPE_FILENAME_PATTERN="{date}.md"
```

**Comandos:**
```bash
npm install -g @ivorpad/mercadona    # Mercadona CLI (auth via import-curl, ~6 semanas)
```

Setups detallados: `references/cookidough_setup.md`, `references/spoonacular_setup.md`, `references/mercadona-cli-setup.md`.

---

## Scripts

```bash
# Generar .md
python3 scripts/recipe_md_generator.py --input menu.json [--output out.md] [--stdout]

# Mercadona
python3  # via wrapper Python
```

```python
from scripts.mercadona_cli_wrapper import MercadonaCLI
cli = MercadonaCLI()
resolved = cli.resolve_shopping_list(shopping_list)  # sólo items con qty>0
basket = cli.generate_basket_file(resolved["resolved"], "/tmp/basket.txt")
# ⚠️ Validar cantidades enteras aquí (ver Pitfall #1)
preview = cli.preview_total(basket)   # Gate 1
# → esperar aprobación de Xavi
cli.fill_cart(basket, max_eur=80.0)   # Gate 2
```

---

## Pitfalls críticos

**#1 · Cantidades decimales rompen Mercadona.** `mercadona cart set-many` devuelve HTTP 400 con `Invalid quantity X for a product sold by unit` si el basket tiene qty decimales (0.2, 1.5, etc). Redondear al entero superior ANTES de Gate 1 y mostrar el total ajustado. Si el ajuste cambia >5€, requiere re-aprobación.

**#2 · Filtrar ingredientes con `quantity: 0`.** Cookidoo devuelve qty=0 para ingredientes de despensa (aceite, sal). Filtrar `[i for i in shopping_list if i.get('quantity',0) > 0]` antes de `resolve_shopping_list()`, sino `mercadona total` falla con `invalid qty "0"`. Avisar de faltantes principales al usuario.

**#3 · Unidades correctas en shopping list.** Productos en pack/conserva/botella usan `unit: "ud"` con qty entera (1 lata, 1 botella). Sólo frescos vendidos por peso usan `"g"`/`"kg"`. NO usar `"g"` para aceite/leche/conservas → subtotales absurdos.

**#4 · Flag `--fresh` sin `--category` en batch.** El flag `--category` requiere ID numérico, no string → usar sólo `--fresh` (suficiente para verduras/proteínas). Si `batch --fresh` devuelve `id:null` para todos, fallback a `mercadona search '<query>' --json --limit 1` individual.

**#5 · Gate 1 es crítico.** El preview detecta sustituciones inesperadas (albahaca fresca → salsa pesto, pollo → pavo, etc.). Siempre mostrar preview a Xavi antes de tocar el carrito. Template en `references/gate1-approval-pattern.md`.

**#6 · Sustituciones conocidas** (Mercadona no siempre tiene el ingrediente exacto): `references/mercadona-product-substitutions.md`.

---

## Estructura del repo

```
meal-to-cart/
├── scripts/
│   ├── recipe_md_generator.py    # JSON → Markdown (regla #2)
│   ├── cookidough_client.py      # Cookidoo API + calendario (regla #1)
│   └── mercadona_cli_wrapper.py  # Mercadona API vía CLI
├── prompts/
│   ├── menu_planning.md
│   ├── ingredient_consolidation.md
│   └── recipe_format.md          # Spec del .md (regla #2)
├── references/                   # Setups, pitfalls, patrones detallados
└── SKILL.md
```

---

## Preferencias de Xavi

- Proyecto **personal, no open-source**. README sin secciones Contribuir/Soporte, sin rutas internas del vault. Ver `references/public-repo-guidelines.md`.
- Prefiere flujos end-to-end **con pruebas reales** antes de dar por terminado.
- **Gate 1 obligatorio** antes de tocar el carrito real.
