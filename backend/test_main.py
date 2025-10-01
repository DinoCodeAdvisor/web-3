import main
import pytest
import datetime
import mongomock
from fastapi.testclient import TestClient
from rpn_calculator_utils import Expression

# Set up test client
client = TestClient(main.app)

# Create mock MongoDB
mongo_client = mongomock.MongoClient()
mock_db = mongo_client.calculator
mock_calculations = mock_db.calculations
mock_steps = mock_db.calculation_steps

# Automatically patch MongoDB collections in every test
@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    monkeypatch.setattr(main, "collection_calculations", mock_calculations)
    monkeypatch.setattr(main, "collection_steps", mock_steps)

# --------------------------
# ✅ Expression Evaluation Tests (Success)
# --------------------------
@pytest.mark.parametrize("expression_str, expected_result", [
    ("1 + 2", 3),
    ("2 * 3", 6),
    ("(1 + 2) * 3", 9),
    ("10 / 2", 5),
    ("3 + 4 * 2", 11),
    ("100 - (50 + 25)", 25),
])
def test_evaluate_expression_param(expression_str, expected_result):
    # Clean DB
    mock_calculations.delete_many({})
    mock_steps.delete_many({})

    response = client.post("/calculator/evaluate", json={"expression": expression_str})
    assert response.status_code == 200

    result = response.json()
    assert "calculation_id" in result
    assert result["expression"] == expression_str
    assert pytest.approx(result["result"], 0.001) == expected_result

    # Check DB insertion
    saved_calc = mock_calculations.find_one({"calculation_id": result["calculation_id"]})
    assert saved_calc is not None
    assert pytest.approx(saved_calc["result"], 0.001) == expected_result


# --------------------------
# ❌ Expression Evaluation Tests (With Negative Numbers – Expected Failure)
# --------------------------
@pytest.mark.parametrize("expression_str", [
    "-3 + 5",
    "2 * -4",
    "-2 * -3",
    "-3 / -1",
    "5 + -2",
    "(0 - 3) * 2",
    "(1 + -2) * (-3)",
])
def test_evaluate_expression_negatives_fail(expression_str):
    response = client.post("/calculator/evaluate", json={"expression": expression_str})
    assert response.status_code == 400
    assert "Negative numbers are not allowed" in response.text


# --------------------------
# ✅ Calculation History Details
# --------------------------
def test_get_calculation_history_details():
    calc_id = "dummy123"
    mock_steps.insert_one({
        "calculation_id": calc_id,
        "a": 2,
        "b": 3,
        "operator": "+",
        "result": 5,
        "date": datetime.datetime.now(datetime.timezone.utc)
    })

    response = client.get(f"/calculator/history/{calc_id}/details")
    assert response.status_code == 200

    result = response.json()
    assert result["calculation_id"] == calc_id
    assert isinstance(result["steps"], list)
    assert result["steps"][0]["a"] == 2
    assert result["steps"][0]["b"] == 3
    assert result["steps"][0]["operator"] == "+"
    assert result["steps"][0]["result"] == 5


# --------------------------
# ✅ Full Calculation History
# --------------------------
def test_obtain_history():
    mock_calculations.insert_one({
        "calculation_id": "test123",
        "expression": "1 + 2",
        "result": 3,
        "date": datetime.datetime.now(datetime.timezone.utc)
    })

    response = client.get("/calculator/history")
    assert response.status_code == 200

    history = response.json()["history"]
    assert any(h["calculation_id"] == "test123" for h in history)


# --------------------------
# ✅ Latest Calculation
# --------------------------
def test_obtain_latest_calculation():
    mock_calculations.delete_many({})
    mock_steps.delete_many({})

    mock_calculations.insert_one({
        "calculation_id": "latest1",
        "expression": "9 - 5",
        "result": 4,
        "date": datetime.datetime.now(datetime.timezone.utc)
    })

    mock_steps.insert_one({
        "calculation_id": "latest1",
        "a": 9,
        "b": 5,
        "operator": "-",
        "result": 4,
        "date": datetime.datetime.now(datetime.timezone.utc)
    })

    response = client.get("/calculator/history/latest")
    assert response.status_code == 200

    data = response.json()
    assert "history" in data and "steps" in data
    assert data["history"][0]["calculation_id"] == "latest1"
    assert data["history"][0]["expression"] == "9 - 5"
    assert data["steps"][0]["result"] == 4
    assert data["steps"][0]["operator"] == "-"


# --------------------------
# ✅ Microservice Endpoints (Success)
# --------------------------
def test_add_operands():
    response = client.post("/calculator/add", json={"a": 4, "b": 5})
    assert response.status_code == 200
    assert response.json()["result"] == 9

def test_subtract_operands():
    response = client.post("/calculator/subtract", json={"a": 9, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 6

def test_multiply_operands():
    response = client.post("/calculator/multiply", json={"a": 2, "b": 5})
    assert response.status_code == 200
    assert response.json()["result"] == 10

def test_divide_operands():
    response = client.post("/calculator/divide", json={"a": 10, "b": 2})
    assert response.status_code == 200
    assert response.json()["result"] == 5.0


# --------------------------
# ❌ Microservice Error Tests
# --------------------------
def test_add_negatives_fail():
    response = client.post("/calculator/add", json={"a": -1, "b": 2})
    assert response.status_code == 400
    assert "Negative numbers are not allowed" in response.text

def test_subtract_negatives_fail():
    response = client.post("/calculator/subtract", json={"a": 5, "b": -2})
    assert response.status_code == 400
    assert "Negative numbers are not allowed" in response.text

def test_multiply_negatives_fail():
    response = client.post("/calculator/multiply", json={"a": -2, "b": -3})
    assert response.status_code == 400
    assert "Negative numbers are not allowed" in response.text

def test_divide_by_zero_fail():
    response = client.post("/calculator/divide", json={"a": 10, "b": 0})
    assert response.status_code == 400
    assert "Division by zero" in response.text

def test_divide_negatives_fail():
    response = client.post("/calculator/divide", json={"a": -10, "b": 2})
    assert response.status_code == 400
    assert "Negative numbers are not allowed" in response.text
