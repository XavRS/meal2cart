# Referencias — URLs de imágenes de recetas

> Documentación sobre cómo obtener y construir las URLs de imágenes para las recetas de Cookidoo y Spoonacular.

## Implementado 2026-07-14

El generador de markdown (`scripts/recipe_md_generator.py`) ahora incluye automáticamente imágenes de los platos cuando el campo `image_url` está presente en el JSON de la receta.

## Estructura del JSON

Cada receta en el JSON del menú debe incluir opcionalmente:

```json
{
  "title": "Ensalada César con Pollo",
  "source": "spoonacular",
  "image_url": "https://spoonacular.com/recipeImages/123-556x370.jpg",
  ...
}
```

Si `image_url` está presente, se renderiza en el markdown como:

```markdown
## 🐟 Lunes 20 — Cena: Ensalada César con Pollo 🥘

![Ensalada César con Pollo](https://spoonacular.com/recipeImages/123-556x370.jpg)

⏱️ 20 min | 👥 2 personas | ...
```

## Fuentes de imágenes

### Cookidoo (Thermomix)

**Patrón de URL:**
```
https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/{RECIPE_ID}.jpg
```

**Cómo obtener el ID:**
1. La URL de una receta de Cookidoo tiene el formato:
   ```
   https://cookidoo.es/recipes/recipe/es-ES/r123456
   ```
2. Extraer el ID numérico (sin la `r`): `r123456` → `123456`
3. Construir la URL de la imagen: `https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/123456.jpg`

**Ejemplo:**
- Receta: `https://cookidoo.es/recipes/recipe/es-ES/r715538`
- ID: `715538`
- Imagen: `https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/715538.jpg`

**Transformaciones disponibles:**
El CDN de Cookidoo (tmecosys) permite varias transformaciones. Las más útiles:
- `t_web767x639` — tamaño web grande (usado actualmente)
- `t_web480x400` — tamaño web medio
- `t_web320x256` — tamaño web pequeño

**Nota:** No todas las recetas tienen imagen disponible. Si la URL devuelve 404, el markdown mostrará un placeholder roto (el usuario puede omitir `image_url` en ese caso).

### Spoonacular

**Campo de API:**
La API de Spoonacular ya devuelve la URL de la imagen directamente en el campo `image` de cada receta.

**Ejemplo de respuesta:**
```json
{
  "id": 123,
  "title": "Caesar Salad",
  "image": "https://spoonacular.com/recipeImages/123-556x370.jpg",
  ...
}
```

**Cómo usar:**
1. Al llamar a `spoonacular.complexSearch` o `spoonacular.getRecipeInformation`, el campo `image` contiene la URL directa.
2. Copiar directamente a `image_url` en el JSON del menú.

**Tamaños disponibles:**
Spoonacular ofrece varios tamaños. Modificar el sufijo de la URL:
- `123-556x370.jpg` — tamaño grande (por defecto)
- `123-480x360.jpg` — tamaño medio
- `123-312x231.jpg` — tamaño pequeño
- `123-90x90.jpg` — thumbnail

**Nota:** Si la receta no tiene imagen, Spoonacular devuelve `null` o una imagen placeholder genérica.

## Implementación en el flujo

### Planificación del menú (prompts/menu_planning.md)

Al construir el JSON del menú, Hermes debe:

1. **Para recetas Cookidoo:**
   ```python
   recipe_url = "https://cookidoo.es/recipes/recipe/es-ES/r715538"
   recipe_id = recipe_url.split('/')[-1].lstrip('r')  # "715538"
   image_url = f"https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/{recipe_id}.jpg"
   ```

2. **Para recetas Spoonacular:**
   ```python
   # La API ya devuelve el campo "image"
   image_url = spoonacular_recipe["image"]
   ```

3. **Añadir al JSON:**
   ```json
   {
     "title": "...",
     "image_url": "https://...",
     ...
   }
   ```

### Generación del markdown (scripts/recipe_md_generator.py)

El generador ya implementa (desde v2.1.0):

```python
def render_recipe_image(meal: dict[str, Any]) -> str:
    """Renderiza la imagen de la receta si existe."""
    image_url = meal.get("image_url")
    if not image_url:
        return ""
    return f"\n![{meal.get('title', 'Foto del plato')}]({image_url})\n"
```

Se llama automáticamente en `render_menu()` después del header de cada receta.

## Verificación manual

### Cookidoo
```bash
curl -I "https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/715538.jpg"
# → HTTP 200 OK (imagen existe)
# → HTTP 404 (imagen no disponible)
```

### Spoonacular
```bash
curl -I "https://spoonacular.com/recipeImages/123-556x370.jpg"
# → HTTP 200 OK
```

## Fallback

Si la imagen no existe o la URL es incorrecta:
- El markdown incluirá `![titulo](url_rota)` que se renderiza como placeholder roto en el visualizador.
- **Solución:** Omitir el campo `image_url` del JSON cuando la imagen no esté disponible. El generador simplemente no renderiza la sección de imagen.

## Mejoras futuras

1. **Validación de URLs** antes de incluirlas en el JSON (verificar HTTP 200).
2. **Cache local** de imágenes para uso offline.
3. **Thumbnails en la tabla semanal** (requeriría cambio de formato en la tabla markdown).
4. **Imágenes personalizadas** subidas por el usuario para recetas custom.

## Testing

Ver `/tmp/test_menu_images.json` para un ejemplo de JSON con imágenes de ambas fuentes.

```bash
cd /tmp/hermes-meal-to-cart
python3 scripts/recipe_md_generator.py --input /tmp/test_menu_images.json --stdout
```

Verificar que las imágenes se renderizan correctamente en el markdown output.
