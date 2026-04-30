# anomaly_detector.py
import xarray as xr
import numpy as np
from scipy.ndimage import label
from shapely.geometry import Point, mapping
from shapely.ops import unary_union
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


def build_geojson(anomaly_points: list[AnomalyPoint], grid_resolution: float = 0.083) -> dict:
    """
    Convert a list of AnomalyPoint into a GeoJSON FeatureCollection,
    grouping contiguous points into polygons.

    Args:
        anomaly_points: list of AnomalyPoint objects
        grid_resolution: grid spacing in degrees (default: 0.083 for CMEMS global)

    Returns:
        GeoJSON FeatureCollection dict
    """
    if not anomaly_points:
        return {"type": "FeatureCollection", "features": []}

    # --- 1. Build a 2D grid from the points ---
    lats = sorted(set(p.latitude for p in anomaly_points))
    lons = sorted(set(p.longitude for p in anomaly_points))

    lat_idx = {lat: i for i, lat in enumerate(lats)}
    lon_idx = {lon: i for i, lon in enumerate(lons)}

    grid = np.zeros((len(lats), len(lons)), dtype=int)

    point_data = {}
    for p in anomaly_points:
        i = lat_idx[p.latitude]
        j = lon_idx[p.longitude]
        grid[i, j] = 1
        point_data[(i, j)] = p.value

    # --- 2. Label connected regions ---
    structure = np.array([[0, 1, 0],
                          [1, 1, 1],
                          [0, 1, 0]])
    labeled_grid, num_clusters = label(grid, structure=structure)

    # --- 3. Build one polygon per cluster ---
    features = []

    for cluster_id in range(1, num_clusters + 1):
        cluster_indices = np.argwhere(labeled_grid == cluster_id)

        values = [point_data[(i, j)] for i, j in cluster_indices]

        # Build a polygon by buffering points by half the grid resolution
        half_res = grid_resolution / 2
        polygons = [
            Point(lons[j], lats[i]).buffer(half_res)
            for i, j in cluster_indices
        ]
        cluster_polygon = unary_union(polygons)

        feature = {
            "type": "Feature",
            "geometry": mapping(cluster_polygon),
            "properties": {
                "cluster_id": cluster_id,
                "num_points": len(cluster_indices),
                "min_value": round(float(np.min(values)), 3),
                "max_value": round(float(np.max(values)), 3),
                "mean_value": round(float(np.mean(values)), 3),
            },
        }
        features.append(feature)

    logger.info(f"Built GeoJSON with {num_clusters} clusters")

    return {
        "type": "FeatureCollection",
        "features": features,
    }

