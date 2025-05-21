from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import sqlite3
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import uvicorn
from models.OrderRequest import OrderRequest
from models.UserMessage import UserMessage
import random
from datetime import datetime, timedelta

app = FastAPI()

tokenizer = None
model = None

# Load model on startup
@app.on_event("startup")
def load_phi_model_and_prepare_db():
    global tokenizer, model
    print("Loading Phi-1_5 model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-1_5")
    model = AutoModelForCausalLM.from_pretrained("microsoft/phi-1_5")
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    print("Model loaded successfully.")

    if torch.cuda.is_available():
        model = model.cuda()

    # Init DB
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


def generate_response(prompt: str) -> str:
    global tokenizer, model
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)



@app.post("/chat")
def chat(user_input: UserMessage):
    prompt = f"""You are a helpful customer support assistant. 
    Your job is to respond to user queries about order tracking and order cancellation. 
    You should follow company policy: Orders can only be cancelled if they were placed less than 10 days ago.

    You have access to the following functions:
    - track_order(order_id)
    - cancel_order(order_id)

    When answering, explain your reasoning before deciding which action to take. Then finish with a response to the user.

    User: {user_input.message}
    Assistant:
"""
    reply = generate_response(prompt)
    return {"reply": reply}


# For local debugging
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8888, reload=True)