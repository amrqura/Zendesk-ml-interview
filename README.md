# Zendesk-ml-interview
This is my Zendesk interview repo for ML engineering 
```
User Input ➜ [Chatbot Engine] ➜ [LLM + Tool Router] ➜ [Tool Execution Layer: API calls] ➜ [Final Response]
```

## Tech stack
* LLM: Open source LLM for security reasons
* Framework: LangChain (ideal for tool use + memory + reasoning)
* APIs: Simulate with FastAPI endpoints (you define their logic)
* Policies: Hardcoded logic, passed as context or few-shot examples
* Frontend: Streamlit

# Downloading the model offline
In order to download the mistralai model into your computer, you can execute the following commands:
```
huggingface-cli login
huggingface-cli download mistralai/Mistral-7B-Instruct-v0.2 --local-dir ./models/mistral --local-dir-use-symlinks False

```

## API 

We have two end points:

### Cancel order 
Business logic: Only cancel if order_date < 10 days ago

```
curl -X 'POST' \
 'http://127.0.0.1:8888/cancel_order' \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{
  "order_id": "1"
}'
```

### Order tracking 

```
curl -X POST "http://127.0.0.1:8888/track_order" \
     -H "Content-Type: application/json" \
     -d '{"order_id": 1}'

```

### Chat with LLM
* here is an example for sending a request to LLM to cancel an order
```
curl -X POST "http://127.0.0.1:8888/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Can you cancel order 1 for me?"}'

```

* here is an example for sending a request to LLM to track an order
```
curl -X POST "http://127.0.0.1:8888/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Can you track order 1 for me?"}'

```

# LLM Prompting and Tool Use
Define tools (OrderCancellation, OrderTracking)
* Prompt the LLM with policies in system prompt or examples
* Let it invoke tools and reason step-by-step

Example System Prompt:
"You are a helpful support agent. Only allow order cancellations if the order was placed less than 10 days ago. Use tools to track or cancel orders."


# Experiment Design
Design test cases to evaluate chatbot behavior:

### Functional Tests
* Test valid cancellation (e.g., 5-day-old order)
* Test invalid cancellation (e.g., 20-day-old order)
* Test tracking requests

### Metrics
* Accuracy of policy enforcement
* Correctness of tool execution
* Latency of response
* Step-tracing: Whether reasoning steps are followed correctly

### Qualitative Evaluation
* Is the tone polite?
* Are error cases handled gracefully?
* Does the bot explain policy reasons well?

### Additional points:

* Add streaming response or retrieval-based memory
* Use function calling with OpenAI or tool-agent loop with open models
* Add unit tests and evaluation reports
* Include policy updates dynamically (e.g., from a JSON config)



Mistral: This open-source model has demonstrated function-calling capabilities, allowing developers to define custom functions that the model can invoke during inference.

Evaluate using 5–10 controlled test cases to confirm proper reasoning


LLM mdoels:

* Phi-2	
* TinyLlama
* Gemma 2B	
* Mistral 7B (will be slow in CPU)

## Create virtualenv end install libraries
```
virtualenv venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
``` 

## Huggingface login
To login to huggingface and start using iy, execute the following command:
```
huggingface-cli login
```
and then paste your huggingface token 