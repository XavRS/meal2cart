# Gate 1 Approval Document Pattern

**Contexto:** Tras generar el preview de Mercadona (Gate 1), es útil crear un documento de aprobación estructurado que Xavier puede revisar antes de ejecutar Gate 2 (añadir al carrito).

**Cuándo usar:** Siempre que el total estimado > 50€ o haya >20 productos, o cuando el menú incluye recetas Cookidoo (para confirmar que las recetas están correctamente añadidas al calendario).

## Template del Documento

```markdown
╔══════════════════════════════════════════════════════════════╗
║      MENÚ [NOMBRE] - OBSERVACIONES IMPORTANTES               ║
╚══════════════════════════════════════════════════════════════╝

Hola [Usuario],

El menú semanal está listo para tu revisión (Gate 1).

═══════════════════════════════════════════════════════════════
📊 RESUMEN EJECUTIVO
═══════════════════════════════════════════════════════════════

✅ [N] recetas Cookidoo añadidas al calendario "Mi semana"
✅ [N]/[N] productos resueltos en Mercadona (100%)
💰 Total: [XX.XX]€
📄 Resumen: [path/to/summary.md]

═══════════════════════════════════════════════════════════════
⚠️  PUNTOS A REVISAR
═══════════════════════════════════════════════════════════════

[Listar aquí:]
- Sustituciones automáticas (ej: albahaca → pesto)
- Cantidades pequeñas convertidas (ej: 200g quesos)
- Productos ambiguos que pueden no ser el esperado
- Productos cocidos vs crudos
- Cualquier anomalía en el matching

═══════════════════════════════════════════════════════════════
✅ COSAS QUE ESTÁN BIEN
═══════════════════════════════════════════════════════════════

• Todas las recetas TM añadidas al calendario ANTES de Mercadona
• Formato shopping list correcto (ud para packs, g/kg para frescos)
• Sin errores de conversión g→unidades
• Todas las búsquedas con flag --fresh
• Preview total dentro del presupuesto

═══════════════════════════════════════════════════════════════
📋 PRÓXIMOS PASOS (tras tu aprobación)
═══════════════════════════════════════════════════════════════

Si todo OK:
   mercadona cart set-many -f /tmp/basket.txt --max [MAX]

Si necesitas ajustes:
   - Avísame qué productos quieres cambiar
   - Regenero el basket.txt
   - Nuevo preview (Gate 1)

═══════════════════════════════════════════════════════════════
🔧 ARCHIVOS DE TRABAJO
═══════════════════════════════════════════════════════════════

/tmp/basket.txt                      → Listo para mercadona-cli
/tmp/shopping_list.json              → Lista consolidada original
/tmp/mercadona_resolved.json         → Productos resueltos (JSON)
/tmp/preview.json                    → Preview data
/tmp/cookidoo_recipes_details.json   → Recetas Cookidoo completas

═══════════════════════════════════════════════════════════════

¿Aprobado para Gate 2 (añadir al carrito)?
```

## Elementos Clave

1. **Resumen ejecutivo**: stats rápidas (recetas, productos, total)
2. **Puntos a revisar**: SIEMPRE incluir sustituciones automáticas y cantidades pequeñas
3. **Cosas que están bien**: refuerzo positivo de que las reglas críticas se cumplieron
4. **Próximos pasos**: comando exacto para Gate 2
5. **Archivos de trabajo**: paths completos para referencia

## Ejemplo Real

Ver sesión 2026-07-14: menú ensaladas (7 días, 36 productos, 73.62€).

**Observaciones capturadas:**
- Albahaca fresca → Salsa pesto (Pitfall #7)
- Quesos 0.2kg pueden requerir ajuste a paquete completo
- Pechuga pollo cocido vs crudo

**Resultado:** Xavier pudo revisar todas las anomalías ANTES de commit al carrito real.

## Tips

- **Sé específico**: no digas "algunos productos pueden variar", di CUÁLES (nombre + número de producto)
- **Ofrece alternativas**: si hay sustitución, da opciones concretas de cómo ajustar
- **Mantén formato ASCII-box**: legible en terminal/Telegram sin formatting
- **Guarda el documento**: `/tmp/OBSERVACIONES_[USUARIO].txt` para referencia
