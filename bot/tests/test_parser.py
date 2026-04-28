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


def test_parse_with_english_header():
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


def test_parse_russian_header_real_world_columns():
    """Regression: user's actual Excel has 35 columns in arbitrary order."""
    header = [
        "№", "Категория", "Месторасположение", "Организация",
        "Дата поступления в склад АСП", "Дата публикации в Интернете",
        "Кол-во дней в продаже после публикации",
        "Марка", "Модель", "VIN",
        "Состояние а/м", "Комплектация+опции", "Цвет кузова", "Салон а/м",
        "Год выпуска", "Пробег, км.",
        "ВИД ПТС/ЭПТС", "Количество собственников", "Комплектность",
        "НДС", "Цена продажи, руб.",
        "Авито Оценка", "% к рынку Автохаб", "Скидка за кредит",
        "Скидка за ТИ", "Менеджер", "Клиент / Город", "Дата контракта",
        "Направление", "Менеджер, принявший а/м", "Затраты на а/м",
        "Приходная стоимость, руб.", "Скидка по трейд-ин при приеме а/м (без НДС)",
        "Кол-во дней в продаже с поступления а/м",
        "Ч/з сколько дней выставлен в продажу после принятия",
    ]
    row = [None] * len(header)
    row[2] = "Москва"                 # Месторасположение → location
    row[7] = "BMW"                    # Марка
    row[8] = "X5"                     # Модель
    row[9] = "WBAFE41070LN12345"      # VIN
    row[14] = 2020                    # Год выпуска
    row[15] = 45000                   # Пробег
    row[20] = 5600000                 # Цена продажи

    data = _build_xlsx([header, row])
    result = parse_excel(data)
    assert result.errors == [], result.errors
    assert len(result.cars) == 1
    car = result.cars[0]
    assert car.brand == "BMW"
    assert car.vin == "WBAFE41070LN12345"
    assert car.year == 2020
    assert car.mileage == 45000
    assert car.price == 5_600_000
    assert car.location == "Москва"
    assert car.fuel is None
    assert car.transmission is None


def test_parse_without_header_positional():
    data = _build_xlsx([
        ["BMW", "X5", 5600000, 2020, 45000, "Дизель", "АКПП", "VIN0000000000001", "Москва"],
    ])
    result = parse_excel(data)
    assert len(result.cars) == 1
    assert result.cars[0].brand == "BMW"
    assert result.cars[0].fuel == "Дизель"


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


def test_numeric_noise_stripped():
    """Cleans units like 'руб.', 'г.', 'км.', non-breaking spaces, thousand separators."""
    data = _build_xlsx([
        ["Марка", "Модель", "VIN", "Год выпуска", "Пробег, км.", "Цена продажи, руб."],
        ["BMW", "X5", "VIN0001", "2020 г.", "150 000 км.", "1 500 000 руб."],
        ["Audi", "A6", "VIN0002", 2018, "82\u00a0000", "3,200,000"],
    ])
    result = parse_excel(data)
    assert result.errors == [], result.errors
    assert len(result.cars) == 2
    assert result.cars[0].year == 2020
    assert result.cars[0].mileage == 150_000
    assert result.cars[0].price == 1_500_000
    assert result.cars[1].mileage == 82_000
    assert result.cars[1].price == 3_200_000


def test_missing_required_columns_reported():
    data = _build_xlsx([
        ["Марка", "Модель"],
        ["BMW", "X5"],
    ])
    result = parse_excel(data)
    # Header detected (brand present) but no vin/price → detector returns None
    # and parser falls back to positional, then fails on the data row.
    assert result.cars == []
