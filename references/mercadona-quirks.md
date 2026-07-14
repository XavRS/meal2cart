# Mercadona Online — Quirks y soluciones

Registro de problemas encontrados con Playwright + Mercadona y sus soluciones.

## Modal "¿Ya tienes cuenta?"

Al añadir productos sin haber iniciado sesión, Mercadona muestra un modal
con título "¿Ya tienes cuenta?" que bloquea los clicks posteriores. El
modal es un `<div role="dialog" aria-label="¿Ya tienes cuenta?">`.

### Solución implementada (2026-07-13)

Se añadió `_dismiss_login_modal()` al `MercadonaClient` con 4 estrategias
en orden:

1. **Botón X de cierre**: `.ui-modal__close`, `[aria-label="Cerrar"]`
2. **Tecla Escape**: `page.keyboard.press("Escape")`
3. **Click en backdrop**: `.ui-modal__backdrop`, `[class*="backdrop"]`
4. **Botón "Continuar sin cuenta"**: `a:has-text("sin cuenta")`, etc.

El método se llama automáticamente desde `add_many()` cuando
`_check_login_wall()` detecta el modal (se añadió el selector
`[aria-label="¿Ya tienes cuenta?"]` a los indicadores de login wall).

**⚠️ Limitación (verificada 2026-07-13):** ninguna de las 4 estrategias
funcionó en pruebas reales. El modal de Mercadona parece estar diseñado
para ser inmune a cierres programáticos. Cuando aparece, el script salta
ese producto y continúa con el siguiente. Para usar el carrito sin
interrupciones se necesita **login real** en Mercadona (ejecutar una vez
con `--headed` y hacer login manual).

## SPA se rompe tras ~20-25 búsquedas

La SPA de Mercadona (`tienda.mercadona.es`) se vuelve inestable después
de ~20-25 operaciones de búsqueda consecutivas. El síntoma es que el
input de búsqueda (`input[placeholder="Buscar productos"]`) desaparece
del DOM y `wait_for_selector` da timeout.

**Workaround**: limitar las tandas a ~20 productos por ejecución. Si se
necesitan más, partir la lista en lotes y reiniciar el navegador entre
lotes. En el futuro, el script podría detectar el error y hacer un
`page.reload()` automático.

## PEP 668 — Instalación de Playwright en Debian

En sistemas con PEP 668 activo (Debian 12+, Ubuntu 23.04+), `pip install`
sin virtualenv requiere el flag `--break-system-packages`:

```bash
pip install --break-system-packages playwright
python3 -m playwright install chromium
```

Alternativa recomendada: usar `uv` o un virtualenv.

## Cookies / sesión

- El estado se guarda en `/tmp/mercadona_cookies.json`
- Si aparece el modal de CP a pesar de tener cookies, borrar el archivo
  y reintentar
- La primera ejecución tras borrar cookies reintroduce el CP
  automáticamente

## Login automático (implementado 2026-07-13)

Configurar variables de entorno:

```bash
export MERCADONA_EMAIL="tu@email.com"
export MERCADONA_PASSWORD="tu_password"
```

El script automáticamente:

1. Navega a `/?authenticate-user=`
2. Abre el dropdown "Identifícate"
3. Clica "Continuar con email"
4. Rellena email + password
5. Envía el formulario

Si Mercadona cambia los selectores, ejecutar `--login --headed` para
depurar el formulario real y actualizar las constantes `SEL_LOGIN_*`
en `scripts/mercadona_client.py`.

**⚠️ Limitación (2026-07-13):** El formulario de login con email puede
no mostrarse en todas las condiciones (depende del estado de la SPA y
del CP configurado). Si no funciona con credenciales, usar `--login
--headed` para login manual (abre Chromium visible durante 30s).

### ⚠️ Google SSO no soportado

Si tu cuenta Mercadona usa login con Google (no email/password), el
login automático no funcionará. Usa `--login --headed` para hacer
login manual con Google. Las cookies de sesión se guardan en
`/tmp/mercadona_cookies.json` y se reutilizan en futuras ejecuciones
headless.

Si necesitas login email/password, crea una cuenta en Mercadona con
email y contraseña (no Google SSO).

## Login manual (modo headed)

Para usar el carrito con login real (necesario si Mercadona fuerza el
login), ejecutar una vez con `--headed`:

```bash
python3 scripts/mercadona_client.py --search "leche" --headed
```

Esto abre Chromium visible para hacer login manual. Las cookies de
sesión se guardan y las siguientes ejecuciones headless las reutilizan.
