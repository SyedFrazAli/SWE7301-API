"""US-09: Parameter-Based Filtering

This module implements parameter-based filtering functionality for the API.
Allows clients to request filtered data using query parameters.
"""

from flask import request, jsonify

def apply_filters(query_obj, filters):
    """
    Apply filter parameters to a database query.
    
    Args:
        query_obj: SQLAlchemy query object
        filters: Dictionary of filter parameters from request
    
    Returns:
        Filtered query object
    """
    for key, value in filters.items():
        if hasattr(query_obj.model, key):
            query_obj = query_obj.filter(getattr(query_obj.model, key) == value)
    return query_obj

def create_filter_route(app, model, session):
    """
    Create a filtered GET endpoint for the given model.
    
    Args:
        app: Flask application
        model: SQLAlchemy model class
        session: Database session
    """
    @app.route(f'/api/{model.__tablename__}/filter', methods=['GET'])
    def filtered_list():
        try:
            filters = request.args.to_dict()
            query = session.query(model)
            query = apply_filters(query, filters)
            results = query.all()
            return jsonify([item.to_dict() for item in results])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
