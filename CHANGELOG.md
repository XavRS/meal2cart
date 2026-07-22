# Changelog

## [3.0.0] - 2026-07-22

### 🏗️ Refactor a subagentes
- **Arquitectura delegada**: Flujo partido en 3 subagentes (generate, resolve, fill) orquestados por Hermes.
- **SKILL.md reescrito** como orquestador: Hermes interactúa con Xavi y MCP Cookidoo; subagentes procesan.
- **Nuevos prompts**: `subagent-generate.md`, `subagent-resolve.md`, `subagent-fill.md`.
- **Nuevas references**: `cart-quantity-rules.md`, `product-search-mismatches.md`.

### 🧹 Limpieza masiva
- **Eliminado `cookidough_client.py`**: Hermes usa MCP tools directamente, no necesita wrapper Python.
- **Eliminados 16 references obsoletas**: session logs, duplicados, patrones ya documentados, selectores Playwright legacy.
- **Eliminados prompts viejos**: `menu_planning.md`, `ingredient_consolidation.md`, `recipe_format.md` (subsumidos por subagentes).
- **Eliminado `scripts/legacy/`** y `mercadona_client.py` (Playwright deprecated).

### 📦 Resultado
- 33 archivos → 18 archivos
- 25 references → 9 references
- ~10K tokens de contexto → ~2K (el resto va a subagentes aislados)

---

## [2.1.0] - 2026-07-14

### ✨ Añadido
- **Soporte de imágenes en recetarios markdown**: El generador ahora incluye automáticamente fotos de los platos cuando el campo `image_url` está presente en el JSON de cada receta.
- Nueva función `render_recipe_image()` en `recipe_md_generator.py` para renderizar imágenes.
- Actualizado `render_recipe_header()` para incluir el slot (Comida/Cena) dinámicamente.
- Nueva referencia `references/recipe-image-urls.md` con documentación completa sobre cómo obtener URLs de imágenes de Cookidoo y Spoonacular.

### 📝 Documentación
- `prompts/recipe_format.md`: Nueva regla #6 para el formato de imágenes.
- `prompts/menu_planning.md`: Instrucciones actualizadas para construir `image_url` al planificar el menú.
- `README.md`: Característica destacada en la sección de características principales.

### 🔄 Comportamiento
- **Retrocompatible**: Si el campo `image_url` no está presente, simplemente se omite la imagen sin afectar el resto del recetario.

---

## [2.0.0] - 2026-07-14

### 🚀 Migración mercadona-cli
- Migración completa de Playwright a `mercadona-cli` (40× más rápido).
- Wrapper Python operativo (`scripts/mercadona_cli_wrapper.py`).
- Test end-to-end con carrito real: 9/9 productos, 20.95€ (100% éxito).

### 🐛 Fixes críticos
- Conversión g→kg mejorada en wrapper (usa `reference_format`).
- Filtrado de ingredientes con quantity=0 de Cookidoo.

---

## [1.0.0] - 2026-07-13

### 🎉 Primera versión
- Planificación de menú semanal con Cookidoo y Spoonacular.
- Generación de recetarios Markdown.
- Integración con Mercadona vía Playwright (legacy).
