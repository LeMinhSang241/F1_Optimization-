"""Bộ kiểm thử đơn vị & kiểm chứng toàn diện cho các Toán tử Di truyền (GA Operators).
Kiểm tra tính đúng đắn toán học, độ bảo toàn bất biến, và tỷ lệ khả thi 100%.
Phân công: Thành viên 1 (Algorithm & GA Lead) - Đề án DS106 UIT 2026.
"""

import sys
import os
import random
import unittest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ga_strategy.operators import (
    COMPOUNDS,
    CLIFF_LIMITS,
    DEG_COEFFS,
    MIN_STINT_LENGTH,
    tyre_deg_derivative,
    physics_guided_repair,
    heuristic_weighted_initialization,
    adaptive_crossover,
    tri_level_mutation
)


class TestGAOperators(unittest.TestCase):
    """Kiểm thử chuyên sâu cho toàn bộ các hàm trong src/ga_strategy/operators.py."""

    def setUp(self):
        random.seed(42)
        np.random.seed(42)
        self.total_laps = 53

    def test_01_tyre_deg_derivative_analytical(self):
        """Kiểm tra đạo hàm giải tích \u2207t_deg(a) = d1 + 2*d2*a theo chuẩn Pirelli 2023."""
        # Soft: d1=0.120, d2=0.0050. Tại a=10: 0.120 + 2*0.0050*10 = 0.220
        grad_soft = tyre_deg_derivative('Soft', 10)
        self.assertAlmostEqual(grad_soft, 0.220, places=5)

        # Medium: d1=0.070, d2=0.0020. Tại a=15: 0.070 + 2*0.0020*15 = 0.130
        grad_med = tyre_deg_derivative('Medium', 15)
        self.assertAlmostEqual(grad_med, 0.130, places=5)

        # Hard: d1=0.040, d2=0.0010. Tại a=20: 0.040 + 2*0.0010*20 = 0.080
        grad_hard = tyre_deg_derivative('Hard', 20)
        self.assertAlmostEqual(grad_hard, 0.080, places=5)

        # Đạo hàm phải tăng đơn điệu theo tuổi lốp (mòn phi tuyến)
        self.assertGreater(tyre_deg_derivative('Soft', 15), tyre_deg_derivative('Soft', 5))
        self.assertGreater(tyre_deg_derivative('Medium', 20), tyre_deg_derivative('Medium', 10))

    def test_02_physics_repair_10000_random_chromosomes(self):
        """Kiểm tra 10.000 cá thể ngẫu nhiên / dị tật qua bộ sửa chữa vật lý:
        100% cá thể đầu ra phải đạt chuẩn: sum == 53, |{compounds}| >= 2, min_length >= 4.
        """
        num_tests = 10000
        infeasible_count = 0

        for _ in range(num_tests):
            # Sinh cá thể ngẫu nhiên với độ biến thiên cực đoan
            num_stints = random.randint(1, 7)
            raw_strat = []
            for _ in range(num_stints):
                comp = random.choice(COMPOUNDS)
                # Chiều dài bất kỳ (âm, 0, hoặc cực lớn)
                length = random.randint(-5, 90)
                raw_strat.append((comp, length))

            # 20% cá thể bị ép dùng duy nhất 1 loại lốp để test FIA rule
            if random.random() < 0.20:
                mono_comp = random.choice(COMPOUNDS)
                raw_strat = [(mono_comp, l) for _, l in raw_strat]

            # Thực thi sửa chữa vật lý
            repaired = physics_guided_repair(raw_strat, total_laps=self.total_laps)

            # Kiểm tra 3 điều kiện tiên quyết
            total = sum(l for _, l in repaired)
            compounds = {c for c, _ in repaired}
            min_l = min(l for _, l in repaired)

            if total != self.total_laps or len(compounds) < 2 or min_l < MIN_STINT_LENGTH:
                infeasible_count += 1

        self.assertEqual(infeasible_count, 0, f"Có {infeasible_count} / {num_tests} cá thể bất khả thi!")
        feasibility_rate = (num_tests - infeasible_count) / num_tests * 100.0
        self.assertEqual(feasibility_rate, 100.0)

    def test_03_heuristic_initialization_distribution(self):
        """Kiểm tra phân phối khởi tạo có trọng số (65% 1-stop, 30% 2-stop, 5% 3-stop)."""
        pop_size = 1000
        pop = heuristic_weighted_initialization(pop_size, total_laps=self.total_laps)
        
        self.assertEqual(len(pop), pop_size)

        c_1stop = sum(1 for ind in pop if len(ind) == 2)
        c_2stop = sum(1 for ind in pop if len(ind) == 3)
        c_3stop = sum(1 for ind in pop if len(ind) == 4)

        # 65% +/- 5%, 30% +/- 5%, 5% +/- 3%
        self.assertTrue(600 <= c_1stop <= 700, f"1-stop count: {c_1stop}")
        self.assertTrue(250 <= c_2stop <= 350, f"2-stop count: {c_2stop}")
        self.assertTrue(20 <= c_3stop <= 80, f"3-stop count: {c_3stop}")

        # Toàn bộ cá thể trong quần thể phải hợp lệ 100%
        for ind in pop:
            self.assertEqual(sum(l for _, l in ind), self.total_laps)
            self.assertGreaterEqual(len({c for c, _ in ind}), 2)
            self.assertGreaterEqual(min(l for _, l in ind), MIN_STINT_LENGTH)

    def test_04_macro_mutation_split_and_merge(self):
        """Kiểm tra cơ chế đột biến đa hình thái Split Stint và Merge Stint."""
        # Test 1: Cá thể 1-stop (2 stints) khi bị đột biến Macro PHẢI chuyển thành 2-stop (3 stints)
        strat_1stop = [('Medium', 28), ('Hard', 25)]
        split_success = 0
        for _ in range(50):
            # Ép gọi đột biến với pm=1.0 và random choice ở cấp độ Macro (>=0.85)
            mutated = tri_level_mutation(strat_1stop, total_laps=self.total_laps, pm=1.0)
            if len(mutated) == 3:
                split_success += 1
                self.assertEqual(sum(l for _, l in mutated), 53)
                self.assertGreaterEqual(len({c for c, _ in mutated}), 2)
        self.assertGreater(split_success, 0, "Cá thể 1-stop phải có khả năng Split thành 2-stop")

        # Test 2: Cá thể 3-stop (4 stints) khi bị đột biến Macro PHẢI chuyển thành ít stint hơn (Merge)
        strat_3stop = [('Soft', 12), ('Medium', 14), ('Medium', 14), ('Soft', 13)]
        merge_success = 0
        for _ in range(50):
            mutated = tri_level_mutation(strat_3stop, total_laps=self.total_laps, pm=1.0)
            if len(mutated) < 4:
                merge_success += 1
                self.assertEqual(sum(l for _, l in mutated), 53)
                self.assertGreaterEqual(len({c for c, _ in mutated}), 2)
        self.assertGreater(merge_success, 0, "Cá thể 3-stop phải có khả năng Merge thành 2-stop")

    def test_05_adaptive_crossover_integrity(self):
        """Kiểm tra tính toàn vẹn của phép lai ghép trên cả cha mẹ cùng và khác số stint."""
        # 1. Cùng số stint (2-stop và 2-stop)
        p1 = [('Medium', 20), ('Hard', 18), ('Soft', 15)]
        p2 = [('Soft', 14), ('Medium', 20), ('Medium', 19)]
        c1, c2 = adaptive_crossover(p1, p2, total_laps=53, pc=1.0)
        self.assertEqual(sum(l for _, l in c1), 53)
        self.assertEqual(sum(l for _, l in c2), 53)
        self.assertGreaterEqual(len({c for c, _ in c1}), 2)
        self.assertGreaterEqual(len({c for c, _ in c2}), 2)

        # 2. Khác số stint (1-stop vs 2-stop)
        p3 = [('Medium', 26), ('Hard', 27)]
        p4 = [('Soft', 15), ('Medium', 20), ('Hard', 18)]
        c3, c4 = adaptive_crossover(p3, p4, total_laps=53, pc=1.0)
        self.assertEqual(sum(l for _, l in c3), 53)
        self.assertEqual(sum(l for _, l in c4), 53)
        self.assertGreaterEqual(len({c for c, _ in c3}), 2)
        self.assertGreaterEqual(len({c for c, _ in c4}), 2)

    def test_06_repair_small_and_extreme_lap_counts(self):
        """Kiểm tra độ bền của physics_guided_repair trước các bài toán con có số vòng nhỏ (SC laps) và cực đoan."""
        test_laps = [1, 2, 3, 5, 7, 8, 12, 53, 78]
        test_inputs = [
            [],
            [('Soft', 100)],
            [('Medium', -10)],
            [('Hard', 1), ('Soft', 1)],
            [('Soft', 50), ('Medium', 50), ('Hard', 50)]
        ]

        for laps in test_laps:
            for raw in test_inputs:
                repaired = physics_guided_repair(raw, total_laps=laps)
                self.assertEqual(sum(l for _, l in repaired), laps, f"Laps={laps}, raw={raw}")
                # Đảm bảo không có stint nào mang độ dài <= 0
                for comp, length in repaired:
                    self.assertGreaterEqual(length, 1, f"Stint length phai >= 1, nhung nhan duoc {length} o {comp}")

    def test_07_silverstone_physics_parameters(self):
        """Kiểm tra tính năng hỗ trợ đa chặng đua: Đạo hàm giải tích với thông số Silverstone GP."""
        # Silverstone Soft: d1=0.145, d2=0.0065. Tại age=10: 0.145 + 2*0.0065*10 = 0.275
        silverstone_coeffs = {
            'Soft': (0.145, 0.0065),
            'Medium': (0.085, 0.0028),
            'Hard': (0.050, 0.0014)
        }
        grad_soft = tyre_deg_derivative('Soft', 10, deg_coeffs=silverstone_coeffs)
        self.assertAlmostEqual(grad_soft, 0.275, places=5)

        grad_med = tyre_deg_derivative('Medium', 10, deg_coeffs=silverstone_coeffs)
        self.assertAlmostEqual(grad_med, 0.141, places=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
