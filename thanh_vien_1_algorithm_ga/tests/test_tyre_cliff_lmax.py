"""Kiểm thử cơ chế kiểm soát vách lốp an toàn L_max (Tyre Cliff Control).
Bảo đảm 100% tuân thủ mục 2.4, 2.5 và 5.5 từ tài liệu TV3.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
from src.simulator.race_sim import F1RaceSimulator
from src.ga_strategy.operators import physics_guided_repair, CLIFF_LIMITS, DEG_COEFFS


class TestTyreCliffAndLMax(unittest.TestCase):
    """Kiểm thử cơ chế bảo vệ trước vách mòn lốp Tyre Cliff."""

    def setUp(self):
        self.model = PirelliPhysicsTyreModel(track="Monza")
        self.sim = F1RaceSimulator(total_laps=53, pit_loss=23.2, tyre_model=self.model)

    def test_pirelli_cliff_limits_values(self):
        """Khẳng định ngưỡng an toàn vách lốp chuẩn Monza: Soft=22, Medium=35, Hard=48."""
        self.assertEqual(self.model.get_safe_limit('Soft'), 22)
        self.assertEqual(self.model.get_safe_limit('Medium'), 35)
        self.assertEqual(self.model.get_safe_limit('Hard'), 48)

    def test_simulator_zero_penalty_within_cliff_limits(self):
        """Chiến lược hợp lệ nằm dưới L_max không bị phạt vách lốp."""
        # Medium 20 (<= 35), Soft 14 (<= 22), Medium 19 (<= 35) -> Tổng 53 vòng
        strat = [('Medium', 20), ('Soft', 14), ('Medium', 19)]
        score, details = self.sim.evaluate_strategy(strat)

        self.assertEqual(details['penalty'], 0.0)
        self.assertTrue(details['is_valid_fia'])
        self.assertAlmostEqual(score, details['pure_race_time'], places=5)

    def test_simulator_quadratic_penalty_exceeding_cliff(self):
        """Chiến lược chạy quá L_max bị phạt theo cấp số bậc hai mô tả sự sụp đổ độ bám."""
        # Soft chạy 26 vòng (vượt L_max=22 mất 4 vòng), Hard chạy 27 vòng (<= 48)
        over = 4
        expected_cliff_penalty = over * 50.0 + (over ** 2) * 5.0  # 4*50 + 16*5 = 200 + 80 = 280s

        strat = [('Soft', 26), ('Hard', 27)]
        score, details = self.sim.evaluate_strategy(strat)

        self.assertAlmostEqual(details['penalty'], expected_cliff_penalty, places=5)
        self.assertGreater(score, details['pure_race_time'])

    def test_physics_guided_repair_pulls_back_from_cliff(self):
        """Toán tử sửa chữa định hướng vật lý tự động kéo bớt vòng ở stint vượt L_max."""
        # Cá thể ban đầu Soft 26 (vượt L_max=22), Hard 27
        individual = [('Soft', 26), ('Hard', 27)]
        # Giả sử cần thêm vòng do chặng 55 vòng
        repaired = physics_guided_repair(individual, total_laps=53, cliff_limits=CLIFF_LIMITS, deg_coeffs=DEG_COEFFS)

        # Soft phải được co lại về mức an toàn hơn
        soft_len = next(length for c, length in repaired if c == 'Soft')
        hard_len = next(length for c, length in repaired if c == 'Hard')

        self.assertLessEqual(soft_len, 22, f"Soft sau sửa chữa vẫn vượt quá L_max=22: {soft_len}")
        self.assertEqual(soft_len + hard_len, 53)

    def test_physics_guided_repair_deficiency_allocation(self):
        """Khi thiếu vòng (ΔN > 0), toán tử ưu tiên bù vòng vào hợp chất mòn chậm nhất và xa vách lốp nhất."""
        # Ban đầu chỉ có 45 vòng, thiếu 8 vòng
        individual = [('Soft', 15), ('Hard', 30)]
        repaired = physics_guided_repair(individual, total_laps=53, cliff_limits=CLIFF_LIMITS, deg_coeffs=DEG_COEFFS)

        self.assertEqual(sum(l for _, l in repaired), 53)
        soft_len = next(l for c, l in repaired if c == 'Soft')
        hard_len = next(l for c, l in repaired if c == 'Hard')

        # Hard có dung sai (48 - 30 = 18) và gradient mài mòn thấp hơn Soft -> Hard phải nhận đa số vòng bù
        self.assertGreater(hard_len - 30, soft_len - 15)


if __name__ == '__main__':
    unittest.main()
