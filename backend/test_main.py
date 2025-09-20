import pytest
import mongomock
from fastapi.testclient import TestClient
import main  # important: we need to patch main.collection_historial

client = TestClient(main.app)

# Create mock DB and collection
mongo_client = mongomock.MongoClient()
database = mongo_client.practica1
mock_collection = database.historial


@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (2.5, 2.5, 5.0),
    (1e10, 1e10, 2e10)
])
def test_sum_numbers(monkeypatch, a, b, expected):
    # 🔹 Patch the collection that main.py uses
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    # Clean before test
    mock_collection.delete_many({})

    response = client.get(f"/calculator/sum?a={a}&b={b}")
    
    # ✅ Assert response correctness
    assert response.status_code == 200
    assert response.json() == {"a": a, "b": b, "result": expected}
    
    # ✅ Assert that the record was inserted into mongomock
    saved = mock_collection.find_one({"a": a, "b": b})
    assert saved is not None
    assert saved["result"] == expected

import datetime
import pytest
import mongomock
from fastapi.testclient import TestClient
import main  # important: we need to patch main.collection_historial

client = TestClient(main.app)

# Create mock DB and collection
mongo_client = mongomock.MongoClient()
database = mongo_client.practica1
mock_collection = database.historial


@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (2.5, 2.5, 5.0),
    (1e10, 1e10, 2e10)
])
def test_sum_numbers(monkeypatch, a, b, expected):
    # Patch the collection that main.py uses
    monkeypatch.setattr(main, "collection_historial", mock_collection)

    # Clean before test
    mock_collection.delete_many({})

    response = client.get(f"/calculator/sum?a={a}&b={b}")
    
    # Assert response correctness
    assert response.status_code == 200
    assert response.json() == {"a": a, "b": b, "result": expected}
    
    # Assert that the record was inserted into mongomock
    saved = mock_collection.find_one({"a": a, "b": b})
    assert saved is not None
    assert saved["result"] == expected


def test_obtain_history(monkeypatch):
    # Patch the collection that main.py uses
    monkeypatch.setattr(main, "collection_historial", mock_collection)
    
    response = client.get("/calculator/history")
    assert response.status_code == 200
    
    history = response.json().get("history", [])
    mock_collection_data = list(mock_collection.find({}))

    expected_data = []
    for record in history:
        expected_data.append({
            "a": record.get("a"),
            "b": record.get("b"),
            "result": record.get("result"),
            "date": record["date"] if "date" in record else None
        })

    print(f"DEBUG: expected_data: {expected_data}")
    print(f"DEBUG: history: {history}")

    # Assert that history matches expected data
    assert history == expected_data
