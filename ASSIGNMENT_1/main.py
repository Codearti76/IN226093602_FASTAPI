from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# -----------------------------
# Home Endpoint
# -----------------------------
@app.get("/")
def home():
    return {"message": "FastAPI Assignment Running"}


# -----------------------------
# Product Data
# -----------------------------
products = [
    {"id": 1, "name": "Wireless Mouse", "category": "Electronics", "price": 500, "in_stock": True},
    {"id": 2, "name": "USB Hub", "category": "Electronics", "price": 300, "in_stock": True},
    {"id": 3, "name": "Notebook", "category": "Stationery", "price": 50, "in_stock": False},
    {"id": 4, "name": "Pen Pack", "category": "Stationery", "price": 100, "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "category": "Accessories", "price": 700, "in_stock": True},
    {"id": 6, "name": "Monitor", "category": "Electronics", "price": 8000, "in_stock": True},
    {"id": 7, "name": "Headphones", "category": "Electronics", "price": 1500, "in_stock": False}
]

# -----------------------------
# Day 1 Endpoints
# -----------------------------

@app.get("/products")
def get_products():
    return {"total": len(products), "products": products}


@app.get("/products/category/{category}")
def get_products_by_category(category: str):
    return [p for p in products if p["category"].lower() == category.lower()]


@app.get("/products/instock")
def get_instock_products():
    return [p for p in products if p["in_stock"]]


@app.get("/products/search/{keyword}")
def search_product(keyword: str):
    return [p for p in products if keyword.lower() in p["name"].lower()]


@app.get("/store/summary")
def store_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock)
    }


@app.get("/products/deals")
def product_deals():
    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    return {
        "cheapest_product": cheapest,
        "most_expensive_product": expensive
    }


# -----------------------------
# Day 2 - Product Filters
# -----------------------------

@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None)
):
    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    return result


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


# -----------------------------
# Customer Feedback
# -----------------------------

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


feedback_list = []


@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):
    feedback_list.append(feedback.dict())

    return {
        "message": "Feedback submitted successfully",
        "data": feedback,
        "total_feedback": len(feedback_list)
    }


# -----------------------------
# Product Summary Dashboard
# -----------------------------

@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": expensive,
        "cheapest": cheapest,
        "categories": categories
    }


# -----------------------------
# Bulk Order Models
# -----------------------------

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)


class BulkOrder(BaseModel):
    company_name: str
    contact_email: str
    items: List[OrderItem]


orders = []


# -----------------------------
# Bulk Order Endpoint
# -----------------------------

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    total_price = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
            continue

        if not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": "Out of stock"
            })
            continue

        subtotal = product["price"] * item.quantity
        total_price += subtotal

        confirmed.append({
            "product": product["name"],
            "quantity": item.quantity,
            "subtotal": subtotal
        })

    new_order = {
        "order_id": len(orders) + 1,
        "company": order.company_name,
        "confirmed_orders": confirmed,
        "failed_orders": failed,
        "total_amount": total_price,
        "status": "pending"
    }

    orders.append(new_order)

    return new_order


# -----------------------------
# ⭐ Bonus - Confirm Order
# -----------------------------

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}