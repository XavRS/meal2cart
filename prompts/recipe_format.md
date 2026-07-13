# Plantilla — Formato del recetario Markdown

Esta plantilla define la SALIDA EXACTA que debe producir `scripts/recipe_md_generator.py`. Hermes la usa al presentar/volcar el recetario.

## Estructura

````markdown
# Menú semanal — {día_inicio} al {día_fin} de {mes} de {año}
**{preferencias}**

## 📅 Tabla semanal

| Día | Comida | Cena |
|-----|--------|------|
| **Lunes {n}** | {emoji_comida} {titulo} ({tiempo} min) ⭐{rating} — {kcal} kcal | {emoji_cena} {titulo} ({tiempo} min) ⭐{rating} — {kcal} kcal |
| **Martes {n}** | ... | ... |
| ... (7 filas, L-D) |

> 🍳 = Thermomix, 🥘 = Tradicional
> 🔥 Media: ~{avg} kcal/cena | Total semanal: ~{total} kcal
> 📅 Las recetas 🍳 están sincronizadas en Cookidoo → disponibles en tu Thermomix

---

## {emoji_día} {Día} {n} — {slot}: {titulo} {emoji_fuente}
⏱️ {tiempo} min | 👥 {servings} personas | 🔥 {kcal} kcal/ración | 🔗 [{Fuente}]({url})

### Ingredientes
- {cantidad}{unidad} {ingrediente}
- ...

### Preparación{ (Thermomix) si Cookidoo}
1. {paso}
2. {paso}
...

---

(repetir bloque por cada receta)

---

## 📊 Lista de la compra consolidada

### 🥩 Proteínas
| Ingrediente | Cantidad | Para recetas |
|-------------|----------|--------------|
| ... | ... | L, M, ... |

### 🥬 Verduras y frutas
| Ingrediente | Cantidad | Para recetas |
|-------------|----------|--------------|
| ... | ... | ... |

### 🥫 Despensa
| Ingrediente | Cantidad | Para recetas |
|-------------|----------|--------------|
| ... | ... | ... |

### 🧂 Condimentos y básicos
| Ingrediente | Cantidad | Para recetas |
|-------------|----------|--------------|
| ... | — (comprobar stock) | Varias |

---

*Generado por Hermes Meal-to-Cart — {DD/MM/YYYY}*
````

## Reglas de formato

1. **Título**: `# Menú semanal — {d_init} al {d_end} de {mes_nombre} de {año}` (mes en español minúscula: enero, febrero, …).
2. **Subtítulo**: preferencias en negrita. Si no hay, omitir la línea.
3. **Tabla**: siempre 7 filas. Si falta slot, usar `—`.
4. **Iconos celdas**: 🍳 Cookidoo / 🥘 Spoonacular. `⭐{rating}` sólo si hay rating. `— {kcal} kcal` siempre (si falta, omítelo).
5. **Cabecera de receta**: `## {emoji_día} {Día} {día_num} — {slot}: {título} {emoji_fuente}`
   - `emoji_día`: 🐟 L, 🥣 M, 🍛 X, 🐸 J, 🥑 V, 🐟 S, 🍳 D
   - `slot`: "Comida" o "Cena" (capitalizado).
6. **Meta**: `⏱️ N min | 👥 N personas | 🔥 N kcal/ración | 🔗 [Cookidoo|Spoonacular](url)` — separador ` | `, N como entero.
7. **Ingredientes**: lista `- {cantidad}{unidad} {nombre}`. Units:
   - `g` → `400g` (sin espacio)
   - `ml` → `200 ml`
   - `uds` → `5 uds` (singular `1 ud`)
   - sin unidad → `- {nombre}`
8. **Preparación**: header `### Preparación (Thermomix)` si `source=cookidoo`, sino `### Preparación`.
9. **Pasos**: numerados `1. ... 2. ...` (sin reset entre recetas no — sí reset por receta).
10. **Separador**: `---` entre recetas, entre tabla y recetas, y entre recetas y lista.
11. **Lista de la compra**: 4 tablas fijas (Proteínas, Verduras y frutas, Despensa, Condimentos y básicos), aunque estén vacías se muestran con fila `| — | — | — |`.
12. **Letras recetas**: L,M,X,J,V,S,D. Si un ingrediente se usa en muchas, mostrar todas separadas por `, `.
13. **Footer**: `*Generado por Hermes Meal-to-Cart — {DD/MM/YYYY}*` con fecha del día de generación.

## Ejemplo mínimo

````markdown
# Menú semanal — 13 al 19 de julio de 2026
**2 personas | Mediterránea | 30 min max | Sin gluten**

## 📅 Tabla semanal

| Día | Comida | Cena |
|-----|--------|------|
| **Lunes 13** | — | 🍳 Salmón al vapor (25 min) ⭐4.5 — 480 kcal |
...

---

## 🐟 Lunes 13 — Cena: Salmón al vapor con verduras 🍳
⏱️ 25 min | 👥 2 personas | 🔥 480 kcal/ración | 🔗 [Cookidoo](https://cookidoo.es/recipes/715538)

### Ingredientes
- 400g salmón fresco
- 2 uds de calabacín

### Preparación (Thermomix)
1. Cortar los calabacines
2. Cocer al vapor 20 min / Varoma

---
````

Ver `references/ejemplo_menu_semanal.md` para un ejemplo completo de 7 días.