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

# Parametrized test for multiple expressions including negatives
@pytest.mark.parametrize("expression_str, expected_result", [
    # Basic expressions
    ("1 + 2", 3),
    ("2 * 3", 6),
    ("(1 + 2) * 3", 9),
    ("10 / 2", 5),
    ("3 + 4 * 2", 11),
    ("100 - (50 + 25)", 25),

    # Negative numbers
    ("-3 + 5", 2),
    ("2 * -4", -8),
    ("-2 * -3", 6),
    ("-3 / -1", 3),
    ("5 + -2", 3),
    ("(0 - 3) * 2", -6), 

    # Complex with nested parentheses and negatives
    ("(1 + -2) * (-3)", 3),
])
def test_evaluate_expression_param(expression_str, expected_result):
    # Clean database before test
    mock_calculations.delete_many({})
    mock_steps.delete_many({})

    # Call API
    response = client.post("/calculator/evaluate", json={"expression": expression_str})
    assert response.status_code == 200

    result = response.json()
    assert "calculation_id" in result
    assert result["expression"] == expression_str
    assert pytest.approx(result["result"], 0.001) == expected_result

    # Verify calculation saved in DB
    saved_calc = mock_calculations.find_one({"calculation_id": result["calculation_id"]})
    assert saved_calc is not None
    assert pytest.approx(saved_calc["result"], 0.001) == expected_result


# Test detailed steps of a known calculation
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


# Test full calculation history list
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


# Test latest calculation
def test_obtain_latest_calculation():
    mock_calculations.delete_many({})
    mock_steps.delete_many({})

    # Insert dummy latest calculation
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
