# Cookidoo Ingredientes con Cantidad 0

**Problema identificado:** 2026-07-14 (sesión menú ensaladas jueves-domingo)

## Síntoma

Cuando extraes ingredientes de recetas de Cookidoo vía `cookidough_client.get_recipe()`, algunos ingredientes aparecen con `quantity: 0` o sin el campo `quantity`.

**Ejemplo real (r77976 — Ensalada campera con naranja):**

```json
{
  "ingredients": [
    {"name": "agua", "quantity": 400, "unit": "ml"},
    {"name": "huevos", "quantity": 4, "unit": "ud"},
    {"name": "patatas", "quantity": 200, "unit": "g"},
    {"name": "zanahorias", "quantity": 200, "unit": "g"},
    {"name": "diente de ajo", "quantity": 1, "unit": "ud"},
    {"name": "perejil fresco", "quantity": 20, "unit": "g"},
    {"name": "pimiento verde", "quantity": 1, "unit": "ud"},
    {"name": "aceitunas verdes sin hueso", "quantity": 50, "unit": "g"},
    {"name": "aceite de oliva virgen extra", "quantity": 20, "unit": "g"},
    {"name": "vinagre de Jerez", "quantity": 10, "unit": "g"},
    {"name": "sal fina", "quantity": 2, "unit": "g"},
    {"name": "atún en aceite de girasol", "quantity": 160, "unit": "g"},
    {"name": "yemas de espárragos", "quantity": 140, "unit": "g"},
    {"name": "naranja", "quantity": 1, "unit": "ud"},
    {"name": "pimiento rojo", "quantity": 1, "unit": "ud"}
  ]
}
```

Tras consolidar varias recetas, los ingredientes con cantidades pequeñas de gramos (aceite, vinagre, sal) o que la API no devuelve correctamente terminan con `quantity: 0` en la shopping list consolidada.

**Output del script 2026-07-14:**
- Total ingredientes consolidados: **39**
- Ingredientes con quantity > 0: **15**
- Ingredientes con quantity = 0: **24**

## Causa Raíz

1. **Ingredientes de despensa:** La API de Cookidoo a veces NO devuelve cantidad para ingredientes básicos (aceite, sal, vinagre, pimienta, azúcar).
2. **Consolidación defectuosa:** Si dos recetas usan "aceite de oliva" pero con unidades diferentes (ml vs g), la consolidación puede no sumar correctamente y dejar uno con qty=0.
3. **Ingredientes auxiliares:** Ingredientes como "agua", "hielo", "cerveza" (usados en aliños pero no críticos) pueden venir sin cantidad.

## Consecuencia

Si pasas la shopping list directa a `mercadona_cli_wrapper.resolve_shopping_list()`, el wrapper intenta buscar **todos** los ingredientes (incluyendo los de qty=0), y luego `generate_basket_file()` escribe líneas como:

```
4740 0  # Aceite de oliva virgen extra Hacendado
```

Cuando ejecutas `mercadona total -f basket.txt`, falla con:

```
error: line 19: invalid qty "0" (want a positive number)
```

## Solución

### Paso 1: Filtrar antes de Mercadona

```python
# Cargar shopping list consolidada
with open('shopping_list.json', 'r') as f:
    shopping_list = json.load(f)

# FILTRAR cantidades <= 0 ANTES de resolver
shopping_list_clean = [
    item for item in shopping_list 
    if item.get('quantity', 0) > 0
]

print(f"Productos originales: {len(shopping_list)}")
print(f"Productos con cantidad > 0: {len(shopping_list_clean)}")

# Resolver solo los válidos
mercadona = MercadonaCLI()
resolved = mercadona.resolve_shopping_list(shopping_list_clean)
```

### Paso 2: Avisar al usuario de ingredientes faltantes

Genera una sección "Ingredientes Faltantes" en el documento final para que el usuario sepa qué NO está en el carrito:

```python
faltantes = [
    item for item in shopping_list 
    if item.get('quantity', 0) <= 0
]

if faltantes:
    print("\n⚠️ Ingredientes faltantes (quantity=0, NO en carrito):")
    for item in faltantes:
        print(f"  - {item['name']}")
```

### Paso 3: Clasificar ingredientes faltantes

**Despensa (asumir en casa):**
- Aceite de oliva
- Vinagre (cualquier tipo)
- Sal
- Pimienta
- Azúcar
- Agua

