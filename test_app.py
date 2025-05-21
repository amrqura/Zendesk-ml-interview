# test_chat_real_llm.py
import os
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from openai_model import app, init_db

client = TestClient(app)

TEST_DB = "test_orders.db"
os.environ["DB_PATH"] = TEST_DB

def setup_test_db():

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS orders")
    cur.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            order_date TEXT,
            status TEXT
        )
    """)
    cur.execute("INSERT INTO orders (customer_name, order_date, status) VALUES (?, ?, ?)",
                ("Alice", datetime.now().strftime("%Y-%m-%d"), "pending"))  # ID = 1
    conn.commit()
    conn.close()

def setup_module(module):
    setup_test_db()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    init_db()  # Ensure DB is initialized by the app

def test_chat_live_llm_track():
    response = client.post("/chat", json={"message": "Can you track order 1?"})
    assert response.status_code == 200
    print(response.json())
    assert "track_order" in response.json()["function_call"]
    assert "pending" in str(response.json()).lower()

# def test_chat_live_llm_cancel():
#     response = client.post("/chat", json={"message": "Can you cancel order 1?"})
#     assert response.status_code == 200
#     print(response.json())
#     assert "cancelled" in str(response.json()).lower()

