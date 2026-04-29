from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.models import BulkCreateResult, Car, CarCreate, CarRead

router = APIRouter(prefix="/api/cars", tags=["cars"])


@router.get("", response_model=list[CarRead])
def list_cars(
    session: Session = Depends(get_session),
    brand: str | None = None,
    max_price: int | None = Query(default=None, ge=0),
    min_year: int | None = Query(default=None, ge=1900),
    max_mileage: int | None = Query(default=None, ge=0),
) -> list[Car]:
    statement = select(Car)
    if brand:
        statement = statement.where(Car.brand == brand)
    if max_price is not None:
        statement = statement.where(Car.price <= max_price)
    if min_year is not None:
        statement = statement.where(Car.year >= min_year)
    if max_mileage is not None:
        statement = statement.where(Car.mileage <= max_mileage)
    statement = statement.order_by(Car.created_at.desc())
    return list(session.exec(statement).all())


@router.post("", response_model=CarRead, status_code=201)
def create_car(car: CarCreate, session: Session = Depends(get_session)) -> Car:
    db_car = Car.model_validate(car)
    session.add(db_car)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Duplicate VIN: {car.vin}") from exc
    session.refresh(db_car)
    return db_car


@router.post("/bulk", response_model=BulkCreateResult)
def bulk_create(
    cars: list[CarCreate], session: Session = Depends(get_session)
) -> BulkCreateResult:
    created = 0
    skipped = 0
    errors: list[str] = []

    existing_vins = set(session.exec(select(Car.vin)).all())

    for incoming in cars:
        if incoming.vin in existing_vins:
            skipped += 1
            continue
        try:
            db_car = Car.model_validate(incoming)
            session.add(db_car)
            session.flush()
            existing_vins.add(incoming.vin)
            created += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
        except Exception as exc:
            session.rollback()
            errors.append(f"{incoming.vin}: {exc}")

    session.commit()
    return BulkCreateResult(
        created=created,
        skipped_duplicates=skipped,
        invalid=len(errors),
        errors=errors,
    )


@router.delete("/{car_id}", status_code=204)
def delete_car(car_id: int, session: Session = Depends(get_session)) -> None:
    car = session.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    session.delete(car)
    session.commit()
