# 🍽️ Meal-to-Cart

**Planificación de menús semanales automatizada con compra en Mercadona Online.**

Combina recetas de **Cookidoo** (Thermomix) y **Spoonacular** (cocina tradicional) para generar un menú semanal, consolidar la lista de compra y añadirla automáticamente al carrito de Mercadona.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Características

- 🗓️ **Planificación semanal** con recetas reales de Cookidoo y Spoonacular
- 📱 **Sync automático** a calendario Thermomix "Mi semana"
- 📝 **Recetario Markdown** con tabla semanal, ingredientes y pasos
- 🛒 **Automatización Mercadona** vía API REST (40× más rápido que scraping)
- 💰 **Spending guard** nativo (rechaza si supera presupuesto)
- ✅ **Verificación automática** (total estimado = total real)
- 🚀 **Sin límites** (añade 100+ productos sin crash)

---

## 📋 Requisitos

### Software

- **Python 3.11+**
- **Node.js 18+** (para mercadona-cli y MCP servers)
- **mercadona-cli** (`npm install -g @ivorpad/mercadona`)
- **Hermes Agent** (opcional, pero recomendado para orquestación)

### Cuentas y APIs

- **Cuenta Mercadona** (con login Google SSO o email/password)
- **Cuenta Cookidoo** (opcional, solo si usas Thermomix)
- **API key Spoonacular** (opcional, tier gratuito 150 req/día)

---

## 🚀 Instalación

### 1. Instalar mercadona-cli

```bash
# Vía npm (recomendado)
npm install -g @ivorpad/mercadona

# Verificar
mercadona version
```

### 2. Clonar/instalar la skill

**Si usas Hermes Agent:**

```bash
# La skill ya está en ~/.hermes/skills/meal-to-cart/
# Si no, clona el repo:
git clone https://github.com/XavRS/meal2cart.git ~/.hermes/skills/meal-to-cart
```

**Si usas standalone (sin Hermes):**

```bash
git clone https://github.com/XavRS/meal2cart.git
cd meal2cart
```

### 3. Configurar mercadona-cli

#### a) Configurar warehouse (código postal)

```bash
mercadona set-postal 08001
# → ok — postal code 08001 → warehouse bcn1
```

#### b) Autenticación (una sola vez)

**Método 1: Copy as cURL (más rápido)**

1. Abre `tienda.mercadona.es` en Chrome (ya logueado)
2. **DevTools** (F12) → **Network**
3. Haz una acción (buscar producto, abrir carrito)
4. Busca un request a `api/customers` o `api/cart`
5. **Click derecho** → **Copy** → **Copy as cURL (bash)**
6. Guarda el cURL en un archivo:

```bash
cat > /tmp/mercadona_curl.txt
# Pegar el cURL aquí
# Ctrl+D para terminar

mercadona import-curl --file /tmp/mercadona_curl.txt
rm /tmp/mercadona_curl.txt  # Borrar por seguridad
```

**Método 2: HAR export (token duradero)**

1. Abre `tienda.mercadona.es` en Chrome
2. **DevTools** (F12) → **Network**
3. **Haz login** (si no lo estás)
4. **Click derecho** en área blanca → **Save all as HAR with content**
5. Guarda como `tienda.mercadona.es.har`
6. Comprimir (opcional pero recomendado):

```bash
zip tienda.mercadona.es.har.zip tienda.mercadona.es.har
```

7. Importar:

```bash
mercadona import-har --file tienda.mercadona.es.har
rm tienda.mercadona.es.har  # Borrar por seguridad
```

#### c) Verificar autenticación

```bash
mercadona whoami
# → ok — authenticated. customer id=...

mercadona cart get
# → cart ... (v1, 0 productos, total 0.00€)
```

✅ **Setup completo**

---

## 📖 Uso

### Opción A: Uso con Hermes Agent (recomendado)

Hermes orquesta todo el flujo automáticamente:

```bash
# Activar skill
hermes chat

# En el chat:
"Planifica el menú de esta semana con Cookidoo y Spoonacular, 
genera el recetario y añade la compra a Mercadona.
Presupuesto máximo: 80€"
```

Hermes ejecutará:
1. Planificación menú (7 días, recetas balanceadas)
2. Consolidación de ingredientes
3. Búsqueda en Mercadona
4. Preview del total (Gate 1: te muestra antes de añadir)
5. Tras tu confirmación → añade al carrito

