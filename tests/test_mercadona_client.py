"""Tests unitarios para scripts/mercadona_client.py.

No requieren Playwright instalado: se mockean los objetos Page/Context.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

import scripts.mercadona_client as mc


# ---------------------------------------------------------------------------
# Helpers puramente síncronos
# ---------------------------------------------------------------------------
def test_parse_items_from_string():
    assert mc.parse_items("tomate, cebolla, pan") == ["tomate", "cebolla", "pan"]


def test_parse_items_strips_and_filters_empty():
    assert mc.parse_items(" leche , , pan ") == ["leche", "pan"]


def test_parse_items_from_iterable():
    assert mc.parse_items(["leche", "pan", "huevos"]) == ["leche", "pan", "huevos"]


def test_product_to_dict():
    p = mc.Product(name="Leche", price="1,20", search_term="leche")
    assert p.to_dict() == {
        "name": "Leche",
        "price": "1,20",
        "search_term": "leche",
    }


def test_price_regex():
    m = mc.PRICE_RE.search("1,20 €/ud")
    assert m is not None
    assert m.group(1) == "1,20"


def test_price_regex_with_dot():
    m = mc.PRICE_RE.search("precio 3.50€ extra")
    assert m and m.group(1) == "3.50"


# ---------------------------------------------------------------------------
# Load list file
# ---------------------------------------------------------------------------
def test_load_list_file_json_array(tmp_path: Path):
    f = tmp_path / "list.json"
    f.write_text(json.dumps(["tomate", "pan"]), encoding="utf-8")
    assert mc.load_list_file(str(f)) == ["tomate", "pan"]


def test_load_list_file_json_dict(tmp_path: Path):
    f = tmp_path / "list.json"
    f.write_text('{"shopping_list": ["a", "b"]}', encoding="utf-8")
    assert mc.load_list_file(str(f)) == ["a", "b"]


def test_load_list_file_plain_text(tmp_path: Path):
    f = tmp_path / "list.txt"
    f.write_text("leche\npan\nhuevos\n", encoding="utf-8")
    assert mc.load_list_file(str(f)) == ["leche", "pan", "huevos"]


def test_load_list_file_comma_separated(tmp_path: Path):
    f = tmp_path / "list.txt"
    f.write_text("leche, pan, huevos", encoding="utf-8")
    assert mc.load_list_file(str(f)) == ["leche", "pan", "huevos"]


def test_load_list_file_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        mc.load_list_file(str(tmp_path / "nope.json"))


# ---------------------------------------------------------------------------
# CLI argumentos
# ---------------------------------------------------------------------------
def test_cli_requires_one_action(capsys):
    with pytest.raises(SystemExit):
        mc.build_parser().parse_args([])


def test_cli_search_flag():
    args = mc.build_parser().parse_args(["--search", "leche"])
    assert args.search == "leche"
    assert args.dry_run is False


def test_cli_add_flag():
    args = mc.build_parser().parse_args(["--add", "tomate, cebolla"])
    assert args.add == "tomate, cebolla"


def test_cli_dry_run_flag():
    args = mc.build_parser().parse_args(["--list", "leche", "--dry-run"])
    assert args.dry_run is True


def test_cli_json_flag():
    args = mc.build_parser().parse_args(["--search", "leche", "--json"])
    assert args.json is True


def test_cli_cp_override():
    args = mc.build_parser().parse_args(["--search", "x", "--cp", "46001"])
    assert args.cp == "46001"


def test_cli_login_flag():
    args = mc.build_parser().parse_args(["--search", "leche", "--login"])
    assert args.login is True


def test_cli_login_default():
    args = mc.build_parser().parse_args(["--search", "leche"])
    assert args.login is False


# ---------------------------------------------------------------------------
# Mock Playwright para probar MercadonaClient
# ---------------------------------------------------------------------------
class FakeLocator:
    """Mock minimalista de un Locator de Playwright."""

    def __init__(self, items=None, inner_texts=None):
        self._items = items or []
        self._inner_texts = inner_texts or []

    async def count(self):
        return len(self._items)

    def nth(self, i):
        return self._items[i]

    def first(self):
        return self._items[0] if self._items else FakeLocator()

    async def inner_text(self):
        return self._inner_texts.pop(0) if self._inner_texts else ""

    async def click(self):
        return None

    async def fill(self, value):
        return None

    def __getattr__(self, name):
        # Devuelve FakeLocator para llamadas encadenadas arbitrarias
        def _return(self_obj=FakeLocator()):
            return MagicMockAsync(name).__new__  # placeholder
        raise AttributeError(name)


class _Awaitable:
    """Simple awaitable para simplificar el mock."""

    def __init__(self, value):
        self.value = value

    def __await__(self):
        async def _coro():
            return self.value

        return _coro().__await__()


class FakeContext:
    def __init__(self):
        self.url = "https://www.mercadona.es/"

    async def new_page(self):
        return FakePage()

    async def close(self):
        pass

    async def storage_state(self, path=None):
        if path:
            Path(path).write_text("{}", encoding="utf-8")


class FakePage:
    def __init__(self):
        self.url = "https://www.mercadona.es/"

    def locator(self, sel):
        return _FakeLocator(sel)


class _FakeLocator:
    def __init__(self, sel):
        self.sel = sel

    async def count(self):
        return 0

    def first(self):
        return self

    def nth(self, i):
        return self

    async def click(self):
        return None

    async def inner_text(self):
        return ""


def test_parsing_full_works_without_playwright_import(monkeypatch):
    # importa el modulo sin playwright y aún así las utilidades funcionan
    monkeypatch.setattr(mc, "async_playwright", None, raising=False)
    items = mc.parse_items("a, b, c")
    assert items == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# run() integra el flujo minimizado con mocks
# ---------------------------------------------------------------------------
def test_run_search_dryrun_with_mocks(monkeypatch, capsys, tmp_path):
    """Comprueba que run() fluye correctamente con un cliente simulado."""

    class StubClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def open(self, force_login=False):
            return None

        async def add_many(self, items, dry_run=True):
            return [{"item": "leche", "found": True, "product": {}, "added": False}]

    monkeypatch.setattr(mc, "MercadonaClient", lambda **kwargs: StubClient())

    rc = mc.main(["--search", "leche", "--json", "--cookie-file", str(tmp_path / "c.json")])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["item"] == "leche"


def test_main_returns_nonzero_on_error(monkeypatch, capsys):
    # Simulamos un error real dentro del flujo async (no mockeando asyncio.run
    # para evitar el warning "coroutine was never awaited")
    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def open(self, force_login=False):
            raise RuntimeError("foo")

        async def add_many(self, items, dry_run=True):
            return []

    monkeypatch.setattr(mc, "MercadonaClient", lambda **kw: FailingClient())
    rc = mc.main(["--search", "x"])
    assert rc == 1