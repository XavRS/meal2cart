---
name: meal-to-cart
description: "Planifica menús semanales con Cookidoo (Thermomix) y Spoonacular (tradicional), genera recetario .md y automatiza la compra en Mercadona Online."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Skill: Hermes Meal-to-Cart

Planifica menús semanales combinando **Cookidoo** (Thermomix) y
**Spoonacular** (cocina tradicional), genera un recetario Markdown y
automatiza la lista de la compra en **Mercadona Online**.

## Qué hace

1. **Planifica la semana** en función de tus preferencias (dieta, nº de
   comensales, tiempo máximo, alergias) usando recetas reales de los dos
   MCP servers.
2. **Produce un fichero Markdown** con la tabla semanal, las recetas
   detalladas (ingredientes + pasos) y la lista de la compra consolidada.
3. **Abre Mercadona Online** con Playwright y añade automáticamente
   todos los productos al carrito.

## Configuración

Variables de entorno (en `~/.hermes/.env`):

```bash
# Path donde se guardan los recetarios .md
RECIPE_OUTPUT_PATH=/mnt/vault/Personal/Menjars

# Patrón del nombre de archivo ({date} = YYYY-MM-DD)
RECIPE_FILENAME_PATTERN={date}.md
```

O por flag: `--output /ruta/personalizada.md`

## Prerequisitos

- Python 3.11+
- Playwright + Chromium: `pip install --break-system-packages playwright && python3 -m playwright install chromium` (en Debian/PEP 668 usar `--break-system-packages` o virtualenv)
- Cuenta Cookidoo activa (si vas a usar Thermomix) → ver
  `references/cookidough_setup.md`.
- API key de Spoonacular (free tier 150 req/día) → ver
  `references/spoonacular_setup.md`.
- `uvx` (para `cookidough-mcp`) → <https://docs.astral.sh/uv/>.
- `npx`/Node 18+ (para `spoonacular-mcp`).
- Navegador con cookie de sesión Mercadona configurada para tu CP
  (ej. `08001`). La primera vez el script pedirá el CP; el estado
  se guarda en `/tmp/mercadona_cookies.json`.

## Configuración

### 1. Variables de entorno

```bash
export COOKIDOUGH_EMAIL="…"
export COOKIDOUGH_PASSWORD="…"
export COOKIDOUGH_COUNTRY="es"                 # ⚠️ REQUERIDO. Default es "de"
export COOKIDOUGH_LANGUAGE="es"                # ⚠️ REQUERIDO. Default es "de"
export SPOONACULAR_API_KEY="…"
export MERCADONA_CP="08001"                    # opcional, default 08001
export RECIPE_OUTPUT_PATH="/mnt/vault/Personal/Menjars"
export RECIPE_FILENAME_PATTERN="{date}.md"
```

### 2. `config.yaml` de Hermes

Copia `config.yaml.example` a `~/.hermes/config.yaml` (o donde Hermes
espere leer). El fichero referencía las APIS y la salida de los .md.

### 3. Permisos / primera ejecución

- Borrar `/tmp/mercadona_cookies.json` la primera vez si hay comportamientos raros.
- Ejecutar una vez con `--headed` para resolver captcha/login manualmente:

  ```bash
  python3 scripts/mercadona_client.py --search "leche" --headed
  ```

## Uso

### Planificar el menú

Hermes (con el prompt `prompts/menu_planning.md`) generará un JSON de
menú semanal conforme al esquema descrito en `prompts/recipe_format.md`.

Si los MCPs no están disponibles como herramientas nativas de Hermes,
usa `subprocess.Popen` o pipes para llamarlos vía JSON-RPC sobre stdio.
Ver **`references/cookidough-mcp-usage.md`** para el protocolo exacto,
el manejo de stdin, y los quirks conocidos.

### Sincronizar con Cookidoo ("Mi semana")

Una vez generado el menú, las recetas de Cookidoo pueden añadirse al
calendario de la Thermomix con `add_recipes_to_calendar`. Ver
**`references/cookidoo-calendar-sync.md`** para el flujo completo y
ejemplos de código.

### Generar el Markdown de recetas

```bash
python3 scripts/recipe_md_generator.py --input menu_semana.json \
    --output /mnt/vault/Personal/Menjars/semana_13_julio.md
```

Sin `--output`, se usan `RECIPE_OUTPUT_PATH` y `RECIPE_FILENAME_PATTERN`.
Con `--stdout`, se imprime sin escribir archivo (útil para verificación).

### Consolidar ingredientes

Hermes aplica el prompt `prompts/ingredient_consolidation.md` para
reducir el JSON de menú a una lista de la compra en
`{ "shopping_list": [ … ] }` que se pasa a Mercadona.

### Añadir todo al carrito de Mercadona

```bash
# Dry-run (sólo busca)
python3 scripts/mercadona_client.py --list "leche, pan, huevos" --dry-run --json

# Añade la lista de un fichero JSON
python3 scripts/mercadona_client.py --add-from-file shopping_list.json

# Añade coma-separada
python3 scripts/mercadona_client.py --add "tomate, cebolla, pan"

# Buscar un único producto y mostrar JSON
python3 scripts/mercadona_client.py --search "leche semidesnatada" --json
```

Flags útiles:

