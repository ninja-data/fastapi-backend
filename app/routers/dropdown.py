from fastapi import Depends, APIRouter, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..database import get_db
from .. import models, schemas

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# APIRouter instance for dropdown-related endpoints
router = APIRouter(
    prefix="/dropdowns",
    tags=["Dropdown"]
)


@router.get("/countries", response_model=List[schemas.Country])
def get_countries(db: Session = Depends(get_db)):
    """
    Retrieve a list of all countries.

    This endpoint returns a list of countries from the database, sorted alphabetically by name.
    Typically used to populate a dropdown list on the frontend.

    ### Response
    - **200 OK**: List of countries with fields like `id`, `name`, and `emoji`.

    ### Example Request
    ```
    GET /dropdowns/countries
    ```

    ### Example Response
    ```json
    [
        {
            "id": 1,
            "name": "Azerbaijan",
            "emoji": "🇦🇿"
        },
        {
            "id": 2,
            "name": "Turkey",
            "emoji": "🇹🇷"
        }
    ]
    ```

    :param db: SQLAlchemy Session, injected by FastAPI's dependency system.
    :return: List of countries.
    """
    return db.query(models.Country).order_by(models.Country.name).all()


@router.get("/cities", response_model=List[schemas.City])
def get_cities(
    country_id: int,
    search: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated and optionally filtered list of cities for a given country.

    This endpoint supports:
    - Filtering by `country_id`
    - Optional case-insensitive search by city name (`search`)
    - Pagination via `limit` and `offset` parameters

    ### Query Parameters
    - **country_id** (int, required): ID of the country to filter cities by
    - **search** (str, optional): Search string to filter cities by name (case-insensitive, partial match)
    - **limit** (int, optional): Max number of cities to return (default: 50, max: 100)
    - **offset** (int, optional): Number of records to skip for pagination (default: 0)

    ### Example Request
    ```
    GET /dropdowns/cities?country_id=1&search=ba&limit=20&offset=0
    ```

    ### Example Response
    ```json
    [
        {
            "id": 1,
            "name": "Baku",
            "country_id": 1
        },
        {
            "id": 2,
            "name": "Balakan",
            "country_id": 1
        }
    ]
    ```

    :param country_id: ID of the country whose cities to fetch.
    :param search: Optional filter for city name (partial match, case-insensitive).
    :param limit: Max number of results to return (default 50, max 100).
    :param offset: Number of results to skip for pagination.
    :param db: SQLAlchemy session.
    :return: List of cities matching the filters.
    """
    query = db.query(models.City).filter(models.City.country_id == country_id)

    if search:
        query = query.filter(models.City.name.ilike(f"%{search}%"))

    return query.order_by(models.City.name).offset(offset).limit(limit).all()
