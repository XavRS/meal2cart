# Selectores de Mercadona Online (verificados)

Documento de referencia para `scripts/mercadona_client.py`. Todos los selectores fueron verificados en un **spike** con Playwright el **2026-07**.

> ⚠️ Mercadona es una SPA (React) y puede cambiar el DOM sin aviso. Si un selector falla, vuelve a este doc y regenera la evidencia con `--headed` antes de tocar el código.

## URLs

| Fase | URL |
|------|-----|
| Portal (CP) | `https://www.mercadona.es/` |
| Tienda (tras CP) | `https://tienda.mercadona.es/` |
| Carrito | `https://tienda.mercadona.es/cart` |
| Cuenta/login | `https://tienda.mercadona.es/account/login` |

## Flujo

```
mercadona.es
    │
    │  1. Aceptar cookies
    ▼
[input postal-code-form]
    │  2. Rellenar CP y submit
    ▼
tienda.mercadona.es  (5s redirect SPA)
    │
    │  3. Buscar producto + Enter
    ▼
tienda.mercadona.es/search?query=...
    │  4. .product-cell--actionable aparece (puede tardar 2-5s)
    ▼
[button add-to-cart] (de la primera card)
    │  5. Click → añade al carrito
    ▼
(esperar 1.5s entre productos)
```

## Selectores canónicos

### 1. Cookies — botón Aceptar

```css
button:has-text("Aceptar")
```

> Fallbacks: `#didomi-notice-agree-button`, `button[data-testid="accept-cookies"]`

### 2. Código postal — input

```css
input[aria-label="Código postal"]
```

> Fallback: `input[name="cp"]`, `input.input-text[name="postal_code"]`

### 3. CP — botón submit

```css
input.postal-code-form__button
```

> Fallback: `button.postal-code-form__button`, `input[type="submit"][value="Enviar"]`

### 4. Buscador — input

```css
input[placeholder="Buscar productos"]
```

> Fallback: `input[type="search"]`, `input[data-testid="search-input"]`

### 5. Tarjeta de producto

```css
.product-cell--actionable
```

Dentro de cada card:

| Sub-elemento | Selector | Notas |
|--------------|----------|-------|
| Nombre | `.product-cell__description-name` | texto simple |
| Precio | `.product-cell__price` | formato `1,20€` o `1,20 €/ud` |
| Imagen | `.product-cell__image img[src]` | no usada por el script |
| Contenedor de acciones | `.product-cell__action` | contiene el botón add |

### 6. Añadir al carrito — botón

Selector primario:

```css
button[data-testid="product-quantity-button"]
```

Fallback (texto accesible):

```css
button[aria-label="Añadir al carro"]
```

> En el spike, el `data-testid` aparecía tanto en el botón "+" como en el botón principal de "Añadir". Si el producto ya está en el carrito, el botón muestra "- N +". El script intenta el primario y luego el fallback.

### 7. Indicador de carrito

```css
.cart-info, [data-testid="cart-icon"]
```

Útil para verificar que se añadió algo (el número aumenta).

### 8. Login wall

Cuando el carrito excede un nº de items sin login, Mercadona muestra:

```css
text="Inicia sesión"
input[type="email"]
```

El script lo detecta y aborta el add, informando al usuario para que haga login manual (primera vez).

## Snippets de Playwright (Python async) verificados

```python
# 1. Aceptar cookies
page.locator('button:has-text("Aceptar")').click()

# 2. CP
page.fill('input[aria-label="Código postal"]', "08001")
page.click('input.postal-code-form__button')
#    SPA -> preparar wait de hasta 10s a que URL contenga "tienda.mercadona.es"

# 3. Buscar
page.fill('input[placeholder="Buscar productos"]', "leche semidesnatada")
page.press('input[placeholder="Buscar productos"]', "Enter")

# 4. Esperar cards
page.wait_for_selector(".product-cell--actionable", timeout=10_000)
cards = page.locator(".product-cell--actionable")
for i in range(await cards.count()):
    name = await cards.nth(i).locator(".product-cell__description-name").inner_text()

# 5. Añadir (primera card)
card = cards.first
btn = card.locator('button[data-testid="product-quantity-button"]').first
if await btn.count() == 0:
    btn = card.locator('button[aria-label="Añadir al carro"]').first
await btn.click()
```

## Latencias recomendadas

| Acción | Espera |
|--------|--------|
| Después de enviar CP | 5s (redirect SPA) |
| Después de Enter en buscador | 5s (fetch productos) |
| Entre clics "Añadir" | 1.5s (rate-limit + animación) |
| Tras login wall detectado | abortar |

## Cookies / storage_state

```python
# guardar
await context.storage_state(path="/tmp/mercadona_cookies.json")
# cargar
context = await browser.new_context(storage_state="/tmp/mercadona_cookies.json")
```

Eso evita re-introducir el CP cada ejecución. **No** salta el login de carrito (ese requiere sesión de usuario real).

## Cuándo regenera este documento

- Un selector falla sistemáticamente → abre `--headed` y copia el HTML actual.
- Mercadona añade/retira tests IDs (revisar cada release mayor, ~6 meses).
- Cambia el dominio del portal (de `mercadona.es` a algo distinto).

Actualiza también las constantes `SEL_*` en `scripts/mercadona_client.py`.