| Flag           | Descripción                                |
|----------------|--------------------------------------------|
| `--search`     | Busca un producto y devuelve JSON          |
| `--add`        | Lista separada por comas a añadir al carrito |
| `--add-from-file` | Lee lista JSON/TXT (ver formato en script) |
| `--list`       | Igual que --add pero compatible con --dry-run |
| `--dry-run`    | Sólo busca los productos, no añade al carrito |
| `--json`       | Salida en JSON (para scripting)            |
| `--headed`     | Mostrar navegador (no headless)            |
| `--login`      | Forzar inicio de sesión (usa credenciales `MERCADONA_EMAIL`/`MERCADONA_PASSWORD`, o manual con `--headed`) |
| `--cp`         | Override del código postal                 |
| `--cookie-file`| Ruta del fichero de cookies                |

## Estructura del proyecto

```
meal2cart/
├── scripts/
│   ├── mercadona_client.py       # Playwright CLI
│   ├── recipe_md_generator.py    # JSON → Markdown
│   └── cookidough_client.py      # Cliente Python para cookidough MCP
├── prompts/
│   ├── menu_planning.md
│   ├── ingredient_consolidation.md
│   └── recipe_format.md
├── references/
│   ├── spoonacular_setup.md
│   ├── cookidough_setup.md
│   ├── cookidough-mcp-usage.md    # Guía de uso programático del MCP
│   ├── cookidoo-calendar-sync.md  # Sincronización con "Mi semana"
│   ├── mcp-setup-lessons.md       # Lecciones de instalación de MCPs
│   ├── mercadona_selectors.md
│   └── mercadona-quirks.md        # Modal login, PEP 668, cookies
├── tests/
│   ├── test_mercadona_client.py
│   └── test_recipe_generator.py
├── config.yaml.example
├── SKILL.md
└── README.md
```

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `Playwright no está instalado` | Falta el paquete o el navegador | `pip install --break-system-packages playwright && python3 -m playwright install chromium` |
| Mercadona no avanza tras CP | Cookie stale o captcha | Borra `/tmp/mercadona_cookies.json` y reintenta con `--headed` |
| `Login wall detected` | Mercadona pide inicio de sesión | El script ahora cierra el modal automáticamente (ver `references/mercadona-quirks.md`). Si persiste, inicia sesión manualmente con `--headed` |
| Modal "¿Ya tienes cuenta?" bloquea clicks | Modal de registro intercepta eventos | El script tiene `_dismiss_login_modal()` con 4 estrategias. Ver `references/mercadona-quirks.md` |
| Spoonacular 401/402 | API key inválida o cuota agotada | Ver `references/spoonacular_setup.md`. La key actual (`SPOONACULAR_API_KEY`) puede requerir regeneración en https://spoonacular.com/food-api/console |
| cookidough 403 | Cookies caducadas | Borra `~/.hermes/data/cookidough_cookies.json` y re-logín |
| `cookidough_client.py` no autentica (403 silencioso) | El script usa `COOKIDOO_*` en vez de `COOKIDOUGH_*` (typo heredado) | Verifica que `scripts/cookidough_client.py` lee `COOKIDOUGH_PASSWORD` y `COOKIDOUGH_COUNTRY` (no `COOKIDOO_*`). Corregido en versión ≥ post-2026-07-13 |
| Markdown vacío | JSON de entrada mal formado | Verifica `week_start` y `meals.*.{comida,cena}` |
| Productos no encontrados en Mercadona | Nombre no normalizado | Edita `prompts/ingredient_consolidation.md` y reintenta |
| MCP `-32602 Invalid request parameters` | Método incorrecto — se usó `method: "search_recipes"` en vez de `method: "tools/call"` | Usa siempre `method: "tools/call"` con `params.name`. Ver `references/cookidough-mcp-usage.md` |
| MCP no responde tras enviar comandos | stdin se cierra antes de que el servidor procese | Mantén stdin abierto con `sleep N` o usa `subprocess.Popen`. Ver `references/cookidough-mcp-usage.md` |
| `get_recipe_details` no devuelve pasos | El endpoint de Cookidoo no incluye `steps` en la respuesta | Escribe los pasos manualmente o consulta la URL de la receta. Ver `references/cookidough-mcp-usage.md` |
| Resultados de Cookidoo en alemán | `COOKIDOUGH_COUNTRY` y `COOKIDOUGH_LANGUAGE` no están configurados (default ambos `\"de\"`) | Establecer `COOKIDOUGH_COUNTRY=es` y `COOKIDOUGH_LANGUAGE=es`. Borrar cookies viejas (`rm ~/.hermes/data/cookidough_cookies.json`) y re-logín. Ver `references/cookidough_setup.md` |

## Development

- Tests: `pytest -q tests/`
- Los tests NO abren navegador (mockean Playwright vía monkeypatch).
- **⚠️ No mockear `asyncio.run` directamente** en tests — produce
  "coroutine was never awaited". Mockea la clase cliente en su lugar.
  Ver `references/testing-patterns.md`.
- Para activar formato de logs, usa `LOG_LEVEL=DEBUG` (no implementado
  pero reservado en `mercadona_client.log` para futura mejora).

## Licencia

GPL-3.0 (ver `LICENSE`).