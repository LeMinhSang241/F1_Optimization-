from pathlib import Path

import pandas as pd


INPUT_PATH = Path("silverstone_2023") / "raw_laps.parquet"
OUTPUT_PATH = Path("silverstone_2023") / "clean_laps.parquet"

# Fuel-effect correction parameters for Silverstone 2023
ALPHA_FUEL = 0.058  # seconds per lap
N_TOTAL = 52         # Total race laps


def clean_laps(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Filter green-flag laps and correct lap times for fuel effect."""

    # 1. Load raw lap data
    laps = pd.read_parquet(input_path)

    # 2. Check required columns
    required_columns = {"TrackStatus", "LapNumber", "LapTime"}
    missing_columns = required_columns - set(laps.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    # 3. Keep only green-flag laps
    track_status = laps["TrackStatus"].astype("string").str.strip()
    cleaned_laps = laps.loc[track_status == "1"].copy()

    # 4. Get lap numbers as numeric values
    lap_numbers = pd.to_numeric(
        cleaned_laps["LapNumber"],
        errors="coerce",
    )

    # 5. Convert lap times to seconds
    # FastF1 normally stores LapTime as a pandas timedelta.
    lap_times = cleaned_laps["LapTime"]

    if pd.api.types.is_timedelta64_dtype(lap_times.dtype):
        raw_seconds = lap_times.dt.total_seconds()

    elif pd.api.types.is_numeric_dtype(lap_times.dtype):
        # Assumes numeric lap times are already in seconds.
        raw_seconds = pd.to_numeric(lap_times, errors="coerce")

    else:
        raw_seconds = pd.to_timedelta(
            lap_times, errors="coerce"
        ).dt.total_seconds()

    # 6. Calculate fuel-effect correction
    cleaned_laps["LapTimeSeconds"] = raw_seconds

    cleaned_laps["FuelEffectSeconds"] = (
        ALPHA_FUEL * (N_TOTAL - lap_numbers)
    )

    # 7. Calculate corrected lap times
    cleaned_laps["LapTimeCorrectedSeconds"] = (
        cleaned_laps["LapTimeSeconds"]
        - cleaned_laps["FuelEffectSeconds"]
    )

    # 8. Export cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_laps.to_parquet(output_path, index=False)

    return cleaned_laps


if __name__ == "__main__":
    cleaned = clean_laps()

    print(f"Wrote {len(cleaned)} clean laps to {OUTPUT_PATH}")

    print(
        cleaned[
            [
                "Driver",
                "LapNumber",
                "LapTimeSeconds",
                "FuelEffectSeconds",
                "LapTimeCorrectedSeconds",
            ]
        ].head(10)
    )
