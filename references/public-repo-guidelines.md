# Directrices para documentación pública del repo

**Proyecto:** meal-to-cart  
**Tipo:** Personal (no open-source colaborativo)  
**Autor:** Xavi

---

## Contenido a EXCLUIR del README.md público

### 1. Sección "Soporte" ❌
```markdown
## 📧 Soporte
- Issues: ...
- Email: ...
```
**Razón:** No invitar a soporte/bugs externos.

### 2. Sección "Contribuir" ❌
```markdown
## 🤝 Contribuir
1. Fork el repo
2. Crea branch...
3. Abre PR...
```
**Razón:** Proyecto personal, no acepta contribuciones externas.

### 3. Rutas internas del vault ❌
```markdown
- Análisis migración: `/mnt/vault/Personal/Hermes/meal-to-cart/...`
```
**Razón:** Paths internos de Hermes no deben exponerse públicamente.

---

## Contenido a MANTENER

✅ Características del proyecto  
✅ Guía de instalación  
✅ Ejemplos de uso  
✅ Referencias a documentos dentro del repo (`references/`, `SKILL.md`)  
✅ Licencia  
✅ Créditos a dependencias externas  
✅ Firma de autor: "Hecho con ❤️ y 🤖 por Xavi"

---

## Aplicado en commits

- `c2551ec` — Remove vault path reference
- `e1fb8df` — Remove contributing section
- `f169e7f` — Remove support section, update author name

---

**Lección:** Al publicar un repo personal, eliminar cualquier elemento que invite a colaboración externa o exponga estructura interna del entorno de desarrollo.
