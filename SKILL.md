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

## Prerequisitos

- Python 3.11+
- Playwright + Chromium: `pip install playwright && playwright install chromium`
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
export COOKIDOO_EMAIL="…"
export COOKIDOO_PASSWORD="…"
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
| `--cp`         | Override del código postal                 |
| `--cookie-file`| Ruta del fichero de cookies                |

## Estructura del proyecto

```
meal2cart/
├── scripts/
│   ├── mercadona_client.py       # Playwright CLI
│   └── recipe_md_generator.py    # JSON → Markdown
├── prompts/
│   ├── menu_planning.md
│   ├── ingredient_consolidation.md
│   └── recipe_format.md
├── references/
│   ├── spoonacular_setup.md
│   ├── cookidough_setup.md
│   └── mercadona_selectors.md
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
| `Playwright no está instalado` | Falta el paquete o el navegador | `pip install playwright && playwright install chromium` |
| Mercadona no avanza tras CP | Cookie stale o captcha | Borra `/tmp/mercadona_cookies.json` y reintenta con `--headed` |
| `Login wall detected` | Mercadona pide inicio de sesión | Inicia sesión manualmente (mod headed) y vuelve a ejecutar |
| Spoonacular 401/402 | API key inválida o cuota agotada | Ver `references/spoonacular_setup.md` |
| cookidough 403 | Cookies caducadas | Borra `~/.hermes/data/cookidough_cookies.json` y re-logín |
| Markdown vacío | JSON de entrada mal formado | Verifica `week_start` y `meals.*.{comida,cena}` |
| Productos no encontrados en Mercadona | Nombre no normalizado | Edita `prompts/ingredient_consolidation.md` y reintenta |

## Development

- Tests: `pytest -q tests/`
- Los tests NO abren navegador (mockean Playwright vía monkeypatch).
- Para activar formato de logs, usa `LOG_LEVEL=DEBUG` (no implementado
  pero reservado en `mercadona_client.log` para futura mejora).

## Licencia

GPL-3.0 (ver `LICENSE`).