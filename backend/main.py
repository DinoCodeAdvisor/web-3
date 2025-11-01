import datetime
import logging
import os
from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

# Set up logging
logger = logging.getLogger("custom_logger")
logging_data = os.getenv("LOG_LEVEL", "INFO").upper()

if logging_data == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif logging_data == "INFO":
    logger.setLevel(logging.INFO)

# Create an instance of the custom handler
custom_handler = LokiLoggerHandler(
    url="http://loki:3100/loki/api/v1/push",
    labels={"application": "FastApi"},
    label_keys={},
    timeout=10,
)

logger.addHandler(custom_handler)
logger.info("Logger initialized")

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
database = client.practica1
collection_historial = database.historial

@app.get("/calculator/sum")
def sum_numbers(a: float, b: float):
    result = a + b

    document = {
        "a": a,
        "b": b,
        "result": result,
        "date": datetime.datetime.now(tz=datetime.timezone.utc)
    }

    collection_historial.insert_one(document)

    logger.info(f"Operación suma exitoso")
    logger.debug(f"Operación suma: a={a}, b={b}, result={result}")

    return {"a": a, "b": b, "result": result}

@app.get("/calculator/divide")
def divide_numbers(a: float, b: float):

    if b == 0:
        return {"error": "No se puede dividir entre cero."}
    
    if a < 0:
        return {"error": "No se puede dividir entre numeros negativos."}
    
    result = a / b

    document = {
        "result": result,
        "a": a,
        "b": b,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }

    # collection_historial.insert_one(document)

    logger.info(f"Operación dividir exitoso")
    logger.debug(f"Operación dividir: a={a}, b={b}, result={result}")

    return {"a": a, "b": b, "result": result}

@app.get("/calculator/history")
def obtain_history():
    records = collection_historial.find().sort("date", -1).limit(10)

    history = []
    for record in records:
        history.append({
            "a": record.get("a"),
            "b": record.get("b"),
            "result": record.get("result"),
            "date": record["date"] if "date" in record else None
        })    
    
    logger.info(f"Retrieved history")

    return {"history": history}

Instrumentator().instrument(app).expose(app)