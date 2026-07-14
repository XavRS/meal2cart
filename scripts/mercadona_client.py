#!/usr/bin/env python3
"""Cliente de Mercadona Online mediante Playwright (async).

Selectors verificados durante el spike (ver references/mercadona_selectors.md):
  - CP input:   input[aria-label="Código postal"]
  - CP submit:  input.postal-code-form__button
  - Search:     input[placeholder="Buscar productos"]
  - Product:    .product-cell--actionable
  - Add to cart:button[data-testid="product-quantity-button"]  o
                button[aria-label="Añadir al carro"]

Uso:
  python3 scripts/mercadona_client.py --search "leche semidesnatada"
  python3 scripts/mercadona_client.py --add "tomate, cebolla, pan"
  python3 scripts/mercadona_client.py --add-from-file lista.json
  python3 scripts/mercadona_client.py --list "leche, pan, huevos" --dry-run
  python3 scripts/mercadona_client.py --search "leche" --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:  # pragma: no cover - importación opcional para tests
    async_playwright = None  # type: ignore
    Page = Any  # type: ignore
    BrowserContext = Any  # type: ignore

MERCADONA_URL = "https://www.mercadona.es/"
TIENDA_HOST = "tienda.mercadona.es"
LOGIN_URL = "https://tienda.mercadona.es/?authenticate-user="
DEFAULT_CP = os.environ.get("MERCADONA_CP", "08001")
COOKIE_FILE = os.environ.get(
    "MERCADONA_COOKIES_FILE", "/tmp/mercadona_cookies.json"
)
MERCADONA_EMAIL = os.environ.get("MERCADONA_EMAIL", "")
MERCADONA_PASSWORD = os.environ.get("MERCADONA_PASSWORD", "")
ADD_TO_CART_DELAY = 1.5  # segundos entre clics de añadir al carrito
SEARCH_WAIT = 5.0  # segundos tras buscar
CP_REDIRECT_WAIT = 5.0  # segundos tras enviar el CP
LOGIN_TIMEOUT = 30.0  # segundos para login manual/interactivo

PRICE_RE = re.compile(r"(\d+[.,]\d+)\s*€")

# Selectors exactos (verified spike)
SEL_CP_INPUT = 'input[aria-label="Código postal"]'
SEL_CP_SUBMIT = "input.postal-code-form__button"
SEL_SEARCH = 'input[placeholder="Buscar productos"]'
SEL_PRODUCT = ".product-cell--actionable"
SEL_ADD_CART_PRIMARY = 'button[data-testid="product-quantity-button"]'
SEL_ADD_CART_FALLBACK = 'button[aria-label="Añadir al carro"]'
SEL_COOKIE_ACCEPT = 'button:has-text("Aceptar")'

# Login selectors (verificados spike 2026-07)
SEL_IDENTIFICATE = 'button[data-testid="dropdown-button"]:has-text("Identifícate")'
SEL_LOGIN_EMAIL_OPTION = 'text="Continuar con email"'
SEL_LOGIN_EMAIL_INPUT = 'input[type="email"]'
SEL_LOGIN_PASSWORD_INPUT = 'input[type="password"]'
SEL_LOGIN_SUBMIT = 'button:has-text("Continuar"), button:has-text("Iniciar sesión"), button:has-text("Entrar")'
SEL_LOGIN_SUCCESS_INDICATOR = 'text="Mi cuenta", [data-testid="user-menu"]'
SEL_LOGIN_ERROR = '[role="alert"], text="incorrect", text="inténtalo"'


def log(step: str, msg: str = "") -> None:
    """Log simple a stdout con prefijo de paso."""
    prefix = f"[{step}] " if step else ""
    print(f"{prefix}{msg}", flush=True)


@dataclass
class Product:
    name: str
    price: str | None
    search_term: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_items(raw: str | Iterable[str]) -> list[str]:
    """Acepta una cadena separada por comas o un iterable."""
    if isinstance(raw, str):
        items = [s.strip() for s in raw.split(",") if s.strip()]
    else:
        items = [str(s).strip() for s in raw if str(s).strip()]
    return items


def load_list_file(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")
    text = p.read_text(encoding="utf-8").strip()
    # Acepta JSON o texto plano (uno por línea / separado por comas)
    if text.startswith("[") or text.startswith("{"):
        data = json.loads(text)
        if isinstance(data, dict):
            # {"items": [...]} o {"shopping_list": [...]}
            for key in ("items", "shopping_list", "products"):
                if key in data:
                    data = data[key]
                    break
            else:
                data = list(data.values())
        return [str(item).strip() for item in data if str(item).strip()]
    items = [line.strip() for line in text.replace(",", "\n").splitlines() if line.strip()]
    return items


# ---------------------------------------------------------------------------
# Cliente Playwright
# ---------------------------------------------------------------------------
class MercadonaClient:
    def __init__(
        self,
        cookie_file: str = COOKIE_FILE,
        headless: bool = True,
        cp: str = DEFAULT_CP,
    ) -> None:
        self.cookie_file = cookie_file
        self.headless = headless
        self.cp = cp
        self._playwright = None
        self._browser = None
        self._context = None
        self._page: Page | None = None

    async def __aenter__(self) -> "MercadonaClient":
        if async_playwright is None:
            raise RuntimeError(
                "Playwright no está instalado. Ejecuta: pip install playwright && playwright install chromium"
            )
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            locale="es-ES", storage_state=self._load_state()
        )
        self._page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._context is not None:
            await self._save_state()
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    # -- estado / cookies -------------------------------------------------
    def _load_state(self) -> str | None:
        p = Path(self.cookie_file)
        if p.exists():
            log("cookies", f"Cargando estado desde {p}")
            return str(p)
        return None

    async def _save_state(self) -> None:
        if self._context is not None:
            await self._context.storage_state(path=self.cookie_file)
            log("cookies", f"Estado guardado en {self.cookie_file}")

    # -- navegación --------------------------------------------------------
    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Página no inicializada. Usa 'async with MercadonaClient()'")
        return self._page

    async def open(self, force_login: bool = False) -> None:
        log("nav", f"Abriendo {MERCADONA_URL}")
        await self.page.goto(MERCADONA_URL, wait_until="domcontentloaded")
        await self._accept_cookies()
        if not await self._is_in_tienda():
            await self._set_postal_code(self.cp)

        # Intentar login solo si se fuerza explícitamente con --login
        if force_login:
            await self._do_login()

    async def _accept_cookies(self) -> None:
        try:
            accept = self.page.locator(SEL_COOKIE_ACCEPT)
            if await accept.count() > 0:
                await accept.first.click()
                log("cookies", "Cookies aceptadas")
        except Exception as exc:  # pragma: no cover
            log("cookies", f"Aceptar cookies omitido: {exc}")

    async def _is_in_tienda(self) -> bool:
        url = self.page.url
        return TIENDA_HOST in url or "tienda" in url

    async def _set_postal_code(self, cp: str) -> None:
        log("cp", f"Configurando código postal {cp}")
        try:
            await self.page.wait_for_selector(SEL_CP_INPUT, timeout=8000)
        except Exception:
            log("cp", "No se encontró el input de CP (¿ya configurado?)")
            return
        await self.page.fill(SEL_CP_INPUT, cp)
        await self.page.click(SEL_CP_SUBMIT)
        log("cp", "CP enviado. Esperando redirección a la tienda…")
        try:
            await self.page.wait_for_url(
                lambda url: TIENDA_HOST in url, timeout=CP_REDIRECT_WAIT * 1000 + 5000
            )
        except Exception:
            await self.page.wait_for_timeout(int(CP_REDIRECT_WAIT * 1000))
        await self.page.wait_for_timeout(1000)
        log("cp", f"URL actual: {self.page.url}")

    # -- overlays / modals --------------------------------------------------
    async def _dismiss_overlays(self) -> None:
        """Cierra modales/overlays que bloquean la interacción (info, avisos)."""
        dismiss_selectors = [
            'button[aria-label="Cerrar"]',
            'button:has-text("Cerrar")',
            ".modal__close",
            '[data-testid="modal-close-button"]',
        ]
        for sel in dismiss_selectors:
            try:
                el = self.page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.click(timeout=3000)
                    log("overlay", f"Modal cerrado: {sel}")
                    await self.page.wait_for_timeout(1000)
            except Exception:
                pass
        # También intentar tecla Escape
        try:
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(500)
        except Exception:
            pass

    # -- login wall --------------------------------------------------------
    async def _check_login_wall(self) -> bool:
        """Detecta si Mercadona pide login para acceder al carrito."""
        try:
            login_indicators = [
                'text="Inicia sesión"',
                'text="Mi cuenta"',
                'input[type="email"]',
            ]
            for sel in login_indicators:
                if await self.page.locator(sel).count() > 0:
                    return True
        except Exception:
            pass
        return False

    # -- login --------------------------------------------------------------
    async def _do_login(self, email: str = "", password: str = "") -> bool:
        """Inicia sesión en Mercadona con email/password.

        Si email/password están vacíos y el navegador está en modo headed,
        espera LOGIN_TIMEOUT segundos para que el usuario haga login manual.
        Devuelve True si el login tuvo éxito.
        """
        email = email or MERCADONA_EMAIL
        password = password or MERCADONA_PASSWORD

        log("login", "Abriendo página de autenticación…")
        await self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await self.page.wait_for_timeout(3000)

        # Cerrar modal de cookies si aparece
        await self._accept_cookies()

        # Cerrar cualquier modal que bloquee la página (info, avisos, etc.)
        await self._dismiss_overlays()

        # Abrir dropdown "Identifícate"
        identifica = self.page.locator(SEL_IDENTIFICATE)
        if await identifica.count() > 0:
            await identifica.first.click()
            await self.page.wait_for_timeout(2000)
            log("login", "Dropdown Identifícate abierto")
        else:
            log("login", "Botón Identifícate no encontrado (¿ya logueado?)")
            if await self._is_logged_in():
                log("login", "✓ Ya hay sesión activa")
                return True

        # Click en "Continuar con email"
        email_opt = self.page.locator(SEL_LOGIN_EMAIL_OPTION)
        if await email_opt.count() > 0:
            await email_opt.first.click()
            await self.page.wait_for_timeout(3000)
            log("login", "Opción 'Continuar con email' seleccionada")
        else:
            log("login", "No se encontró opción 'Continuar con email'")

        # Rellenar formulario si hay credenciales
        if email and password:
            log("login", "Rellenando credenciales…")
            email_input = self.page.locator(SEL_LOGIN_EMAIL_INPUT).first
            pass_input = self.page.locator(SEL_LOGIN_PASSWORD_INPUT).first

            if await email_input.count() > 0 and await pass_input.count() > 0:
                await email_input.fill(email)
                await pass_input.fill(password)
                await self.page.wait_for_timeout(500)

                submit = self.page.locator(SEL_LOGIN_SUBMIT).first
                if await submit.count() > 0:
                    await submit.click()
                    await self.page.wait_for_timeout(5000)
                    log("login", "Formulario enviado")
                else:
                    log("login", "⚠ No se encontró botón de submit")
            else:
                log("login", "⚠ No se encontraron campos email/password")
                log("login", "Prueba con --headed para hacer login manual")
        elif not self.headless:
            log("login", f"Modo headed sin credenciales: esperando {LOGIN_TIMEOUT}s para login manual…")
            log("login", "  (Define MERCADONA_EMAIL y MERCADONA_PASSWORD para login automático)")
            await self.page.wait_for_timeout(int(LOGIN_TIMEOUT * 1000))
        else:
            log("login", "No hay credenciales configuradas. Define MERCADONA_EMAIL y MERCADONA_PASSWORD")

        # Verificar si el login funcionó
        if await self._is_logged_in():
            log("login", "✓ Login exitoso")
            await self._save_state()
            return True

        # Buscar mensajes de error
        error_el = self.page.locator(SEL_LOGIN_ERROR).first
        if await error_el.count() > 0:
            try:
                err_text = await error_el.inner_text()
                log("login", f"✗ Error de login: {err_text[:200]}")
            except Exception:
                log("login", "✗ Login fallido (sin mensaje de error)")
        else:
            log("login", "✗ Login fallido — verifica credenciales o usa --headed")

        return False

    async def _is_logged_in(self) -> bool:
        """Detecta si hay sesión activa buscando indicadores de usuario logueado."""
        for sel in SEL_LOGIN_SUCCESS_INDICATOR.split(", "):
            try:
                if await self.page.locator(sel.strip()).count() > 0:
                    return True
            except Exception:
                pass
        # También buscar que ya no aparece el botón "Identifícate"
        identifica = self.page.locator(SEL_IDENTIFICATE)
        if await identifica.count() == 0:
            # Podría estar logueado o la página no cargó — verificar contexto
            try:
                # Si estamos en la tienda y no hay dropdown, asumimos login
                if "tienda" in self.page.url:
                    return True
            except Exception:
                pass
        return False

    # -- búsqueda ----------------------------------------------------------
    async def search(self, term: str) -> list[Product]:
        log("search", f"Buscando: {term!r}")
        await self.page.wait_for_selector(SEL_SEARCH, timeout=10000)
        await self.page.fill(SEL_SEARCH, "")
        await self.page.fill(SEL_SEARCH, term)
        await self.page.press(SEL_SEARCH, "Enter")
        await self.page.wait_for_timeout(int(SEARCH_WAIT * 1000))
        return await self.extract_products(term)

    async def extract_products(self, search_term: str) -> list[Product]:
        log("extract", "Extrayendo productos de la página…")
        products: list[Product] = []
        try:
            await self.page.wait_for_selector(SEL_PRODUCT, timeout=10000)
        except Exception:
            log("extract", "No se encontraron productos")
            return products

        cards = self.page.locator(SEL_PRODUCT)
        count = await cards.count()
        log("extract", f"Se encontraron {count} tarjetas de productos")
        for i in range(count):
            try:
                card = cards.nth(i)
                name_el = card.locator(
                    ".product-cell__description-name, h2, h3, [class*='name']"
                ).first
                name = (await name_el.inner_text() if await name_el.count() else "").strip()
                if not name:
                    name = (await card.inner_text()).split("\n")[0].strip()
                price_txt = ""
                price_el = card.locator(
                    ".product-cell__price, [class*='price']"
                ).first
                if await price_el.count():
                    price_txt = (await price_el.inner_text()).strip()
                match = PRICE_RE.search(price_txt)
                price = match.group(1) if match else (price_txt or None)
                if name:
                    products.append(Product(name=name, price=price, search_term=search_term))
            except Exception as exc:  # pragma: no cover
                log("extract", f"Error leyendo tarjeta {i}: {exc}")
        return products

    # -- añadir al carrito -------------------------------------------------
    async def add_to_cart(self, product: Product, retries: list[str] | None = None) -> bool:
        retries = retries or [""]
        terms = [product.search_term, *retries]
        for term in terms:
            await self.search(term)
            found = await self._click_add_for_first_match()
            if found:
                log("add", f"Añadido: {product.name} (búsqueda {term!r})")
                await self.page.wait_for_timeout(int(ADD_TO_CART_DELAY * 1000))
                return True
        log("add", f"No encontrado: {product.name}")
        return False

    async def _click_add_for_first_match(self) -> bool:
        card = self.page.locator(SEL_PRODUCT).first
        if await card.count() == 0:
            return False
        for sel in (SEL_ADD_CART_PRIMARY, SEL_ADD_CART_FALLBACK):
            btn = card.locator(sel).first
            if await btn.count():
                try:
                    await btn.click()
                    return True
                except Exception as exc:
                    log("add", f"Error al hacer click en {sel}: {exc}")
                    continue
        # intentar a nivel de página
        for sel in (SEL_ADD_CART_PRIMARY, SEL_ADD_CART_FALLBACK):
            btn = self.page.locator(sel).first
            if await btn.count():
                try:
                    await btn.click()
                    return True
                except Exception:
                    continue
        return False

    async def add_many(self, items: list[str], dry_run: bool = False) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for item in items:
            log("item", f"---- {item} ----")
            products = await self.search(item)
            if products:
                top = products[0]
                log("item", f"Mejor coincidencia: {top.name} @ {top.price}€")
                if dry_run:
                    results.append({"item": item, "found": True, "product": top.to_dict(), "added": False})
                    continue
                if await self._check_login_wall():
                    log("login", "Se requiere login en Mercadona. Inicia sesión manualmente.")
                    results.append({"item": item, "found": True, "product": top.to_dict(), "added": False, "login_wall": True})
                    continue
                added = await self.add_to_cart(top, retries=[item + " blanca", item + " fresco"])
                results.append({"item": item, "found": True, "product": top.to_dict(), "added": added})
            else:
                log("item", f"No se encontraron resultados para {item!r}")
                results.append({"item": item, "found": False, "added": False})
        cart_url = "https://tienda.mercadona.es/cart"
        log("summary", f"Procesados {len(items)} items. Carrito: {cart_url}")
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Cliente de Mercadona Online con Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--search", help="Buscar un único producto y mostrar resultados")
    g.add_argument("--add", help="Lista separada por comas de productos a añadir al carrito")
    g.add_argument("--add-from-file", help="Archivo JSON/TXT con lista de productos")
    g.add_argument("--list", help="Lista separada por comas (con --dry-run para solo búsqueda)")
    p.add_argument("--dry-run", action="store_true", help="Solo buscar, no añadir al carrito")
    p.add_argument("--json", action="store_true", help="Salida en formato JSON")
    p.add_argument("--headed", action="store_true", help="Mostrar navegador (no headless)")
    p.add_argument("--login", action="store_true", help="Forzar login (con credenciales de entorno o manual si --headed)")
    p.add_argument("--cp", default=DEFAULT_CP, help=f"Código postal (default: {DEFAULT_CP})")
    p.add_argument("--cookie-file", default=COOKIE_FILE, help="Ruta del fichero de cookies")
    return p


async def run(args: argparse.Namespace) -> int:
    items: list[str] | None = None
    single_search = None
    dry_run = args.dry_run

    if args.search:
        single_search = args.search
        items = [args.search]
        dry_run = True
    elif args.add:
        items = parse_items(args.add)
        dry_run = False
    elif args.add_from_file:
        items = load_list_file(args.add_from_file)
    elif args.list:
        items = parse_items(args.list)
    else:  # unreachable due to argparse
        return 2

    async with MercadonaClient(
        cookie_file=args.cookie_file, headless=not args.headed, cp=args.cp
    ) as client:
        await client.open(force_login=args.login)
        results = await client.add_many(items, dry_run=dry_run)

    single_search = args.search is not None
    if args.json or single_search:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        log("abort", "Interrumpido por el usuario")
        return 130
    except Exception as exc:
        log("error", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())