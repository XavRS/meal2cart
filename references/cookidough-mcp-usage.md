# cookidough-mcp — Uso programático y quirks

Guía para llamar al MCP de Cookidoo desde terminal/Python cuando no está
disponible como herramienta nativa de Hermes.

## Protocolo MCP (JSON-RPC sobre stdio)

El MCP usa JSON-RPC 2.0. La secuencia correcta es:

```
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}
← {"jsonrpc":"2.0","id":1,"result":{...}}
→ {"jsonrpc":"2.0","method":"notifications/initialized"}
→ {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_recipes","arguments":{...}}}
← {"jsonrpc":"2.0","id":2,"result":{...}}
```

### ⚠️ El método SIEMPRE es `tools/call`

**NO usar** `method: "search_recipes"` directamente. El nombre de la
herramienta va en `params.name`. Esto es parte del estándar MCP y aplica
a todos los MCP servers (cookidough, spoonacular, etc.).

Error común:
```json
// MAL — da -32602 Invalid request parameters
{"method": "search_recipes", "params": {"query": "gazpacho"}}

// BIEN
{"method": "tools/call", "params": {"name": "search_recipes", "arguments": {"query": "gazpacho"}}}
```

## Timing de stdin

El servidor MCP procesa línea por línea pero necesita que stdin **no se
cierre** inmediatamente después de enviar los comandos. Si se cierra
stdin (EOF), el proceso termina antes de responder.

**Fix**: mantener stdin abierto con `sleep N` al final del pipe, o usar
`subprocess.Popen` con `stdin.write()` + `flush()` + `readline()`.

### Pipe simple (funciona si hay sleep al final)

```bash
{ echo '...init...'; echo '...notif...'; echo '...call...'; sleep 5; } | cookidough-mcp
```

### Python con subprocess (recomendado para >1 llamada)

```python
proc = subprocess.Popen(["cookidough-mcp"], stdin=PIPE, stdout=PIPE, text=True)
proc.stdin.write(init + "\n" + notif + "\n"); proc.stdin.flush()
proc.stdout.readline()  # consume init response
# ... por cada tool call:
proc.stdin.write(call + "\n"); proc.stdin.flush()
line = proc.stdout.readline()  # bloquea hasta respuesta
```

## Lazy login

`get_user_profile` dispara el login lazy. La primera llamada tarda ~1-2s
extra. Si no se ha hecho login antes, cualquier tool call lo hará
automáticamente.

Las cookies se guardan en `COOKIDOUGH_COOKIES_FILE`.

## Idioma de resultados

El MCP usa `COOKIDOUGH_COUNTRY` (código ISO 3166-1 alpha-2, ej. `"es"`)
y `COOKIDOUGH_LANGUAGE` (código ISO 639-1, ej. `"es"`). **Ambos**
controlan el idioma. El default es `"de"` para ambos — si no se
configuran, los resultados salen en alemán.

Para forzar español:
```bash
export COOKIDOUGH_COUNTRY="es"
export COOKIDOUGH_LANGUAGE="es"
```

Si se cambia el país/idioma, hay que **borrar las cookies antiguas**
(`rm ~/.hermes/data/cookidough_cookies.json`) porque la sesión anterior
está ligada al dominio anterior (ej. `cookidoo.de` vs `cookidoo.es`).

Las URLs de las recetas apuntan al dominio correcto según `COOKIDOUGH_COUNTRY`
(ej. `https://cookidoo.es/recipes/recipe/es-ES/r55691`).

## Formato de respuestas

### `search_recipes`

Los resultados vienen como múltiples entradas `content[]`, una por
receta, cada una con texto JSON:

```json
{
  "content": [
    {"type": "text", "text": "{\"id\":\"r132404\",\"name\":\"Gazpacho Andalusia\",...}"},
    {"type": "text", "text": "{\"id\":\"r97361\",\"name\":\"Gazpacho\",...}"}
  ]
}
```

Hay que parsear cada `content[i].text` como JSON independiente.

### `get_recipe_details`

Devuelve un solo objeto en `content[0].text` con:
- `id`, `name`, `url`, `difficulty`, `serving_size`
- `total_time_seconds`, `active_time_seconds`
- `ingredients`: array de `{id, name, description}` — la descripción
  contiene la cantidad (ej. `"500 g"`)
- `categories`: array de `{id, name}`
- `nutrition`: array con valores nutricionales por ración
- `images`, `collections`, `utensils`, `notes`

**⚠️ NO devuelve `steps`** — el campo no existe en la respuesta del
endpoint. Para obtener los pasos hay que:
1. Abrir la URL de la receta en el navegador
2. Usar el campo `notes` que a veces contiene instrucciones resumidas
3. Escribir los pasos manualmente basándose en los ingredientes y
   el conocimiento culinario

**⚠️ Los ingredientes vienen SIN nombre** (verificado 2026-07-13).
El array `ingredients` contiene objetos `{id, name, description}` donde
`name` suele ser `null` o vacío, y `description` contiene solo la
cantidad (ej. `"200 g"`, `"1 chorrito"`, `"4 - 5"`). No hay forma de
obtener el nombre del ingrediente desde la API. Estrategias:
1. Inferir el ingrediente por el contexto de la receta y cantidades típicas
2. Abrir la URL de la receta en el navegador para leer los ingredientes reales
3. Usar Spoonacular como fuente alternativa para ingredientes bien estructurados

## Variables de entorno necesarias

```bash
export COOKIDOUGH_EMAIL="xmirror@gmail.com"
export COOKIDOUGH_PASSWORD="..."
export COOKIDOUGH_COOKIES_FILE="/root/.hermes/data/cookidough_cookies.json"
export COOKIDOUGH_COUNTRY="es"
export COOKIDOUGH_LANGUAGE="es"
```

La carpeta de cookies debe existir: `mkdir -p $(dirname "$COOKIDOUGH_COOKIES_FILE")`.

## Cambio de país/idioma

Al cambiar `COOKIDOUGH_COUNTRY` o `COOKIDOUGH_LANGUAGE` (ej. de `de` a `es`),
las cookies antiguas del dominio anterior son inválidas. **SIEMPRE** borrar
el archivo de cookies tras un cambio de locale:

```bash
rm -f /root/.hermes/data/cookidough_cookies.json
```

La siguiente llamada a `get_user_profile` (u otra herramienta autenticada)
hará login fresco contra el nuevo dominio (ej. `cookidoo.es`).

### Login race

El login es lazy: la primera herramienta autenticada que se llama dispara la
autenticación. Si `get_user_profile` se llama antes de que el login termine,
puede devolver error aunque el login se complete después. Las herramientas
posteriores (ej. `add_recipes_to_calendar`) funcionarán correctamente.

**Patrón seguro**: llamar `get_user_profile` y luego `sleep(0.5)` antes de
cualquier otra herramienta autenticada.
