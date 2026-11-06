from pathlib import Path
import sys
import os
import pandas as pd
import numpy as np

# Thêm root workspace vào sys.path để import race_configs
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from data.race_configs import RACE_CONFIGS
except ImportError:
    RACE_CONFIGS = {
        "monza": {
            "n_laps": 53,
            "alpha_fuel": 0.058,
            "gamma_track": 0.022,
        },
        "silverstone": {
            "n_laps": 52,
            "alpha_fuel": 0.062,
            "gamma_track": 0.025,
        }
    }

DATA_DIR = Path(__file__).resolve().parent


def clean_circuit_laps(circuit_name: str = "silverstone") -> pd.DataFrame:
    """Lọc dữ liệu sạch cho chặng đua chỉ định (Monza hoặc Silverstone).
    
    Quy trình xử lý:
    1. Đọc dữ liệu raw_laps.parquet.
    2. Lọc cờ xanh (TrackStatus == '1').
    3. Lọc bỏ các vòng pit stop (PitDuration không rỗng).
    4. Lọc bỏ vòng xuất phát đầu tiên (Lap 1 - Standing start).
    5. Loại bỏ ngoại lai dị biệt: t_lap > 1.07 * median(compound).
    6. Hiệu chỉnh thời gian theo cả 2 hiệu ứng giải tích:
       t_isolated = t_lap - alpha_fuel * (N - lap) + gamma_track * lap
    7. Lưu file clean_laps.parquet tương ứng.
    """
    circuit_key = circuit_name.lower()
    folder_name = f"{circuit_key}_2023"
    input_path = DATA_DIR / folder_name / "raw_laps.parquet"
    output_path = DATA_DIR / folder_name / "clean_laps.parquet"

    if not input_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {input_path}")

    cfg = RACE_CONFIGS.get(circuit_key, RACE_CONFIGS.get("monza"))
    n_total = cfg.get("n_laps", 53)
    alpha_fuel = cfg.get("alpha_fuel", 0.058)
    gamma_track = cfg.get("gamma_track", 0.022)

    # 1. Load raw lap data
    laps = pd.read_parquet(input_path)

    # 2. Check required columns
    required_columns = {"TrackStatus", "LapNumber", "LapTime"}
    missing_columns = required_columns - set(laps.columns)
    if missing_columns:
        raise ValueError(f"Thiếu các cột bắt buộc: {sorted(missing_columns)}")

    # 3. Chỉ giữ các vòng cờ xanh (Green flag: TrackStatus == '1')
    track_status = laps["TrackStatus"].astype("string").str.strip()
    cleaned = laps.loc[track_status == "1"].copy()

    # 4. Lọc bỏ các vòng Pit Stop (In-lap / Out-lap) nếu có cột PitDuration
    if "PitDuration" in cleaned.columns:
        cleaned = cleaned.loc[cleaned["PitDuration"].isna()].copy()

    # 5. Ép kiểu LapNumber và loại bỏ vòng 1 (Standing start lap)
    cleaned["LapNumber"] = pd.to_numeric(cleaned["LapNumber"], errors="coerce")
    cleaned = cleaned.loc[cleaned["LapNumber"] > 1].copy()

    # 6. Chuyển đổi LapTime sang giây
    lap_times = cleaned["LapTime"]
    if pd.api.types.is_timedelta64_dtype(lap_times.dtype):
        raw_seconds = lap_times.dt.total_seconds()
    elif pd.api.types.is_numeric_dtype(lap_times.dtype):
        raw_seconds = pd.to_numeric(lap_times, errors="coerce")
    else:
        raw_seconds = pd.to_timedelta(lap_times, errors="coerce").dt.total_seconds()

    cleaned["LapTimeSeconds"] = raw_seconds
    cleaned = cleaned.dropna(subset=["LapTimeSeconds", "LapNumber"])

    # 7. Lọc nhiễu ngoại lai theo hợp chất: t_lap <= 1.07 * median(compound)
    if "Compound" in cleaned.columns:
        valid_rows = []
        for comp, comp_group in cleaned.groupby("Compound"):
            med = comp_group["LapTimeSeconds"].median()
            valid_rows.append(comp_group.loc[comp_group["LapTimeSeconds"] <= 1.07 * med])
        if valid_rows:
            cleaned = pd.concat(valid_rows).sort_index()

    # 8. Hiệu chỉnh giải tích hai thành phần (Tải nhiên liệu & Cao su mặt đường)
    cleaned["FuelEffectSeconds"] = alpha_fuel * (n_total - cleaned["LapNumber"])
    cleaned["TrackRubberSeconds"] = gamma_track * cleaned["LapNumber"]
    
    # Biến phản hồi đã cô lập mòn lốp thuần túy (Isolate Tyre Degradation)
    cleaned["LapTimeIsolatedSeconds"] = (
        cleaned["LapTimeSeconds"]
        - cleaned["FuelEffectSeconds"]
        + cleaned["TrackRubberSeconds"]
    )
    cleaned["LapTimeCorrectedSeconds"] = cleaned["LapTimeIsolatedSeconds"]

    # 9. Xuất dữ liệu sạch
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(output_path, index=False)

    # Xuất thêm bản copy về data/clean_laps.parquet nếu là chặng Monza
    if circuit_key == "monza":
        root_data_target = ROOT_DIR / "data" / "clean_laps.parquet"
        root_data_target.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_parquet(root_data_target, index=False)

    return cleaned


def clean_laps() -> pd.DataFrame:
    """Wrapper tương thích ngược mặc định cho Silverstone."""
    return clean_circuit_laps("silverstone")


if __name__ == "__main__":
    for c in ["monza", "silverstone"]:
        try:
            df = clean_circuit_laps(c)
            out_file = DATA_DIR / f"{c}_2023" / "clean_laps.parquet"
            print(f"[{c.upper()}] Da xu ly thanh cong {len(df)} vong sach -> {out_file}")
            print(df[["Driver", "LapNumber", "Compound", "LapTimeSeconds", "LapTimeIsolatedSeconds"]].head(3))
        except Exception as e:
            print(f"[{c.upper()}] Loi: {e}")
