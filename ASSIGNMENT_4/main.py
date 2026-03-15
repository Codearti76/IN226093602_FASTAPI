from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Store products
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 649, "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "in_stock": True}
]

# Temporary storage
cart = []
orders = []

# Checkout request model
class Checkout(BaseModel):
    customer_name: str
    delivery_address: str


# Helper function to find product
def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


# Root endpoint
@app.get("/")
def home():
    return {"message": "Cart API Running"}


# Add item to cart
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # If item already in cart update quantity
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["unit_price"]

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    subtotal = product["price"] * quantity

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": subtotal
    }

    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }


# View cart
@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# Remove item from cart
@app.delete("/cart/{product_id}")
def remove_item(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}

    raise HTTPException(status_code=404, detail="Item not found in cart")


# Checkout
@app.post("/cart/checkout")
def checkout(data: Checkout):

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order_list = []
    grand_total = 0

    for item in cart:
        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        order_list.append(order)
        grand_total += item["subtotal"]

    cart.clear()

    return {
        "message": "Order placed successfully",
        "orders_placed": order_list,
        "grand_total": grand_total
    }


# View orders
@app.get("/orders")
def get_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }