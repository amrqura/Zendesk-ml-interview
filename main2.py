import re
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import sqlite3
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import uvicorn
from models.OrderRequest import OrderRequest
from models.UserMessage import UserMessage
import random
from datetime import datetime, timedelta
from langchain.llms import HuggingFacePipeline
from langchain.agents import Tool, initialize_agent, AgentType

app = FastAPI()
agent = None
tools = None
from langchain.agents import AgentExecutor

agent_executor = None  # Declare at module level

@app.on_event("startup")
def load_phi_model_and_prepare_db():
    global tokenizer, model, pipe, llm, agent, tools, agent_executor

    print("Loading Phi-1_5 model and tokenizer...")
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-1_5")
    model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-1_5")

    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()
    print("Model loaded successfully.")

    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)
    llm = HuggingFacePipeline(pipeline=pipe)

    tools = [
        Tool(
            name="track_order",
            func=lambda order_id: track_order_tool(int(order_id)),
            description="Tracks the status of an order given the order_id."
        ),
        Tool(
            name="cancel_order",
            func=lambda order_id: cancel_order_tool(int(order_id)),
            description="Cancels an order given the order_id if it's within 10 days."
        )
    ]

    # agent = initialize_agent(
    #     tools,
    #     llm,
    #     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    #     verbose=True,
    #     handle_parsing_errors=True,
    #     max_iterations=1,
    # )

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=1,
        agent_kwargs={
            "prefix": (
                "You are a helpful assistant that can track and cancel orders using the tools provided.\n"
                "When given a task, decide the correct tool to use and call it with the right input.\n"
                "Always return the final result after one step."
            )
        }
    )

    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent.agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=1,
        return_intermediate_steps=True
    )

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


def generate_response_with_tool_call(prompt: str):
    global tokenizer, model,pipe, llm
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=False)
    full_reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract actual assistant response
    assistant_response = full_reply.split("Assistant:")[-1].strip()
    return assistant_response


def extract_tool_call(text):
    print("The text is {}".format(text))
    """Extracts something like track_order(1) or cancel_order(2) from LLM response"""
    match = re.search(r'(track_order|cancel_order)\((\d+)\)', text)
    if match:
        func = match.group(1)
        order_id = int(match.group(2))
        return func, order_id
    return None, None

def call_tool(func, order_id):
    if func == "track_order":
        return track_order(OrderRequest(order_id=order_id))
    elif func == "cancel_order":
        return cancel_order(OrderRequest(order_id=order_id))
    else:
        return {"error": f"Unknown function: {func}"}


# Define tool wrappers
def track_order_tool(order_id: int) -> str:
    try:
        result = track_order(OrderRequest(order_id=order_id))
        return f"Order {result['order_id']} is {result['status']} (placed on {result['order_date']})."
    except Exception as e:
        return f"Error tracking order {order_id}: {str(e)}"

def cancel_order_tool(order_id: int) -> str:
    try:
        result = cancel_order(OrderRequest(order_id=order_id))
        return result['message']
    except Exception as e:
        return f"Error canceling order {order_id}: {str(e)}"


def ask_agent(user_query: str):
    return agent.run(user_query)

# @app.post("/chat")
# def chat(user_input: UserMessage):
#     try:
#         result = ask_agent(user_input.message)
#         return {"reply": result}
#     except Exception as e:
#         return {"error": str(e)}


# Then in chat endpoint
# @app.post("/chat")
# def chat(user_input: UserMessage):
#     try:
#         result = agent_executor.run(user_input.message)
#         return {"reply": result}
#     except Exception as e:
#         return {"error": str(e)}


@app.post("/chat")
def chat(user_input: UserMessage):
    try:
        output = agent_executor.invoke({"input": user_input.message})

        final_answer = output.get("output", "")
        steps = output.get("intermediate_steps", [])

        return {
            "reply": final_answer,
            "intermediate_steps": [
                {
                    "tool": step[0].tool,
                    "tool_input": step[0].tool_input,
                    "observation": step[1]
                }
                for step in steps
            ]
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("main2:app", host="127.0.0.1", port=8888, reload=True)