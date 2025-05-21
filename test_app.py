# test_chat_real_llm.py
import os
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

os.environ["DB_PATH"] = "test_orders.db"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

from openai_model import app


TEST_DB = "test_orders.db"

def setup_test_db():
    conn = sqlite3.connect(os.environ["DB_PATH"])
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

    # Order 2: old (cannot be cancelled)
    old_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    cur.execute("INSERT INTO orders (customer_name, order_date, status) VALUES (?, ?, ?)",
                ("Bob", old_date, "shipped"))  # ID = 2

    conn.commit()
    conn.close()


def setup_module(module):
    setup_test_db()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def test_chat_live_llm_track():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you track order 1?"})
    assert response.status_code == 200
    assert "track_order" in response.json()["function_call"]
    assert "pending" == response.json()["result"]["status"].lower()


def test_chat_live_llm_track_shipped():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you track order 2?"})
    assert response.status_code == 200
    assert "track_order" in response.json()["function_call"]
    assert "shipped" == response.json()["result"]["status"].lower()


def test_chat_live_llm_cancel_invalid():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you cancel order 2?"})
    assert response.status_code == 200
    assert "cancel_order" in response.json()["function_call"]
    assert "failed" == response.json()["result"]["status"].lower()


def test_chat_live_llm_cancel_valid():
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you cancel order 1?"})
    assert response.status_code == 200
    assert "cancel_order" in response.json()["function_call"]
    assert "success" == response.json()["result"]["status"].lower()



