# test_chat_real_llm.py
import os
import sqlite3
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time

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

# quantitative evaluation

def test_chat_live_llm_track():
    """
    Test that the chatbot will call track_order function
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you track order 1?"})
    assert response.status_code == 200
    assert "track_order" in response.json()["function_call"]
    assert "pending" == response.json()["result"]["status"].lower()


def test_chat_live_llm_track_shipped():
    """
    Test that the chatbot will call track_order function
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you track order 2?"})
    assert response.status_code == 200
    assert "track_order" in response.json()["function_call"]
    assert "shipped" == response.json()["result"]["status"].lower()


def test_chat_live_llm_cancel_invalid():
    """
    Test that the chatbot will call cancel_order function and that failed will be in status
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you cancel order 2?"})
    assert response.status_code == 200
    assert "cancel_order" in response.json()["function_call"]
    assert "failed" == response.json()["result"]["status"].lower()


def test_chat_live_llm_cancel_valid():
    """
    Test that the chatbot will call cancel_order function and that success will be in status
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you cancel order 1?"})
    assert response.status_code == 200
    assert "cancel_order" in response.json()["function_call"]
    assert "success" == response.json()["result"]["status"].lower()


# qualitative evaluation
def score_politeness(text: str) -> bool:
    """
    call another LLM with the response and make sure it is polite enough
    :param text:
    :return:
    """
    prompt = f"""Rate the following response for politeness on a scale from 1 (rude) to 5 (very polite). Return only the number.

    Response:
    {text}
    """
    from openai import OpenAI

    client2 = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    result = client2.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    score = int(result.choices[0].message.content.strip())
    return score >= 4


def test_chat_response_is_polite():
    """
    This test to make sure that the response that is returning from the chatbot is polite
    in order to make sure that is polite enough, We will send the response to another LLM
    and make sure that the score of politness is high
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you track order 1?"})
    assert response.status_code == 200
    reasoning = response.json().get("reasoning", "").lower()
    assert score_politeness(reasoning), "Response not polite enough"


def test_chat_execution_time_under_1_minute():
    """
    Make sure that the chatbot respond within one minute
    :return:
    """
    client = TestClient(app)
    start_time = time.time()

    response = client.post("/chat", json={"message": "Can you cancel order 1?"})

    end_time = time.time()
    duration = end_time - start_time

    print(f"Execution time: {duration:.2f} seconds")

    assert response.status_code == 200
    assert duration < 60, "Chat response took longer than 1 minute"


def test_chat_live_llm_cancel_invalid_with_proper_reasoning():
    """
    Test that the chatbot will call cancel_order function ,failed will be in status and there is clear message
    :return:
    """
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Can you cancel order 2?"})
    assert response.status_code == 200
    assert "cancel_order" in response.json()["function_call"]
    assert "failed" == response.json()["result"]["status"].lower()
    assert "cancellation window" in response.json()["result"]["message"].lower()