import uuid
import datetime
from fastapi import FastAPI, HTTPException, Body
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from rpn_calculator_utils import transform_to_rpn, evaluate_rpn_async, Expression
from httpx import HTTPStatusError

# New Imports
import os
import sys
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

# -------------------------
# Logger Setup
# -------------------------
logger = logging.getLogger("custom_logger")
logging_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(logging_level)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logger.level)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s - %(message)s")
console_handler.setFormatter(formatter)

loki_handler = LokiLoggerHandler(
    url="http://loki:3100/loki/api/v1/push",
    labels={"application": "FastApi"},
    label_keys={},
    timeout=10,
)

logger.addHandler(console_handler)
logger.addHandler(loki_handler)
logger.info("Logger initialized")

# -------------------------
# FastAPI App Setup
# -------------------------
app = FastAPI(title="Calculator Service", description="A microservice calculator with RPN and MongoDB logging.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# -------------------------
# Prometheus Setup
# -------------------------
Instrumentator().instrument(app).expose(app)
logger.info("Prometheus app instrumentator configured")


# -------------------------
# MongoDB Setup
# -------------------------
try:
    client = MongoClient("mongodb://admin_user:web3@mongo:27017/")
    database = client.calculator
    collection_calculations = database.calculations
    collection_steps = database.calculation_steps
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise e


# -------------------------
# Helper Logging Function
# -------------------------
def log_step(a: float, b: float, operator: str, result: float, calculation_id: str):
    """
    Stores the details of a single RPN evaluation step.

    Parameters:
        a (float): Operand A
        b (float): Operand B
        operator (str): Mathematical operator applied
        result (float): Result of the operation
        calculation_id (str): Unique calculation identifier
    """
    logger.debug(f"Logging calculation step: {a} {operator} {b} = {result}")

    document = {
        "calculation_id": calculation_id,
        "a": a,
        "b": b,
        "operator": operator,
        "result": result,
        "date": datetime.datetime.now(datetime.timezone.utc)
    }

    collection_steps.insert_one(document)
    logger.debug("Step inserted into MongoDB")


# -------------------------
# API ENDPOINTS
# -------------------------

@app.post("/calculator/evaluate")
async def evaluate_expression(expression: Expression):
    """
    Evaluates a mathematical expression using RPN and logs
    the calculation and each step into MongoDB.

    Parameters:
        expression (Expression): Input expression object containing a string.

    Returns:
        dict: calculation_id, input expression, and final result
    """
    logger.info(f"Received new expression for evaluation: {expression.expression}")

    try:
        rpn = transform_to_rpn(expression.expression)
        logger.debug(f"Expression transformed to RPN: {rpn}")

        calculation_id = str(uuid.uuid4())
        logger.debug(f"Generated calculation ID: {calculation_id}")

        result = await evaluate_rpn_async(
            rpn,
            log_function=log_step,
            calculation_id=calculation_id
        )

        logger.info(f"Expression evaluated successfully: result={result}")

        document = {
            "calculation_id": calculation_id,
            "expression": expression.expression,
            "result": result,
            "date": datetime.datetime.now(datetime.timezone.utc)
        }

        collection_calculations.insert_one(document)
        logger.debug("Final calculation saved to MongoDB")

        return {
            "calculation_id": calculation_id,
            "expression": expression.expression,
            "result": result,
        }

    except ZeroDivisionError as e:
        logger.warning(f"ZeroDivisionError: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        logger.warning(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid operation: {str(e)}")

    except HTTPStatusError as e:
        logger.error(f"HTTPStatusError from microservice: {e}")
        if e.response.status_code == 400:
            raise HTTPException(status_code=400, detail=f"Invalid operation: {e.response.text}")
        else:
            raise HTTPException(status_code=500, detail="Internal microservice error.")

    except Exception as e:
        logger.exception(f"Unexpected server error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.get("/calculator/history/{calculation_id}/details")
def get_calculation_history_details(calculation_id: str):
    """
    Retrieves all step-by-step operations for a specific calculation ID.
    """
    logger.info(f"Fetching detailed history for calculation_id={calculation_id}")

    records = collection_steps.find({"calculation_id": calculation_id}).sort("date", 1)

    steps = [
        {
            "a": record.get("a"),
            "b": record.get("b"),
            "operator": record.get("operator"),
            "result": record.get("result"),
            "date": record.get("date"),
        }
        for record in records
    ]

    return {"calculation_id": calculation_id, "steps": steps}


@app.get("/calculator/history")
def obtain_history(
    operation_types: str = None,
    start_date: str = None,
    end_date: str = None,
    sort_by: str = "date",
    sort_order: str = "desc",
):
    """
    Retrieves calculation history with optional filtering.

    Filters:
        - operation_types: comma-separated operator types (sum, sub, mul, div)
        - start_date / end_date: ISO date filters
        - sort_by: 'date' or 'result'
        - sort_order: 'asc' or 'desc'
    """
    logger.info("Fetching calculation history with filters")

    query = {}

    # Operator filtering
    if operation_types:
        mapping = {"sum": r"\+", "sub": r"-", "mul": r"\*", "div": r"/"}
        regex = "|".join([mapping.get(op, "") for op in operation_types.split(",") if mapping.get(op)])
        if regex:
            query["expression"] = {"$regex": regex}
            logger.debug(f"Filtering by operations: {regex}")

    # Date range filtering
    if start_date:
        try:
            start = datetime.datetime.fromisoformat(start_date)
            query["date"] = {"$gte": start}
        except ValueError:
            logger.warning("Invalid start_date format")
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end = datetime.datetime.fromisoformat(end_date)
            query.setdefault("date", {})["$lte"] = end
        except ValueError:
            logger.warning("Invalid end_date format")
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    sort_field = "date" if sort_by == "date" else "result"
    sort_value = 1 if sort_order == "asc" else -1

    records = collection_calculations.find(query).sort(sort_field, sort_value)

    history = [
        {
            "calculation_id": record.get("calculation_id"),
            "expression": record.get("expression"),
            "result": record.get("result"),
            "date": record.get("date"),
        }
        for record in records
    ]

    return {"history": history}


@app.get("/calculator/history/latest")
def obtain_latest_calculation():
    """
    Retrieves the most recent calculation and its step-by-step breakdown.
    """
    logger.info("Fetching latest calculation")

    records = collection_calculations.find().sort("date", -1).limit(1)
    
    history = [{**record, "_id": str(record["_id"])} for record in records]

    if not history:
        logger.warning("No history available")
        return {"history": [], "steps": []}

    calc_id = history[0]["calculation_id"]

    steps = [
        {
            "a": record.get("a"),
            "b": record.get("b"),
            "operator": record.get("operator"),
            "result": record.get("result"),
            "date": record.get("date"),
        }
        for record in collection_steps.find({"calculation_id": calc_id}).sort("date", 1)
    ]

    return {"history": history, "steps": steps}


# -------------------------
# Microservice Arithmetic Endpoints
# -------------------------

@app.post("/calculator/add")
def add_operands(a: float = Body(...), b: float = Body(...)):
    """Adds two operands. No negatives allowed."""
    logger.debug(f"Add request: {a} + {b}")
    if a < 0 or b < 0:
        logger.warning("Negative numbers rejected for addition")
        raise HTTPException(status_code=400, detail="Negative numbers are not allowed")
    return {"result": a + b}


@app.post("/calculator/subtract")
def subtract_operands(a: float = Body(...), b: float = Body(...)):
    """Subtracts two operands. No negatives allowed."""
    logger.debug(f"Subtract request: {a} - {b}")
    if a < 0 or b < 0:
        logger.warning("Negative numbers rejected for subtraction")
        raise HTTPException(status_code=400, detail="Negative numbers are not allowed")
    return {"result": a - b}


@app.post("/calculator/multiply")
def multiply_operands(a: float = Body(...), b: float = Body(...)):
    """Multiplies two operands. No negatives allowed."""
    logger.debug(f"Multiply request: {a} * {b}")
    if a < 0 or b < 0:
        logger.warning("Negative numbers rejected for multiplication")
        raise HTTPException(status_code=400, detail="Negative numbers are not allowed")
    return {"result": a * b}


@app.post("/calculator/divide")
def divide_operands(a: float = Body(...), b: float = Body(...)):
    """Divides two operands. No negatives allowed. Zero division protected."""
    logger.debug(f"Divide request: {a} / {b}")
    if a < 0 or b < 0:
        logger.warning("Negative numbers rejected for division")
        raise HTTPException(status_code=400, detail="Negative numbers are not allowed")
    if b == 0:
        logger.warning("Attempted division by zero")
        raise HTTPException(status_code=400, detail="Division by zero")
    return {"result": a / b}
