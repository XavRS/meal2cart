# 🍽️ Meal-to-Cart

**Planificación de menús semanales automatizada con compra en Mercadona Online.**

Combina recetas de **Cookidoo** (Thermomix) y **Spoonacular** (cocina tradicional) para generar un menú semanal, consolidar la lista de compra y añadirla automáticamente al carrito de Mercadona. Usa **subagentes** para procesamiento pesado.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Características

- 🗓️ **Planificación semanal** con recetas reales de Cookidoo y Spoonacular
- 📱 **Sync automático** a calendario Thermomix "Mi semana"
- 📝 **Recetario Markdown** con tabla semanal, ingredientes, pasos y fotos de los platos
- 🤖 **Subagentes** para generación .md, resolución Mercadona y fill_cart (contexto aislado)
- 🛒 **Automatización Mercadona** vía API REST (40× más rápido que scraping)
- 💰 **Spending guard** nativo (rechaza si supera presupuesto)
- ✅ **Gate 1 obligatorio**: preview antes de tocar el carrito real

---

## 🏗️ Arquitectura (v3.0)

```
Hermes (orquestador)
  ├── Fase 1: Planificar menú (interactivo con Xavi, MCP)
  ├── Fase 2: Sync Cookidoo calendar
  ├── Subagente A → generar .md + shopping list
  ├── Subagente B → resolver Mercadona + basket preview
  ├── Gate 1: Preview → Xavi revisa → OK
  └── Subagente C → fill_cart
```

---

## 📁 Estructura del proyecto

```
meal2cart/
├── scripts/
│   ├── mercadona_cli_wrapper.py       # Wrapper Python del CLI
│   └── recipe_md_generator.py         # JSON → Markdown
├── prompts/
│   ├── subagent-generate.md           # Prompt subagente A
│   ├── subagent-resolve.md            # Prompt subagente B
│   └── subagent-fill.md               # Prompt subagente C
├── references/
│   ├── cart-quantity-rules.md         # Reglas de cantidades enteras
│   ├── cookidoo-calendar-sync.md      # Sync calendario Cookidoo
│   ├── cookidoo-zero-quantity-ingredients.md
│   ├── gate1-approval-pattern.md      # Patrón de Gate 1
│   ├── mercadona-cli-setup.md         # Setup detallado
│   ├── mercadona-product-substitutions.md
│   ├── product-search-mismatches.md   # Falsos positivos de batch
│   ├── public-repo-guidelines.md
│   └── spoonacular_setup.md
├── tests/
│   └── test_e2e_mercadona_cli.py
├── SKILL.md                            # Documentación completa (orquestador)
├── CHANGELOG.md
└── README.md
```

---

## 📋 Requisitos

### Software

- **Python 3.11+**
- **Node.js 18+** (para mercadona-cli)
- **mercadona-cli** (`npm install -g @ivorpad/mercadona`)
- **Hermes Agent** (para orquestación con subagentes)

### Cuentas y APIs

- **Cuenta Mercadona** (con login Google SSO)
- **Cuenta Cookidoo** (si usas Thermomix)
- **API key Spoonacular** (opcional, tier gratuito 150 req/día)

---

## 🚀 Instalación

### 1. Instalar mercadona-cli

```bash
npm install -g @ivorpad/mercadona
mercadona version
```

### 2. Clonar

```bash
git clone https://github.com/XavRS/meal2cart.git ~/.hermes/skills/meal-to-cart
```

### 3. Configurar mercadona-cli

```bash
mercadona set-postal 08001
# Autenticación vía "Copy as cURL" desde Chrome DevTools:
mercadona import-curl --file /tmp/mercadona_curl.txt
```

---

## 📖 Uso con Hermes

```bash
hermes chat
# "Planifica el menú de esta semana. Presupuesto: 80€"
```

Hermes ejecuta:
1. Planificación interactiva (recetas Cookidoo + Spoonacular)
2. Sync al calendario Thermomix
3. **Subagente A**: genera recetario .md + shopping list
4. **Subagente B**: resuelve productos Mercadona + preview
5. **Gate 1**: te muestra total → espera OK
6. **Subagente C**: fill_cart al carrito real

---

## 🧪 Testing

```bash
# Test del wrapper
python3 scripts/mercadona_cli_wrapper.py --test-search

# Test e2e
PYTHONPATH=scripts:$PYTHONPATH python3 tests/test_e2e_mercadona_cli.py
```

---

## 🐛 Troubleshooting

### `error: not authenticated`
Token expiró (~6 semanas). Re-hacer `import-curl`.

### `Invalid quantity X for a product sold by unit`
Cantidades deben ser ENTERAS. Ver `references/cart-quantity-rules.md`.

### Productos no encontrados
Ser más específico en la query. Batch `--fresh` puede devolver falsos positivos (patata→fritas). Ver `references/product-search-mismatches.md`.

---

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE)

## 🙏 Créditos

- **mercadona-cli** por [@ivorpad](https://github.com/ivorpad/mercadona-cli)
- **Hermes Agent** por [Nous Research](https://nousresearch.com)
