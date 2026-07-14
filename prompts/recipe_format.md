# Plantilla — Formato del recetario Markdown (v2.2)

Esta plantilla define la SALIDA EXACTA que produce `scripts/recipe_md_generator.py`.

## Filosofía del layout

El .md tiene **dos secciones únicamente**:

1. **Cabecera + tabla resumen semanal arriba** (con kcal visibles).
2. **Recetas detalladas debajo**, cada una con: foto del plato, meta con kcal, descripción breve, ingredientes y pasos.

**Ya NO se incluye** en el .md: lista de la compra consolidada, resumen del carrito Mercadona, ni resúmenes nutricionales adicionales. Esas partes se gestionan aparte (vía `mercadona_cli_wrapper` y el flujo Gate 1/Gate 2 en Telegram).

## Estructura

````markdown
# 🍽️ Menú semanal — {día_inicio} al {día_fin} de {mes} de {año}
_{preferencias}_

## 📅 Resumen de la semana

| Día | Receta | Tiempo | kcal |
|-----|--------|--------|------|
| **Lunes {n}** | {emoji_fuente} {titulo} | {t} min | {kcal} kcal |
| ... (7 filas L-D) |

> 🍳 = Thermomix · 🥘 = Tradicional
> 🔥 Media: **~{avg} kcal/plato** · Total semanal: **~{total} kcal**

---

## 📋 Recetas detalladas

### {emoji_fuente} {Día} {n} · {slot}: {titulo}

![{titulo}]({image_url})

⏱️ **{t} min** · 👥 **{servings} personas** · 🔥 **{kcal} kcal/ración** · ⭐ **{rating}** · 🔗 [{Fuente}]({url})

> {descripción breve del plato en 1-2 frases}

### 🛒 Ingredientes
- {cantidad}{unidad} {ingrediente}
- ...

### 👨‍🍳 Preparación{ (Thermomix) si Cookidoo}
1. {paso}
2. {paso}

---

(repetir bloque por cada receta)

_Generado por Hermes Meal-to-Cart — {DD/MM/YYYY}_
````

## Reglas de formato

1. **Título H1**: `# 🍽️ Menú semanal — {rango de fechas}` (mes en español minúscula).
2. **Subtítulo**: preferencias en cursiva `_..._`. Si no hay, omitir.
3. **Tabla resumen**: 4 columnas fijas (Día, Receta, Tiempo, kcal). Si hay comidas Y cenas, cambia a 3 columnas (Día, Comida, Cena) con `(tiempo · kcal)` en cada celda. Días vacíos con `—`.
4. **Blockquote resumen**: leyenda de iconos + media/total kcal en negrita.
5. **Cabecera de receta**: `### {emoji_fuente} {Día} {n} · {slot}: {título}` — el emoji del día se elimina (redundante con el día ya nombrado); el emoji de fuente (🍳/🥘) va delante.
6. **Foto del plato**: `![{titulo}]({image_url})` inmediatamente debajo del header (línea vacía antes y después). Si no hay `image_url`, se omite.
7. **Meta con kcal**: badges en línea separados por ` · `, en este orden fijo: `⏱️ Xmin · 👥 X personas · 🔥 X kcal/ración · ⭐ X · 🔗 [Fuente](url)`. Todos los valores numéricos en **negrita**. `⭐` solo si hay rating. `🔥 kcal/ración` siempre — es requisito.
8. **Descripción**: blockquote `> ...` (opcional pero recomendado) entre meta e ingredientes.
9. **Ingredientes**: `### 🛒 Ingredientes` + lista `- {cantidad}{unidad} {nombre}`. Units: `g`→`400g`, `ml`→`200 ml`, `uds`→`5 uds` (singular `1 ud`), sin unidad → `- {nombre}`.
10. **Preparación**: `### 👨‍🍳 Preparación (Thermomix)` si `source=cookidoo`, sino `### 👨‍🍳 Preparación`. Pasos numerados `1. 2. ...` (el generador re-numera automáticamente — no incluir "1." en el texto de `steps`).
11. **Separador `---`**: entre tabla y sección de recetas, y entre cada receta.
12. **Footer**: `_Generado por Hermes Meal-to-Cart — {DD/MM/YYYY}_` en cursiva.

## Campos JSON obligatorios por receta

Para que el markdown salga bien:

- `title` (str)
- `source` (`"cookidoo"` | `"spoonacular"`)
- `url` (str)
- `image_url` (str) — **muy recomendado**, sin él la ficha pierde impacto visual
- `time_minutes` (int)
- `servings` (int)
- `calories_per_serving` (int) — **obligatorio**, se muestra tanto en la tabla como en la meta
- `ingredients` (`[{name, amount, unit}]`)
- `steps` (`[str]` sin numeración previa)

Opcionales pero recomendados:

- `description` (str, 1-2 frases)
- `rating` (float)

## Ejemplo mínimo

````markdown
# 🍽️ Menú semanal — 20 al 26 de julio de 2026
_2 personas · Mediterránea · sin gluten_

## 📅 Resumen de la semana

| Día | Receta | Tiempo | kcal |
|-----|--------|--------|------|
| **Lunes 20** | 🍳 Salmón al vapor | 25 min | 480 kcal |
| ...

> 🍳 = Thermomix · 🥘 = Tradicional
> 🔥 Media: **~450 kcal/plato** · Total semanal: **~3.150 kcal**

---

## 📋 Recetas detalladas

### 🍳 Lunes 20 · Cena: Salmón al vapor con verduras

![Salmón al vapor con verduras](https://assets.tmecosys.com/image/upload/t_web767x639/img/recipe/ras/Assets/715538.jpg)

⏱️ **25 min** · 👥 **2 personas** · 🔥 **480 kcal/ración** · ⭐ **4.5** · 🔗 [Cookidoo](https://cookidoo.es/recipes/715538)

> Salmón jugoso al vapor sobre lecho de verduras variadas, ligero y rápido.

### 🛒 Ingredientes
- 400g salmón fresco
- 2 uds de calabacín

### 👨‍🍳 Preparación (Thermomix)
1. Cortar los calabacines
2. Cocer al vapor 20 min / Varoma

---

_Generado por Hermes Meal-to-Cart — 14/07/2026_
````
