"""Excel → list[CarDTO] parser. First sheet only."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

EXPECTED_COLUMNS = (
    "brand",
    "model",
    "price",
    "year",
    "mileage",
    "fuel",
    "transmission",
    "vin",
    "location",
)


@dataclass
class CarDTO:
    brand: str
    model: str
    price: int
    year: int
    mileage: int
    fuel: str
    transmission: str
    vin: str
    location: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "year": self.year,
            "mileage": self.mileage,
            "fuel": self.fuel,
            "transmission": self.transmission,
            "vin": self.vin,
        }
        if self.location:
            payload["location"] = self.location
        return payload


@dataclass
class ParseResult:
    cars: list[CarDTO] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _is_header(row: tuple[Any, ...]) -> bool:
    if not row:
        return False
    first = row[0]
    if not isinstance(first, str):
        return False
    return first.strip().lower() in {"brand", "марка", "make"}


def _to_int(value: Any) -> int:
    if value is None or value == "":
        raise ValueError("empty")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        cleaned = value.replace(" ", "").replace("\u00a0", "").replace(",", "")
        return int(float(cleaned))
    raise ValueError(f"cannot convert {value!r} to int")


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_excel(data: bytes) -> ParseResult:
    """Parse the first sheet of an xlsx file into CarDTO objects.

    Header row is detected by checking if the first column equals brand/марка/make.
    """
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    ws = wb.worksheets[0]

    rows = ws.iter_rows(values_only=True)
    result = ParseResult()

    first_row = next(rows, None)
    if first_row is None:
        return result

    if not _is_header(first_row):
        rows_to_process = [first_row, *list(rows)]
    else:
        rows_to_process = list(rows)

    for idx, raw in enumerate(rows_to_process, start=2 if _is_header(first_row) else 1):
        if raw is None or all(cell is None or cell == "" for cell in raw):
            continue
        padded = list(raw) + [None] * (len(EXPECTED_COLUMNS) - len(raw))
        try:
            car = CarDTO(
                brand=_to_str(padded[0]),
                model=_to_str(padded[1]),
                price=_to_int(padded[2]),
                year=_to_int(padded[3]),
                mileage=_to_int(padded[4]),
                fuel=_to_str(padded[5]),
                transmission=_to_str(padded[6]),
                vin=_to_str(padded[7]),
                location=_to_str(padded[8]) or None,
            )
            if not car.brand or not car.model or not car.vin:
                raise ValueError("missing brand/model/vin")
        except (ValueError, TypeError) as exc:
            result.errors.append(f"строка {idx}: {exc}")
            continue
        result.cars.append(car)

    return result
