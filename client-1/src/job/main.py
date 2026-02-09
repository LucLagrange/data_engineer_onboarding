import requests
import logging
import os
import datetime
import psycopg
from typing import Any, Dict, Optional
from timeit import default_timer as timer

# Script Configuration
OPEN_WEATHER_MAP_API_KEY = os.getenv("OPEN_WEATHER_MAP_API_KEY").strip()
LATITUDE = os.getenv("LATITUDE").strip()
LONGITUDE = os.getenv("LONGITUDE").strip()

# DB Variables
DB_HOST = os.getenv("DB_HOST").strip()
DB_USER = os.getenv("DB_USER").strip()
DB_PASS = os.getenv("DB_PASS").strip()
DB_NAME = os.getenv("DB_NAME").strip()
DB_PORT = os.getenv("DB_PORT").strip()

# Configure the logging module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def validate_config(
    lat: Optional[str], lon: Optional[str], api_key: Optional[str]
) -> bool:
    """
    Check that latitude, longitude, and API key are present.

    Args:
        lat: Latitude coordinate string.
        lon: Longitude coordinate string.
        api_key: OpenWeatherMap API key string.

    Returns:
        True if all variables are present, False otherwise.
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


def get_current_weather(
    LATITUDE: Optional[str],
    LONGITUDE: Optional[str],
    OPEN_WEATHER_MAP_API_KEY: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Extracts the current weather from the OpenWeatherMap API.

    Args:
        LATITUDE: Latitude coordinate for the location. Hard-coded in the docker-compose.yaml file
        LONGITUDE: Longitude coordinate for the location. Hard-coded in the docker-compose.yaml file
        OPEN_WEATHER_MAP_API_KEY: API key for authentication.

    Returns:
        A dictionary containing the API response or None if an error occurs.
    """
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?lat={LATITUDE}"
        f"&lon={LONGITUDE}&appid={OPEN_WEATHER_MAP_API_KEY}"
    )

    params = {
        "units": "metric",
        "lang": "en",
    }

    logging.info("Fetching the weather information for %s, %s", LATITUDE, LONGITUDE)

    try:
        response = requests.get(url, params=params, timeout=10)

        response.raise_for_status()

        data: Dict[str, Any] = response.json()
        logging.info("Succesfuly fetched weather information")
        # logging.info("API response: %s", data)
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching the weather data: %s", e)
        return None

    return data


def extract_weather_information_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract specific weather details from the raw API JSON response.

    Args:
        data: Raw dictionary response from the weather API.

    Returns:
        A dictionary containing processed weather info and formatted date.
    """
    logging.info("Extracting weather information from the API response")

    # Initialize the result dictionary
    weather_info: Dict[str, Any] = {
        "weather": None,
        "description": None,
        "temperature": None,
        "humidity": None,
        "date": None,
    }

    # Extract the information from the API response
    try:
        weather_info["weather"] = data["weather"][0]["main"]
    except (IndexError, KeyError, TypeError) as e:
        logging.error("Failed to extract 'weather': %s", e)
        weather_info["weather"] = "No weather data available"

    try:
        weather_info["description"] = data["weather"][0]["description"]
    except (IndexError, KeyError, TypeError) as e:
        logging.error("Failed to extract 'description': %s", e)
        weather_info["description"] = "No description available"

    try:
        weather_info["temperature"] = data["main"]["temp"]
    except KeyError as e:
        logging.error("Failed to extract 'temperature': %s", e)
        weather_info["temperature"] = "No temperature available"

    try:
        weather_info["humidity"] = data["main"]["humidity"]
    except KeyError as e:
        logging.error("Failed to extract 'humidity': %s", e)
        weather_info["humidity"] = "No humidity data available"

    # Convert the timestamp to a readable local date
    try:
        timestamp = data["dt"]
        timezone_offset = data.get("timezone", 0)
        utc_time = datetime.datetime.fromtimestamp(timestamp, datetime.UTC)
        local_time = utc_time + datetime.timedelta(seconds=timezone_offset)
        weather_info["date"] = local_time.strftime("%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError) as e:
        logging.error("Failed to convert timestamp to date: %s", e)
        weather_info["date"] = "No date available"

    logging.info("Successfully extracted weather information: %s", weather_info)

    return weather_info


def save_to_db(info: Dict[str, Any]) -> bool:
    """Insert the weather data into PostgreSQL 18."""
    conn_str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    query = """
    INSERT INTO weather_metrics (weather, description, temperature, humidity, observed_at)
    VALUES (%s, %s, %s, %s, %s);
    """

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        info["weather"],
                        info["description"],
                        info["temperature"],
                        info["humidity"],
                        info["date"],
                    ),
                )
        logging.info("Successfully ingested data into Postgres.")
        return True
    except psycopg.Error as e:
        logging.error("Database insertion failed: %s", e)
        return False


def main() -> None:
    """
    Main execution logic to fetch and display weather information.
    """
    start = timer()
    if not validate_config(LATITUDE, LONGITUDE, OPEN_WEATHER_MAP_API_KEY):
        logging.error("Configuration validation failed. Exiting.")
        return
    data = get_current_weather(LATITUDE, LONGITUDE, OPEN_WEATHER_MAP_API_KEY)

    # Check if data exists before extraction to avoid errors
    if data:
        weather_information = extract_weather_information_from_json(data)
        save_to_db(weather_information)

    end = timer()
    duration = round(end - start, 1)
    logging.info("The script took %ss to complete", duration)


if __name__ == "__main__":
    main()
