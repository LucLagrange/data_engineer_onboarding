import dlt
import requests
import os
import logging
from datetime import datetime, timezone
from typing import Iterator, Dict, Any, Optional
from timeit import default_timer as timer

# Script Configuration
OPEN_WEATHER_MAP_API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY", "").strip()
LATITUDE = os.getenv("LATITUDE", "").strip()
LONGITUDE = os.getenv("LONGITUDE", "").strip()

# Configure the logging module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def validate_config(
    lat: Optional[str], lon: Optional[str], api_key: Optional[str]
) -> bool:
    """Check that latitude, longitude, and API key are present.

    Args:
        lat: Latitude coordinate string.
        lon: Longitude coordinate string.
        api_key: OpenWeatherMap API key string.

    Returns:
        bool: True if all variables are present, False otherwise.
    """
    if not all([lat, lon, api_key]):
        missing = [
            name
            for name, val in {
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "API_KEY": api_key,
            }.items()
            if not val
        ]
        logging.error("Missing required configuration: %s", ", ".join(missing))
        return False
    return True


@dlt.resource(name="weather_report", write_disposition="append")
def weather_resource() -> Iterator[Dict[str, Any]]:
    """A dlt resource that yields weather data from the OpenWeatherMap API.

    Yields:
        Iterator[Dict[str, Any]]: Processed weather metrics for ingestion.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": OPEN_WEATHER_MAP_API_KEY,
        "units": "metric",
        "lang": "en",
    }

    logging.info("Fetching weather information for %s, %s", LATITUDE, LONGITUDE)

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Successfully fetched weather information.")

        yield {
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "observed_at": datetime.fromtimestamp(data["dt"], timezone.utc),
        }

    except requests.exceptions.RequestException as e:
        logging.error("Error fetching the weather data: %s", e)
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to extract data from API response: %s", e)


def main() -> None:
    """Main execution logic to run the dlt ingestion pipeline."""
    start = timer()

    # Validates the environment variables
    if not validate_config(LATITUDE, LONGITUDE, OPEN_WEATHER_MAP_API_KEY):
        return

    # Initialize the dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="weather_ingestion",
        destination="postgres",
        dataset_name="raw_weather_data",
    )

    try:
        logging.info("Starting the dlt pipeline ingestion.")
        load_info = pipeline.run(weather_resource())
        logging.info("Pipeline run results: %s", load_info)
    except Exception as e:
        logging.error("The pipeline failed to run: %s", e)

    end = timer()
    duration = round(end - start, 1)
    logging.info("The script took %ss to complete.", duration)


if __name__ == "__main__":
    main()
