from flask import request, jsonify

# Mock Database for this module (In-memory)
orders = {
    1: {"id": 1, "order_title": "Sausage Pizza"}
}
current_order_id = 2

def register(app, session=None):
    """
    Registers the Bulk Operations endpoint.
    """

    # Bulk create orders endpoint
    @app.route("/api/orders/bulk", methods=["POST"])
    def bulk_create_orders():
        global current_order_id
        data = request.get_json()

        if not data or "orders" not in data:
            return jsonify({
                "error": "Bad Request",
                 "message": "'orders' array is required",
                "code": 400
            }), 400

        if not isinstance(data["orders"], list):
            return jsonify({
                "error": "Bad Request",
                "message": "'orders' must be an array",
                "code": 400
            }), 400
        
        results = {
            "created": [],
            "failed": []
        }

        for idx, order_data in enumerate(data["orders"]):
            if not isinstance(order_data, dict) or "order_title" not in order_data:
                results["failed"].append({
                    "index": idx,
                    "data": order_data,
                    "error": "Missing or invalid 'order_title'"
                })
                continue

            new_order = {
                "id": current_order_id,
                "order_title": order_data["order_title"]
            }
            orders[current_order_id] = new_order
            results["created"].append(new_order)
            current_order_id += 1


        # Partial failure handling
        if results["failed"] and not results["created"]:
            return jsonify({
                "error": "All order creations failed",
                "message": "No orders were created",
                "details": results["failed"],
                "code": 400
            }), 400
        
        status_code = 207 if results["failed"] else 201
        return jsonify(results), status_code
    
    # Bulk update orders endpoint
    @app.route("/api/orders/bulk", methods=["PUT"])
    def bulk_update_orders():
        data = request.get_json()

        if not data or "orders" not in data:
            return jsonify({
                "error": "Bad Request",
                "message": "'orders' array is required",
                "code": 400
            }), 400
        
        if not isinstance(data["orders"], list):
            return jsonify({
                "error": "Bad Request",
                "message": "'orders' must be an array",
                "code": 400
            }), 400
        
        results = {
            "updated": [],
            "failed": []
        }

        for idx, order_data in enumerate(data["orders"]):
            if (not isinstance(order_data, dict) or 
                "id" not in order_data or 
                "order_title" not in order_data):
                results["failed"].append({
                    "index": idx,
                    "data": order_data,
                    "error": "Missing 'id' or 'order_title'"
                })
                continue

            order_id = order_data["id"]

            if order_id not in orders:
                results["failed"].append({
                    "index": idx,
                    "id": order_id,
                    "error": "Order not found"
                })
                continue

            if "order_title" not in order_data:
                results["failed"].append({
                    "index": idx,
                    "id": order_id,
                    "error": "Missing 'order_title'"
                })
                continue

            orders[order_id]["order_title"] = order_data["order_title"]
            results["updated"].append(orders[order_id])

        # Partial failure handling
        if results["failed"] and not results["updated"]:
            return jsonify({
                "error": "All order updates failed",
                "message": "No orders were updated",
                "details": results["failed"],
                "code": 400
            }), 400
        status_code = 207 if results["failed"] else 200
        return jsonify(results), status_code
    
     