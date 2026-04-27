from datetime import datetime

from sqlmodel import Field, SQLModel


class CarBase(SQLModel):
    brand: str = Field(index=True)
    model: str
    price: int
    year: int = Field(index=True)
    mileage: int
    fuel: str
    transmission: str
    vin: str = Field(index=True, unique=True)
    location: str | None = None


class Car(CarBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CarCreate(CarBase):
    pass


class CarRead(CarBase):
    id: int
    created_at: datetime


class BulkCreateResult(SQLModel):
    created: int
    skipped_duplicates: int
    invalid: int
    errors: list[str] = []
