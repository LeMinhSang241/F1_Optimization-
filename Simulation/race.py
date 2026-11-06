import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Thêm root workspace vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from thanh_vien_1_algorithm_ga.src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
except ImportError:
    try:
        from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
    except ImportError:
        PirelliPhysicsTyreModel = None


def get_f1_lap_time_fn(circuit: str = "Monza", t_track: float = 30.0):
    """Khởi tạo hàm tính thời gian vòng đua từ mô hình động lực học lốp Pirelli chuẩn."""
    if PirelliPhysicsTyreModel is not None:
        model = PirelliPhysicsTyreModel(track=circuit, t_track=t_track)
        return model.predict_lap_time, model.pit_loss
    
    # Fallback giải tích theo hệ số danh định nếu chưa import được
    def fallback_lap_time(compound: str, tyre_age: int, race_lap: int, total_laps: int) -> float:
        base_map = {"Soft": 81.50, "Medium": 82.20, "Hard": 83.00}
        deg_map = {"Soft": (0.120, 0.0050), "Medium": (0.070, 0.0020), "Hard": (0.040, 0.0010)}
        t_base = base_map.get(compound, 82.20)
        d1, d2 = deg_map.get(compound, (0.070, 0.0020))
        return t_base + (d1 * tyre_age + d2 * (tyre_age ** 2)) + 0.058 * (total_laps - race_lap) - 0.022 * race_lap
    
    return fallback_lap_time, 23.2


def build_strategy_timeline(
    strategy: List[Tuple[str, int]],
    lap_time_fn,
    pit_duration: float = 23.2
) -> Tuple[List[Dict[str, Any]], float]:
    """Xây dựng dòng thời gian chi tiết từng vòng và từng lần pit của chiến lược."""
    timeline = []
    current_time = 0.0
    race_lap = 1
    total_laps = sum(length for _, length in strategy)

    for stint_idx, (compound, length) in enumerate(strategy):
        for age in range(1, length + 1):
            duration = lap_time_fn(
                compound=compound,
                tyre_age=age,
                race_lap=race_lap,
                total_laps=total_laps
            )
            timeline.append({
                "type": "LAP",
                "lap": race_lap,
                "stint_idx": stint_idx + 1,
                "compound": compound,
                "tyre_age": age,
                "duration": duration,
                "start": current_time,
                "end": current_time + duration
            })
            current_time += duration
            race_lap += 1

        # Nếu chưa phải stint cuối, thêm biến cố Pit Stop
        if stint_idx < len(strategy) - 1:
            timeline.append({
                "type": "PIT",
                "lap": race_lap - 1,
                "stint_idx": stint_idx + 1,
                "compound": compound,
                "tyre_age": length,
                "duration": pit_duration,
                "start": current_time,
                "end": current_time + pit_duration
            })
            current_time += pit_duration

    return timeline, current_time


class RaceCar:
    """Đại diện cho một chiếc xe đua F1 với chiến lược dừng pit và mô hình lốp đầy đủ."""

    def __init__(
        self,
        name: str,
        color: Tuple[int, int, int],
        strategy: List[Tuple[str, int]],
        circuit: str = "Monza",
        t_track: float = 30.0,
        time_scale: float = 50.0  # Tốc độ tua nhanh mô phỏng
    ):
        self.name = name
        self.color = color
        self.strategy = strategy
        self.total_laps = sum(l for _, l in strategy)
        self.time_scale = time_scale

        lap_fn, pit_loss = get_f1_lap_time_fn(circuit, t_track)
        self.timeline, self.total_race_time = build_strategy_timeline(strategy, lap_fn, pit_loss)

        self.elapsed = 0.0               # Thời gian mô phỏng (giây ảo)
        self.progress = 0.0              # Tiến độ vòng hiện tại [0.0, 1.0]
        self.laps_completed = 0          # Số vòng đã hoàn thành
        self.finished = False            # Trạng thái về đích
        self.status = "STARTING"         # Trạng thái hiển thị
        self.current_compound = strategy[0][0]
        self.current_tyre_age = 1
        self.pit_count = 0

    def update(self, dt: float) -> None:
        """Cập nhật trạng thái xe sau khoảng thời gian dt thực (đã nhân time_scale)."""
        if self.finished:
            return

        self.elapsed = min(self.elapsed + dt * self.time_scale, self.total_race_time)

        if self.elapsed >= self.total_race_time:
            self.finished = True
            self.laps_completed = self.total_laps
            self.progress = 1.0
            self.status = "FINISHED"
            return

        # Tra cứu trạng thái hiện tại trong timeline
        current_event = None
        for event in self.timeline:
            if event["start"] <= self.elapsed < event["end"]:
                current_event = event
                break

        if current_event is None:
            current_event = self.timeline[-1]

        self.current_compound = current_event["compound"]
        self.current_tyre_age = current_event["tyre_age"]

        if current_event["type"] == "PIT":
            self.status = f"PIT (Lốp {self.current_compound})"
            # Khi ở trong pit lane, xe di chuyển chậm hoặc giữ nguyên mốc vạch pit
            self.progress = 0.05
        else:
            self.status = f"RACING ({self.current_compound} - T.{self.current_tyre_age})"
            lap_elapsed = self.elapsed - current_event["start"]
            lap_duration = current_event["duration"]
            self.progress = max(0.0, min(0.999, lap_elapsed / max(0.001, lap_duration)))
            self.laps_completed = current_event["lap"] - 1
