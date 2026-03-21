from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ══ MODELS ════════════════════════════════════════════════════════

class OrderRequest(BaseModel):
    customer_name:    str = Field(..., min_length=2, max_length=100)
    product_id:       int = Field(..., gt=0)
    quantity:         int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class NewProduct(BaseModel):
    name:     str  = Field(..., min_length=2, max_length=100)
    price:    int  = Field(..., gt=0)
    category: str  = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name:    str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ══ DATA ══════════════════════════════════════════════════════════

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook',       'price':  99, 'category': 'Stationery',  'in_stock': True},
    {'id': 3, 'name': 'USB Hub',        'price': 799, 'category': 'Electronics', 'in_stock': True},
    {'id': 4, 'name': 'Pen Set',        'price':  49, 'category': 'Stationery',  'in_stock': True},
]

orders        = []
order_counter = 1
cart          = []

# ══ HELPERS ═══════════════════════════════════════════════════════

def find_product(product_id: int):
    for p in products:
        if p['id'] == product_id:
            return p
    return None

def calculate_total(product: dict, quantity: int) -> int:
    return product['price'] * quantity

def filter_products_logic(category=None, min_price=None,
                          max_price=None, in_stock=None):
    result = products
    if category  is not None:
        result = [p for p in result if p['category'] == category]
    if min_price is not None:
        result = [p for p in result if p['price'] >= min_price]
    if max_price is not None:
        result = [p for p in result if p['price'] <= max_price]
    if in_stock  is not None:
        result = [p for p in result if p['in_stock'] == in_stock]
    return result

# ══ ENDPOINTS ═════════════════════════════════════════════════════
#
# ROUTE ORDER — fixed routes BEFORE variable /{product_id}
# Day 6 new routes: /products/search  /products/sort  /products/page
# All placed ABOVE /products/{product_id}
#
# ══════════════════════════════════════════════════════════════════

# ── Day 1 ─────────────────────────────────────────────────────────

@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}


@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}


# ── Day 2 ─────────────────────────────────────────────────────────

@app.get('/products/filter')
def filter_products(
    category:  str  = Query(None),
    min_price: int  = Query(None),
    max_price: int  = Query(None),
    in_stock:  bool = Query(None),
):
    result = filter_products_logic(category, min_price, max_price, in_stock)
    return {'filtered_products': result, 'count': len(result)}


# ── Day 3 ─────────────────────────────────────────────────────────

@app.get('/products/compare')
def compare_products(
    product_id_1: int = Query(...),
    product_id_2: int = Query(...),
):
    p1 = find_product(product_id_1)
    p2 = find_product(product_id_2)
    if not p1:
        return {'error': f'Product {product_id_1} not found'}
    if not p2:
        return {'error': f'Product {product_id_2} not found'}
    cheaper = p1 if p1['price'] < p2['price'] else p2
    return {
        'product_1':    p1,
        'product_2':    p2,
        'better_value': cheaper['name'],
        'price_diff':   abs(p1['price'] - p2['price']),
    }


# ── Day 6 — Step 21: Search by keyword ───────────────────────────

@app.get('/products/search')
def search_products(
    keyword: str = Query(..., description='Word to search for'),
):
    results = [
        p for p in products
        if keyword.lower() in p['name'].lower()
    ]
    if not results:
        return {'message': f'No products found for: {keyword}', 'results': []}
    return {
        'keyword':     keyword,
        'total_found': len(results),
        'results':     results,
    }


# ── Day 6 — Step 22: Sort by price or name ───────────────────────

@app.get('/products/sort')
def sort_products(
    sort_by: str = Query('price', description='price or name'),
    order:   str = Query('asc',   description='asc or desc'),
):
    if sort_by not in ['price', 'name']:
        return {'error': "sort_by must be 'price' or 'name'"}
    if order not in ['asc', 'desc']:
        return {'error': "order must be 'asc' or 'desc'"}

    reverse         = (order == 'desc')
    sorted_products = sorted(products, key=lambda p: p[sort_by], reverse=reverse)

    return {
        'sort_by':  sort_by,
        'order':    order,
        'products': sorted_products,
    }
@app.get('/products/sort-by-category')
def sort_by_category():
    sorted_products = sorted(
        products,
        key=lambda p: (p['category'], p['price'])
    )

    return {
        "message": "Sorted by category and price",
        "products": sorted_products
    }

# ── Day 6 — Step 23: Pagination ───────────────────────────────────
#----Merged params-------
@app.get('/products/browse')
def browse_products(
    keyword: str = Query(None),
    category: str = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    in_stock: bool = Query(None),
    sort_by: str = Query('price'),
    order: str = Query('asc'),
    page: int = Query(1),
    limit: int = Query(2)
):
    result = products

    # 🔍 Search
    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower()]

    # 🎯 Filter
    if category:
        result = [p for p in result if p['category'] == category]

    if min_price is not None:
        result = [p for p in result if p['price'] >= min_price]

    if max_price is not None:
        result = [p for p in result if p['price'] <= max_price]

    if in_stock is not None:
        result = [p for p in result if p['in_stock'] == in_stock]

    # 🔃 Sort
    if sort_by in ['price', 'name']:
        reverse = True if order == 'desc' else False
        result = sorted(result, key=lambda p: p[sort_by], reverse=reverse)

    # 📄 Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = result[start:end]

    return {
        "total_results": len(result),
        "page": page,
        "limit": limit,
        "products": paginated
    }


