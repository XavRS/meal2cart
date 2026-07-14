# Lecciones de configuración MCP

Registro de problemas encontrados al configurar los MCP servers de Spoonacular y Cookidoo.

## Spoonacular

- **Problema**: `npx ddsky/spoonacular-mcp` falla con `sh: 1: spoonacular-mcp: not found` en el entorno de Hermes.
- **Causa**: `npx` no puede spawnear shell correctamente desde el binario de Node incluido.
- **Solución**: Clonar el repo, compilar con `npx tsc`, y usar `node /tmp/spoonacular-mcp/dist/index.js`.
- **Comando de instalación**:
  ```bash
  cd /tmp && git clone https://github.com/ddsky/spoonacular-mcp.git
  cd spoonacular-mcp && npm install && npx tsc
  ```
- **Config Hermes**:
  ```yaml
  spoonacular:
    command: node
    args: ["/tmp/spoonacular-mcp/dist/index.js"]
    env:
      SPOONACULAR_API_KEY: "${SPOONACULAR_API_KEY}"
  ```

## Cookidoo (cookidough-mcp)

- **Problema**: `pip install cookidough-mcp` falla (no está en PyPI).
- **Solución**: Instalar desde GitHub con `uv tool install`.
- **Requisito**: Python 3.12+. `uv` puede descargarlo automáticamente.
- **Comando de instalación**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv tool install git+https://github.com/Poket-Jony/cookidough-mcp.git --python 3.12
  ```
- **Variables de entorno**: El MCP usa prefijo `COOKIDOUGH_`, NO `COOKIDOO_`:
  - `COOKIDOUGH_EMAIL` (no `COOKIDOO_EMAIL`)
  - `COOKIDOUGH_PASSWORD` (no `COOKIDOO_PASSWORD`)
  - `COOKIDOUGH_COOKIES_FILE` (opcional, para persistencia de sesión)
- **Config Hermes**:
  ```yaml
  cookidough:
    command: /root/.local/bin/cookidough-mcp
    env:
      COOKIDOUGH_EMAIL: "${COOKIDOUGH_EMAIL}"
      COOKIDOUGH_PASSWORD: "${COOKIDOUGH_PASSWORD}"
      COOKIDOUGH_COOKIES_FILE: "/root/.hermes/data/cookidough_cookies.json"
  ```

## Añadir MCPs a Hermes

- **Problema**: `hermes mcp add` puede colgarse (timeout) si el MCP tarda en iniciar.
- **Solución**: Editar `~/.hermes/config.yaml` directamente con `cat >>`.
- **Verificar**: `hermes mcp list` muestra los servidores y su estado.
