import sys
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parser import parse_excel  # noqa: E402


def _build_xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_with_header():
    data = _build_xlsx([
        ["brand", "model", "price", "year", "mileage", "fuel", "transmission", "vin", "location"],
        ["BMW", "X5", 5600000, 2020, 45000, "Дизель", "АКПП", "VIN0000000000001", "Москва"],
        ["Audi", "A6", 3200000, 2018, 82000, "Бензин", "Робот", "VIN0000000000002", None],
    ])
    result = parse_excel(data)
    assert result.errors == []
    assert len(result.cars) == 2
    assert result.cars[0].brand == "BMW"
    assert result.cars[0].location == "Москва"
    assert result.cars[1].location is None


def test_parse_without_header():
    data = _build_xlsx([
        ["BMW", "X5", 5600000, 2020, 45000, "Дизель", "АКПП", "VIN0000000000001", "Москва"],
    ])
    result = parse_excel(data)
    assert len(result.cars) == 1
    assert result.cars[0].brand == "BMW"


def test_invalid_row_collected_as_error():
    data = _build_xlsx([
        ["brand", "model", "price", "year", "mileage", "fuel", "transmission", "vin"],
        ["BMW", "X5", "не число", 2020, 45000, "Дизель", "АКПП", "VIN0000000000001"],
        ["Audi", "A6", 3200000, 2018, 82000, "Бензин", "Робот", "VIN0000000000002"],
    ])
    result = parse_excel(data)
    assert len(result.errors) == 1
    assert len(result.cars) == 1
    assert result.cars[0].brand == "Audi"


def test_skip_empty_rows():
    data = _build_xlsx([
        ["brand", "model", "price", "year", "mileage", "fuel", "transmission", "vin"],
        [None, None, None, None, None, None, None, None],
        ["BMW", "X5", 5600000, 2020, 45000, "Дизель", "АКПП", "VIN0000000000001"],
    ])
    result = parse_excel(data)
    assert len(result.cars) == 1
    assert result.errors == []


def test_price_with_spaces():
    data = _build_xlsx([
        ["brand", "model", "price", "year", "mileage", "fuel", "transmission", "vin"],
        ["BMW", "X5", "5 600 000", 2020, 45000, "Дизель", "АКПП", "VIN0000000000001"],
    ])
    result = parse_excel(data)
    assert len(result.cars) == 1
    assert result.cars[0].price == 5_600_000
