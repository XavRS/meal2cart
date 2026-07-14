# scripts/legacy/ — Código deprecated

Archivos movidos aquí tras migración a mercadona-cli (2026-07-14).

---

## `mercadona_client.py`

Cliente de Mercadona Online basado en Playwright (navegador headless).

**Razones de deprecación:**

1. **Lentitud:** 5s por producto vs 0.2s con CLI (25× más lento)
2. **Inestabilidad:** SPA crash tras ~20 productos
3. **Bug de cantidades:** Solo añadía 1 unidad, ignoraba qty del input
4. **Sin verificación:** No leía el total del carrito tras añadir
5. **Sin spending guard:** Riesgo de gastos excesivos
6. **Selectores frágiles:** Rotan cada ~6 meses, requiere re-spike
7. **Dependencia pesada:** ~300MB (Chromium + Playwright)

**Reemplazado por:** `mercadona_cli_wrapper.py` (wrapper de mercadona-cli)

**Última versión funcional:** Skill meal-to-cart commit pre-migración (2026-07-14)

---

## ¿Cuándo usar el código legacy?

**NUNCA en producción.**

Solo para referencia si necesitas entender:
- Cómo funcionaban los selectores CSS antiguos
- Lógica de navegación del SPA de Mercadona
- Manejo de modales/cookies en Playwright

Para cualquier nuevo desarrollo, usa `mercadona-cli`.

---

## Historial de mantenimiento

| Fecha | Evento | Impacto |
|-------|--------|---------|
| 2026-07-13 | Spike inicial Playwright | Funcionaba pero con 7 bugs críticos |
| 2026-07-14 | Spike mercadona-cli | Todos los bugs resueltos |
| 2026-07-14 | Migración a CLI | mercadona_client.py → legacy/ |

Ver `/mnt/vault/Personal/Hermes/meal-to-cart/` para análisis completo y plan de integración.
