"""Bộ giải Quy hoạch Động Bellman (Bellman Dynamic Programming Solver).
Tìm nghiệm tối ưu toàn cục chính xác tuyệt đối (Ground Truth Global Optimum) làm thước đo chuẩn cho DAGA-F1.
Tích hợp:
1. Mô hình lốp giải tích Pirelli & hiệu chỉnh nhiệt độ mặt đường T_track.
2. Quy nạp ngược Backward Induction đảm bảo nguyên lý tối ưu Bellman.
3. Ràng buộc luật thể thao FIA (bitmask hợp chất) và vách an toàn L_max.

Phân công: Bàn giao đối chuẩn từ Thành viên 3 (DP Lead) tích hợp vào hệ thống Thành viên 1.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel


COMPOUNDS = ['Soft', 'Medium', 'Hard']
COMPOUND_MAP = {'Soft': 0, 'Medium': 1, 'Hard': 2}
INV_COMPOUND_MAP = {0: 'Soft', 1: 'Medium', 2: 'Hard'}


class BellmanDPSolver:
    """Bộ giải Quy hoạch động tìm nghiệm tối ưu toàn cục cho chiến lược đua F1."""

    def __init__(
        self,
        tyre_model: Optional[PirelliPhysicsTyreModel] = None,
        traffic_penalty: float = 0.0
    ):
        self.model = tyre_model or PirelliPhysicsTyreModel()
        self.N = self.model.total_laps
        self.pit_loss = self.model.pit_loss
        self.traffic_penalty = traffic_penalty
        self.safe_limits = [self.model.get_safe_limit(c) for c in COMPOUNDS]

    def solve(self, max_stops: int = 2) -> Tuple[float, List[Tuple[str, int]]]:
        """Giải bài toán bằng phương pháp quy nạp ngược (Backward Induction).
        
        Trạng thái: (lap, compound, age, stops, fia_mask)
        Trong đó:
            - lap: 1 .. N
            - compound: 0 (Soft), 1 (Medium), 2 (Hard)
            - age: 1 .. min(lap, safe_limit)
            - stops: 0 .. max_stops
            - fia_mask: bitmask đại diện các hợp chất đã dùng (1 .. 7)
        """
        prev_V: Dict[Tuple[int, int, int, int], float] = {}
        for c in range(3):
            for a in range(1, self.safe_limits[c] + 1):
                for k in range(max_stops + 1):
                    for m in range(1, 8):
                        popcount = bin(m).count('1')
                        prev_V[(c, a, k, m)] = 0.0 if popcount >= 2 else 1e9

        actions: Dict[Tuple[int, int, int, int, int], Tuple[str, int]] = {}

        # Quy nạp ngược từ vòng N về vòng 1
        for lap in range(self.N, 0, -1):
            curr_V: Dict[Tuple[int, int, int, int], float] = {}
            for c in range(3):
                comp_name = INV_COMPOUND_MAP[c]
                safe_lim = min(lap, self.safe_limits[c])
                for a in range(1, safe_lim + 1):
                    t_lap = self.model.predict_lap_time(comp_name, a, lap)
                    for k in range(max_stops + 1):
                        for m in range(1, 8):
                            # Lựa chọn 1: Chạy tiếp (Stay)
                            best_val = 1e9
                            best_act = ("STAY", c)
                            if a < self.safe_limits[c]:
                                val_stay = t_lap + prev_V.get((c, a + 1, k, m), 1e9)
                                if val_stay < best_val:
                                    best_val = val_stay
                                    best_act = ("STAY", c)

                            # Lựa chọn 2: Vào pit đổi sang hợp chất khác c' (Pit)
                            if a >= 4 and k < max_stops:
                                for next_c in range(3):
                                    if next_c != c:
                                        next_m = m | (1 << next_c)
                                        penalty_traffic = self.traffic_penalty if k >= 1 else 0.0
                                        val_pit = (
                                            t_lap
                                            + self.pit_loss
                                            + penalty_traffic
                                            + prev_V.get((next_c, 1, k + 1, next_m), 1e9)
                                        )
                                        if val_pit < best_val:
                                            best_val = val_pit
                                            best_act = ("PIT", next_c)

                            curr_V[(c, a, k, m)] = best_val
                            actions[(lap, c, a, k, m)] = best_act

            prev_V = curr_V

        # Tìm hợp chất xuất phát tối ưu ở vòng 1
        best_total_time = 1e9
        best_start = (0, 1, 0, 1)
        for c in range(3):
            init_state = (c, 1, 0, 1 << c)
            if prev_V.get(init_state, 1e9) < best_total_time:
                best_total_time = prev_V[init_state]
                best_start = init_state

        # Tái thiết kế chiến lược tối ưu (Strategy Reconstruction)
        strategy = []
        curr_c, curr_a, curr_k, curr_m = best_start
        stint_len = 0
        current_stint_comp = INV_COMPOUND_MAP[curr_c]

        for lap in range(1, self.N + 1):
            act_type, next_comp = actions[(lap, curr_c, curr_a, curr_k, curr_m)]
            stint_len += 1
            if act_type == "PIT" or lap == self.N:
                strategy.append((current_stint_comp, stint_len))
                if act_type == "PIT":
                    curr_c = next_comp
                    current_stint_comp = INV_COMPOUND_MAP[curr_c]
                    curr_a = 1
                    curr_k += 1
                    curr_m |= (1 << curr_c)
                    stint_len = 0
            else:
                curr_a += 1

        return best_total_time, strategy
