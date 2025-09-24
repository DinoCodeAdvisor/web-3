import uuid # For generating unique IDs for our calculations
import datetime
from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from rpn_calculator_utils import transform_to_rpn, evaluate_rpn, Expression

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use service name + credentials from docker-compose
client = MongoClient("mongodb://admin_user:web3@mongo:27017/")
database = client.calculator # Main database
collection_calculations = database.calculations # One per full expression (ex. "3 + 5 * 2 (8 - 3)")
collection_steps = database.calculation_steps # One per step in a calculation (ex. "3 + 5")

# Logging function
def log_step(a: float, b: float, operator: str, result: float, calculation_id: str):
    """ Inserts an operation log into MongoDB """
    document = {
        "calculation_id": calculation_id,
        "a": a,
        "b": b,
        "operator": operator,
        "result": result,
        "date": datetime.datetime.now(tz=datetime.timezone.utc)
    }

    collection_steps.insert_one(document)

# API Endpoints
# ---> Calculator Evaluate => POST /calculator/evaluate {expression: str}
# ---> Calculator History for a certain calculation => GET /calculator/history/{calculation_id}
# ---> Calculator Full History => GET /calculator/history

@app.post("/calculator/evaluate")
def evaluate_expression(expression: Expression):
    """ Evaluates an expression and returns a result + calculation ID. """
    try: 
        rpn = transform_to_rpn(expression.expression)
        calculation_id = str(uuid.uuid4())
        result = evaluate_rpn(rpn, log_function=log_step, calculation_id=calculation_id)

        document = {
            "calculation_id": calculation_id,
            "expression": expression.expression,
            "result": result,
            "date": datetime.datetime.now(tz=datetime.timezone.utc)
        }
        
        collection_calculations.insert_one(document)

        return {
            "calculation_id": calculation_id,
            "expression": expression.expression,
            "result": result,
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/calculator/history/{calculation_id}/details")
def get_calculation_history_details(calculation_id: str):
    """ Retrieves the history of steps for a given calculation ID """
    records = collection_steps.find({"calculation_id": calculation_id}).sort("date", 1)

    steps = []
    for record in records:
        steps.append({
            "a": record.get("a"),
            "b": record.get("b"),
            "operator": record.get("operator"),
            "result": record.get("result"),
            "date": record.get("date")
        })

    return {
        "calculation_id": calculation_id,
        "steps": steps
    }

@app.get("/calculator/history")
def obtain_history():
    records = collection_calculations.find().sort("date", -1)

    history = []
    for record in records:
        history.append({
            "calculation_id": record.get("calculation_id"),
            "result": record.get("result"),
            "date": record["date"] if "date" in record else None
        })

    return {"history": history}


@app.get("/calculator/history/latest")
def obtain_latest_calculation():
    records = collection_calculations.find().sort("date", -1).limit(1)

    history = []
    steps = []
    for record in records:
        history.append({
            "calculation_id": record.get("calculation_id"),
            "result": record.get("result"),
            "date": record["date"] if "date" in record else None
        })
    
    step_records = collection_steps.find({"calculation_id": history[0]["calculation_id"]}).sort("date", 1)
    for record in step_records:
        steps.append({
            "a": record.get("a"),
            "b": record.get("b"),
            "operator": record.get("operator"),
            "result": record.get("result"),
            "date": record.get("date") if "date" in record else None
        })

    return {"history": history, "steps": steps}