# Changelog

## [2.1.0] - 2026-07-14

### ✨ Añadido
- **Soporte de imágenes en recetarios markdown**: El generador ahora incluye automáticamente fotos de los platos cuando el campo `image_url` está presente en el JSON de cada receta.
- Nueva función `render_recipe_image()` en `recipe_md_generator.py` para renderizar imágenes.
- Actualizado `render_recipe_header()` para incluir el slot (Comida/Cena) dinámicamente.
- Nueva referencia `references/recipe-image-urls.md` con documentación completa sobre cómo obtener URLs de imágenes de Cookidoo y Spoonacular.

### 📝 Documentación
- `prompts/recipe_format.md`: Nueva regla #6 para el formato de imágenes.
- `prompts/menu_planning.md`: Instrucciones actualizadas para construir `image_url` al planificar el menú:
  - **Cookidoo**: Construcción de URL desde recipe ID: `https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/{recipe_id}.jpg`
  - **Spoonacular**: Usar directamente el campo `image` de la API
- `README.md`: Característica destacada en la sección de características principales.
- `SKILL.md`: Versión actualizada y nueva funcionalidad documentada.

### 🧪 Testing
- Tests validados con JSON de ejemplo que incluyen ambas fuentes (Cookidoo y Spoonacular).
- Verificado que el generador maneja correctamente recetas con y sin `image_url`.

### 🔄 Comportamiento
- **Retrocompatible**: Si el campo `image_url` no está presente, simplemente se omite la imagen sin afectar el resto del recetario.
- Las imágenes se renderizan en markdown justo después del título de la receta, antes de los metadatos.

---

## [2.0.0] - 2026-07-14

### 🚀 Migración mercadona-cli
- Migración completa de Playwright a `mercadona-cli` (40× más rápido).
- Wrapper Python operativo (`scripts/mercadona_cli_wrapper.py`).
- Test end-to-end con carrito real: 9/9 productos, 20.95€ (100% éxito).
- Playwright archivado en `scripts/legacy/` con documentación de deprecación.

### 📚 Referencias
- Nueva estructura de documentación con 20+ referencias técnicas.
- Sesiones e2e documentadas como referencias de calidad.
- Patrón CLI wrapper reusable documentado.

### 🐛 Fixes críticos
- Conversión g→kg mejorada en wrapper (usa `reference_format`).
- Eliminación de campos `category` problemáticos.
- Manejo correcto de cantidades decimales (Gate 1).
- Filtrado de ingredientes con quantity=0 de Cookidoo.

---

## [1.0.0] - 2026-07-13

### 🎉 Primera versión
- Planificación de menú semanal con Cookidoo y Spoonacular.
- Generación de recetarios Markdown.
- Integración con Mercadona vía Playwright (legacy).
- Consolidación de lista de la compra.
