---
name: meal-to-cart
description: "Planifica menús semanales con Cookidoo (Thermomix) y Spoonacular (tradicional), genera recetario .md y automatiza la compra en Mercadona Online."
version: 2.0.0
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
3. **Añade al carrito de Mercadona** vía **`mercadona-cli`** (HTTP directo a API REST).
   **✅ Migración completada 2026-07-14:** Wrapper Python operativo, test end-to-end 100% exitoso,
   40× más rápido que Playwright. Ver `references/cli-wrapper-pattern.md` para el patrón de diseño.

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
- **`mercadona-cli`** (⚠️ principal para carrito): `npm install -g @ivorpad/mercadona`.
  Sustituye el enfoque Playwright para añadir productos al carrito.
  Ver `references/mercadona-cli.md` para setup de auth (Google SSO → HAR import).
- Playwright + Chromium (solo como fallback para scraping si la API no cubre algo):
  `pip install --break-system-packages playwright && python3 -m playwright install chromium`
- Cuenta Cookidoo activa (si vas a usar Thermomix) → ver
  `references/cookidough_setup.md`.
- API key de Spoonacular (free tier 150 req/día) → ver
  `references/spoonacular_setup.md`.
- `uvx` (para `cookidough-mcp`) → <https://docs.astral.sh/uv/>.
- `npx`/Node 18+ (para `spoonacular-mcp`).
- Node 18+ (para `mercadona-cli` vía npm).

## Configuración

### 1. Variables de entorno

```bash
export COOKIDOUGH_EMAIL="…"
export COOKIDOUGH_PASSWORD="…"
export COOKIDOUGH_COUNTRY="es"                 # ⚠️ REQUERIDO. Default es "de"
export COOKIDOUGH_LANGUAGE="es"                # ⚠️ REQUERIDO. Default es "de"
export SPOONACULAR_API_KEY="…"
export MERCADONA_CP="08001"                    # opcional, default 08001
export MERCADONA_EMAIL="…"                    # opcional, para login automático
export MERCADONA_PASSWORD="…"                 # opcional, para login automático
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

- Para login automático, define `MERCADONA_EMAIL` + `MERCADONA_PASSWORD` y usa `--login`.
  Si usas Google SSO, haz login manual con `--login --headed` (las cookies se persisten).
  Ver `references/mercadona-quirks.md`.

## Uso

### Planificar el menú

Hermes (con el prompt `prompts/menu_planning.md`) generará un JSON de
menú semanal conforme al esquema descrito en `prompts/recipe_format.md`.

Si los MCPs no están disponibles como herramientas nativas de Hermes,
usa `subprocess.Popen` o pipes para llamarlos vía JSON-RPC sobre stdio.
Ver **`references/cookidough-mcp-usage.md`** para el protocolo exacto,
el manejo de stdin, y los quirks conocidos.

### Sincronizar con Cookidoo ("Mi semana") ⚠️ OBLIGATORIO

**⚠️ REGLA:** Siempre que uses una receta de Cookidoo, DEBES añadirla al calendario "Mi semana" del día planificado.

Las recetas de Cookidoo deben añadirse al calendario de la Thermomix con `add_to_calendar()` para que aparezcan automáticamente en el dispositivo tras sincronizar.

**Flujo obligatorio:**
```python
from scripts.cookidough_client import CookidoughClient
from datetime import date

client = CookidoughClient()

# 1. Buscar/obtener receta
recipe = client.get_recipe("r221200")

# 2. SIEMPRE añadir al calendario del día planificado
day = date.today().isoformat()  # O el día específico del menú
client.add_to_calendar([recipe["id"]], day)

# 3. Continuar con shopping list → Mercadona
# ...

