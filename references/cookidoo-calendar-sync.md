# Cookidoo — Sincronización del calendario ("Mi semana")

Una vez planificado el menú, las recetas de Cookidoo pueden añadirse al
calendario "Mi semana" para que aparezcan automáticamente en la
Thermomix al sincronizar.

## Flujo

1. Planificar el menú → obtener los `recipe_id` de Cookidoo
2. Llamar a `add_recipes_to_calendar` para cada día
3. Verificar con `get_calendar_week`
4. Abrir la app de Thermomix → "Mi semana" → Sync

## Uso vía MCP

```python
# Añadir recetas a un día
call_tool(proc, "add_recipes_to_calendar", {
    "day": "2026-07-13",
    "recipe_ids": ["r505494"]
})

# Añadir múltiples al mismo día (ej. viernes con 3 platos)
call_tool(proc, "add_recipes_to_calendar", {
    "day": "2026-07-17",
    "recipe_ids": ["r505495", "r92771", "r236680"]
})

# Verificar la semana
week = call_tool(proc, "get_calendar_week", {"day": "2026-07-13"})
```

## Ejemplo real (sesión 2026-07-13)

```python
schedule = {
    "2026-07-13": ["r505494"],   # Gambas Piri-Piri
    "2026-07-14": ["r97361"],    # Gazpacho
    "2026-07-15": ["r729218"],   # Caprese Wraps
    "2026-07-16": ["r908611"],   # Salmorejo
    "2026-07-17": ["r505495", "r92771", "r236680"],  # Viernes 3 platos
}
```

## Notas

- `add_recipes_to_calendar` acepta un array de IDs → se pueden añadir
  varios platos al mismo día
- Usar `add_custom_recipes_to_calendar` para recetas propias (custom)
- Para eliminar: `remove_recipe_from_calendar`
- El calendario se visualiza en la app de Thermomix y en Cookidoo web
