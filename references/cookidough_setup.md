# cookidough-mcp — Setup del MCP para Cookidoo (Thermomix)

`cookidough-mcp` es un servidor MCP que expone las recetas de Cookidoo (el portal de recetas oficial de Thermomix) mediante una sesión autenticada.

## 1. Cuenta Cookidoo

1. Ve a <https://cookidoo.es/> (o el dominio de tu país: `.com`, `.fr`, `.de`…).
2. Inicia sesión con tu cuenta **Thermomix/Cookidoo** (la misma del móvil).
3. Sin cuenta activa, los endpoints de recetas no devuelven datos.

> ⚠️ Requiere **suscripción Cookidoo** (incluida con la Thermomix TM6). Sin ella, la API no devolverá contenido completo.

## 2. Instalar `cookidough-mcp`

Requiere [`uv`](https://github.com/astral-sh/uv):

```bash
# Instalar uv si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Probar el servidor
uvx cookidough-mcp
```

Sin flags, leerá de variables de entorno.

## 3. Configuración

### Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `COOKIDOO_EMAIL` | Email de la cuenta Cookidoo | (obligatorio) |
| `COOKIDOO_PASSWORD` | Password de la cuenta | (obligatorio) |
| `COOKIDOUGH_COOKIES_FILE` | Ruta donde persistir cookies | `~/.cache/cookidough/cookies.json` |
| `COOKIDOO_COUNTRY` | Dominio Cookidoo (`es`, `com`, `fr`…) | `es` |

### `~/.hermes/config.yaml`

```yaml
mcp_servers:
  cookidough:
    command: uvx
    args: ["cookidough-mcp"]
    env:
      COOKIDOO_EMAIL: "${COOKIDOO_EMAIL}"
      COOKIDOO_PASSWORD: "${COOOKIDOO_PASSWORD}"
      COOKIDOUGH_COOKIES_FILE: "~/.hermes/data/cookidough_cookies.json"
      COOKIDOO_COUNTRY: "es"
```

Exporta las variables:

```bash
export COOKIDOO_EMAIL="tu@email.es"
export COOKIDOO_PASSWORD="tu_password"
```

## 4. Primera ejecución (login interactivo)

El MCP hace login por HTTP con tus credenciales y guarda una cookie de sesión en `COOKIDOUGH_COOKIES_FILE`. La sesión suele durar **~30 días**.

Si las cookies caducan, basta con reinvocar el MCP — él mismo renovará la sesión.

Para forzar un login limpio:

```bash
rm -f ~/.hermes/data/cookidough_cookies.json
uvx cookidough-mcp
```

## 5. Herramientas expuestas

Aproximadamente (los nombres pueden variar según versión):

| Tool | Descripción |
|------|-------------|
| `search_recipes` | Búsqueda por texto/keyword (ej. "vapor salmón sin gluten") |
| `get_recipe` | Detalle de una receta por ID: title, ingredientes, pasos, time, servings |
| `get_categories` | Categorías/buscador jerárquico |
| `collections` | Colecciones curadas (ej. "Sin gluten", "30 min") |

Cada receta de Cookidoo tiene URL tipo `https://cookidoo.es/recipes/{id}`.

## 6. Probar desde Hermes

```jsonc
{ "tool": "cookidough.search_recipes", "arguments": { "query": "salmon vapor verduras sin gluten" } }
```

El output incluye pasos con marcadores Thermomix (ej. `20 min / Varoma / vel. 1`) — úsalos literalmente en el recetario Markdown.

## 7. Troubleshooting

| Síntoma | Solución |
|---------|----------|
| `401 / Unauthorized` | Email/password incorrectos o cuenta sin suscripción Cookidoo. |
| `cookies.json no se crea` | La carpeta no existe: `mkdir -p ~/.hermes/data`. |
| `uvx no encontrado` | Instala `uv`: ver paso 2. |
| Sesión caduca cada pocas horas | Revisa si tienes 2FA activado — `cookidough-mcp` no soporta 2FA; desactívalo para esta cuenta o usa app-password. |
| Recetas sincronizadas no aparecen en TM6 | Verifica en la app móvil > "Mi Cookidoo" > pulsa sync. |

## 8. Recursos

- Repo: <https://github.com/koenvaneijk/cookidough-mcp> (/community)
- Portal Cookidoo ES: <https://cookidoo.es/>
- Soporte oficial: <https://www.thermomix.es/>