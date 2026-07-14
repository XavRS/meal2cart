# mercadona-cli — Setup

Guía de instalación y configuración del CLI de Mercadona Online para meal-to-cart.

---

## 1. Instalación

Elige una opción:

### Opción A: npm global (recomendado si tienes Node.js)

```bash
npm install -g @ivorpad/mercadona
mercadona version
```

### Opción B: Script de instalación

```bash
curl -fsSL https://raw.githubusercontent.com/ivorpad/mercadona-cli/main/install.sh | sh
mercadona version
```

### Opción C: Binary manual

1. Descargar desde https://github.com/ivorpad/mercadona-cli/releases
2. Extraer y mover a PATH:
   ```bash
   tar -xzf mercadona_*.tar.gz
   sudo mv mercadona /usr/local/bin/
   ```

---

## 2. Configurar warehouse (código postal)

Una sola vez, para que el CLI use el warehouse correcto:

```bash
mercadona set-postal 08330
# → ok — postal code 08330 → warehouse 4182
```

Esto guarda `warehouse=4182` y `postal_code=08330` en `~/.mercadona/config.toml`.

**Importante:** Los IDs de productos y precios son **por warehouse**. Usa siempre el warehouse correcto.

---

## 3. Autenticación (operaciones de carrito)

Las **búsquedas** (`search`, `batch`, `total`) **NO requieren auth**.

El **carrito** (`cart get/set-many/clear`) **SÍ requiere auth**.

### Método: import-curl (recomendado)

1. **Abre `tienda.mercadona.es`** en Chrome (ya logueado)

2. **DevTools** (F12) → **Network**

3. **Haz alguna acción** (buscar producto, abrir carrito)

4. **Busca un request** a `api/customers` o `api/cart`

5. **Click derecho** → **Copy** → **Copy as cURL (bash)**

6. **Guarda el cURL** en un archivo:
   ```bash
   # Pegar el cURL en /tmp/mercadona_curl.txt
   mercadona import-curl --file /tmp/mercadona_curl.txt
   # → imported session: token=419 chars, cookie=1287 chars
   
   rm /tmp/mercadona_curl.txt  # Borrar por seguridad
   ```

7. **Verificar:**
   ```bash
   mercadona whoami
   # → ok — authenticated. customer id=...
   ```

**Token válido:** ~6 semanas. Repetir `import-curl` cuando expire.

---

## 4. Verificación completa

```bash
# 1. Warehouse configurado
grep -E "^warehouse|^postal_code" ~/.mercadona/config.toml
# warehouse = "4182"
# postal_code = "08330"

# 2. Auth OK
mercadona whoami
# ok — authenticated. customer id=...

# 3. Test búsqueda
printf 'tomate\ncebolla\n' | mercadona batch -f - --fresh
# • tomate  → [69975] Tomates pera — 2.11€
# • cebolla → [69089] Cebollas — 1.60€

# 4. Test carrito
mercadona cart get
# cart ... (v1, 0 productos, total 0.00€)
```

Si todos los tests pasan → **setup completo** ✅

---

## Troubleshooting

### `error: not authenticated`

Re-hacer `import-curl` (el token expiró tras ~6 semanas).

### `error: no such command 'mercadona'`

El CLI no está en PATH. Verificar instalación:
```bash
which mercadona
npm list -g @ivorpad/mercadona
```

### Warehouse incorrecto (productos no encontrados)

Verificar que el warehouse coincide con tu CP:
```bash
mercadona set-postal 08330  # Tu CP real
```

### `HTTP 400: Invalid quantity 0.5 for a product sold by unit`

El producto se vende por unidad, no por peso. Usar cantidad entera:
```bash
# ❌ 4740 0.5  # Aceite (unitario)
# ✅ 4740 1    # Aceite (1 botella)
```

Ver `mercadona-cli-usage.md` para más ejemplos.
