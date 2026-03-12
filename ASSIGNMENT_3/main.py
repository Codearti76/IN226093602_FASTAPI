# Import libraries
from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel
from typing import Optional

# Create FastAPI app

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# Product database
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
     {"id": 3, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
   
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

# Root API
@app.get("/")
def home():
    return {"message": "FastAPI Assignment Running"}

# Product model
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

# Add product
@app.post("/products", status_code=201)
def add_product(product: NewProduct, response: Response):

    # Check duplicate name
    for p in products:
        if p["name"].lower() == product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Product already exists"}

    # Generate next ID
    next_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": next_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return new_product



# Inventory audit
@app.get("/products/audit")
def product_audit():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    total_value = sum(p["price"] * 10 for p in in_stock)

    expensive = max(products, key=lambda p: p["price"])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_products": [p["name"] for p in out_stock],
        "total_stock_value": total_value,
        "most_expensive_product": expensive
    }
# Apply category discount
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(...),
    discount_percent: int = Query(..., ge=1, le=99)
):

    updated = []

    for p in products:
        if p["category"].lower() == category.lower():

            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category {category}"}

    return {
        "message": f"{discount_percent}% discount applied",
        "updated_products": updated
    }
# Get single product
@app.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return product

    return {"error": "Product not found"}
# Update product
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    price: Optional[int] = None,
    in_stock: Optional[bool] = None
):

    for product in products:
        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return {"message": "Product updated", "product": product}

    return {"error": "Product not found"}

# Delete product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": f"{product['name']} deleted successfully"}

    return {"error": "404,Product not found"}
