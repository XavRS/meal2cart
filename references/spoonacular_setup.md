# Spoonacular — Setup del MCP y obtención de API key

## 1. Obtener una API key gratuita

1. Ve a <https://spoonacular.com/food-api/console#SignUp>.
2. Regístrate con email + contraseña (o cuenta Google).
3. En el **Dashboard** copia tu **API Key** (formato: 32 caracteres alfanuméricos).
4. El **free tier** permite **150 peticiones/día** — suficiente para planificar ~5 menús/semana con margen.

> ⚠️ La key gratuita es pública-quota compartida: evita scripts que bucleeen sin caché.

## 2. Limitaciones del free tier

| Límite | Free | Paid |
|--------|------|------|
| Requests/día | 150 | 6.000+ |
| `complexSearch` resultados | 10 | 100 |
| `analyzedInstructions` | ✅ | ✅ |
| `nutrition` | ✅ limitado | ✅ |
| `mealPlanner` | ❌ (legacy) | ✅ |

Para nuestro caso (búsqueda de recetas + nutritional info) el free tier basta.

## 3. Instalar el MCP

El servidor usado es <https://github.com/ddsky/spoonacular-mcp-server>, expuesto vía `npx`:

```bash
npx ddsky/spoonacular-mcp
```

Requisitos: **Node.js 18+**. No hace falta instalación global.

Comprueba que arranca:

```bash
SPOONACULAR_API_KEY=xxxx npx ddsky/spoonacular-mcp
# debe quedar escuchando en stdio (MCP)
```

## 4. Configurar en Hermes

`~/.hermes/config.yaml`:

```yaml
mcp_servers:
  spoonacular:
    command: npx
    args: ["ddsky/spoonacular-mcp"]
    env:
      SPOONACULAR_API_KEY: "${SPOONACULAR_API_KEY}"
```

Exporta la variable en tu shell:

```bash
# ~/.zshrc o ~/.bashrc
export SPOONACULAR_API_KEY="tu_api_key_aqui"
```

## 5. Probar

Desde Hermes o con cualquier cliente MCP, llama a `search_recipes` o `complexSearch`:

```jsonc
{ "tool": "spoonacular.searchRecipes", "arguments": { "query": "gluten free salmon", "maxReadyTime": 30, "number": 5 } }
```

## 6. Troubleshooting

| Síntoma | Solución |
|---------|----------|
| `401 Unauthorized` | API key mal copiada o cuota activada en otra IP. Crea otra key. |
| `429 Too Many Requests` | Cuota diaria agotada. Espera a las 00:00 UTC. |
| `npx no descarga el paquete` | Borra caché: `npx clear-npx-cache` o installa global: `npm i -g ddsky/spoonacular-mcp`. |
| MCP no aparece en Hermes | Verifica `command: npx` + `args: ["ddsky/spoonacular-mcp"]` y que `npx --version` funciona. |

## 7. Recursos

- Docs API: <https://spoonacular.com/food-api/docs>
- Playground: <https://spoonacular.com/food-api/console>
- Repo MCP: <https://github.com/ddsky/spoonacular-mcp-server>