"""Tests unitarios para scripts/recipe_md_generator.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.recipe_md_generator as rg


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------
def test_parse_week_start():
    d = rg.parse_week_start("2026-07-13")
    assert d.day == 13 and d.month == 7


def test_format_date_range_same_month():
    from datetime import date

    assert rg.format_date_range(date(2026, 7, 13)) == "13 al 19 de julio de 2026"


def test_format_date_range_cross_month():
    from datetime import date

    assert rg.format_date_range(date(2026, 1, 28)) == "28 de enero al 3 de febrero de 2026"


def test_weekday_index():
    assert rg.weekday_index("Lunes") == 0
    assert rg.weekday_index("Domingo") == 6
    assert rg.weekday_index("NoExiste") == -1


def test_weekday_letter():
    assert rg.weekday_letter("Lunes") == "L"
    assert rg.weekday_letter("Miércoles") == "M"


# ---------------------------------------------------------------------------
# source_to_label
# ---------------------------------------------------------------------------
def test_source_to_label_cookidoo():
    icon, label = rg.source_to_label("cookidoo")
    assert icon == "🍳"
    assert label == "Cookidoo"


def test_source_to_label_spoonacular():
    icon, label = rg.source_to_label("spoonacular")
    assert icon == "🥘"
    assert label == "Spoonacular"


def test_source_to_label_none():
    icon, label = rg.source_to_label(None)
    assert label == "Spoonacular"


# ---------------------------------------------------------------------------
# Ingredientes
# ---------------------------------------------------------------------------
def test_ingredient_from_dict():
    ing = rg.Ingredient.from_dict({"name": "leche", "amount": 2, "unit": "uds"})
    assert ing.name == "leche"
    assert ing.amount == 2
    assert ing.unit == "uds"


def test_format_ingredient_line_grams():
    ing = rg.Ingredient("salmón", 400, "g")
    assert rg.format_ingredient_line(ing) == "- 400g salmón"


def test_format_ingredient_line_ml():
    ing = rg.Ingredient("leche de coco", 200, "ml")
    assert rg.format_ingredient_line(ing) == "- 200 ml leche de coco"


def test_format_ingredient_line_units_singular():
    ing = rg.Ingredient("calabacín", 1, "uds")
    assert rg.format_ingredient_line(ing) == "- 1 ud de calabacín"


def test_format_ingredient_line_units_plural():
    ing = rg.Ingredient("calabacín", 3, "uds")
    assert rg.format_ingredient_line(ing) == "- 3 uds de calabacín"


def test_format_ingredient_line_kg():
    assert rg.format_ingredient_line(rg.Ingredient("harina", 1, "kg")) == "- 1kg harina"


def test_format_ingredient_line_l():
    assert rg.format_ingredient_line(rg.Ingredient("leche", 1, "l")) == "- 1l leche"


def test_format_ingredient_line_no_unit():
    assert rg.format_ingredient_line(rg.Ingredient("sal", 1, "")) == "- sal"


def test_format_amount_total_grams():
    assert rg.format_amount_total([100, 250], "g") == "350g"


def test_format_amount_total_units_singular():
    assert rg.format_amount_total([1], "uds") == "1 ud"


def test_format_amount_total_units_plural():
    assert rg.format_amount_total([2, 3], "uds") == "5 uds"


def test_merge_amount_same_units():
    existing = rg.Ingredient("cebolla", 2, "uds", used_in=["L"])
    new = rg.Ingredient("cebolla", 3, "uds")
    rg._merge_amount(existing, new)
    assert existing.amount == 5
    existing.used_in.append("M")
    assert existing.used_in == ["L", "M"]


def test_merge_amount_different_units_does_not_sum():
    existing = rg.Ingredient("leche", 1, "l")
    new = rg.Ingredient("leche", 500, "ml")
    rg._merge_amount(existing, new)
    assert existing.amount == 1  # no se suma porque unidades distintas


# ---------------------------------------------------------------------------
# Consolidación de la lista de la compra
# ---------------------------------------------------------------------------
def test_consolidate_ingredients_sums_repeated():
    meals = {
        "Lunes": {"cena": {"ingredients": [
            {"name": "cebolla", "amount": 1, "unit": "uds"},
        ]}},
        "Martes": {"cena": {"ingredients": [
            {"name": "cebolla", "amount": 2, "unit": "uds"},
        ]}},
    }
    consolidated = {i.name.lower(): i for i in rg.consolidate_ingredients(meals)}
    assert consolidated["cebolla"].amount == 3
    assert set(consolidated["cebolla"].used_in) == {"L", "M"}


def test_categorize_proteinas():
    assert rg.categorize(rg.Ingredient("Pollo", 400, "g")) == "proteinas"
    assert rg.categorize(rg.Ingredient("Salmón fresco", 400, "g")) == "proteinas"


def test_categorize_verduras():
    assert rg.categorize(rg.Ingredient("Calabacín", 2, "uds")) == "verduras"
    assert rg.categorize(rg.Ingredient("Tomates cherry", 100, "g")) == "verduras"


def test_categorize_despensa():
    assert rg.categorize(rg.Ingredient("Arroz basmati", 200, "g")) == "despensa"
    assert rg.categorize(rg.Ingredient("Leche de coco", 200, "ml")) == "despensa"


def test_categorize_condimentos():
    assert rg.categorize(rg.Ingredient("Curry en polvo", 2, "cucharadas")) == "condimentos"


def test_recipe_letters_dedup():
    ing = rg.Ingredient("cebolla", 1, "uds", used_in=["L", "L", "M"])
    assert rg.recipe_letters(ing) == "L, M"


# ---------------------------------------------------------------------------
# Rendering completo
# ---------------------------------------------------------------------------
def test_render_table_includes_all_days():
    from datetime import date

    meals = {"Lunes": {"comida": None, "cena": None}, "Martes": {"comida": None, "cena": None}}
    table = rg.render_table(meals, date(2026, 7, 13))
    for day in rg.WEEKDAYS_ES:
        assert day in table


def test_render_cell_none():
    assert rg._render_cell(None) == "—"


def test_render_cell_with_meal():
    cell = rg._render_cell(
        {"title": "Sopa", "source": "cookidoo", "time_minutes": 20, "calories_per_serving": 200}
    )
    assert "🍳" in cell
    assert "Sopa" in cell
    assert "(20 min)" in cell
    assert "200 kcal" in cell


def test_render_recipe_meta_format():
    meta = rg.render_recipe_meta(
        {
            "time_minutes": 25,
            "servings": 2,
            "calories_per_serving": 480,
            "source": "cookidoo",
            "url": "https://cookidoo.es/recipes/715538",
        }
    )
    assert "⏱️ 25 min" in meta
    assert "👥 2 personas" in meta
    assert "🔥 480 kcal/ración" in meta
    assert "[Cookidoo](https://cookidoo.es/recipes/715538)" in meta


def test_render_recipe_steps_string():
    steps = rg.extract_recipe_steps("Paso 1\nPaso 2")
    assert steps == ["Paso 1", "Paso 2"]


def test_render_recipe_steps_list():
    steps = rg.extract_recipe_steps(["A", "B", "C"])
    assert steps == ["A", "B", "C"]


def test_render_recipe_header_format():
    header = rg.render_recipe_header("Lunes", 13, {"source": "cookidoo", "title": "Salmón"})
    assert header == "## 🐟 Lunes 13 — Cena: Salmón 🍳"


def test_compute_stats_empty():
    avg, total = rg.compute_stats({})
    assert avg == 0 and total == 0


def test_compute_stats_with_values():
    meals = {"Lunes": {"cena": {"calories_per_serving": 480}}, "Martes": {"cena": {"calories_per_serving": 320}}}
    avg, total = rg.compute_stats(meals)
    assert avg == 400
    assert total == 800


# ---------------------------------------------------------------------------
# render_menu end-to-end (golden smoke test)
# ---------------------------------------------------------------------------
SAMPLE_JSON = {
    "week_start": "2026-07-13",
    "preferences": "2 personas | Mediterránea | 30 min max | Sin gluten",
    "meals": {
        "Lunes": {
            "comida": None,
            "cena": {
                "title": "Salmón al vapor con verduras",
                "source": "cookidoo",
                "url": "https://cookidoo.es/recipes/715538",
                "time_minutes": 25,
                "servings": 2,
                "rating": 4.5,
                "calories_per_serving": 480,
                "ingredients": [
                    {"name": "salmón fresco", "amount": 400, "unit": "g"},
                    {"name": "calabacín", "amount": 2, "unit": "uds"},
                ],
                "steps": ["A", "B"],
            },
        },
        "Viernes": {
            "comida": None,
            "cena": {
                "title": "Ensalada de quinoa",
                "source": "spoonacular",
                "url": "https://spoonacular.com/recipes/645789",
                "time_minutes": 15,
                "servings": 2,
                "rating": 4.1,
                "calories_per_serving": 380,
                "ingredients": [
                    {"name": "quinoa", "amount": 150, "unit": "g"},
                    {"name": "cebolla", "amount": 1, "unit": "uds"},
                ],
                "steps": ["X", "Y"],
            },
        },
    },
}


def test_render_menu_contains_title_and_range():
    md = rg.render_menu(SAMPLE_JSON)
    assert "# Menú semanal — 13 al 19 de julio de 2026" in md
    assert "2 personas | Mediterránea" in md


def test_render_menu_contains_table():
    md = rg.render_menu(SAMPLE_JSON)
    assert "| Día | Comida | Cena |" in md
    assert "| **Lunes 13**" in md
    assert "| **Domingo 19**" in md


def test_render_menu_separates_recipes_with_hr():
    md = rg.render_menu(SAMPLE_JSON)
    # cada receta termina con un separador ---
    assert md.count("---") >= 3  # al menos: tabla-recetas, entre recetas, lista-footer


def test_render_menu_contains_cookidoo_and_spoonacular_links():
    md = rg.render_menu(SAMPLE_JSON)
    assert "[Cookidoo](https://cookidoo.es/recipes/715538)" in md
    assert "[Spoonacular](https://spoonacular.com/recipes/645789)" in md


def test_render_menu_contains_shopping_list():
    md = rg.render_menu(SAMPLE_JSON)
    assert "## 📊 Lista de la compra consolidada" in md
    assert "### 🥩 Proteínas" in md
    assert "### 🥬 Verduras y frutas" in md
    assert "### 🥫 Despensa" in md


def test_render_menu_contains_footer_date():
    md = rg.render_menu(SAMPLE_JSON)
    assert "Generado por Hermes Meal-to-Cart" in md


def test_render_menu_consolidates_onion_across_recipes():
    # cebolla aparece en ambas recetas -> sumar
    md = rg.render_menu(SAMPLE_JSON)
    # busca la fila de cebolla en la tabla de verduras
    assert "Cebolla" in md


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def test_cli_requires_input(capsys):
    with pytest.raises(SystemExit):
        rg.build_parser().parse_args([])


def test_cli_input_flag():
    args = rg.build_parser().parse_args(["--input", "x.json"])
    assert args.input == "x.json"


def test_cli_output_flag():
    args = rg.build_parser().parse_args(["--input", "x.json", "--output", "out.md"])
    assert args.output == "out.md"


def test_cli_stdout_flag():
    args = rg.build_parser().parse_args(["--input", "x.json", "--stdout"])
    assert args.stdout is True


def test_main_writes_output_file(tmp_path: Path):
    in_path = tmp_path / "in.json"
    out_path = tmp_path / "out.md"
    in_path.write_text(json.dumps(SAMPLE_JSON), encoding="utf-8")
    rc = rg.main(["--input", str(in_path), "--output", str(out_path)])
    assert rc == 0
    content = out_path.read_text(encoding="utf-8")
    assert "# Menú semanal" in content


def test_main_stdout(tmp_path: Path, capsys):
    in_path = tmp_path / "in.json"
    in_path.write_text(json.dumps(SAMPLE_JSON), encoding="utf-8")
    rc = rg.main(["--input", str(in_path), "--stdout"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "# Menú semanal" in captured


def test_main_missing_input_file_returns_nonzero(capsys):
    rc = rg.main(["--input", "/tmp/no_existe_xyz.json", "--stdout"])
    assert rc == 1


def test_main_invalid_json_returns_nonzero(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid", encoding="utf-8")
    rc = rg.main(["--input", str(bad), "--stdout"])
    assert rc == 1


def test_resolve_output_path_with_env(monkeypatch):
    monkeypatch.setenv("RECIPE_OUTPUT_PATH", "/tmp/custom_recetas")
    monkeypatch.setenv("RECIPE_FILENAME_PATTERN", "semana_{date}.md")
    args = rg.build_parser().parse_args(["--input", "x.json"])
    path = rg.resolve_output_path(args, "2026-07-13")
    assert str(path) == "/tmp/custom_recetas/semana_2026-07-13.md"


def test_resolve_output_path_default(monkeypatch):
    monkeypatch.delenv("RECIPE_OUTPUT_PATH", raising=False)
    monkeypatch.setenv("HOME", "/tmp/fake_home")
    args = rg.build_parser().parse_args(["--input", "x.json"])
    path = rg.resolve_output_path(args, "2026-07-13")
    assert str(path).endswith("/recetas/2026-07-13.md")