"""Bộ kiểm thử chuyên sâu cho Toán tử Đột biến Đa hình thái 3 Cấp độ (Tri-Level Polymorphic Mutation).
Tập trung kiểm chứng cơ chế Split Stint / Merge Stint tự động tiến hóa số lần dừng pit K ∈ {1, 2, 3}.
Deliverable Tuần 3: Thành viên 1 (Algorithm & GA Lead) - Đề án DS106 UIT 2026.
"""

import sys
import os
import unittest
import random
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ga_strategy.operators import (
    COMPOUNDS,
    MIN_STINT_LENGTH,
    tri_level_mutation,
    physics_guided_repair
)


class TestMutationSplitMerge(unittest.TestCase):
    """Kiểm chứng tính toàn vẹn và động lực học tiến hóa của đột biến Macro Split/Merge."""

    def setUp(self):
        random.seed(42)
        np.random.seed(42)
        self.total_laps = 53

    def test_01_single_stint_split(self):
        """Kiểm tra cá thể 1 stint (ví dụ sau SC hoặc bài toán con) có thể Split thành 2 stints mà không gây lỗi."""
        strat = [('Hard', 30)]
        split_count = 0
        for _ in range(50):
            mutated = tri_level_mutation(strat, total_laps=30, pm=1.0, min_compounds=1, min_stints=1)
            self.assertEqual(sum(l for _, l in mutated), 30)
            self.assertGreaterEqual(min(l for _, l in mutated), 1)
            if len(mutated) == 2:
                split_count += 1
        self.assertGreater(split_count, 0, "Cá thể 1 stint dài phải có khả năng Split thành 2 stints")

    def test_02_1stop_to_2stop_split(self):
        """Kiểm tra đột biến Split Stint biến đổi cá thể 1-stop (2 stints) thành 2-stop (3 stints)."""
        strat_1stop = [('Medium', 28), ('Hard', 25)]
        split_success = 0
        for _ in range(100):
            mutated = tri_level_mutation(strat_1stop, total_laps=self.total_laps, pm=1.0)
            self.assertEqual(sum(l for _, l in mutated), self.total_laps)
            self.assertGreaterEqual(len({c for c, _ in mutated}), 2)
            if len(mutated) == 3:
                split_success += 1
                # Kiểm tra mỗi stint sau split đều >= MIN_STINT_LENGTH
                for _, length in mutated:
                    self.assertGreaterEqual(length, MIN_STINT_LENGTH)

        self.assertGreater(split_success, 0, "Phải có ít nhất một lần Split thành công từ 1-stop sang 2-stop")

    def test_03_2stop_bidirectional_transitions(self):
        """Kiểm tra cá thể 2-stop (3 stints) có thể vừa Split lên 3-stop vừa Merge về 1-stop."""
        strat_2stop = [('Soft', 14), ('Medium', 20), ('Medium', 19)]
        split_to_3stop = 0
        merge_to_1stop = 0

        for _ in range(150):
            mutated = tri_level_mutation(strat_2stop, total_laps=self.total_laps, pm=1.0)
            self.assertEqual(sum(l for _, l in mutated), self.total_laps)
            self.assertGreaterEqual(len({c for c, _ in mutated}), 2)
            if len(mutated) == 4:
                split_to_3stop += 1
            elif len(mutated) == 2:
                merge_to_1stop += 1

        self.assertGreater(split_to_3stop, 0, "Cá thể 2-stop phải có khả năng Split lên 3-stop (4 stints)")
        self.assertGreater(merge_to_1stop, 0, "Cá thể 2-stop phải có khả năng Merge về 1-stop (2 stints)")

    def test_04_3stop_to_fewer_stops_merge(self):
        """Kiểm tra cá thể 3-stop (4 stints) khi bị đột biến Macro bắt buộc phải Merge về ít stint hơn."""
        strat_3stop = [('Soft', 10), ('Medium', 15), ('Soft', 12), ('Medium', 16)]
        merge_count = 0

        for _ in range(100):
            mutated = tri_level_mutation(strat_3stop, total_laps=self.total_laps, pm=1.0)
            self.assertEqual(sum(l for _, l in mutated), self.total_laps)
            self.assertGreaterEqual(len({c for c, _ in mutated}), 2)
            if len(mutated) < 4:
                merge_count += 1

        self.assertGreater(merge_count, 0, "Cá thể 3-stop phải Merge về <= 3 stints")

    def test_05_extreme_boundary_and_random_stability(self):
        """Kiểm tra tính ổn định tuyệt đối: 2.000 lần đột biến liên tục không xuất hiện ngoại lệ hoặc dị tật."""
        current = [('Medium', 26), ('Hard', 27)]
        for _ in range(2000):
            current = tri_level_mutation(current, total_laps=self.total_laps, pm=0.5)
            self.assertEqual(sum(l for _, l in current), self.total_laps)
            self.assertGreaterEqual(len({c for c, _ in current}), 2)
            self.assertGreaterEqual(min(l for _, l in current), MIN_STINT_LENGTH)
            self.assertTrue(1 <= len(current) - 1 <= 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
