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

## API 

We have two end points:

### Cancel order 
Business logic: Only cancel if order_date < 10 days ago

```
curl -X 'POST' \
 'http://127.0.0.1:8000/cancel_order' \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{
  "order_id": "12345",
  "order_date": "2024-04-01"
}'
```

### Order tracking 

```
curl -X 'GET' \
 'http://127.0.0.1:8000/track_order?order_id=12345'
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