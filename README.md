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
* Framework: LangChain 
* APIs: Simulate with FastAPI endpoints
* Policies: Hardcoded logic, the current logic is that customer can't cancel order older than 10 days ago


## Project structure

Here is the project structure:

* `openai_model.py`: contains a code to integrate the chatbot with chatgpt and function calling tools
* `phi_model.py`: contains a code to load `phi-1.5` with prompt engineering to call function
* `phi_model2.py` contains a code to load `phi-1.5` with function call
* `test_app.py` contains the experiment  test cases to test several scenarios including sending requests to track order, cancel orders and evaluate the performance of the model. since `phi` model was hallucinate a lot, the test cases in this file was against the openai integration


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
The response will be something like:

```
{"reasoning":"I will now check the status of your order with ID 5 to see what might be causing the delay. Please hold on for a moment while I retrieve the information.","function_call":"track_order","arguments":{"order_id":5},"result":{"order_id":5,"status":"shipped","order_date":"2025-05-16"}}
```
* Chatting with the chatbot asking to `track` an order.
```
curl -X POST "http://127.0.0.1:8888/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "I have an order that i am waiting since long time, Can you track order 5 for me?"}'


```

The response will be something like this:

```
{"reasoning":"I will check the status of order number 5 for you to give you an update on its progress. Let's see where it stands now.","function_call":"track_order","arguments":{"order_id":5},"result":{"order_id":5,"status":"cancelled","order_date":"2025-05-05"}}
```

## Unit test
here is the command to run the test cases. you will need define `OPENAI_API_KEY` as enviroment variable
```
export OPENAI_API_KEY='sk-...' # put your openapi key
pytest test_app.py -v -s
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

* `test_app.py` is the test cases that handles testing quantitative and/or qualitative metrics 
here are the metrics that we will test

### Metrics
* Accuracy of policy enforcement (test case for invalid cancellation)
* Correctness of tool execution
* Latency of response
* Step-tracing: Whether reasoning steps are followed correctly

### Qualitative Evaluation
* Is the tone polite?
* Are error cases handled gracefully?
* Does the bot explain policy reasons well?

# Key Insights
## Chatbot Effectiveness
* Successfully routes intent to correct backend logic (track_order, cancel_order)
* Handles edge cases such as expired orders with proper messaging
* Responds with correct status and helpful explanations

## Performance
* All test cases complete in under 1 minute, with real LLM interaction
* Latency remains stable across multiple query types
## Politeness
* GPT-4 confirms that chatbot responses are polite and user-friendly
* Response tone aligns with a professional assistant persona
## multi-step  handling
* The system failed at the moment to handle multi steps like "track -> cancel". so when I use this curl:
```
curl -X POST "http://127.0.0.1:8888/chat"      -H "Content-Type: application/json"      -d '{"message": "Can you check the status of order 1 and cancel it if possible?"}
```
It only shows to me the `track_order` function is called:
```
{"reasoning":"First, I'll check the status of order 1 to understand its current status. This will help us determine if it's possible to cancel the order. Let me do that now.","function_call":"track_order","arguments":{"order_id":1},"result":{"order_id":1,"status":"pending","order_date":"2025-05-10"}}
```




