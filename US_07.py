from flask import request, jsonify

# In-memory data store for this module
orders = {
    1: {"id": 1, "order_title": "Sausage Pizza"}
}
current_order_id = 2

def registerOrder(app, session=None):
    """
    This registers the full rest API which supports basic crud operations: GET, POST, PUT, PATCH, and DELETE
    """

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method Not Allowed"}), 405
    
    # --- GET: Read All (Fulfills GET) ---
    @app.route("/api/orders", methods=["GET"])
    def get_orders():
        return jsonify({"orders": list(orders.values())}), 200

    # --- GET REQUEST: This api is for fetching a single order ---
    @app.route("/api/orders/<int:order_id>", methods=["GET"])
    def get_order(order_id):
        order = orders.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        return jsonify(order), 200

    # --- POST: This is a POST request to create a new order ---
    @app.route("/api/orders", methods=["POST"])
    def create_order():
        global current_order_id
        data = request.get_json()
        if not data or "order_title" not in data:
            return jsonify({"error": "Bad Request: 'order_title' is required"}), 400
        
        new_order = {"id": current_order_id, "order_title": data["order_title"]}
        orders[current_order_id] = new_order
        current_order_id += 1
        return jsonify(new_order), 201

    # --- PUT: This is a PUT request to update an existing order, this will fully replace an entity present in the database using the ID---
    @app.route("/api/orders/<int:order_id>", methods=["PUT"])
    def update_order(order_id):
        if order_id not in orders:
            return jsonify({"error": "Order not found"}), 404
        
        data = request.get_json()
        if not data or "order_title" not in data:
            return jsonify({"error": "Bad Request: 'order_title' is required"}), 400
            
        orders[order_id]["order_title"] = data["order_title"]
        return jsonify(orders[order_id]), 200

    # --- PATCH: This Endpoint allows partial updates of a database entity ---
    @app.route("/api/orders/<int:order_id>", methods=["PATCH"])
    def patch_order(order_id):
        if order_id not in orders:
            return jsonify({"error": "Order not found"}), 404
        
        data = request.get_json()
        if "order_title" in data:
            orders[order_id]["order_title"] = data["order_title"]
        return jsonify(orders[order_id]), 200

    # --- DELETE: This Endpoint is used to delete an order from the database ---
    @app.route("/api/orders/<int:order_id>", methods=["DELETE"])
    def delete_order(order_id):
        if order_id not in orders:
            return jsonify({"error": "Order not found"}), 404
    
        del orders[order_id]
        return "", 204


def register(app, session=None):
    """
    Backwards-compatible register wrapper expected by `app.py`.
    """
    # Delegate to the original implementation
    return registerOrder(app, session)
