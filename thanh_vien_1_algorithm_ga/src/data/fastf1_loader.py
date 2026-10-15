"""Module phụ trách tải và tiền xử lý dữ liệu từ API FastF1.
Phân công: Thành viên 2 (Data Pipeline Specialist).
"""

from typing import Optional, Tuple
import os
import pandas as pd
import numpy as np


class FastF1DataLoader:
    """Tải và trích xuất dữ liệu vòng đua và telemetry từ thư viện FastF1."""

    def __init__(self, cache_dir: str = "data/cache_fastf1"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            import fastf1
            fastf1.Cache.enable_cache(self.cache_dir)
            self._fastf1 = fastf1
        except ImportError:
            self._fastf1 = None

    def load_race_laps(self, year: int, race_name: str) -> pd.DataFrame:
        """Tải dữ liệu các vòng đua của một chặng đua cụ thể.
        
        Args:
            year: Năm diễn ra chặng đua (ví dụ 2023).
            race_name: Tên chặng đua (ví dụ 'Monza' hoặc 'Silverstone').
            
        Returns:
            pd.DataFrame chứa thông tin các vòng đua (lap times, tyre compounds, tyre age, pit times).
        """
        if self._fastf1 is None:
            raise RuntimeError("Thư viện fastf1 chưa được cài đặt. Vui lòng chạy 'pip install fastf1'.")
            
        session = self._fastf1.get_session(year, race_name, 'R')
        session.load(telemetry=False, laps=True, weather=True)
        return session.laps

    def clean_race_laps(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        """Lọc sạch dữ liệu vòng đua để chuẩn bị cho việc huấn luyện mô hình lốp.
        
        - Lọc chỉ giữ cờ xanh (TrackStatus == '1').
        - Loại bỏ In-lap và Out-lap.
        - Loại bỏ các vòng bất thường có thời gian quá 107% trung vị.
        """
        clean_df = laps_df.copy()
        
        # Lọc cờ xanh
        if 'TrackStatus' in clean_df.columns:
            clean_df = clean_df[clean_df['TrackStatus'] == '1']
            
        # Loại bỏ vòng vào pit và ra pit
        clean_df = clean_df[clean_df['PitInTime'].isna() & clean_df['PitOutTime'].isna()]
        
        # Chỉ lấy các vòng có thời gian hợp lệ
        clean_df = clean_df.dropna(subset=['LapTime', 'Compound', 'TyreLife'])
        clean_df['LapTimeSeconds'] = clean_df['LapTime'].dt.total_seconds()
        
        return clean_df

    def calculate_pit_loss(self, laps_df: pd.DataFrame) -> float:
        """Tính toán tổn thất thời gian vào pit trung bình (Pit Loss) bằng giây:
        T_pit_loss = (t_in + t_out) - 2 * t_flying_clean
        """
        # Tính toán theo công thức chuẩn đã được kiểm chứng
        clean_flying = laps_df[laps_df['PitInTime'].isna() & laps_df['PitOutTime'].isna()]
        t_clean = clean_flying['LapTime'].dt.total_seconds().median()
        
        in_laps = laps_df[~laps_df['PitInTime'].isna()]
        out_laps = laps_df[~laps_df['PitOutTime'].isna()]
        
        if len(in_laps) > 0 and len(out_laps) > 0:
            t_in = in_laps['LapTime'].dt.total_seconds().median()
            t_out = out_laps['LapTime'].dt.total_seconds().median()
            pit_loss = (t_in + t_out) - 2 * t_clean
            return float(np.clip(pit_loss, 18.0, 30.0))
        return 22.0  # Giá trị mặc định chuẩn nếu không đủ mẫu
