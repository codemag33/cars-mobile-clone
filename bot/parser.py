"""Excel → list[CarDTO] parser.

Reads the first sheet. Columns are matched by header name (RU/EN aliases),
so source files can have any column order and extra columns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

# Supported header aliases (normalized: lowercased, stripped, punctuation removed).
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "brand": ("brand", "make", "марка", "марка автомобиля", "бренд"),
    "model": ("model", "модель"),
    "price": (
        "price",
        "цена",
        "цена продажи",
        "цена продажи руб",
        "стоимость",
        "стоимость продажи",
    ),
    "year": ("year", "год", "год выпуска"),
    "mileage": ("mileage", "пробег", "пробег км"),
    "fuel": ("fuel", "топливо", "тип топлива", "двигатель"),
    "transmission": ("transmission", "коробка", "кпп", "трансмиссия", "тип кпп"),
    "vin": ("vin", "вин", "номер vin"),
    "location": (
        "location",
        "город",
        "местоположение",
        "месторасположение",
        "регион",
    ),
}

REQUIRED_FIELDS = ("brand", "model", "price", "year", "mileage", "vin")

# Suffixes / units we strip before parsing numbers.
_NUMERIC_NOISE_RE = re.compile(
    r"(руб(лей|ля|\.)?|р\.?|г(ода|\.)?|км\.?|тыс\.?|\s|,)",
    flags=re.IGNORECASE,
)


@dataclass
class CarDTO:
    brand: str
    model: str
    price: int
    year: int
    mileage: int
    vin: str
    fuel: str | None = None
    transmission: str | None = None
    location: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "year": self.year,
            "mileage": self.mileage,
            "vin": self.vin,
        }
        if self.fuel:
            payload["fuel"] = self.fuel
        if self.transmission:
            payload["transmission"] = self.transmission
        if self.location:
            payload["location"] = self.location
        return payload


@dataclass
class ParseResult:
    cars: list[CarDTO] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _normalize_header(cell: Any) -> str:
    if cell is None:
        return ""
    text = str(cell).strip().lower().strip('"\'«»').strip()
    # Drop any punctuation (commas, dots, slashes etc), collapse whitespace.
    text = re.sub(r"[.,;:!?()\[\]/\\]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _detect_header(row: tuple[Any, ...]) -> dict[str, int] | None:
    """Return a mapping {field_name: column_index}, or None if no header found."""
    mapping: dict[str, int] = {}
    for idx, cell in enumerate(row):
        norm = _normalize_header(cell)
        if not norm:
            continue
        for field_name, aliases in COLUMN_ALIASES.items():
            if field_name in mapping:
                continue
            if norm in aliases:
                mapping[field_name] = idx
                break
    # A row is a header only if we matched at least brand + vin or brand + price.
    if "brand" in mapping and ("vin" in mapping or "price" in mapping):
        return mapping
    return None


def _to_int(value: Any) -> int:
    if value is None or value == "":
        raise ValueError("пусто")
    if isinstance(value, bool):  # bool is a subclass of int, treat specially
        raise ValueError(f"не число: {value!r}")
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        cleaned = _NUMERIC_NOISE_RE.sub("", value).replace("\u00a0", "")
        if not cleaned:
            raise ValueError(f"пусто (было {value!r})")
        try:
            return int(float(cleaned))
        except ValueError as exc:
            raise ValueError(f"не число: {value!r}") from exc
    raise ValueError(f"не число: {value!r}")


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _positional_mapping() -> dict[str, int]:
    """Legacy fallback: A..I = brand, model, price, year, mileage, fuel, transmission, vin, location."""
    return {
        "brand": 0,
        "model": 1,
        "price": 2,
        "year": 3,
        "mileage": 4,
        "fuel": 5,
        "transmission": 6,
        "vin": 7,
        "location": 8,
    }


def _get(row: tuple[Any, ...], mapping: dict[str, int], field_name: str) -> Any:
    idx = mapping.get(field_name)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def parse_excel(data: bytes) -> ParseResult:
    """Parse the first sheet of an xlsx file into CarDTO objects.

    Columns are matched by header name. If no recognisable header is found,
    the legacy positional layout (A..I) is used for backward compatibility.
    """
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    ws = wb.worksheets[0]

    rows_iter = ws.iter_rows(values_only=True)
    result = ParseResult()

    first_row = next(rows_iter, None)
    if first_row is None:
        return result

    mapping = _detect_header(first_row)
    if mapping is None:
        mapping = _positional_mapping()
        data_rows: list[tuple[Any, ...]] = [first_row, *list(rows_iter)]
        header_present = False
    else:
        missing = [f for f in REQUIRED_FIELDS if f not in mapping]
        if missing:
            result.errors.append(
                "В заголовке не найдены обязательные колонки: "
                + ", ".join(missing)
            )
            return result
        data_rows = list(rows_iter)
        header_present = True

    start_row = 2 if header_present else 1
    for offset, raw in enumerate(data_rows):
        row_idx = start_row + offset
        if raw is None or all(cell is None or cell == "" for cell in raw):
            continue
        try:
            brand = _to_str(_get(raw, mapping, "brand"))
            model = _to_str(_get(raw, mapping, "model"))
            vin = _to_str(_get(raw, mapping, "vin"))
            if not brand or not model or not vin:
                raise ValueError("пустые brand/model/vin")
            car = CarDTO(
                brand=brand,
                model=model,
                price=_to_int(_get(raw, mapping, "price")),
                year=_to_int(_get(raw, mapping, "year")),
                mileage=_to_int(_get(raw, mapping, "mileage")),
                vin=vin,
                fuel=_to_str(_get(raw, mapping, "fuel")) or None,
                transmission=_to_str(_get(raw, mapping, "transmission")) or None,
                location=_to_str(_get(raw, mapping, "location")) or None,
            )
        except (ValueError, TypeError) as exc:
            result.errors.append(f"строка {row_idx}: {exc}")
            continue
        result.cars.append(car)

    return result
