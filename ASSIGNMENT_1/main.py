from fastapi import FastAPI

app = FastAPI()

# Product data
products = [
    {"id": 1, "name": "Laptop", "category": "Electronics", "price": 800, "in_stock": True},
    {"id": 2, "name": "Wireless Mouse", "category": "Electronics", "price": 25, "in_stock": True},
    {"id": 3, "name": "Keyboard", "category": "Electronics", "price": 45, "in_stock": False},
    {"id": 4, "name": "Book", "category": "Books", "price": 15, "in_stock": True},
    {"id": 5, "name": "Notebook", "category": "Stationery", "price": 5, "in_stock": True},
    {"id": 6, "name": "Pen", "category": "Stationery", "price": 2, "in_stock": False},
    {"id": 7, "name": "Headphones", "category": "Electronics", "price": 120, "in_stock": True}
]


# Q1 — Return all products
@app.get("/products")
def get_products():
    return {
        "total": len(products),
        "products": products
    }


# Q2 — Filter by category
@app.get("/products/category/{category}")
def get_products_by_category(category: str):
    result = [
        product for product in products
        if product["category"].lower() == category.lower()
    ]
    return {
        "category": category,
        "count": len(result),
        "products": result
    }


# Q3 — Products in stock
@app.get("/products/instock")
def get_instock_products():
    result = [product for product in products if product["in_stock"]]
    return {
        "available_products": len(result),
        "products": result
    }


# Q4 — Store summary
@app.get("/store/summary")
def store_summary():
    categories = list(set([p["category"] for p in products]))
    total_products = len(products)
    in_stock = len([p for p in products if p["in_stock"]])

    return {
        "total_products": total_products,
        "in_stock_products": in_stock,
        "out_of_stock_products": total_products - in_stock,
        "categories": categories
    }


# Q5 — Search products
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    result = [
        product for product in products
        if keyword.lower() in product["name"].lower()
    ]
    return {
        "search_keyword": keyword,
        "results_found": len(result),
        "products": result
    }


# ⭐ Bonus — Cheapest and most expensive
@app.get("/products/deals")
def product_deals():
    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    return {
        "cheapest_product": cheapest,
        "most_expensive_product": expensive
    }