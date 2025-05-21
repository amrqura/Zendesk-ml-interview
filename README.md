# Zendesk-ml-interview
This is my Zendesk interview repo for ML engineering 
I have tried two different models:
* closed source: `chatgpt-4`
* open source model: `phi 1.5` 

If I will neeed to implement this in production system, I will prefer the open source model like LLAMA to use. the main
reason is that I will prefer to use the open source model, so we don't send senstive data like `order_id` or customer name 
in external servers like chatgpt. but because I'm using my current computer which don't have GPU, this is why I tried ligher models
like `phi 1.5`

I'm going to use an agent using `langchain` and will use function calling as a tool for the agent. when sending a prompt to 
the LLM, will instruct the LLM call either `track_order` function to track the order, or `cancel_order` to cancel the order.

you can find below the structure of my solution
```
User Input ➜ [Chatbot Engine] ➜ [LLM + Tool Router] ➜ [Tool Execution Layer: API calls] ➜ [Final Response]
```


Note: `phi-1.5` in cpu is very small model that can be loaded in CPU, but was hallucinate alot. I tried alot to stop hallucination 
but it needs more time to do so. openai integration was super smooth

## Create virtualenv end install libraries
create a python virtual envirnment using the following commands
```
virtualenv venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
``` 

## Tech stack
* LLM: Open source LLM for security reasons, or closed source like chatgpt for easy integration
* Framework: LangChain (ideal for tool use + memory + reasoning)
* APIs: Simulate with FastAPI endpoints
* Policies: Hardcoded logic, the current logic is that customer can't cancel order older than 10 days ago


## Project structure

Here is the project structure:

* `openai_model.py`: contains a code to integrate the chatbot with chatgpt and function calling tools
* `phi_model.py`: contains a code to load `phi-1.5` with prompt engineering to call function
* `phi_model2.py` contains a code to load `phi-1.5` with function call
* `test_app.py` contains a test case to test several scenarios including sending requests to track order, cancel orders and evaluate the performance of the model. since `phi` model was hallucinate a lot, the test cases in this file was against the openai integration


## API 

We have two end points:

### Cancel order 
Business logic: Only cancel if order_date < 10 days ago, here is a simple `curl` command to test calling the function.

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
Track the order, here is a simple `curl` to test it.
```
curl -X POST "http://127.0.0.1:8888/track_order" \
     -H "Content-Type: application/json" \
     -d '{"order_id": 1}'

```

### Chat with LLM
This is the main function to chat with the chatbot. I will show two examples chatting with the chatbot.

* Chatting with the chatbot asking to `cancel` an order. 
```
curl -X POST "http://127.0.0.1:8888/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Can you cancel order 1 for me?"}'

```

* Chatting with the chatbot asking to `track` an order.
```
curl -X POST "http://127.0.0.1:8888/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Can you track order 1 for me?"}'

```

## Unit test
here is the command to run the test cases. you will need define `OPENAI_API_KEY` as enviroment variable
```
export OPENAI_API_KEY='sk-...' # put your openapi key
pytest test_app.py -v
```

## Running the phi model
if you want to run phi model(it is hallucinate, but you will be able to see the reasoning), you will need to do the following steps:

```
export HUGGINGFACE_HUB_TOKEN='your_hf_token'
python3 phi_model.py
(or) python3 phi_model2.py
```

if it asks you to login into `hf`, you can execute the following commands:
```
huggingface-cli login
```
and then paste your huggingface token

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


Evaluate using 5–10 controlled test cases to confirm proper reasoning


