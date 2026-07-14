#!/usr/bin/env python3
"""
Test end-to-end de meal-to-cart con mercadona-cli.
"""

import json
import sys
from pathlib import Path

# Añadir scripts/ al path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from mercadona_cli_wrapper import MercadonaCLI


def test_e2e():
    """Test completo del flujo."""
    print("=" * 60)
    print("TEST END-TO-END: meal-to-cart + mercadona-cli")
    print("=" * 60)
    
    # 1. Shopping list de prueba (output de ingredient_consolidation.md)
    shopping_list = [
        {"name": "tomate", "quantity": 6, "unit": "ud", "fresh": True, "category": None},
        {"name": "cebolla", "quantity": 2, "unit": "ud", "fresh": True, "category": None},
        {"name": "arroz redondo", "quantity": 1, "unit": "kg", "fresh": False, "category": None},
        {"name": "salmón", "quantity": 400, "unit": "g", "fresh": True, "category": "Marisco y pescado"},
        {"name": "aceite oliva", "quantity": 1, "unit": "ud", "fresh": False, "category": None}
    ]
    
    print("\n1. Shopping list de entrada:")
    print(json.dumps(shopping_list, indent=2, ensure_ascii=False))
    
    # 2. Resolver a productos de Mercadona
    print("\n2. Resolviendo a productos de Mercadona...")
    cli = MercadonaCLI()
    resolved = cli.resolve_shopping_list(shopping_list)
    
    print(f"\n✓ Resueltos: {len(resolved['resolved'])} productos")
    print(f"✗ No encontrados: {len(resolved['unresolved'])} productos")
    print(f"Total estimado: {resolved['total']}€")
    
    for item in resolved["resolved"]:
        print(f"  • {item['query']} → [{item['product_id']}] {item['product_name']} — {item['quantity']} × {item['unit_price']}€ = {item['subtotal']}€")
    
    if resolved["unresolved"]:
        print("\n⚠ No encontrados:")
        for item in resolved["unresolved"]:
            print(f"  • {item['query']} — {item['reason']}")
    
    # 3. Generar basket file
    print("\n3. Generando basket.txt...")
    basket_file = "/tmp/meal2cart_test_basket.txt"
    cli.generate_basket_file(resolved["resolved"], basket_file)
    print(f"✓ Basket generado: {basket_file}")
    
    with open(basket_file) as f:
        print("\nContenido:")
        print(f.read())
    
    # 4. Preview total
    print("\n4. Preview total (verificación)...")
    preview = cli.preview_total(basket_file)
    print(f"Total: {preview['total']}€ ({preview['count']} productos)")
    
    # 5. Dry-run (NO añade al carrito real)
    print("\n5. Dry-run (simulación de añadir al carrito)...")
    result = cli.fill_cart(basket_file, max_eur=50.0, dry_run=True)
    print(f"✓ Simulación OK: {result['count']} productos, total {result['total']}€")
    
    # 6. Resumen final
    print("\n" + "=" * 60)
    print("TEST COMPLETADO ✅")
    print("=" * 60)
    print(f"Productos resueltos: {len(resolved['resolved'])}/{len(shopping_list)}")
    print(f"Total estimado: {resolved['total']}€")
    print(f"Preview total: {preview['total']}€")
    print("\n⚠️ Para añadir al carrito REAL:")
    print("   result = cli.fill_cart(basket_file, max_eur=50.0, dry_run=False)")
    print("   cart = cli.get_cart()")
    

if __name__ == "__main__":
    try:
        test_e2e()
    except Exception as e:
        print(f"\n❌ Test falló: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