client.close()
```

**Métodos disponibles:**
- `add_to_calendar(recipe_ids, day)` — Añadir una o varias recetas a un día
- `get_calendar_week(day)` — Ver el calendario de la semana
- `remove_from_calendar(recipe_id, day)` — Eliminar una receta

Ver **`references/cookidoo-calendar-sync.md`** para ejemplos avanzados (múltiples recetas por día, semanas completas).

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

**⚠️ Formato crítico 2026-07-14:** La shopping list DEBE usar **unidades de venta reales** de Mercadona, NO cantidades exactas en gramos de la receta.

**Correcto:**
```json
[
  {"name": "aceitunas negras", "quantity": 1, "unit": "ud", "fresh": false},
  {"name": "mozzarella", "quantity": 2, "unit": "ud", "fresh": true}
]
```

**Incorrecto (causa bug de conversión):**
```json
[
  {"name": "aceitunas negras", "quantity": 150, "unit": "g", "fresh": false}
  // → wrapper NO convierte correctamente → 150 unidades = 285€
]
```

**Regla:** Si el producto es conserva, aceite, leche, queso rallado, pasta seca → usar `unit: "ud"` con cantidad entera (1 lata, 1 botella, 2 paquetes). Solo verduras/frutas/carnes frescas vendidas por peso usan `unit: "g"` o `"kg"` (el wrapper SÍ convierte bien estos).

### Añadir todo al carrito de Mercadona

> ✅ **Migración completada 2026-07-14:** Spike exitoso con **carrito real probado**.
> `mercadona-cli` confirmado 40× más rápido que Playwright y resuelve todos los bugs críticos.
> Wrapper Python (`mercadona_cli_wrapper.py`) operativo. Playwright archivado en `scripts/legacy/`.

**Método principal (mercadona-cli via wrapper Python):**

```python
from scripts.mercadona_cli_wrapper import MercadonaCLI

# 1. Inicializar (usa warehouse configurado en ~/.mercadona/config.toml)
cli = MercadonaCLI()

# 2. Resolver shopping list a productos concretos
shopping_list = [
    {"name": "tomate", "quantity": 6, "fresh": True},
    {"name": "salmón", "quantity": 400, "unit": "g", "fresh": True, "category": "Marisco y pescado"}
]
resolved = cli.resolve_shopping_list(shopping_list)

# 3. Generar archivo basket.txt
basket_file = cli.generate_basket_file(resolved["resolved"], "/tmp/basket.txt")

# 4. Preview total (Gate 1 - mostrar a Xavier en Telegram)
preview = cli.preview_total(basket_file)
print(f"Total: {preview['total']}€ ({preview['count']} productos)")

# → ESPERAR CONFIRMACIÓN DE XAVIER

# 5. Añadir al carrito (Gate 2 - tras confirmación)
result = cli.fill_cart(basket_file, max_eur=80.0, dry_run=False)
print(f"✓ Añadidos {result['products_count']} productos, total {result['summary']['total']}€")

# 6. Verificar
cart = cli.get_cart()
```

**Flags importantes:**
- `fresh=True`: Excluye congelados y conservas (default para verduras/proteínas)
- `category`: Filtra por sección de Mercadona (mejora matching)
- `max_eur`: Spending guard (rechaza si el total supera el límite)

**CLI directo (para testing manual):**

```bash
# Búsqueda batch
printf 'tomate\ncebolla\narroz redondo\n' | mercadona batch -f - --fresh --json

# Preview total
mercadona total -f basket.txt
# → total: 13.24€  (5 líneas)

# Llenar carrito
mercadona cart set-many -f basket.txt --max 80

