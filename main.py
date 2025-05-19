from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import uvicorn

app = FastAPI()

# Load Phi-2 model (CPU-based)
# import os
# os.environ["HUGGINGFACE_HUB_TOKEN"] =''
# from huggingface_hub import whoami
# print(whoami())

# from huggingface_hub import HfApi
# api = HfApi()
# api.model_info("microsoft/phi-2")

# tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")
# tokenizer.add_special_tokens({'pad_token': '[PAD]'})
# model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2")
# model.resize_token_embeddings(len(tokenizer))


from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "microsoft/phi-1_5"  # Open-access
HUGGINGFACE_TOKEN = "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"
tokenizer = AutoTokenizer.from_pretrained(model_id, token=HUGGINGFACE_TOKEN, force_download=True)
model = AutoModelForCausalLM.from_pretrained(model_id, token=HUGGINGFACE_TOKEN, force_download=True)


HUGGINGFACE_TOKEN = "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"

model_id = "microsoft/phi-2"

tokenizer = AutoTokenizer.from_pretrained(model_id, token=HUGGINGFACE_TOKEN)
model = AutoModelForCausalLM.from_pretrained(model_id, token=HUGGINGFACE_TOKEN)


from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "microsoft/phi-2"

tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=True)
model = AutoModelForCausalLM.from_pretrained(model_id, use_auth_token=True)




model.eval()

if torch.cuda.is_available():
    model = model.cuda()

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
    conn.commit()
    conn.close()

init_db()

# Request model
class UserMessage(BaseModel):
    message: str

# Order simulation
@app.post("/track_order")
def track_order(order_id: int):
    conn = sqlite3.connect("orders.db")
    cur = conn.cursor()
    cur.execute("SELECT id, order_date, status FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"order_id": row[0], "status": row[2], "order_date": row[1]}
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/cancel_order")
def cancel_order(order_id: int):
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

# Helper: Generate model output
def generate_response(prompt: str) -> str:
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Main chatbot entry point
@app.post("/chat")
def chat(user_input: UserMessage):
    prompt = f"""
You are an assistant that helps with order tracking and cancellation. 
Company Policy: Orders can only be cancelled if they were placed less than 10 days ago.
Available functions: track_order(order_id), cancel_order(order_id)

User: {user_input.message}
Assistant:
"""
    reply = generate_response(prompt)
    return {"reply": reply}


# For local debugging
if __name__ == "__main__":
    uvicorn.run("serving-intermediate-models:app", host="127.0.0.1", port=8000, reload=True)