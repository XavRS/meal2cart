# Subagente A: generate — Recetario .md + Shopping List

## Tu tarea

Recibes un `menu.json` con 7 días de menú. Debes:

1. Ejecutar `recipe_md_generator.py` para generar el .md
2. Extraer la shopping list consolidada
3. Filtrar ingredientes con cantidad ≤ 0
4. Devolver resultados

## Input

El orquestador te pasará:
- `menu_json`: ruta absoluta del menu.json (ej. `/tmp/menu-2026-07-20.json`)
- `output_md`: ruta donde escribir el .md (ej. `/mnt/vault/Personal/Menjars/2026-07-20.md`)
- `skill_dir`: ruta base de la skill (para encontrar scripts)

## Pasos

### 1. Generar .md

```bash
python3 {skill_dir}/scripts/recipe_md_generator.py --input {menu_json} --output {output_md}
```

Verifica que el .md se ha creado (`ls -la {output_md}`).

### 2. Extraer shopping list

Lee el menu.json y extrae todos los ingredientes de todas las recetas.
Consolida duplicados (mismo nombre + misma unidad → sumar cantidades).

### 3. Filtrar qty ≤ 0

Elimina ingredientes con `amount == 0` o `quantity == 0`. Son ingredientes de despensa
(aceite, sal, pimienta) que Cookidoo marca con cantidad cero. Avisa de estos en `pantry_items`.

### 4. Clasificar por categoría

Agrupa en: `proteinas`, `verduras`, `despensa`, `condimentos`.

Usa estas heurísticas:
- PROTEINAS: salmón, pollo, merluza, huevo, jamón, atún, bacalao, ternera, cerdo, pavo
- VERDURAS: calabacín, cebolla, pimiento, ajo, zanahoria, tomate, patata, aguacate, limón, jengibre, cilantro, menta, perejil, puerro, berenjena, calabaza, espinaca, lechuga
- DESPENSA: arroz, quinoa, lentejas, leche de coco, caldo, pimiento asado, quesito
- CONDIMENTOS: el resto

### 5. Asignar campos para Mercadona

Para cada ingrediente, añade:
- `fresh`: true para verduras/carnes/pescados frescos, false para despensa/conservas
- `category`: categoría Mercadona (null si no estás seguro)
  - "Fruta y verdura", "Marisco y pescado", "Carnes y aves", "Conservas, caldos y cremas"
- `unit`: "ud" para productos por unidad, "g" para peso, "kg", "ml", "L"
  - REGLA: productos envasados (aceite, leche, conservas, pan) → "ud" con qty entera
  - 500ml aceite → `{"quantity": 1, "unit": "ud"}` (NO 0.5)

## Output

Devuelve un informe con esta estructura exacta:

```
## Resultados Subagente A

### .md generado
- Ruta: {output_md}
- Tamaño: {size}

### Shopping list consolidada
{pega el JSON completo de la shopping list}

### Items despensa (no comprar)
- {item1} (qty=0 en Cookidoo)
- {item2}

### Kcal semanales
- Total: {sum} kcal
- Media por cena: {avg} kcal
```

La shopping list JSON debe tener este formato:
```json
[
  {
    "name": "salmón fresco",
    "quantity": 400,
    "unit": "g",
    "fresh": true,
    "category": "Marisco y pescado"
  },
  {
    "name": "tomate",
    "quantity": 6,
    "unit": "ud",
    "fresh": true,
    "category": "Fruta y verdura"
  }
]
```

## Pitfalls

- NO uses qty decimales. Redondea a enteros.
- Productos envasados → "ud", NO "g"/"ml".
- Si el .md no se genera, reporta el error de stderr.
