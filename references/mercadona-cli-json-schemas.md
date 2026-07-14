# mercadona-cli — Esquemas JSON

Estructuras de datos del CLI para parsing en Python.

---

## Batch search output

```json
[
  {
    "query": "tomate",
    "nbHits": 32,
    "hits": [
      {
        "id": "69975",
        "display_name": "Tomates pera",
        "packaging": "Bandeja",
        "share_url": "https://tienda.mercadona.es/product/69975/...",
        "categories": [
          {"id": 1, "name": "Verdura"}
        ],
        "price_instructions": {
          "unit_price": "2.11",
          "reference_price": "1.900",
          "reference_format": "kg",
          "is_pack": false
        }
      }
    ]
  }
]
```

**Campos clave:**
- `id`: Product ID (string, puede tener decimales como "82830.1")
- `display_name`: Nombre completo del producto
- `unit_price`: Precio del item as-sold (string, ej. "2.11")
- `reference_price`: Precio normalizado por kg/L (string, ej. "1.900")
- `reference_format`: Unidad de referencia ("kg", "L", "ud")
- `is_pack`: Boolean, true si se vende en pack (ej. leche pack-6)
- `packaging`: "Bandeja", "Pack-6", "Pieza", etc.

---

## Total output

```json
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
```

**Campos clave:**
- `total`: String con total en euros (ej. "7.02")
- `count`: Número de líneas en el basket
- `complete`: Boolean, false si alguna línea falló al buscar precio

---

## Cart output (GET)

```json
{
  "id": "770fb2c8-cf41-4602-b093-34aeef9e7cd2",
  "version": 2,
  "products_count": 3,
  "open_order_id": null,
  "lines": [
    {
      "quantity": 2.0,
      "sources": [],
      "product": {
        "id": "69975",
        "display_name": "Tomates pera",
        "price_instructions": {
          "unit_price": "2.11",
          "reference_price": "1.900",
          "reference_format": "kg"
        }
      }
    }
  ],
  "summary": {
    "total": "7.02"
  }
}
```

**Campos clave:**
- `id`: Cart ID (UUID)
- `version`: Version del carrito (incrementa con cada write)
- `products_count`: Número de productos (suma de quantities)
- `lines[].quantity`: Float (puede ser decimal para productos por peso)
- `summary.total`: String con total en euros

---

## Error output

```json
{
  "errors": [
    {
      "detail": "Invalid quantity 0.5 for a product sold by unit",
      "code": "invalid"
    }
  ]
}
```

**HTTP status codes:**
- `400`: Bad request (parámetros inválidos)
- `401`: Not authenticated (token expirado)
- `403`: Forbidden (Akamai challenge o IP datacenter)
- `404`: Product not found (ID incorrecto o warehouse distinto)
- `429`: Rate limit (auto-retry con backoff)

---

## Parsing en Python

```python
import json
import subprocess

# Batch search
result = subprocess.run(
    ["mercadona", "batch", "-f", "-", "--fresh", "--json"],
    input="tomate\ncebolla\n",
    capture_output=True,
    text=True,
    check=True
)
data = json.loads(result.stdout)

for query_result in data:
    query = query_result["query"]
    if query_result["hits"]:
        hit = query_result["hits"][0]
        product_id = hit["id"]
        name = hit["display_name"]
        price = hit["price_instructions"]["unit_price"]
        print(f"{query} → [{product_id}] {name} — {price}€")

# Total
result = subprocess.run(
    ["mercadona", "total", "-f", "basket.txt", "--json"],
    capture_output=True,
    text=True,
    check=True
)
data = json.loads(result.stdout)
total = float(data["total"])
count = data["count"]
print(f"Total: {total}€ ({count} productos)")
```

Ver `mercadona_cli_wrapper.py` para implementación completa.
