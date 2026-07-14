#!/usr/bin/env python3
"""
Wrapper de mercadona-cli para meal-to-cart.

Expone funciones Python para operaciones de Mercadona usando el CLI
de ivorpad/mercadona-cli bajo el capó.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional


class MercadonaCLI:
    """Wrapper del CLI mercadona."""
    
    def __init__(self, warehouse: Optional[str] = None):
        """
        Args:
            warehouse: Warehouse ID (ej. "4182", "bcn1"). 
                       Si None, usa el configurado en ~/.mercadona/config.toml
        """
        self.warehouse = warehouse
        
    def _run(self, args: List[str], input_text: Optional[str] = None) -> Dict:
        """
        Ejecuta el CLI y devuelve JSON parseado.
        
        Args:
            args: Argumentos del comando (ej. ["batch", "-f", "-", "--fresh"])
            input_text: Texto a enviar por stdin (opcional)
            
        Returns:
            Dict parseado del JSON de salida
            
        Raises:
            subprocess.CalledProcessError: Si el comando falla
            json.JSONDecodeError: Si la salida no es JSON válido
        """
        cmd = ["mercadona"] + args
        if self.warehouse:
            cmd.extend(["--wh", self.warehouse])
        cmd.append("--json")
        
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    
    def batch_search(
        self, 
        items: List[str], 
        fresh: bool = True,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca múltiples productos en un solo request.
        
        Args:
            items: Lista de términos de búsqueda (ej. ["tomate", "cebolla"])
            fresh: Si True, excluye congelados y conservas
            category: Filtrar por categoría (ej. "Marisco y pescado")
            
        Returns:
            Lista de resultados, uno por término:
            [
                {
                    "query": "tomate",
                    "nbHits": 32,
                    "hits": [
                        {
                            "id": "69975",
                            "display_name": "Tomates pera",
                            "price_instructions": {
                                "unit_price": "2.11",
                                "reference_price": "1.900",
                                "reference_format": "kg",
                                "is_pack": false
                            },
                            "packaging": "Bandeja",
                            "categories": [{"name": "Verdura"}]
                        }
                    ]
                }
            ]
        """
        args = ["batch", "-f", "-"]
        if fresh:
            args.append("--fresh")
        if category:
            args.extend(["--category", category])
        
        input_text = "\n".join(items)
        return self._run(args, input_text)
    
    def resolve_shopping_list(
        self, 
        shopping_list: List[Dict]
    ) -> Dict:
        """
        Resuelve una shopping list (output de ingredient_consolidation.md)
        a productos concretos de Mercadona.
        
        Args:
            shopping_list: Lista de ingredientes con hints:
            [
                {
                    "name": "tomate",
                    "quantity": 6,
                    "fresh": true,
                    "category": null
                },
                {
                    "name": "salmón",
                    "quantity": 400,
                    "unit": "g",
                    "fresh": true,
                    "category": "Marisco y pescado"
                }
            ]
            
        Returns:
            {
                "resolved": [
                    {
                        "query": "tomate",
                        "product_id": "69975",
                        "product_name": "Tomates pera",
                        "quantity": 6,
                        "unit_price": "2.11",
                        "subtotal": "12.66",
                        "notes": ""
                    }
                ],
                "unresolved": [],
                "total": "65.40"
            }
        """
        resolved = []
        unresolved = []
        
        for item in shopping_list:
            query = item["name"]
            fresh = item.get("fresh", True)
            category = item.get("category")
            qty = item.get("quantity", 1)
            
            # Buscar producto
            results = self.batch_search([query], fresh=fresh, category=category)
            
            if not results or not results[0]["hits"]:
                unresolved.append({
                    "query": query,
                    "reason": "No results found"
                })
                continue
            
            # Tomar el primer hit (top match)
            hit = results[0]["hits"][0]
            product_id = hit["id"]
            product_name = hit["display_name"]
            unit_price = float(hit["price_instructions"]["unit_price"])
            is_pack = hit["price_instructions"].get("is_pack", False)
            
            # Ajustar cantidad si es necesario
            # Si el producto es pack y la cantidad es por unidad, convertir
            notes = ""
            if item.get("unit") == "g" and not is_pack:
                # Convertir gramos a kg si el producto se vende por peso
                qty = qty / 1000.0
                notes = f"Convertido {item['quantity']}g → {qty}kg"
            
            # Calcular subtotal
            subtotal = round(unit_price * qty, 2)
            
            resolved.append({
                "query": query,
                "product_id": product_id,
                "product_name": product_name,
                "quantity": qty,
                "unit_price": f"{unit_price:.2f}",
                "subtotal": f"{subtotal:.2f}",
                "notes": notes
            })
        
        # Calcular total
        total = sum(float(item["subtotal"]) for item in resolved)
        
        return {
            "resolved": resolved,
            "unresolved": unresolved,
            "total": f"{total:.2f}"
        }
    
    def generate_basket_file(
        self, 
        resolved: List[Dict], 
        output_path: str
    ) -> str:
        """
        Genera un archivo basket.txt para mercadona total/cart set-many.
        
        Args:
            resolved: Lista de productos resueltos (de resolve_shopping_list)
            output_path: Ruta donde guardar el archivo
            
        Returns:
            Ruta del archivo generado
        """
        lines = []
        lines.append("# Basket generado por meal-to-cart")
        lines.append("")
        
        for item in resolved:
            product_id = item["product_id"]
            qty = item["quantity"]
            name = item["product_name"]
            
            # Formato: "id qty  # name"
            lines.append(f"{product_id} {qty}  # {name}")
        
        output = Path(output_path)
        output.write_text("\n".join(lines), encoding="utf-8")
        
        return str(output)
    
    def preview_total(self, basket_file: str) -> Dict:
        """
        Calcula el total exacto de un basket antes de añadir al carrito.
        
        Args:
            basket_file: Ruta del archivo basket.txt
            
        Returns:
            {
                "lines": [
                    {
                        "id": "69975",
                        "name": "Tomates pera",
                        "qty": 2,
                        "unit_price": "2.11",
                        "subtotal": "4.22"
                    }
                ],
                "total": "7.02",
                "count": 3,
                "complete": true
            }
        """
        args = ["total", "-f", basket_file]
        return self._run(args)
    
    def fill_cart(
        self, 
        basket_file: str, 
        max_eur: float,
        dry_run: bool = False
    ) -> Dict:
        """
        Añade productos al carrito real de Mercadona.
        
        Args:
            basket_file: Ruta del archivo basket.txt
            max_eur: Límite de gasto (spending guard)
            dry_run: Si True, solo simula (usa preview_total)
            
        Returns:
            Si dry_run=True: output de preview_total
            Si dry_run=False: output del carrito tras añadir
            {
                "id": "770fb2c8-...",
                "version": 2,
                "products_count": 3,
                "lines": [...],
                "summary": {"total": "7.02"}
            }
        """
        if dry_run:
            return self.preview_total(basket_file)
        
        args = ["cart", "set-many", "-f", basket_file, "--max", str(max_eur)]
        return self._run(args)
    
    def get_cart(self) -> Dict:
        """
        Lee el carrito actual.
        
        Returns:
            {
                "id": "770fb2c8-...",
                "version": 2,
                "products_count": 3,
                "lines": [...],
                "summary": {"total": "7.02"}
            }
        """
        args = ["cart", "get"]
        return self._run(args)
    
    def clear_cart(self) -> Dict:
        """
        Vacía el carrito.
        
        Returns:
            Carrito vacío tras limpiar
        """
        args = ["cart", "clear"]
        return self._run(args)


# ============================================================================
# CLI para testing
# ============================================================================

def main():
    """CLI de prueba del wrapper."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Wrapper de mercadona-cli")
    parser.add_argument("--test-search", action="store_true", 
                       help="Test de búsqueda batch")
    parser.add_argument("--test-resolve", metavar="JSON", 
                       help="Test de resolución desde JSON")
    parser.add_argument("--warehouse", help="Warehouse ID (ej. 4182, bcn1)")
    
    args = parser.parse_args()
    
    cli = MercadonaCLI(warehouse=args.warehouse)
    
    if args.test_search:
        print("Test: batch search")
        items = ["tomate", "cebolla", "arroz redondo"]
        results = cli.batch_search(items, fresh=True)
        for result in results:
            query = result["query"]
            if result["hits"]:
                hit = result["hits"][0]
                print(f"  {query} → [{hit['id']}] {hit['display_name']} — {hit['price_instructions']['unit_price']}€")
            else:
                print(f"  {query} → no results")
    
    elif args.test_resolve:
        print("Test: resolve shopping list")
        with open(args.test_resolve) as f:
            shopping_list = json.load(f)
        
        resolved_data = cli.resolve_shopping_list(shopping_list)
        print(json.dumps(resolved_data, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
