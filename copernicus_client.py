# copernicus_client.py
import copernicusmarine
import xarray as xr
from datetime import datetime, timedelta
from config import settings
import logging

logger = logging.getLogger(__name__)


def fetch_forecast_data(
    variable: str,
    min_longitude: float = -180,
    max_longitude: float = 180,
    min_latitude: float = -90,
    max_latitude: float = 90,
    depth: float = 0.5,
    forecast_days: int = None,
) -> xr.Dataset:
    """
    Fetch forecast data from Copernicus Marine Service.
    Returns an xarray Dataset.
    """

    dataset_config = settings.DATASET_CONFIG[variable]
    forecast_days = forecast_days or settings.FORECAST_DAYS

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=forecast_days)

    logger.info(f"Fetching {variable} forecast from {start_date} to {end_date}")

    try:
        dataset = copernicusmarine.open_dataset(
            dataset_id=dataset_config["dataset_id"],
            variables=[dataset_config["variable"]],
            minimum_longitude=min_longitude,
            maximum_longitude=max_longitude,
            minimum_latitude=min_latitude,
            maximum_latitude=max_latitude,
            minimum_depth=depth,
            maximum_depth=depth,
            start_datetime=start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            end_datetime=end_date.strftime("%Y-%m-%dT%H:%M:%S"),
            username=settings.COPERNICUS_USERNAME,
            password=settings.COPERNICUS_PASSWORD,
        )

        logger.info(f"Successfully fetched dataset with shape: {dataset}")
        return dataset

    except Exception as e:
        logger.error(f"Failed to fetch Copernicus data: {str(e)}")
        raise
