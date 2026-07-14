# Sustituciones de productos no disponibles en Mercadona

Lista viva de ingredientes que aparecen en recetas Cookidoo/Spoonacular pero
no existen (o son difíciles de encontrar) en el catálogo de Mercadona.

Cada entrada documenta: qué pide la receta, por qué Mercadona no lo tiene,
y con qué sustituirlo (incluyendo ID de producto si aplica).

---

## Hierbas frescas

| Receta pide | Mercadona tiene | Sustituir por | ID |
|-------------|----------------|---------------|-----|
| Menta fresca (ramitas) | ❌ Solo infusiones (Menta Poleo) | Hierbabuena fresca | 68037 |
| Albahaca fresca (maceta/planta) | ⚠️ A veces sin stock | Albahaca en bandeja (hojas cortadas) | 69287 |
| Eneldo fresco | ❌ No disponible | Hinojo fresco (bulbo) o semillas de hinojo | — |
| Cilantro fresco | ✅ Sí (bandeja) | — | 69690 |
| Perejil fresco | ✅ Sí (paquete troceado) | — | 69701 |

## Verduras específicas

| Receta pide | Mercadona tiene | Sustituir por | ID |
|-------------|----------------|---------------|-----|
| Chalota | ❌ No disponible | Cebolla normal (misma malla) | 69089 |
| Cebolleta tierna | ⚠️ Encurtida (tarro), no fresca | Cebolla normal picada fina + un poco de la parte verde | 69089 |
| Puerro | ✅ Sí | — | — |
| Calabacín | ✅ Sí | — | — |
| Berenjena | ✅ Sí | — | — |

## Carnes y pescados

| Receta pide | Mercadona tiene | Nota |
|-------------|----------------|------|
| Contramuslo de pollo | ✅ Sí (2789, pero batch devuelve pavo) | Usar `mercadona search` individual para encontrar el ID correcto |
| Boquerones frescos | ✅ Sí (81661.2, pero puede no aparecer con --fresh) | Quitar --fresh o buscar en pescadería directamente |
| Pechuga de pollo | ✅ Sí | — |

## Otros

| Receta pide | Mercadona tiene | Sustituir por | ID |
|-------------|----------------|---------------|-----|
| Levadura química | ✅ Sí (Royal, etc.) | — | — |
| Pan de molde | ✅ Sí | — | — |
| Piñones | ✅ Sí (Hacendado) | — | — |

---

## Metodología de búsqueda

Cuando un ingrediente no aparece en batch:

1. `mercadona search '<ingrediente>' --limit 5 --json` — búsqueda individual con más resultados
2. `mercadona search '<alternativa>' --limit 5 --json` — probar nombres alternativos
3. Si no hay resultado: consultar esta tabla de sustituciones
4. Si no está en la tabla: proponer una sustitución culinariamente razonable y documentarla aquí

---

> **Actualizado:** 2026-07-14 — sesión menú ensaladas verano (Xavier)
