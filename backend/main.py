import uuid # For generating unique IDs for our calculations
import datetime
from fastapi import FastAPI, HTTPException, Body
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from rpn_calculator_utils import transform_to_rpn, evaluate_rpn_async, Expression
from httpx import HTTPStatusError

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
async def evaluate_expression(expression: Expression):
    """ Evaluates an expression and returns a result + calculation ID. """
    try:
        print(f"Received expression: {expression.expression}")

        rpn = transform_to_rpn(expression.expression)
        calculation_id = str(uuid.uuid4())

        result = await evaluate_rpn_async(rpn, log_function=log_step, calculation_id=calculation_id)

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
    except ZeroDivisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {str(e)}")
    except HTTPStatusError as e:
        # Catch microservice 400 errors
        if e.response.status_code == 400:
            # Forward the microservice 400 error message
            raise HTTPException(status_code=400, detail=f"Invalid operation: {str(e.response.text)[1:-1].replace('"', '').replace('detail:','')}")
        else:
            raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")

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
def obtain_history(
    operation_types: str = None,  # Comma-separated list of operation types
    start_date: str = None,  # Start date for date range filter
    end_date: str = None,  # End date for date range filter
    sort_by: str = "date",  # Sort by either 'date' or 'result'
    sort_order: str = "desc"  # Sort order, 'asc' or 'desc'
):
    # Build the query
    query = {}

    # Filter by operation type (Regex on expression for addition, subtraction, etc.)
    if operation_types:
        operations = operation_types.split(",")
        regex = "|".join({
            "sum": r"\+",
            "sub": r"-",
            "mul": r"\*",
            "div": r"/"
        }.get(op, "") for op in operations)
        
        if regex:
            query["expression"] = {"$regex": regex}

    # Filter by date range if start and end date are provided
    if start_date:
        try:
            start_date = datetime.datetime.fromisoformat(start_date)
            query["date"] = {"$gte": start_date}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_date = datetime.datetime.fromisoformat(end_date)
            if "date" not in query:
                query["date"] = {}
            query["date"]["$lte"] = end_date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Sorting logic based on 'sort_by' and 'sort_order'
    sort_field = "date" if sort_by == "date" else "result"
    sort_order_value = 1 if sort_order == "asc" else -1

    # Query MongoDB collection for calculations matching the filters
    records = collection_calculations.find(query).sort(sort_field, sort_order_value)

    # Construct the history list to return
    history = []
    for record in records:
        history.append({
            "calculation_id": record.get("calculation_id"),
            "expression": record.get("expression"),
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
            "expression": record.get("expression"),
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

# Microservices Endpoints
# ---> Calculator add => POST /calculator/add {a: float, b: float}
# ---> Calculator subtract => POST /calculator/substract {a: float, b: float}
# ---> Calculator multiply => POST /calculator/multiply {a: float, b: float}
# ---> Calculator divide => POST /calculator/divide {a: float, b: float}
@app.post("/calculator/add")
def add_operands(a: float = Body(...), b: float = Body(...)):
    if a < 0 or b < 0:
        raise HTTPException(status_code=400, detail=" Negative numbers are not allowed")
    return {"result": a + b}

@app.post("/calculator/subtract")
def subtract_operands(a: float = Body(...), b: float = Body(...)):
    if a < 0 or b < 0:
        raise HTTPException(status_code=400, detail=" Negative numbers are not allowed")
    return {"result": a - b}

@app.post("/calculator/multiply")
def multiply_operands(a: float = Body(...), b: float = Body(...)):
    if a < 0 or b < 0:
        raise HTTPException(status_code=400, detail=" Negative numbers are not allowed")
    return {"result": a * b}

@app.post("/calculator/divide")
def divide_operands(a: float = Body(...), b: float = Body(...)):
    if a < 0 or b < 0:
        raise HTTPException(status_code=400, detail=" Negative numbers are not allowed")
    if b == 0:
        raise HTTPException(status_code=400, detail=" Division by zero")
    return {"result": a / b}