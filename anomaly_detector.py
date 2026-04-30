# anomaly_detector.py
import xarray as xr
import numpy as np
from models import AnomalyPoint, ComparisonOperator
from config import settings
import logging

logger = logging.getLogger(__name__)


OPERATORS = {
    ComparisonOperator.greater_than: np.greater,
    ComparisonOperator.less_than: np.less,
    ComparisonOperator.greater_or_equal: np.greater_equal,
    ComparisonOperator.less_or_equal: np.less_equal,
}


def detect_anomalies(
    dataset: xr.Dataset,
    variable: str,
    threshold: float,
    operator: ComparisonOperator,
) -> list[AnomalyPoint]:
    """
    Detect where and when the variable exceeds the threshold.
    Returns a list of AnomalyPoint.
    """

    var_name = settings.DATASET_CONFIG[variable]["variable"]
    data_array = dataset[var_name]

    # Apply threshold condition
    compare_fn = OPERATORS[operator]
    condition = compare_fn(data_array.values, threshold)

    # Get indices where condition is True
    indices = np.argwhere(condition)

    if len(indices) == 0:
        logger.info("No anomalies detected")
        return []

    anomalies = []
    dims = data_array.dims  # e.g. ('time', 'depth', 'latitude', 'longitude')

    logger.info(f"Found {len(indices)} anomaly points, processing...")

    for idx in indices:
        coords = {dim: data_array[dim].values[idx[i]] for i, dim in enumerate(dims)}

        anomaly = AnomalyPoint(
            latitude=float(coords.get("latitude", coords.get("lat", 0))),
            longitude=float(coords.get("longitude", coords.get("lon", 0))),
            depth=float(coords["depth"]) if "depth" in coords else None,
            datetime=str(coords["time"]),
            value=round(float(data_array.values[tuple(idx)]), 4),
        )
        anomalies.append(anomaly)

    return anomalies