**Principales (AVISAR para añadir manualmente):**
- Huevos
- Patatas
- Atún en lata
- Espárragos
- Naranjas
- Pimientos
- Aceitunas verdes
- Quinoa
- Manzanas

## Patrón Completo (Pre-Gate-1)

```python
# 1. Consolidar ingredientes (output puede tener qty=0)
shopping_list = consolidate_ingredients(menu_plan)

# 2. Separar válidos vs faltantes
shopping_list_clean = [i for i in shopping_list if i.get('quantity', 0) > 0]
faltantes = [i for i in shopping_list if i.get('quantity', 0) <= 0]

# 3. Clasificar faltantes
despensa = ['aceite', 'vinagre', 'sal', 'pimienta', 'azúcar', 'agua']
faltantes_criticos = [
    f for f in faltantes 
    if not any(d in f['name'].lower() for d in despensa)
]

# 4. Resolver en Mercadona (solo válidos)
mercadona = MercadonaCLI()
resolved = mercadona.resolve_shopping_list(shopping_list_clean)

# 5. Generar basket y validar cantidades decimales (Pitfall #9)
basket_file = mercadona.generate_basket_file(resolved['resolved'], '/tmp/basket.txt')

# 6. Validar decimales y redondear
validate_and_round_quantities(basket_file)  # Ver Pitfall #9

# 7. Preview Gate 1
preview = mercadona.preview_total(basket_file)

# 8. Mostrar al usuario con advertencias
print(f"Total: {preview['total']}€ ({preview['count']} productos)")

if faltantes_criticos:
    print(f"\n⚠️ INGREDIENTES FALTANTES ({len(faltantes_criticos)}):")
    print("Debes añadir manualmente:")
    for f in faltantes_criticos:
        print(f"  - {f['name']}")
```

## Ejemplo Real (2026-07-14)

**Input:** Menú ensaladas jueves-domingo (4 recetas: 2 Cookidoo + 2 manuales)

**Consolidación:**
- Total ingredientes: 39
- Cantidad > 0: 15
- Cantidad = 0: 24

**Faltantes críticos:**
- Huevos (4 ud)
- Patatas (200g)
- Atún en lata (160g)
- Espárragos (140g)
- Naranja (1 ud)
- Pimiento rojo (1 ud)
- Pimiento verde (1 ud)
- Aceitunas verdes (50g)
- Quinoa cocida (300g)
- Manzana Granny Smith (1 ud)
- Queso untar finas hierbas (100g)

**Carrito inicial (tras filtrado qty>0):**
- 15 productos
- Total: 23.82€
- **INCOMPLETO** — falta ~40€ de ingredientes

**Completado manualmente (tras search individual):**
- Añadidos 15 productos más (los faltantes críticos)
- Total: 68.83€ (31 productos)
- **COMPLETO** — todos los ingredientes necesarios para el menú

**Nota:** `mercadona batch --fresh` devolvió nulls para los 15 faltantes → fallback a `mercadona search '<query>' --json --limit 1` individual para cada uno (ver Pitfall #11).

## Lecciones

1. **Siempre filtrar quantity > 0 antes de Mercadona** — no asumir que la consolidación produce lista limpia.
2. **Gate 1 debe mostrar ingredientes faltantes explícitamente** — el usuario necesita saber que el carrito está incompleto.
3. **Ingredientes de despensa pueden omitirse** — asumir que aceite, sal, vinagre están en casa.
4. **Ingredientes principales con qty=0 son bugs críticos** — el menú no es ejecutable sin ellos.

## Mejora Futura

**Opción 1:** Mejorar lógica de consolidación para manejar ingredientes sin cantidad (asignar 1 por defecto si es crítico).

**Opción 2:** Añadir paso de validación post-extracción que detecte ingredientes principales sin cantidad y pida al usuario que los especifique manualmente.

**Opción 3:** Mantener base de datos de cantidades típicas por ingrediente (ej: "huevos" → default 4 ud, "aceite" → default 1 botella).

---

**Referencias:**
- Sesión completa: `/mnt/vault/Personal/Menjars/2026-07-17.md`
- Script usado: `/tmp/meal_plan_ensaladas_flow.py`
- Shopping list original: `/tmp/shopping_list_ensaladas.json`
- Shopping list limpia: `/tmp/shopping_list_ensaladas_clean.json`
- Basket final: `/tmp/basket_ensaladas_final.txt`
