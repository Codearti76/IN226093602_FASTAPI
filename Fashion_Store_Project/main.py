from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional
import math

app = FastAPI()

# -------------------------
# DATA
# -------------------------
products = [
    {"id": 1, "name": "Casual Shirt", "brand": "Zara", "category": "Shirt", "price": 1299, "sizes_available": ["S","M","L"], "in_stock": True},
    {"id": 2, "name": "Denim Jeans", "brand": "Levis", "category": "Jeans", "price": 1999, "sizes_available": ["M","L","XL"], "in_stock": True},
    {"id": 3, "name": "Running Shoes", "brand": "Nike", "category": "Shoes", "price": 3499, "sizes_available": ["8","9","10"], "in_stock": True},
    {"id": 4, "name": "Summer Dress", "brand": "H&M", "category": "Dress", "price": 1599, "sizes_available": ["S","M"], "in_stock": True},
    {"id": 5, "name": "Leather Jacket", "brand": "Puma", "category": "Jacket", "price": 4999, "sizes_available": ["M","L"], "in_stock": False},
    {"id": 6, "name": "Formal Shirt", "brand": "Allen Solly", "category": "Shirt", "price": 1499, "sizes_available": ["S","M","L","XL"], "in_stock": True}
]

orders = []
wishlist = []
order_counter = 1

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

    if category is not None:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if brand is not None:
        result = [p for p in result if p["brand"].lower() == brand.lower()]

    if max_price is not None:
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
    name: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    price: float = Field(..., gt=0)
    sizes_available: List[str]
    in_stock: bool = True


class WishlistOrderRequest(BaseModel):
    customer_name: str
    delivery_address: str


# -------------------------
# BASIC APIs
# -------------------------
@app.get("/")
def home():
    return {"message": "Welcome to TrendZone Fashion Store"}


@app.get("/products")
def get_products():
    total = len(products)
    in_stock_count = sum(1 for p in products if p["in_stock"])
    return {"total": total, "in_stock_count": in_stock_count, "products": products}


@app.get("/products/summary")
def summary():
    total = len(products)
    in_stock = sum(1 for p in products if p["in_stock"])
    brands = list(set(p["brand"] for p in products))

    category_count = {}
    for p in products:
        category_count[p["category"]] = category_count.get(p["category"], 0) + 1

    return {
        "total": total,
        "in_stock": in_stock,
        "out_of_stock": total - in_stock,
        "brands": brands,
        "category_count": category_count
    }
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
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# -------------------------
# PRODUCT CRUD
# -------------------------
@app.post("/products", status_code=201)
def create_product(product: NewProduct):
    for p in products:
        if p["name"].lower() == product.name.lower() and p["brand"].lower() == product.brand.lower():
            raise HTTPException(status_code=400, detail="Product already exists")

    new_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": new_id,
        **product.dict()
    }

    products.append(new_product)
    return new_product


@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if price is not None:
        product["price"] = price

    if in_stock is not None:
        product["in_stock"] = in_stock

    return product

@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    in_stock: Optional[bool] = Query(None),
    max_price: Optional[int] = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, gt=0),
    limit: int = Query(3, gt=0)
):

    result = products

    # 🔍 1. SEARCH
    if keyword is not None:
        k = keyword.lower()
        result = [
            p for p in result
            if k in p["name"].lower()
            or k in p["brand"].lower()
            or k in p["category"].lower()
        ]

    # 🎯 2. FILTER
    if category is not None:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if brand is not None:
        result = [p for p in result if p["brand"].lower() == brand.lower()]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    # 🔄 3. SORT
    allowed_fields = ["price", "name", "brand", "category"]
    allowed_order = ["asc", "desc"]

    if sort_by not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Allowed: {allowed_fields}")

    if order not in allowed_order:
        raise HTTPException(status_code=400, detail="Order must be asc/desc")

    reverse = True if order == "desc" else False

    result = sorted(
        result,
        key=lambda x: x[sort_by].lower() if isinstance(x[sort_by], str) else x[sort_by],
        reverse=reverse
    )

    # 📄 4. PAGINATION
    total_items = len(result)
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1

    start = (page - 1) * limit
    end = start + limit

    paginated = result[start:end]

    return {
        "filters": {
            "keyword": keyword,
            "category": category,
            "brand": brand,
            "in_stock": in_stock,
            "max_price": max_price
        },
        "sorting": {
            "sort_by": sort_by,
            "order": order
        },
        "pagination": {
            "current_page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages
        },
        "results": paginated
    }
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if any(order.get("product_id") == product_id for order in orders):
        raise HTTPException(status_code=400, detail="Cannot delete product with existing orders")

    products.remove(product)

    return {"message": "Product deleted", "product_id": product_id}


# -------------------------
# ORDER APIs
# -------------------------
@app.get("/orders")
def get_orders():
    total_revenue = sum(o.get("total_price", 0) for o in orders)
    return {"orders": orders, "total": len(orders), "total_revenue": total_revenue}


@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    product = find_product(order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail="Out of stock")

    if order.size not in product["sizes_available"]:
        raise HTTPException(status_code=400, detail=f"Available sizes: {product['sizes_available']}")

    breakdown = calculate_order_total(product["price"], order.quantity, order.gift_wrap, order.season_sale)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
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
    return {"page": page, "total_pages": math.ceil(total/limit), "orders": orders[start:end]}


# -------------------------
# WISHLIST
# -------------------------
@app.post("/wishlist/add")
def add_wishlist(customer_name: str, product_id: int, size: str):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if size not in product["sizes_available"]:
        raise HTTPException(status_code=400, detail=f"Available sizes: {product['sizes_available']}")

    if any(w["customer_name"] == customer_name and w["product_id"] == product_id and w["size"] == size for w in wishlist):
        raise HTTPException(status_code=400, detail="Already in wishlist")

    item = {
        "customer_name": customer_name,
        "product_id": product_id,
        "size": size
    }

    wishlist.append(item)
    return item


@app.get("/wishlist")
def get_wishlist():
    total_value = sum(find_product(w["product_id"])["price"] for w in wishlist)
    return {"wishlist": wishlist, "total_value": total_value}


@app.delete("/wishlist/remove")
def remove_wishlist(customer_name: str, product_id: int):
    for item in wishlist:
        if item["customer_name"] == customer_name and item["product_id"] == product_id:
            wishlist.remove(item)
            return {"message": "Removed"}

    raise HTTPException(status_code=404, detail="Item not found")


@app.post("/wishlist/order-all", status_code=201)
def order_all(data: WishlistOrderRequest):
    global order_counter

    user_items = [w for w in wishlist if w["customer_name"] == data.customer_name]

    if not user_items:
        raise HTTPException(status_code=400, detail="Wishlist empty")

    created_orders = []
    total = 0

    for item in user_items:
        product = find_product(item["product_id"])

        breakdown = calculate_order_total(product["price"], 1, False, False)

        new_order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "product_id": product["id"],
            "product_name": product["name"],
            "brand": product["brand"],
            "size": item["size"],
            "quantity": 1,
            "delivery_address": data.delivery_address,
            "total_price": breakdown["final_total"]
        }

        orders.append(new_order)
        created_orders.append(new_order)
        total += breakdown["final_total"]

        order_counter += 1

    wishlist[:] = [w for w in wishlist if w["customer_name"] != data.customer_name]

    return {
        "orders": created_orders,
        "grand_total": total
    }