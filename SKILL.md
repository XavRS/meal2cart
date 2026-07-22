---
name: meal-to-cart
description: "Planifica menús semanales con Cookidoo (Thermomix) y Spoonacular (tradicional), genera recetario .md con foto y kcal por plato, y automatiza la compra en Mercadona Online. Usa subagentes para procesamiento pesado (generación .md, resolución Mercadona, fill_cart)."
version: 3.0.0
---

# Meal-to-Cart — Orquestador con subagentes

Planifica menú semanal → sincroniza Cookidoo → **delega proceso pesado a subagentes** → gates con Xavi → carrito Mercadona.

## Arquitectura

```
Hermes (orquestador)
  ├── Fase 1: Planificar menú (interactivo con Xavi, MCP Cookidoo + Spoonacular)
  ├── Fase 2: Sync Cookidoo calendar (MCP directo)
  ├── Fase 3: Subagente A → generar .md + shopping list
  ├── Fase 4: Subagente B → resolver Mercadona + basket preview
  ├── Gate 1: Preview → Xavi revisa → OK
  └── Fase 5: Subagente C → fill_cart
```

**Por qué subagentes**: el flujo E2E requiere cargar ~10K tokens de contexto (scripts, referencias, reglas). Los subagentes aíslan cada fase — Hermes solo ve el resultado final.

---

## 🔴 Reglas obligatorias (no negociables)

### 1. Recetas Cookidoo → SIEMPRE al calendario ANTES de Mercadona

Cada receta Cookidoo debe añadirse al calendario "Mi semana" usando las tools MCP `mcp__cookidough__add_recipes_to_calendar` **antes** de procesar la shopping list.

```
Orden:
1. Buscar receta (mcp__cookidough__search_recipes)
2. Añadir al calendario (mcp__cookidough__add_recipes_to_calendar)
3. Generar menu.json
4. Delegar a subagentes
```

### 2. Cantidades enteras en Mercadona

`mercadona cart set-many` devuelve HTTP 400 con qty decimales. Usar SIEMPRE enteros en el basket. Productos que en `product info` muestran `ref=kg` pueden rechazar decimales (se venden por bandeja, no por peso). Ver `references/cart-quantity-rules.md`.

### 3. Gate 1 es crítico

El preview detecta sustituciones inesperadas. Siempre mostrar preview a Xavi antes de tocar el carrito. Ver `references/gate1-approval-pattern.md`.

### 4. Filtrar ingredientes con quantity ≤ 0

Cookidoo devuelve qty=0 para ingredientes de despensa. Filtrarlos antes de `resolve_shopping_list()`.

---

## Fase 1 — Planificar menú (Hermes interactivo)

1. Preguntar a Xavi: `week_start`, comensales, preferencias, split TM/tradicional
2. Buscar recetas Cookidoo con `mcp__cookidough__search_recipes`
3. Buscar recetas Spoonacular con API (curl)
4. Presentar tabla resumen:

| Día | Cena | Fuente | Tiempo | kcal |
|-----|------|--------|--------|------|

5. Xavi confirma → producir `menu.json`

**Formato `menu.json`**:
```json
{
  "week_start": "2026-07-20",
  "preferences": "2 personas | Mediterránea | 30 min",
  "meals": {
    "Lunes": {"cena": {"title": "...", "source": "cookidoo", "url": "...", "time_minutes": 25, "servings": 2, "calories_per_serving": 480, "ingredients": [{"name": "...", "amount": 400, "unit": "g"}], "steps": ["..."]}},
    "...": {}
  }
}
```

---

## Fase 2 — Sync Cookidoo calendar (Hermes, MCP directo)

```python
# Para cada receta con source=cookidoo en el menu.json:
mcp__cookidough__add_recipes_to_calendar(day="2026-07-20", recipe_ids=["r715538"])
```

No delegar — las tools MCP solo están disponibles para Hermes.

---

## Fase 3 — Subagente A: generate

**Disparador**: menu.json listo + Cookidoo synceado.

**Delegar con**:
```
delegate_task(
  goal="Generar recetario .md y shopping list consolidada a partir de menu.json",
  context="menu.json en {path}. Usa recipe_md_generator.py en {skill_dir}/scripts/. Escribe el .md en {output_path}. Devuelve también la shopping list consolidada como JSON."
)
```

