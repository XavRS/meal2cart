#!/usr/bin/env python3
"""Generador de recetas Markdown a partir de un JSON de menú semanal.

Uso:
  python3 scripts/recipe_md_generator.py --input recipes.json
  python3 scripts/recipe_md_generator.py --input recipes.json \
      --output /mnt/vault/Personal/Menjars/semana_13_julio.md

Variables de entorno:
  RECIPE_OUTPUT_PATH  Carpeta por defecto (default: ~/recetas)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

WEEKDAYS_ES = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]
WEEKDAY_EMOJI = {
    "Lunes": "🐟",
    "Martes": "🥣",
    "Miércoles": "🍛",
    "Jueves": "🫘",
    "Viernes": "🥑",
    "Sábado": "🐟",
    "Domingo": "🍳",
}

# Categorías para la lista de la compra (heurística simple en español)
PROTEINAS = {
    "salmón", "salmon", "pollo", "merluza", "huevo", "huevos", "jamón",
    "jamón serrano", "atún", "bacalao", "ternera", "cerdo", "lomo",
    "pavo", "chuleta", "hamburguesa",
}
VERDURAS = {
    "calabacín", "calabacin", "cebolla", "pimiento", "pimiento rojo",
    "pimiento verde", "ajo", "ajos", "zanahoria", "tomate", "tomates cherry",
    "patata", "patatas", "aguacate", "mango", "limón", "limon", "lima",
    "jengibre", "cilantro", "menta", "perejil", "puerro", "berenjena",
    "calabaza", "espinaca", "espinacas", "lechuga",
}
DESPENSA = {
    "arroz", "arroz basmati", "quinoa", "lentejas", "lentejas pardinas",
    "leche de coco", "caldo", "caldo de verduras", "pimiento asado",
    "quesito",
}

# Unidades abreviadas
UNIT_ABBR = {"g": "g", "ml": "ml", "uds": "uds", "ud": "ud", "kg": "kg", "l": "l"}


@dataclass
class Ingredient:
    name: str
    amount: float | int | str
    unit: str
    # recetas (L/M/...) en las que aparece
    used_in: list[str] | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Ingredient":
        return cls(
            name=str(d.get("name", "")).strip(),
            amount=d.get("amount", ""),
            unit=str(d.get("unit", "")).strip(),
        )


# ---------------------------------------------------------------------------
# Utilidades de fecha
# ---------------------------------------------------------------------------
def parse_week_start(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def format_date_range(start: date) -> str:
    end = start + timedelta(days=6)
    months_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    if start.month == end.month:
        return f"{start.day} al {end.day} de {months_es[start.month - 1]} de {start.year}"
    return (
        f"{start.day} de {months_es[start.month - 1]} al {end.day} de "
        f"{months_es[end.month - 1]} de {end.year}"
    )


def short_date_only(d: date) -> str:
    return f"{d.day}"


# ---------------------------------------------------------------------------
# Helpers de rendering
# ---------------------------------------------------------------------------
def source_to_label(source: str | None) -> tuple[str, str]:
    """Devuelve (emoji_icon, label)."""
    src = (source or "").lower()
    if src == "cookidoo":
        return "🍳", "Cookidoo"
    return "🥘", "Spoonacular"


def format_ingredient_line(ing: Ingredient) -> str:
    amount = ing.amount
    unit = ing.unit
    if isinstance(amount, (int, float)) and amount == int(amount):
        amount = int(amount)
    unit = UNIT_ABBR.get(unit, unit)
    if unit in ("uds", "ud"):
        unit_str = "ud" if amount == 1 else "uds"
        return f"- {amount} {unit_str} de {ing.name}"
    if unit == "g":
        return f"- {amount}g {ing.name}"
    if unit == "ml":
        return f"- {amount} ml {ing.name}"
    if unit == "kg":
        return f"- {amount}kg {ing.name}"
    if unit == "l":
        return f"- {amount}l {ing.name}"
    if unit:
        return f"- {amount} {unit} {ing.name}"
    return f"- {ing.name}"


def format_amount_total(amounts: list[float | int], unit: str) -> str:
    if not amounts:
        return ""
    total: float = 0
    for a in amounts:
        try:
            total += float(a)
        except (TypeError, ValueError):
            pass
    if total == int(total):
        total = int(total)  # type: ignore
    unit = UNIT_ABBR.get(unit, unit)
    if unit == "g":
        return f"{total}g"
    if unit in ("uds", "ud"):
        unit_str = "ud" if total == 1 else "uds"
        return f"{total} {unit_str}"
    if unit == "ml":
        return f"{total} ml"
    if unit == "kg":
        return f"{total}kg"
    if unit == "l":
        return f"{total}l"
    return f"{total} {unit}".strip()


def weekday_letter(day_name: str) -> str:
    return day_name[0] if day_name else "?"


def weekday_index(day_name: str) -> int:
    try:
        return WEEKDAYS_ES.index(day_name)
    except ValueError:
        return -1


def pick_emoji(day_name: str, meal: dict[str, Any] | None) -> str:
    if meal is None:
        return "—"
    icon, _ = source_to_label(meal.get("source"))
    return icon or WEEKDAY_EMOJI.get(day_name, "🍽️")


def extract_recipe_steps(recipe: dict[str, Any] | str | list[str]) -> list[str]:
    # Acepta dict (con clave "steps"), string multilínea, o lista directa
    if isinstance(recipe, dict):
        steps = recipe.get("steps") or []
    else:
        steps = recipe
    if isinstance(steps, str):
        return [s.strip() for s in steps.split("\n") if s.strip()]
    return [str(s).strip() for s in steps if str(s).strip()]


def render_recipe_header(day_name: str, day_num: int, meal: dict[str, Any], slot: str = "Cena") -> str:
    title = meal.get("title", "(sin título)")
    icon_day = WEEKDAY_EMOJI.get(day_name, "🍽️")
    icon, _ = source_to_label(meal.get("source"))
    return f"## {icon_day} {day_name} {day_num} — {slot.capitalize()}: {title} {icon}"


def render_recipe_image(meal: dict[str, Any]) -> str:
    """Renderiza la imagen de la receta si existe."""
    image_url = meal.get("image_url")
    if not image_url:
        return ""
    return f"\n![{meal.get('title', 'Foto del plato')}]({image_url})\n"


def render_recipe_meta(meal: dict[str, Any]) -> str:
    time = meal.get("time_minutes")
    servings = meal.get("servings")
    cal = meal.get("calories_per_serving")
    url = meal.get("url")
    _, label = source_to_label(meal.get("source"))
    link = f"[{label}]({url})" if url else label
    parts = []
    if time is not None:
        parts.append(f"⏱️ {time} min")
    if servings is not None:
        parts.append(f"👥 {servings} personas")
    if cal is not None:
        parts.append(f"🔥 {cal} kcal/ración")
    parts.append(f"🔗 {link}")
    return " | ".join(parts)


def render_recipe(recipe: dict[str, Any]) -> str:
    ings = [Ingredient.from_dict(d) for d in recipe.get("ingredients", [])]
    steps = extract_recipe_steps(recipe)
    src = (recipe.get("source") or "").lower()
    steps_header = "Preparación (Thermomix)" if src == "cookidoo" else "Preparación"
    lines = [
        "### Ingredientes",
        *[format_ingredient_line(i) for i in ings],
        "",
        f"### {steps_header}",
        *[f"{n}. {s}" for n, s in enumerate(steps, 1)],
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Consolidación de la lista de la compra
# ---------------------------------------------------------------------------
def consolidate_ingredients(meals: dict[str, dict[str, Any]]) -> list[Ingredient]:
    """ combina ingredientes de todas las recetas."""
    consolidated: dict[str, Ingredient] = {}

    for day_name, day_meals in meals.items():
        for slot in ("comida", "cena"):
            meal = day_meals.get(slot)
            if not meal:
                continue
            letter = weekday_letter(day_name)
            for raw in meal.get("ingredients", []):
                ing = Ingredient.from_dict(raw)
                key = ing.name.lower().strip()
                if key in consolidated:
                    existing = consolidated[key]
                    _merge_amount(existing, ing)
                    if existing.used_in is not None and letter not in existing.used_in:
                        existing.used_in.append(letter)
                else:
                    ing.used_in = [letter]
                    consolidated[key] = ing
    return list(consolidated.values())


def _merge_amount(existing: Ingredient, new: Ingredient) -> None:
    """Suma amounts cuando las unidades coinciden; si no, mantiene la original."""
    try:
        a1 = float(existing.amount)
        a2 = float(new.amount)
        if existing.unit == new.unit:
            existing.amount = a1 + a2
            if isinstance(existing.amount, float) and existing.amount == int(existing.amount):
                existing.amount = int(existing.amount)
    except (TypeError, ValueError):
        # Si los amounts no son numéricos, dejamos el primero
        pass


def categorize(ingredient: Ingredient) -> str:
    name = ingredient.name.lower()
    for kw in PROTEINAS:
        if kw in name:
            return "proteinas"
    for kw in VERDURAS:
        if kw in name:
            return "verduras"
    for kw in DESPENSA:
        if kw in name:
            return "despensa"
    return "condimentos"


def recipe_letters(ing: Ingredient) -> str:
    if not ing.used_in:
        return ""
    # eliminar duplicados manteniendo orden
    seen: list[str] = []
    for l in ing.used_in:
        if l not in seen:
            seen.append(l)
    return ", ".join(seen)


def render_shopping_list(ingredients: list[Ingredient]) -> str:
    cats = {
        "proteinas": ("🥩 Proteínas", []),
        "verduras": ("🥬 Verduras y frutas", []),
        "despensa": ("🥫 Despensa", []),
        "condimentos": ("🧂 Condimentos y básicos", []),
    }
    for ing in ingredients:
        cats[categorize(ing)][1].append(ing)

    blocks: list[str] = ["## 📊 Lista de la compra consolidada", ""]
    for key in ("proteinas", "verduras", "despensa", "condimentos"):
        title, items = cats[key]
        blocks.append(f"### {title}")
        blocks.append("| Ingrediente | Cantidad | Para recetas |")
        blocks.append("|-------------|----------|--------------|")
        if not items:
            blocks.append(f"| — | — | — |")
        else:
            for ing in items:
                unit = ing.unit or ""
                qty = ing.amount
                if isinstance(qty, (int, float)) and qty != "":
                    qty_str = format_amount_total([qty], ing.unit) if unit else str(qty)
                else:
                    qty_str = str(qty) if qty else "—"
                # si el ingrediente no tiene cantidad (condimentos)
                if not qty or qty_str in ("None", ""):
                    qty_str = "— (comprobar stock)"
                blocks.append(
                    f"| {ing.name.capitalize()} | {qty_str} | {recipe_letters(ing) or 'Varias'} |"
                )
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------
def render_table(meals: dict[str, dict[str, Any]], start: date) -> str:
    lines = ["| Día | Comida | Cena |", "|-----|--------|------|"]
    for i, day_name in enumerate(WEEKDAYS_ES):
        day = start + timedelta(days=i)
        day_meals = meals.get(day_name, {})
        comida = day_meals.get("comida")
        cena = day_meals.get("cena")
        lines.append(
            f"| **{day_name} {day.day}** | {_render_cell(comida)} | {_render_cell(cena)} |"
        )
    return "\n".join(lines)


def _render_cell(meal: dict[str, Any] | None) -> str:
    if meal is None:
        return "—"
    icon, _ = source_to_label(meal.get("source"))
    time = meal.get("time_minutes")
    rating = meal.get("rating")
    cal = meal.get("calories_per_serving")
    parts = [f"{icon} {meal.get('title', '(sin título)')}"]
    if time is not None:
        parts.append(f"({time} min)")
    if rating is not None:
        parts.append(f"⭐{rating}")
    if cal is not None:
        parts.append(f"— {cal} kcal")
    return " ".join(parts)


def compute_stats(meals: dict[str, dict[str, Any]]) -> tuple[float, int]:
    cals: list[int] = []
    for day_meals in meals.values():
        for slot in ("comida", "cena"):
            meal = day_meals.get(slot)
            if meal and meal.get("calories_per_serving") is not None:
                cals.append(int(meal["calories_per_serving"]))
    if not cals:
        return 0.0, 0
    return sum(cals) / len(cals), sum(cals)


def render_weekly_summary(meals: dict[str, dict[str, Any]]) -> str:
    avg, total = compute_stats(meals)
    return (
        "> 🍳 = Thermomix, 🥘 = Tradicional\n"
        f"> 🔥 Media: ~{avg:.0f} kcal/cena | Total semanal: ~{total:,} kcal\n"
        "> 📅 Las recetas 🍳 están sincronizadas en Cookidoo → disponibles en tu Thermomix"
    ).replace(",", ".")


def render_menu(data: dict[str, Any]) -> str:
    week_start = parse_week_start(data["week_start"])
    prefs = data.get("preferences", "")
    meals = data.get("meals", {})

    out: list[str] = []
    out.append(f"# Menú semanal — {format_date_range(week_start)}")
    out.append(f"**{prefs}**" if prefs else "")
    out.append("")
    out.append("## 📅 Tabla semanal")
    out.append("")
    out.append(render_table(meals, week_start))
    out.append("")
    out.append(render_weekly_summary(meals))
    out.append("")
    out.append("---")
    out.append("")

    # Recetas ordenadas L-D
    for i, day_name in enumerate(WEEKDAYS_ES):
        day = week_start + timedelta(days=i)
        day_meals = meals.get(day_name, {})
        for slot in ("comida", "cena"):
            meal = day_meals.get(slot)
            if not meal:
                continue
            out.append("")
            out.append(render_recipe_header(day_name, day.day, meal, slot))
            image = render_recipe_image(meal)
            if image:
                out.append(image)
            out.append(render_recipe_meta(meal))
            out.append("")
            out.append(render_recipe(meal))
            out.append("")
            out.append("---")
            out.append("")

    # Lista de la compra consolidada
    ingredients = consolidate_ingredients(meals)
    out.append("")
    out.append(render_shopping_list(ingredients))
    out.append("")
    out.append("---")
    out.append("")
    today = datetime.now().strftime("%d/%m/%Y")
    out.append(f"*Generado por Hermes Meal-to-Cart — {today}*")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Genera un fichero Markdown con el menú semanal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--input", "-i", required=True, help="Fichero JSON de entrada")
    p.add_argument("--output", "-o", help="Fichero de salida .md")
    p.add_argument("--stdout", action="store_true", help="Imprimir a stdout sin escribir archivo")
    return p


def resolve_output_path(args: argparse.Namespace, week_start: str) -> Path:
    if args.output:
        return Path(args.output)
    folder = os.environ.get("RECIPE_OUTPUT_PATH", str(Path.home() / "recetas"))
    pattern = os.environ.get("RECIPE_FILENAME_PATTERN", "{date}.md")
    filename = pattern.format(date=week_start)
    return Path(folder) / filename


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: no existe el fichero {args.input}", file=sys.stderr)
        return 1
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error parseando JSON: {exc}", file=sys.stderr)
        return 1

    md = render_menu(data)

    if args.stdout:
        print(md)
        return 0

    out_path = resolve_output_path(args, data.get("week_start", "semana"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"✓ Menú generado en {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())