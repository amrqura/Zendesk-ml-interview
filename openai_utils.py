function_specs = [
    {
        "name": "track_order",
        "description": (
            "Use this function only if the user is asking to *check*, *view*, or *track* the status of an order. "
            "Do not use this if they want to cancel or modify the order."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to track"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "cancel_order",
        "description": (
            "Use this function only if the user is asking to *cancel* or *remove* an order. "
            "Only call this if the user explicitly wants to cancel."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The ID of the order to cancel"
                }
            },
            "required": ["order_id"]
        }
    }
]