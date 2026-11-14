from pathlib import Path

import fastf1
import pandas as pd


YEAR = 2023
EVENT = "Italian Grand Prix"
SESSION = "Race"
DATA_DIR = Path(__file__).resolve().parent
CACHE_PATH = DATA_DIR / "f1_cache"
OUTPUT_PATH = DATA_DIR / "monza_2023" / "weather_telemetry.parquet"
WEATHER_COLUMNS = [
    "Time",
    "AirTemp",
    "Humidity",
    "Rainfall",
    "TrackTemp",
    "WindDirection",
    "WindSpeed",
]


def collect_weather(
    output_path: Path = OUTPUT_PATH,
    cache_path: Path = CACHE_PATH,
) -> pd.DataFrame:
    """Extract the requested weather telemetry for the 2023 Italian GP."""
    fastf1.Cache.configure(cache_dir=str(cache_path))

    session = fastf1.get_session(YEAR, EVENT, SESSION)
    session.load(
        laps=False,
        telemetry=True,
        weather=True,
        messages=False,
    )

    weather = session.weather_data.loc[:, WEATHER_COLUMNS].copy()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    weather.to_parquet(output_path, index=False)
    return weather


if __name__ == "__main__":
    weather = collect_weather()
    print(f"Wrote {len(weather)} weather records to {OUTPUT_PATH}")
