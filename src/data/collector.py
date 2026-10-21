from pathlib import Path

import fastf1
import pandas as pd


YEAR = 2023
EVENT = "Italian Grand Prix"
SESSION = "Race"
CACHE_PATH = Path("f1_cache")
OUTPUT_PATH = Path("raw_laps.parquet")


def collect_laps(
    output_path: Path = OUTPUT_PATH,
    cache_path: Path = CACHE_PATH,
) -> pd.DataFrame:
    """Extract lap data and pit durations for the 2023 Italian Grand Prix."""
    fastf1.Cache.enable_cache(str(cache_path))

    session = fastf1.get_session(YEAR, EVENT, SESSION)
    session.load(
        laps=True,
        telemetry=False,
        weather=False,
        messages=False,
    )

    laps = session.laps.copy()

    # FastF1 records pit entry on one lap and pit exit on the next. Find the
    # next pit exit for each driver so the duration can be assigned to the
    # corresponding pit-entry lap.
    next_pit_out = laps.groupby("Driver", sort=False)["PitOutTime"].bfill()
    pit_duration = next_pit_out - laps["PitInTime"]
    pit_duration = pit_duration.where(laps["PitInTime"].notna())

    extracted = laps.assign(PitDuration=pit_duration)[
        [
            "Driver",
            "LapNumber",
            "LapTime",
            "TyreLife",
            "Compound",
            "TrackStatus",
            "PitDuration",
        ]
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    extracted.to_parquet(output_path, index=False)
    return extracted


if __name__ == "__main__":
    laps = collect_laps()
    print(f"Wrote {len(laps)} laps to {OUTPUT_PATH}")
