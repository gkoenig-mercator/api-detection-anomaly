# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging

from models import AnomalyRequest, AnomalyResponse
from copernicus_client import fetch_forecast_data
from anomaly_detector import detect_anomalies
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Copernicus Marine Anomaly Detection API",
    description="Detect threshold anomalies in ocean forecast data",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/detect-anomalies", response_model=AnomalyResponse)
async def detect_anomalies_endpoint(request: AnomalyRequest):
    """
    Detect locations and times where the variable exceeds the threshold
    in the next forecast days.
    """

    # Default to global bbox if not provided
    min_lon = request.min_longitude if request.min_longitude is not None else -180
    max_lon = request.max_longitude if request.max_longitude is not None else 180
    min_lat = request.min_latitude if request.min_latitude is not None else -90
    max_lat = request.max_latitude if request.max_latitude is not None else 90
    depth = request.depth if request.depth is not None else 0.5

    try:
        # 1. Fetch forecast data
        logger.info(f"Processing request for {request.variable} with threshold {request.threshold}")
        dataset = fetch_forecast_data(
            variable=request.variable,
            min_longitude=min_lon,
            max_longitude=max_lon,
            min_latitude=min_lat,
            max_latitude=max_lat,
            depth=depth,
        )

        # 2. Detect anomalies
        anomalies = detect_anomalies(
            dataset=dataset,
            variable=request.variable,
            threshold=request.threshold,
            operator=request.operator,
        )

        # 3. Build response
        now = datetime.utcnow()
        response = AnomalyResponse(
            variable=request.variable,
            unit=settings.DATASET_CONFIG[request.variable]["unit"],
            threshold=request.threshold,
            operator=request.operator.value,
            forecast_range={
                "start": now.isoformat(),
                "end": (now + timedelta(days=settings.FORECAST_DAYS)).isoformat(),
            },
            total_anomalies=len(anomalies),
            anomalies=anomalies,
            metadata={
                "dataset_id": settings.DATASET_CONFIG[request.variable]["dataset_id"],
                "bbox": {
                    "min_lon": min_lon, "max_lon": max_lon,
                    "min_lat": min_lat, "max_lat": max_lat,
                },
                "depth_m": depth,
            },
        )

        return JSONResponse(content=response.model_dump())

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
