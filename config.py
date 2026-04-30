# config.py
from dotenv import load_dotenv
import os

load_dotenv(override=True)

class Settings:
    COPERNICUS_USERNAME: str = os.getenv("COPERNICUS_USERNAME", "")
    COPERNICUS_PASSWORD: str = os.getenv("COPERNICUS_PASSWORD", "")

    # Dataset IDs for forecasts - adjust based on your region/needs
    DATASET_CONFIG = {
        "temperature": {
            "dataset_id": "cmems_mod_glo_phy-thetao_anfc_0.083deg_PT6H-i",
            "variable": "thetao",
            "unit": "°C",
        },
        "salinity": {
            "dataset_id": "cmems_mod_glo_phy-so_anfc_0.083deg_PT6H-i",
            "variable": "so",
            "unit": "PSU",
        },
    }

    FORECAST_DAYS: int = 5  # How many days ahead to check

settings = Settings()
