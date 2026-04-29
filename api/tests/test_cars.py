import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE = {
    "brand": "BMW",
    "model": "X5",
    "price": 5_600_000,
    "year": 2020,
    "mileage": 45_000,
    "fuel": "Дизель",
    "transmission": "АКПП",
    "vin": "WBAFE41070LN12345",
    "location": "Москва",
}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_list_car(client):
    r = client.post("/api/cars", json=SAMPLE)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["brand"] == "BMW"
    assert body["id"] > 0

    r = client.get("/api/cars")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_duplicate_vin_returns_409(client):
    client.post("/api/cars", json=SAMPLE)
    r = client.post("/api/cars", json=SAMPLE)
    assert r.status_code == 409


def test_bulk_dedup_by_vin(client):
    other = {**SAMPLE, "vin": "OTHER000000000001", "model": "M3"}
    r = client.post("/api/cars/bulk", json=[SAMPLE, SAMPLE, other])
    assert r.status_code == 200
    body = r.json()
    assert body["created"] == 2
    assert body["skipped_duplicates"] == 1


def test_filters(client):
    car_a = {**SAMPLE, "vin": "AAA00000000000001", "price": 1_000_000, "year": 2018}
    car_b = {**SAMPLE, "vin": "BBB00000000000001", "price": 3_000_000, "year": 2022, "brand": "Audi"}
    client.post("/api/cars/bulk", json=[car_a, car_b])

    r = client.get("/api/cars", params={"brand": "Audi"})
    assert len(r.json()) == 1

    r = client.get("/api/cars", params={"max_price": 1_500_000})
    assert len(r.json()) == 1

    r = client.get("/api/cars", params={"min_year": 2020})
    assert len(r.json()) == 1


def test_create_car_without_fuel_and_transmission(client):
    """Real-world inventory exports often don't have fuel/transmission columns."""
    minimal = {
        "brand": "BMW",
        "model": "X5",
        "price": 5_600_000,
        "year": 2020,
        "mileage": 45_000,
        "vin": "MINIMAL000000001",
    }
    r = client.post("/api/cars", json=minimal)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["fuel"] is None
    assert body["transmission"] is None