---

### Opción B: Uso standalone (Python scripts)

#### 1. Crear shopping list JSON

```json
// shopping_list.json
[
  {
    "name": "tomate",
    "quantity": 6,
    "unit": "ud",
    "fresh": true,
    "category": null
  },
  {
    "name": "salmón",
    "quantity": 400,
    "unit": "g",
    "fresh": true,
    "category": "Marisco y pescado"
  }
]
```

#### 2. Resolver a productos Mercadona

```python
from scripts.mercadona_cli_wrapper import MercadonaCLI
import json

# Cargar shopping list
with open('shopping_list.json') as f:
    shopping_list = json.load(f)

# Resolver
cli = MercadonaCLI()
resolved = cli.resolve_shopping_list(shopping_list)

print(f"Resueltos: {len(resolved['resolved'])}/{len(shopping_list)}")
print(f"Total estimado: {resolved['total']}€")

for item in resolved["resolved"]:
    print(f"  • {item['product_name']} — {item['quantity']} × {item['unit_price']}€")
```

#### 3. Generar basket y preview

```python
# Generar basket.txt
basket_file = cli.generate_basket_file(
    resolved["resolved"], 
    "/tmp/basket.txt"
)

# Preview total (NO toca el carrito)
preview = cli.preview_total(basket_file)
print(f"Preview: {preview['total']}€ ({preview['count']} productos)")
```

#### 4. Añadir al carrito REAL

⚠️ **Esto SÍ modificará tu carrito de Mercadona**

```python
# Añadir con spending guard
result = cli.fill_cart(
    basket_file, 
    max_eur=80.0,      # Rechaza si supera 80€
    dry_run=False      # dry_run=True para simular
)

print(f"✓ Añadidos {result['products_count']} productos")
print(f"Total real: {result['summary']['total']}€")

# Verificar
cart = cli.get_cart()
```

#### 5. Limpiar (opcional)

```python
cli.clear_cart()
```

---

### Opción C: CLI directo (testing/debugging)

```bash
# Búsqueda batch
printf 'tomate\ncebolla\narroz\n' | mercadona batch -f - --fresh --json

# Preview de un basket
cat > /tmp/basket.txt << EOF
69975 2    # Tomates pera
69089 1    # Cebollas
5044  1    # Arroz redondo
EOF

mercadona total -f /tmp/basket.txt
# → total: 7.02€ (3 productos)

# Añadir al carrito
mercadona cart set-many -f /tmp/basket.txt --max 80

# Ver carrito
mercadona cart get

# Limpiar
mercadona cart clear
```

---

## 🔧 Configuración avanzada

### Variables de entorno (opcional)

```bash
# ~/.hermes/.env o export en tu shell

# Cookidoo (si usas Thermomix)
export COOKIDOUGH_EMAIL="tu@email.com"
export COOKIDOUGH_PASSWORD="..."
export COOKIDOUGH_COUNTRY="es"
export COOKIDOUGH_LANGUAGE="es"

# Spoonacular (si usas recetas tradicionales)
export SPOONACULAR_API_KEY="..."

# Salida de recetarios
export RECIPE_OUTPUT_PATH="/ruta/donde/guardar/recetas"
export RECIPE_FILENAME_PATTERN="{date}_menu.md"
```

### Warehouse personalizado

```bash
# Usar warehouse específico para comandos
mercadona search "tomate" --wh 4182

# O en Python
cli = MercadonaCLI(warehouse="4182")
```

---

## 📁 Estructura del proyecto

```
meal2cart/
├── scripts/
│   ├── mercadona_cli_wrapper.py       # Wrapper Python del CLI
│   ├── recipe_md_generator.py         # JSON → Markdown
│   ├── cookidough_client.py           # Cliente Cookidoo MCP
│   └── legacy/
│       └── mercadona_client.py        # (deprecated, Playwright)
├── prompts/
│   ├── menu_planning.md               # Prompt planificación
│   ├── ingredient_consolidation.md    # Prompt consolidación
│   └── recipe_format.md               # Schema recetas
├── references/
│   ├── mercadona-cli-setup.md         # Setup detallado
│   ├── mercadona-cli-usage.md         # Ejemplos de uso
│   ├── mercadona-cli-json-schemas.md  # Estructuras JSON
│   ├── spoonacular_setup.md
│   ├── cookidough_setup.md
│   └── ... (otros)
├── tests/
│   ├── test_e2e_mercadona_cli.py      # Test end-to-end
│   └── test_recipe_generator.py
├── SKILL.md                            # Documentación completa
├── config.yaml.example
└── README.md                           # Este archivo
```