**Prompt detallado**: `prompts/subagent-generate.md`

El subagente:
1. Ejecuta `python3 scripts/recipe_md_generator.py --input {menu_json} --output {out_md}`
2. Extrae la shopping list consolidada del .md generado
3. Filtra ingredientes con qty ≤ 0
4. Devuelve: path del .md, shopping list JSON, kcal totales

---

## Fase 4 — Subagente B: resolve

**Disparador**: Subagente A completado.

**Delegar con**:
```
delegate_task(
  goal="Resolver shopping list en Mercadona y generar basket con preview",
  context="Shopping list: {json}. Usa mercadona_cli_wrapper.py en {skill_dir}/scripts/. Warehouse 4182. Genera basket en /tmp/basket.txt. Devuelve preview total."
)
```

**Prompt detallado**: `prompts/subagent-resolve.md`

El subagente:
1. Recibe shopping list JSON (de Subagente A)
2. Ejecuta `MercadonaCLI(warehouse="4182").resolve_shopping_list(shopping_list)`
3. Revisa batch results por mismatches conocidos (patata→fritas, albahaca→pesto). Usa `mercadona search` individual para corregir.
4. Genera basket con `generate_basket_file()`
5. Ejecuta `preview_total()`
6. Ajusta cantidades a enteros (Pitfall #1)
7. Devuelve: basket path, preview (productos, subtotales, total), unresolved

---

## Gate 1 — Preview (Hermes ↔ Xavi)

Mostrar a Xavi:
- Productos resueltos (nombre Mercadona, qty, precio unitario, subtotal)
- Productos no resueltos (si los hay)
- **Total exacto**
- Sustituciones sospechosas marcadas

Esperar OK explícito antes de continuar. Si cambios >10€ por ajuste a enteros → re-aprobación.

---

## Fase 5 — Subagente C: fill

**Disparador**: Gate 1 aprobado.

**Delegar con**:
```
delegate_task(
  goal="Ejecutar fill_cart en Mercadona",
  context="Basket en {basket_path}. max_eur={total_aprobado}. Usa MercadonaCLI en {skill_dir}/scripts/mercadona_cli_wrapper.py."
)
```

**Prompt detallado**: `prompts/subagent-fill.md`

---

## Setup

**Variables de entorno** (`~/.hermes/.env`):
```bash
COOKIDOUGH_EMAIL="…"
COOKIDOUGH_PASSWORD="…"
COOKIDOUGH_COUNTRY="es"
COOKIDOUGH_LANGUAGE="es"
SPOONACULAR_API_KEY="…"
```

**Mercadona CLI**:
```bash
npm install -g @ivorpad/mercadona
```

**Scripts** (en `{skill_dir}/scripts/`):
- `recipe_md_generator.py` — menu.json → .md + shopping list
- `mercadona_cli_wrapper.py` — wrapper Python del CLI Mercadona

---

## Pitfalls críticos

1. **Cantidades decimales rompen Mercadona** → ajustar a enteros antes del basket. Ver `references/cart-quantity-rules.md`.
2. **Filtrar qty ≤ 0** → ingredientes de despensa (aceite, sal) vienen con qty=0 de Cookidoo.
3. **`batch --fresh` da falsos positivos** → patata→fritas, albahaca→pesto. Corregir con `mercadona search` individual. Ver `references/product-search-mismatches.md`.
4. **Sustituciones conocidas** → Mercadona no siempre tiene el ingrediente exacto. Ver `references/mercadona-product-substitutions.md`.
5. **Gate 1 obligatorio** → preview antes de tocar carrito real. Ver `references/gate1-approval-pattern.md`.
6. **MCP solo en Hermes** → los subagentes NO tienen acceso a `mcp__cookidough__*`. El sync de calendario lo hace Hermes.

---

## Preferencias de Xavi

- Proyecto personal, no open-source.
- Flujos end-to-end con pruebas reales.
- Gate 1 obligatorio antes de tocar el carrito.
- Warehouse Mercadona: **4182**.
