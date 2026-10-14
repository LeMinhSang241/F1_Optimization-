"""Trình mô phỏng chặng đua F1 (F1 Race Simulator).
Tính toán thời gian hoàn thành toàn bộ cuộc đua, tích hợp:
1. Đánh giá stint siêu tốc bằng công thức tổng đóng giải tích Faulhaber O(1).
2. Kiểm soát vách mòn lốp (Tyre Cliff Penalty) theo khuyến cáo an toàn Pirelli L_max.
3. Ràng buộc luật thể thao FIA (bắt buộc dùng tối thiểu 2 hợp chất lốp khô).
4. Tổn thất dừng pit và hiệu ứng khí bẩn / kẹt xe (Dirty Air / Traffic).

Phân công: Thành viên 1 (Algorithm & GA Lead) nâng cấp tích hợp tài liệu TV3.
"""

from typing import List, Tuple, Dict, Any, Optional
from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel


class F1RaceSimulator:
    """Mô phỏng chặng đua và đánh giá độ thích nghi (Fitness Evaluation) cho chiến lược pit-stop."""

    def __init__(
        self,
        total_laps: int = 53,
        pit_loss: float = 23.2,
        tyre_model: Optional[Any] = None,
        traffic_penalty: float = 0.0
    ):
        self.total_laps = total_laps
        self.pit_loss = pit_loss
        self.traffic_penalty = traffic_penalty
        self.tyre_model = tyre_model or PirelliPhysicsTyreModel()

    def evaluate_strategy(
        self,
        strategy: List[Tuple[str, int]],
        detailed: bool = False
    ) -> Tuple[float, Dict[str, Any]]:
        """Tính toán tổng thời gian hoàn thành chặng đua kèm hàm phạt nếu vi phạm luật FIA hoặc vách lốp.
        
        Args:
            strategy: Danh sách các stint [(compound, num_laps), ...]
            detailed: Nếu True, sinh chi tiết mảng lap_times từng vòng.
            
        Returns:
            (total_time_with_penalty, details_dict)
        """
        # Kiểm tra tính toàn vẹn tổng số vòng
        stint_sum = sum(length for _, length in strategy)
        lap_count_mismatch = (stint_sum != self.total_laps)

        total_time = 0.0
        compounds_used = set()
        lap_times: List[float] = []
        num_stops = max(0, len(strategy) - 1)
        curr_lap = 1

        has_closed_form = hasattr(self.tyre_model, 'closed_form_stint_lap_time')

        for compound, stint_length in strategy:
            compounds_used.add(compound)

            if detailed or not has_closed_form:
                # Mô phỏng chi tiết từng vòng lap-by-lap
                for age in range(1, stint_length + 1):
                    lap_t = self.tyre_model.predict_lap_time(
                        compound=compound,
                        tyre_age=age,
                        race_lap=curr_lap,
                        total_laps=self.total_laps
                    )
                    lap_times.append(lap_t)
                    total_time += lap_t
                    curr_lap += 1
            else:
                # Tính siêu tốc bằng giải tích đóng Faulhaber O(1)
                stint_time = self.tyre_model.closed_form_stint_lap_time(
                    compound=compound,
                    length=stint_length,
                    start_lap=curr_lap
                )
                total_time += stint_time
                curr_lap += stint_length

        # Tổn thất thời gian dừng pit
        pit_time_loss = num_stops * self.pit_loss
        total_time += pit_time_loss

        # Tổn thất kẹt xe / khí bẩn nếu có (Dirty Air Penalty)
        traffic_loss = (num_stops * self.traffic_penalty) if num_stops > 0 else 0.0
        total_time += traffic_loss

        # Hệ thống hàm phạt vật lý và thể thao (Penalties)
        penalty = 0.0

        # 1. Phạt nếu sai tổng cự ly chặng đua
        if lap_count_mismatch:
            penalty += abs(stint_sum - self.total_laps) * 500.0

        # 2. Ràng buộc FIA: Bắt buộc dùng ít nhất 2 loại hợp chất lốp khô khác nhau
        if len(compounds_used) < 2:
            penalty += 100000.0  # Phạt 10^5 giây loại trừ hoàn toàn

        # 3. Phạt Tyre Cliff (vượt ngưỡng tuổi thọ an toàn L_max của Pirelli)
        safe_limits = getattr(self.tyre_model, 'safe_limits', {'Soft': 22, 'Medium': 35, 'Hard': 48})
        for compound, length in strategy:
            limit = safe_limits.get(compound, 40)
            if length > limit:
                over = length - limit
                # Phạt tuyến tính kết hợp phi tuyến bậc hai mô tả vách đá tụt độ bám
                penalty += (over * 50.0 + (over ** 2) * 5.0)

        details = {
            'pure_race_time': total_time,
            'pit_time_loss': pit_time_loss,
            'traffic_loss': traffic_loss,
            'num_stops': num_stops,
            'compounds_used': list(compounds_used),
            'penalty': penalty,
            'is_valid_fia': len(compounds_used) >= 2,
            'lap_times': lap_times if detailed else []
        }

        return total_time + penalty, details
