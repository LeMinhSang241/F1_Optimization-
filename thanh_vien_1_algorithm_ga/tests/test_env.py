import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from src.tyre_model.rcga_ensemble import RealValuedGATyreEnsemble
from src.simulator.race_sim import F1RaceSimulator
from src.ga_strategy.operators import (
    heuristic_weighted_initialization,
    repair_operator,
    adaptive_crossover,
    adaptive_mutation
)
from src.ga_strategy.optimizer import F1StrategyGAOptimizer


class TestEnvironmentAndSmoke(unittest.TestCase):
    """Bộ kiểm thử môi trường và chạy khói tích hợp (Smoke Tests)."""

    def test_01_tyre_model_prediction(self):
        """Kiểm tra mô hình dự đoán mòn lốp."""
        model = RealValuedGATyreEnsemble()
        t_soft_new = model.predict_lap_time('Soft', tyre_age=1, race_lap=1, total_laps=53)
        t_soft_old = model.predict_lap_time('Soft', tyre_age=15, race_lap=15, total_laps=53)
        self.assertGreater(t_soft_old, t_soft_new, "Lốp cũ phải chạy chậm hơn lốp mới")

    def test_02_simulator_fia_rule(self):
        """Kiểm tra cơ chế phạt khi vi phạm luật FIA (chỉ dùng 1 loại lốp)."""
        sim = F1RaceSimulator(total_laps=53, pit_loss=23.2)
        # Chiến lược phạm luật: chỉ dùng Soft
        illegal_strat = [('Soft', 53)]
        total_time, details = sim.evaluate_strategy(illegal_strat)
        self.assertFalse(details['is_valid_fia'], "Chiến lược 1 loại lốp phải vi phạm luật FIA")
        self.assertGreaterEqual(details['penalty'], 100000.0, "Phải bị phạt 10^5 giây")

        # Chiến lược hợp lệ: Soft + Hard
        legal_strat = [('Soft', 20), ('Hard', 33)]
        total_time_legal, details_legal = sim.evaluate_strategy(legal_strat)
        self.assertTrue(details_legal['is_valid_fia'], "Chiến lược dùng 2 loại lốp phải hợp lệ")
        self.assertEqual(details_legal['penalty'], 0.0, "Không được bị phạt")

    def test_03_repair_operator(self):
        """Kiểm tra toán tử sửa chữa luôn bảo toàn tổng số vòng đua."""
        strat = [('Soft', 15), ('Hard', 30)]  # Tổng 45 vòng, thiếu 8 vòng
        repaired = repair_operator(strat, total_laps=53)
        total_laps = sum(length for _, length in repaired)
        self.assertEqual(total_laps, 53, f"Tổng số vòng sau khi sửa phải đúng 53, nhưng nhận được {total_laps}")

    def test_04_ga_optimizer_run(self):
        """Kiểm tra chạy nhanh bộ tối ưu hóa GA trong 3 thế hệ."""
        sim = F1RaceSimulator(total_laps=53, pit_loss=23.2)
        opt = F1StrategyGAOptimizer(simulator=sim, pop_size=10, generations=3)
        best_strat, best_time, details = opt.optimize()

        self.assertIsNotNone(best_strat)
        self.assertEqual(sum(l for _, l in best_strat), 53)
        self.assertTrue(details['is_valid_fia'])
        self.assertLess(best_time, 50000)  # Nghiệm hợp lệ không bị dính penalty lớn


if __name__ == '__main__':
    unittest.main()