# Ver/vaciar carrito
mercadona cart get
mercadona cart clear
```

**Ver:** `references/mercadona-cli-setup.md` y `references/mercadona-cli-usage.md` para ejemplos completos.  
**Patrón de diseño:** Ver `references/cli-wrapper-pattern.md` para el patrón de wrapping CLI→Python (reusable en otros contextos).

## Estructura del proyecto

```
meal2cart/
├── scripts/
│   ├── mercadona_cli_wrapper.py  # ✅ Wrapper Python de mercadona-cli (producción)
│   ├── recipe_md_generator.py    # JSON → Markdown
│   ├── cookidough_client.py      # Cliente Python para cookidough MCP
│   └── legacy/
│       ├── mercadona_client.py   # Playwright (deprecated 2026-07-14)
│       └── DEPRECATED.md         # Razones de deprecación
├── prompts/
│   ├── menu_planning.md
│   ├── ingredient_consolidation.md  # ✅ Actualizado con campos fresh/category/unit
│   └── recipe_format.md
├── references/
│   ├── mercadona-cli-setup.md         # ✅ Instalación + auth (import-curl)
│   ├── mercadona-cli-usage.md         # ✅ Ejemplos prácticos CLI
│   ├── mercadona-cli-json-schemas.md  # ✅ Estructuras JSON
│   ├── e2e-testing-pattern.md         # ✅ Patrón test end-to-end con carrito REAL (2026-07-14)
│   ├── cli-wrapper-pattern.md         # ✅ Patrón CLI→Python reusable
│   ├── mercadona-cli.md               # (legacy, pre-wrapper)
│   ├── mercadona-quirks.md
│   ├── mercadona_selectors.md         # (legacy Playwright)
│   ├── spoonacular_setup.md
│   ├── cookidough_setup.md
│   ├── cookidough-mcp-usage.md
│   ├── cookidoo-calendar-sync.md
│   ├── mcp-setup-lessons.md
│   └── testing-patterns.md
├── tests/
│   ├── test_e2e_mercadona_cli.py  # ✅ Test end-to-end wrapper (5/5 productos)
│   ├── test_mercadona_client.py   # (legacy Playwright)
│   └── test_recipe_generator.py
├── config.yaml.example
├── SKILL.md
└── README.md
```

## Pitfalls (lecciones de integración 2026-07-14)

### 1. Categorías de Mercadona son nombres EXACTOS
**Problema:** `ingredient_consolidation.md` generaba `"category": "Verdura"` pero Mercadona usa `"Fruta y verdura"`.  
**Síntoma:** `batch_search()` con category incorrecta devuelve 0 hits.  
**Solución:** Usar nombres exactos de categorías Mercadona o `null` + flag `--fresh` (suficiente para verduras).  
**Categorías válidas:** `"Fruta y verdura"`, `"Marisco y pescado"`, `"Carnes y aves"`, `"Conservas, caldos y cremas"`.

### 2. Productos unitarios requieren cantidad ENTERA
**Problema:** `{"quantity": 0.5, "unit": "ud"}` para aceite (producto unitario) falla con HTTP 400.  
**Síntoma:** `Invalid quantity 0.5 for a product sold by unit`.  
**Solución:** En `ingredient_consolidation.md`, mapear "500ml aceite" → `{"quantity": 1, "unit": "ud"}`, NO 0.5.  
**Regla:** Si el producto es pack/botella (aceite, leche, conservas), usar `unit: "ud"` con qty entera.

### 3. HAR export puede no capturar auth
**Problema:** Export HAR antes de hacer login o sin capturar POST de autenticación → `no auth material found`.  
**Solución verificada:** Usar **Copy as cURL** como método primario para Google SSO:
  1. Chrome DevTools → Network → buscar request a `api/customers/*/cart`
  2. Click derecho → Copy → Copy as cURL (bash)
  3. `mercadona import-curl --file curl.txt`
  4. Token dura ~6 semanas, renovar cuando expire

### 4. Test end-to-end requiere PYTHONPATH
**Problema:** `from mercadona_cli_wrapper import MercadonaCLI` → ModuleNotFoundError.  
**Solución:** `PYTHONPATH=/path/to/scripts:$PYTHONPATH python3 test.py` o mover wrapper a package instalable.  
**Nota:** No afecta uso real (Hermes maneja PYTHONPATH automáticamente).

### 5. Flag --category requiere ID numérico, NO string
**Problema:** `mercadona batch -f - --fresh --category "Fruta y verdura"` → error "category is ambiguous".  
**Síntoma:** `subprocess.CalledProcessError` con exit status 1.  
**Causa:** El flag `--category` de mercadona-cli espera ID numérico (ej: `1`, `145`), no nombre de categoría.  
**Solución:** (1) Obtener ID con `mercadona categories | grep "nombre"`, o (2) **RECOMENDADO:** omitir `--category` y usar solo `--fresh` (suficiente para verduras/proteínas/frescos).  
**Fix aplicado 2026-07-14:** Shopping lists usan `category: None` + flag `--fresh` únicamente.

### 6. Bug conversión g→unidades en wrapper (RESUELTO 2026-07-14)
**Problema:** Productos en conserva/pack con `unit: "g"` se convierten incorrectamente.  
**Ejemplo:** `{"name": "aceitunas negras", "quantity": 150, "unit": "g"}` → wrapper NO convierte a kg → mercadona-cli interpreta como 150 UNIDADES → subtotal 285€ en lugar de ~2€.  
**Causa:** Lógica de conversión en `mercadona_cli_wrapper.py` solo chequeaba `is_pack`, pero productos como aceitunas en lata son pack Y se venden por peso.  
**Solución aplicada:** Wrapper ahora usa `reference_format` para detectar si el producto se vende por kg (convertir g→kg) o por unidad (mantener qty original). Ver commit `fix: improve unit conversion logic in wrapper`.  
**Workaround alternativo:** Usar `unit: "ud"` con cantidad entera (1 lata, 1 bote, 1 paquete) en lugar de gramos.

### 7. Búsquedas ambiguas pueden devolver productos preparados
**Problema:** Query "albahaca fresca" devuelve "Salsa fresca Pesto" en lugar de maceta de albahaca.  
**Causa:** Algoritmo de matching de Mercadona prioriza productos preparados/populares sobre frescos cuando la query es genérica.  
**Solución:** (1) Queries más específicas ("albahaca maceta", "albahaca planta"), (2) usar `--fresh` agresivamente, o (3) validar top result antes de añadir al carrito (Gate 1 con preview).  
**Lección:** El preview (Gate 1) es crítico para detectar sustituciones inesperadas antes de commit al carrito.

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| `mercadona: command not found` | CLI no instalado | `npm install -g @ivorpad/mercadona` |
| `mercadona whoami` → "not authenticated" | Token expirado sin refresh | Si usas Google SSO, necesitas `import-curl` cada ~6 semanas (Copy as cURL desde Chrome DevTools → request api/customers). Alternativamente, conseguir HAR válido con `import-har` da refresh token permanente. |
| HAR export falla ("no auth material found") | HAR se capturó antes/durante login, no después | **Solución verificada:** Usar Copy as cURL como método primario para Google SSO. Chrome DevTools → Network → request a api/customers/*/cart → Copy as cURL → `mercadona import-curl --file curl.txt`. Token dura ~6 semanas. |
| `mercadona cart add` → 401 | Token expirado sin refresh | Si usas Google SSO, necesitas `import-har` (no `login`). El refresh token del HAR auto-renueva. |
| Búsqueda `batch` da resultado incorrecto (ej: "salmón fresco" → comida de perro) | Query ambigua, Algolia top hit no es el esperado | (1) Normalizar query en `ingredient_consolidation.md` ("salmón ahumado" en vez de "salmón fresco"), (2) usar `--category "Marisco y pescado"`, o (3) usar `search` individual con `--limit 5` y elegir manualmente |
| Búsqueda da conserva/congelado en vez de fresco | Falta flag `--fresh` | Añadir `--fresh` a `batch` o `search`: `mercadona batch -f lista.txt --fresh` |
| `BUDGET EXCEEDED` (exit 1) | Total estimado > `--max` | Ajusta `--max` o reduce items. El carrito NO se modificó (preventivo) |
| `faltan X€ para el mínimo` | Basket < 60€ | Añade más productos (mínimo Mercadona ≈ 60€ para delivery) |
| `Playwright no está instalado` | Falta el paquete o el navegador | Solo necesario como fallback. `pip install --break-system-packages playwright && python3 -m playwright install chromium` |
| ✗ Login Mercadona fallido (sin campos email/password) | Cuenta usa Google SSO | **Ya no aplica con `mercadona-cli`**. Usa `mercadona import-har` para extraer refresh token. Una vez hecho, headless. |
| Spoonacular 401/402 | API key inválida o cuota agotada | Ver `references/spoonacular_setup.md`. La key actual (`SPOONACULAR_API_KEY`) puede requerir regeneración en https://spoonacular.com/food-api/console |
| cookidough 403 | Cookies caducadas | Borra `~/.hermes/data/cookidough_cookies.json` y re-logín |
| `cookidough_client.py` no autentica (403 silencioso) | El script usa `COOKIDOO_*` en vez de `COOKIDOUGH_*` (typo heredado) | Verifica que `scripts/cookidough_client.py` lee `COOKIDOUGH_PASSWORD` y `COOKIDOUGH_COUNTRY` (no `COOKIDOO_*`). Corregido en versión ≥ post-2026-07-13 |
| Markdown vacío | JSON de entrada mal formado | Verifica `week_start` y `meals.*.{comida,cena}` |
| Productos no encontrados en Mercadona | Nombre no normalizado | Edita `prompts/ingredient_consolidation.md` y reintenta |
| MCP `-32602 Invalid request parameters` | Método incorrecto — se usó `method: "search_recipes"` en vez de `method: "tools/call"` | Usa siempre `method: "tools/call"` con `params.name`. Ver `references/cookidough-mcp-usage.md` |
| MCP no responde tras enviar comandos | stdin se cierra antes de que el servidor procese | Mantén stdin abierto con `sleep N` o usa `subprocess.Popen`. Ver `references/cookidough-mcp-usage.md` |
| `get_recipe_details` no devuelve pasos | El endpoint de Cookidoo no incluye `steps` en la respuesta | Escribe los pasos manualmente o consulta la URL de la receta. Ver `references/cookidough-mcp-usage.md` |
| Ingredientes de Cookidoo sin nombre (\"200 g\", \"1 chorrito\") | `get_recipe_details` devuelve `description` con cantidades pero `name` es null | Inferir ingredientes por contexto, abrir URL en navegador, o usar Spoonacular como fuente alternativa. Ver `references/cookidough-mcp-usage.md` |
| Resultados de Cookidoo en alemán | `COOKIDOUGH_COUNTRY` y `COOKIDOUGH_LANGUAGE` no están configurados (default ambos `\\\"de\\\"`) | Establecer `COOKIDOUGH_COUNTRY=es` y `COOKIDOUGH_LANGUAGE=es`. Borrar cookies viejas (`rm ~/.hermes/data/cookidough_cookies.json`) y re-logín. Ver `references/cookidough_setup.md` |
| `mercadona batch --category "Fruta y verdura"` → error "ambiguous" | Flag `--category` requiere ID numérico, no string | Usar ID numérico (`mercadona categories` para ver lista) o **MEJOR:** omitir `--category` y usar solo `--fresh` |
| Producto conserva/pack subtotal absurdo (ej: aceitunas 285€) | Wrapper convierte mal cantidades en gramos para productos unitarios | **RESUELTO 2026-07-14:** Fix aplicado en wrapper (usa `reference_format`). Ver Pitfall #6 |
| Búsqueda devuelve preparado en vez de fresco (ej: pesto en vez de albahaca) | Query ambigua, algoritmo Mercadona prioriza preparados | Query más específica ("albahaca maceta") o validar en preview (Gate 1) antes de commit |

## Test end-to-end real completado (2026-07-14)

**Receta:** Ensalada italiana de pasta con pesto (Cookidoo r221200)  
**Flujo:** Cookidoo → Shopping list → Mercadona → Carrito REAL  
**Resultado:** ✅ **100% exitoso**

### Métricas

- Productos resueltos: **9/9 (100%)**
- Total estimado: **20.95€**
- Total real: **20.95€** (coincidencia 100%)
- Tiempo total: **~2 minutos**
- Errores: **0**

### Productos añadidos al carrito

1. Queso rallado mozzarella — 1.60€
2. Piñones Hacendado — 3.25€
3. Aceite oliva virgen extra — 4.80€
4. Ajos morados — 1.85€
5. Salsa pesto albahaca — 1.90€ ⚠️ (buscado: albahaca fresca)
6. Pasta fusilli lentejas — 1.65€
7. Aceitunas negras — 1.90€
8. Tomates cherry — 2.20€
9. Mozzarella × 2 — 1.80€

### Lecciones

1. **Gate 1 es crítico** — preview detectó sustitución albahaca→pesto antes de commit
2. **Conversión g→ud funciona** — tras fix, aceitunas 150g = 1 lata (1.90€), NO 150 unidades (285€)
3. **Flag --fresh suficiente** — no necesita --category (evita errores de ID numérico)
4. **Estimación = Real** — mercadona-cli preview es 100% fiable para presupuestos

**Documentación completa:** Ver `/mnt/vault/Personal/Hermes/meal-to-cart/2026-07-14_TEST_ENSALADA_COMPLETADO.md`

## Development

- Tests: `pytest -q tests/`
- Los tests NO abren navegador (mockean Playwright vía monkeypatch).
- **⚠️ No mockear `asyncio.run` directamente** en tests — produce
  "coroutine was never awaited". Mockea la clase cliente en su lugar.
  Ver `references/testing-patterns.md`.
- Para activar formato de logs, usa `LOG_LEVEL=DEBUG` (no implementado
  pero reservado en `mercadona_client.log` para futura mejora).

### Test end-to-end como gate de calidad

**Patrón:** Tras migración o cambios en wrappers, ejecutar test end-to-end ANTES de considerar completo. Ver **`references/e2e-testing-pattern.md`** para el patrón completo validado con carrito REAL.

```bash
PYTHONPATH=scripts:$PYTHONPATH python3 tests/test_e2e_mercadona_cli.py
```

**Lección 2026-07-14:** El test e2e reveló 2 bugs críticos (categorías incorrectas + conversión g→unidades) que tests unitarios mock no habrían detectado. Los tests e2e con CLI real son el gate definitivo para validar integraciones. Preview (Gate 1) es crítico para detectar sustituciones antes de commit al carrito.

## Licencia

GPL-3.0 (ver `LICENSE`).