---

## 🧪 Testing

### Test básico del wrapper

```bash
cd meal2cart/
python3 scripts/mercadona_cli_wrapper.py --test-search
# → 3/3 búsquedas correctas
```

### Test end-to-end

```bash
cd meal2cart/
PYTHONPATH=scripts:$PYTHONPATH python3 tests/test_e2e_mercadona_cli.py
# → 5/5 productos resueltos (100%)
```

### Test con carrito REAL

⚠️ **Esto añadirá 2 tomates a tu carrito**

```python
from scripts.mercadona_cli_wrapper import MercadonaCLI

cli = MercadonaCLI()
shopping_list = [
    {"name": "tomate", "quantity": 2, "unit": "ud", "fresh": True, "category": None}
]

resolved = cli.resolve_shopping_list(shopping_list)
basket_file = cli.generate_basket_file(resolved["resolved"], "/tmp/test.txt")

# Añadir
result = cli.fill_cart(basket_file, max_eur=10.0, dry_run=False)
print(f"✓ Total: {result['summary']['total']}€")

# Verificar en tienda.mercadona.es

# Limpiar
cli.clear_cart()
```

---

## 🐛 Troubleshooting

### `error: not authenticated`

Tu token expiró (~6 semanas). Re-hacer `import-curl`:

```bash
# Abrir tienda.mercadona.es → Copy as cURL → import-curl
mercadona import-curl --file /tmp/mercadona_curl.txt
```

### Productos no encontrados

**Problema:** Búsqueda muy genérica (ej. "carne" devuelve "carne de pimiento").

**Solución:** Ser más específico:

```python
# ❌ Muy genérico
{"name": "carne", ...}

# ✅ Específico
{"name": "pechuga pollo", "fresh": True, ...}
```

### `Invalid quantity 0.5 for a product sold by unit`

**Problema:** El producto se vende por unidad (botella, pack), no por peso.

**Solución:** Usar cantidad entera con `unit: "ud"`:

```python
# ❌ Incorrecto
{"name": "aceite oliva", "quantity": 0.5, "unit": "L"}

# ✅ Correcto
{"name": "aceite oliva", "quantity": 1, "unit": "ud"}
```

### Categorías incorrectas

**Problema:** `category: "Verdura"` no existe en Mercadona.

**Solución:** Usar nombres exactos o `null`:

```python
# ❌ Incorrecto
{"category": "Verdura"}

# ✅ Correcto
{"category": "Fruta y verdura"}
# o simplemente
{"category": null, "fresh": true}  # --fresh es suficiente
```

---

## 📊 Comparativa vs Playwright (legacy)

| Aspecto | Playwright (antes) | mercadona-cli (ahora) |
|---------|-------------------|----------------------|
| **Velocidad** | ~40s (8 búsquedas) | < 1s (**40× más rápido**) |
| **Cantidades** | ❌ Solo añade 1 ud | ✅ Cantidad exacta |
| **Spending guard** | ❌ No existe | ✅ `--max` rechaza |
| **Verificación** | ❌ No verifica | ✅ Lee total API |
| **Límite productos** | ~20 (SPA crash) | Ilimitado |
| **Mantenibilidad** | Selectores CSS (rotan) | API REST (estable) |

---

## 📚 Documentación adicional

- **Setup detallado:** `references/mercadona-cli-setup.md`
- **Ejemplos de uso:** `references/mercadona-cli-usage.md`
- **Estructuras JSON:** `references/mercadona-cli-json-schemas.md`
- **Skill completa:** `SKILL.md`

---

## 🤝 Contribuir

1. Fork el repo
2. Crea una branch (`git checkout -b feature/mejora`)
3. Commit tus cambios (`git commit -m 'feat: añadir X'`)
4. Push a la branch (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

---

## 🙏 Créditos

- **mercadona-cli** por [@ivorpad](https://github.com/ivorpad/mercadona-cli)
- **Cookidoo MCP** por comunidad Cookidoo
- **Hermes Agent** por [Nous Research](https://nousresearch.com)

---

**Hecho con ❤️ y 🤖 por Xavi**