@app.get('/products/page')
def get_products_paged(
    page:  int = Query(1, ge=1,  description='Page number'),
    limit: int = Query(2, ge=1, le=20, description='Items per page'),
):
    start = (page - 1) * limit
    end   = start + limit
    paged = products[start:end]

    return {
        'page':        page,
        'limit':       limit,
        'total':       len(products),
        'total_pages': -(-len(products) // limit),   # ceiling division
        'products':    paged,
    }


# ── Day 4 — CRUD ──────────────────────────────────────────────────
# Variable route /{product_id} — always AFTER all fixed routes

@app.post('/products')
def add_product(new_product: NewProduct, response: Response):
    existing_names = [p['name'].lower() for p in products]
    if new_product.name.lower() in existing_names:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'error': 'Product with this name already exists'    next_id = max(p['id'] for p in products) + 1
    product = {
        'id':       next_id,
        'name':     new_product.name,
        'price':    new_product.price,
        'category': new_product.category,
        'in_stock': new_product.in_stock
    }
    products.append(product)
    response.status_code = status.HTTP_201_CREATED
    return {'message': 'Product added', 'product': product}


@app.put('/products/{product_id}')
def update_product(
    product_id: int,
    response:   Response,
    in_stock:   bool = Query(None),
    price:      int  = Query(None),
):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
    if in_stock is not None:
        product['in_stock'] = in_stock
    if price is not None:
        product['price'] = price
    return {'message': 'Product updated', 'product': product}


@app.delete('/products/{product_id}')
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
    products.remove(product)
    return {'message': f"Product '{product['name']}' deleted"}


@app.get('/products/{product_id}')
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        return {'error': 'Product not found'}
    return {'product': product}


# ── Day 2 — Orders ────────────────────────────────────────────────

@app.post('/orders')
def place_order(order_data: OrderRequest):
    global order_counter
    product = find_product(order_data.product_id)
    if not product:
        return {'error': 'Product not found'}
    if not product['in_stock']:
        return {'error': f"{product['name']} is out of stock"}
    total = calculate_total(product, order_data.quantity)
    order = {
        'order_id':         order_counter,
        'customer_name':    order_data.customer_name,
        'product':          product['name'],
        'quantity':         order_data.quantity,
        'delivery_address': order_data.delivery_address,
        'total_price':      total,
        'status':           'confirmed',
    }
    orders.append(order)
    order_counter += 1
    return {'message': 'Order placed successfully', 'order': order}


@app.get("/orders")
def get_orders():
    total_revenue = sum(order["total_price"] for order in orders)

    return {
        "orders": orders,
        "total": len(orders),
        "total_revenue": total_revenue
    }

@app.get('/orders/page')
def paginate_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(2, ge=1, le=50)
):
    start = (page - 1) * limit
    end = start + limit

    paginated_orders = orders[start:end]

    total_orders = len(orders)
    total_pages = -(-total_orders // limit)  # ceiling division

    return {
        "page": page,
        "limit": limit,
        "total_orders": total_orders,
        "total_pages": total_pages,
        "orders": paginated_orders
    }

# ── Day 5 — Cart ──────────────────────────────────────────────────
# fixed routes /cart/add and /cart/checkout BEFORE variable /cart/{product_id}

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    # find product
    product = next((p for p in products if p["id"] == product_id), None)

    # check product exists
    if not product:
        return {"error": "Product not found"}

    # check stock
    if not product["in_stock"]:
        return {"error": "Product out of stock"}

    # check if already in cart
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * product["price"]
            return {
                "message": "Cart updated",
                "item": item
            }

    # add new item
    new_item = {
        "product_id": product_id,
        "name": product["name"],
        "quantity": quantity,
        "price": product["price"],
        "subtotal": product["price"] * quantity
    }

    cart.append(new_item)

    return {
        "message": "Item added to cart",
        "item": new_item
    }
@app.get('/cart')
def view_cart():
    if not cart:
        return {'message': 'Cart is empty', 'items': [], 'grand_total': 0}
    return {
        'items':       cart,
        'item_count':  len(cart),
        'grand_total': sum(i['subtotal'] for i in cart),
    }


@app.post('/cart/checkout')
def checkout(checkout_data: CheckoutRequest, response: Response):
    global order_counter
    if not cart:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'error': 'Cart is empty'}
    placed_orders = []
    grand_total   = 0
    for item in cart:
        order = {
            'order_id':         order_counter,
            'customer_name':    checkout_data.customer_name,
            'product':          item['product_name'],
            'quantity':         item['quantity'],
            'delivery_address': checkout_data.delivery_address,
            'total_price':      item['subtotal'],
            'status':           'confirmed',
        }
        orders.append(order)
        placed_orders.append(order)
        grand_total   += item['subtotal']
        order_counter += 1
    cart.clear()
    response.status_code = status.HTTP_201_CREATED
    return {
        'message':       'Checkout successful',
        'orders_placed': placed_orders,
        'grand_total':   grand_total,
    }

@app.get('/orders/search')
def search_orders(customer_name: str):
    results = [
        order for order in orders
        if customer_name.lower() in order['customer_name'].lower()
    ]

    if not results:
        return {
            "message": f"No orders found for '{customer_name}'",
            "results": []
        }

    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }
@app.delete('/cart/{product_id}')
def remove_from_cart(product_id: int, response: Response):
    for item in cart:
        if item['product_id'] == product_id:
            cart.remove(item)
            return {'message': f"{item['product_name']} removed from cart"}
    response.status_code = status.HTTP_404_NOT_FOUND
    return {'error': 'Product not in cart'}
