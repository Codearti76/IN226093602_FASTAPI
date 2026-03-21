from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import math

app = FastAPI()

# -------------------------
# DATA
# -------------------------
products = [
    {"id": 1, "name": "Casual Shirt", "brand": "Zara", "category": "Shirt", "price": 1299, "sizes_available": ["S", "M", "L"], "in_stock": True},
    {"id": 2, "name": "Denim Jeans", "brand": "Levis", "category": "Jeans", "price": 1999, "sizes_available": ["M", "L", "XL"], "in_stock": True},
    {"id": 3, "name": "Running Shoes", "brand": "Nike", "category": "Shoes", "price": 3499, "sizes_available": ["8", "9", "10"], "in_stock": True},
    {"id": 4, "name": "Summer Dress", "brand": "H&M", "category": "Dress", "price": 1599, "sizes_available": ["S", "M"], "in_stock": True},
    {"id": 5, "name": "Leather Jacket", "brand": "Puma", "category": "Jacket", "price": 4999, "sizes_available": ["M", "L"], "in_stock": False}
]

orders = []
order_counter = 1
wishlist = []

# -------------------------
# HELPERS
# -------------------------
def find_product(product_id):
    return next((p for p in products if p["id"] == product_id), None)


def calculate_order_total(price, quantity, gift_wrap, season_sale):
    base = price * quantity
    season_discount = 0.15 * base if season_sale else 0
    after_season = base - season_discount
    gift = 50 * quantity if gift_wrap else 0
    subtotal = after_season + gift
    bulk_discount = 0.05 * subtotal if quantity >= 5 else 0
    final = subtotal - bulk_discount

    return {
        "base_total": base,
        "season_discount": season_discount,
        "gift_wrap_cost": gift,
        "bulk_discount": bulk_discount,
        "final_total": final
    }


def filter_products_logic(category=None, brand=None, max_price=None, in_stock=None):
    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if brand:
        result = [p for p in result if p["brand"].lower() == brand.lower()]
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return result


# -------------------------
# MODELS
# -------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    size: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, le=10)
    delivery_address: str = Field(..., min_length=10)
    gift_wrap: bool = False
    season_sale: bool = False


class NewProduct(BaseModel):
    name: str
    brand: str
    category: str
    price: float
    sizes_available: List[str]
    in_stock: bool = True


class WishlistOrderRequest(BaseModel):
    customer_name: str
    delivery_address: str


# -------------------------
# PRODUCT APIs
# -------------------------
@app.get("/")
def home():
    return {"message": "Welcome to TrendZone Fashion Store"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/search")
def search_products(keyword: str):
    k = keyword.lower()
    result = [p for p in products if k in p["name"].lower() or k in p["brand"].lower() or k in p["category"].lower()]
    return {"total_found": len(result), "products": result}


@app.get("/products/filter")
def filter_products(category: Optional[str] = None, brand: Optional[str] = None, max_price: Optional[int] = None, in_stock: Optional[bool] = None):
    result = filter_products_logic(category, brand, max_price, in_stock)
    return {"total": len(result), "products": result}


@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    reverse = order == "desc"
    return {"products": sorted(products, key=lambda x: x[sort_by], reverse=reverse)}


@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 3):
    total = len(products)
    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "total_pages": math.ceil(total / limit),
        "products": products[start:end]
    }


@app.get("/products/{product_id}")
def get_product(product_id: int):
    p = find_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


# -------------------------
# ORDER APIs
# -------------------------
@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    product = find_product(order.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    if not product["in_stock"]:
        raise HTTPException(400, "Out of stock")

    if order.size not in product["sizes_available"]:
        raise HTTPException(400, f"Available sizes: {product['sizes_available']}")

    breakdown = calculate_order_total(product["price"], order.quantity, order.gift_wrap, order.season_sale)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,   # ✅ FIXED
        "product_id": product["id"],
        "product_name": product["name"],
        "brand": product["brand"],
        "size": order.size,
        "quantity": order.quantity,
        "delivery_address": order.delivery_address,
        "total_price": breakdown["final_total"]
    }

    orders.append(new_order)
    order_counter += 1

    return new_order


@app.get("/orders")
def get_orders():
    return {"orders": orders, "total": len(orders)}


@app.get("/orders/search")
def search_orders(customer_name: str):
    k = customer_name.lower()
    result = [o for o in orders if k in o.get("customer_name", "").lower()]
    return {"total_found": len(result), "orders": result}


@app.get("/orders/sort")
def sort_orders(sort_by: str = "total_price", order: str = "asc"):
    reverse = order == "desc"
    return {"orders": sorted(orders, key=lambda x: x.get(sort_by, 0), reverse=reverse)}


@app.get("/orders/page")
def paginate_orders(page: int = 1, limit: int = 3):
    total = len(orders)
    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "total_pages": math.ceil(total / limit),
        "orders": orders[start:end]
    }