import os
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import sqlite3
import uvicorn
import random

import openai
from models.OrderRequest import OrderRequest
from models.UserMessage import UserMessage
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()


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


@app.on_event("startup")
def prepare_db():
    print("Initializing database...")
    init_db()
    print("Database ready.")


def insert_random_orders(cur):
    sample_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hassan", "Ivy", "Jack"]
    status_options = ["pending", "shipped", "cancelled"]

    for _ in range(random.randint(5, 10)):
        name = random.choice(sample_names)
        days_ago = random.randint(0, 20)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        status = random.choice(status_options)
        print("inserting {} - {} - {}".format(name, order_date, status))
        cur.execute("""
            INSERT INTO orders (customer_name, order_date, status)
            VALUES (?, ?, ?)
            """, (name, order_date, status))
# DB setup
def init_db():
    conn = sqlite3.connect("orders.db")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        order_date TEXT,
        status TEXT
    )
    """)
    insert_random_orders(cur)
    conn.commit()
    conn.close()


# Order simulation
@app.post("/track_order")
def track_order(request: OrderRequest):
    order_id = request.order_id
    conn = sqlite3.connect("orders.db")
    cur = conn.cursor()
    cur.execute("SELECT id, order_date, status FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"order_id": row[0], "status": row[2], "order_date": row[1]}
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/cancel_order")
def cancel_order(request:OrderRequest):
    order_id = request.order_id
    conn = sqlite3.connect("orders.db")
    cur = conn.cursor()
    cur.execute("SELECT order_date, status FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    if row:
        order_date = datetime.strptime(row[0], "%Y-%m-%d")
        if datetime.now() - order_date < timedelta(days=10):
            cur.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Order cancelled"}
        else:
            conn.close()
            return {"status": "failed", "message": "Cancellation window expired"}
    conn.close()
    raise HTTPException(status_code=404, detail="Order not found")


def ask_openai_with_function_call(user_message: str):
    messages = [
        {"role": "system", "content": (
            "You are a helpful assistant that manages order tracking and cancellation. "
            "Think step by step, and call a function only if needed."
        )},
        {"role": "user", "content": user_message}
    ]

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        functions=function_specs,
        function_call="auto"
    )

    message = response.choices[0].message

    # Capture model reasoning if any
    reasoning = message.content or ""  # May be None if function_call is used

    if message.function_call:
        func_name = message.function_call.name
        args = json.loads(message.function_call.arguments)

        if func_name == "track_order":
            result = track_order(OrderRequest(**args))
        elif func_name == "cancel_order":
            result = cancel_order(OrderRequest(**args))
        else:
            result = {"error": "Unknown function call"}

        return {
            "reasoning": reasoning.strip(),
            "function_call": func_name,
            "arguments": args,
            "result": result
        }

    else:
        return {"reasoning": reasoning.strip(), "reply": reasoning.strip()}


@app.post("/chat")
def chat(user_input: UserMessage):
    try:
        result = ask_openai_with_function_call(user_input.message)
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("openai_model:app", host="127.0.0.1", port=8888, reload=True)