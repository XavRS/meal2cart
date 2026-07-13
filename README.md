# meal2cart

> Skill de Hermes que planifica menús semanales (Cookidoo + Spoonacular),
> genera un recetario Markdown y automatiza la lista de la compra en
> Mercadona Online.

## Descripción

`meal2cart` integra tres servicios en un único flujo:

1. **Cookidoo** (recetas Thermomix) y **Spoonacular** (recetas
   tradicionales) vía sus respectivos servidores MCP.
2. **Recipe Markdown generator**: produce un `.md` con tabla semanal,
   recetas detalladas y lista de la compra consolidada.
3. **Mercadona Online**: cliente Playwright que busca y añade productos
   al carrito.

## Arquitectura

```
              ┌──────────────────────────────────────────┐
              │              Hermes (LLM)                  │
              │  prompts/menu_planning.md                  │
              │  prompts/ingredient_consolidation.md       │
              └────────────────┬───────────────────────────┘
                               │ orquesta
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
 ┌─────────────┐       ┌─────────────────┐       ┌──────────────┐
 │ cookidough- │       │ spoonacular-mcp │       │ scripts/     │
 │    mcp      │       │   (npx)         │       │ recipe_md_   │
 │   (uvx)     │       │                 │       │ generator.py │
 └──────┬──────┘       └────────┬────────┘       └──────┬───────┘
        │ recipes JSON           │ recipes JSON            │ menu .md
        └──────────┬─────────────┘                        │
                   ▼                                       │
        ┌────────────────┐                                  │
        │  JSON menú     │──┐                               │
        │  semanal       │  │ prompts/                     │
        └────────────────┘  │ ingredient_consolidation.md  │
                            ▼                              │
                  ┌─────────────────┐                      │
                  │   shopping_list │                      │
                  │  .json          │                      │
                  └────────┬────────┘                      │
                           ▼                               │
                  ┌─────────────────────────┐              │
                  │ scripts/mercadona_client │              │
                  │   .py  (async Playwright)│              │
                  └────────┬────────────────┘              │
                           ▼                                │
                  ┌─────────────────────────┐             │
                  │ tienda.mercadona.es carrito │            │
                  └─────────────────────────┘             │
                                                              │
                  <path_to_md_result>/semana_*.md ◀──┘
```

## Instalación

### Requisitos

- Python 3.11+
- Node.js 18+ (para `npx spoonacular-mcp`)
- `uv` / `uvx` (para `cookidough-mcp`) → <https://docs.astral.sh/uv/>
- Playwright Chromium: `pip install playwright && playwright install chromium`
- pytest (para tests)

### Pasos

```bash
git clone https://github.com/Xavier/meal2cart.git
cd meal2cart
pip install playwright
playwright install chromium
pip install pytest  # opcional, para tests

# Variables de entorno (renómbralo y completa)
cp .env.example .env
$EDITOR .env
source .env
```

Documentación específica:

- `references/spoonacular_setup.md` — cómo obtener API key
- `references/cookidough_setup.md` — cómo configurar cookidough-mcp
- `references/mercadona_selectors.md` — selectores verificados

## Uso

### 1. Planificar el menú

Pídele a Hermes (con este skill activo): *"Planifica el menú de esta
semana, mediterránea, 2 personas, sin gluten, 30 min máx."*

Hermes usará `prompts/menu_planning.md` y devolverá un JSON.

### 2. Generar el .md

```bash
python3 scripts/recipe_md_generator.py --input menu_semana.json \
    --output <path_to_md_result>/semana_13_julio.md
```

### 3. Consolidar ingredientes

Hermes aplicará `prompts/ingredient_consolidation.md` para reducir el
menú a `shopping_list.json`.

### 4. Añadir al carrito de Mercadona

```bash
python3 scripts/mercadona_client.py --add-from-file shopping_list.json
```

Para inspeccionar antes de comprar:

```bash
python3 scripts/mercadona_client.py --add-from-file shopping_list.json --dry-run --json
```

## Development

### Tests

```bash
pytest -q tests/
```

- `tests/test_mercadona_client.py` — utilidades y CLI (sin navegador).
  Mocks Playwright vía `monkeypatch`.
- `tests/test_recipe_generator.py` — formato Markdown, consolidación
  de ingredientes y categorización.

### Estructura

Ver **Estructura del proyecto** en `SKILL.md`.

### Añadir nuevos productos a la heurística de categorías

Edita las constantes `PROTEINAS / VERDURAS / DESPENSA` en
`scripts/recipe_md_generator.py`.

### Actualizar selectores de Mercadona

Si Mercadona cambia la SPA, actualiza los selectores en
`scripts/mercadona_client.py` (ver `references/mercadona_selectors.md`).

## Licencia

GPL-3.0, ver `LICENSE`.