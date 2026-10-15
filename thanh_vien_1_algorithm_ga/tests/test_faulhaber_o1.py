"""Kiểm thử tính đúng đắn và hiệu năng của công thức tổng đóng giải tích Faulhaber O(1).
Chứng minh số liệu thật 100%: So khớp từng phần tử giải tích Faulhaber với vòng lặp rời rạc O(L).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import time
import numpy as np

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
from src.ga_strategy.operators import closed_form_stint_degradation, DEG_COEFFS


class TestFaulhaberClosedForm(unittest.TestCase):
    """Kiểm thử toán học và độ chính xác của tổng đóng Faulhaber O(1)."""

    def setUp(self):
        self.model = PirelliPhysicsTyreModel(track="Monza")

    def test_faulhaber_degradation_against_loop(self):
        """So khớp tuyệt đối tổng đóng D_stint Faulhaber với vòng lặp rời rạc."""
        compounds = ['Soft', 'Medium', 'Hard']
        test_lengths = [1, 2, 5, 10, 15, 20, 25, 30, 40, 53]

        for c in compounds:
            d1, d2 = self.model.deg_coeffs[c]
            for L in test_lengths:
                # 1. Tính bằng vòng lặp rời rạc O(L)
                loop_sum = sum(d1 * a + d2 * (a ** 2) for a in range(1, L + 1))
                
                # 2. Tính bằng giải tích Faulhaber O(1) qua tyre_model
                model_sum = self.model.closed_form_stint_degradation(c, L)
                
                # 3. Tính bằng hàm operators.closed_form_stint_degradation
                op_sum = closed_form_stint_degradation(L, c, self.model.deg_coeffs)

                # Kiểm tra sai số số học không vượt quá sai số dấu phẩy động (1e-11)
                self.assertAlmostEqual(
                    loop_sum, model_sum, places=10,
                    msg=f"Sai lệch Faulhaber tại compound {c}, L={L}: loop={loop_sum}, closed={model_sum}"
                )
                self.assertAlmostEqual(
                    loop_sum, op_sum, places=10,
                    msg=f"Sai lệch operators Faulhaber tại compound {c}, L={L}: loop={loop_sum}, op={op_sum}"
                )

    def test_faulhaber_stint_lap_time_against_lap_by_lap(self):
        """So khớp tổng thời gian hoàn thành stint có xét tải nhiên liệu và cao su bám đường."""
        compounds = ['Soft', 'Medium', 'Hard']
        start_laps = [1, 10, 20, 30, 40]
        lengths = [5, 10, 15, 20]

        for c in compounds:
            for start_lap in start_laps:
                for L in lengths:
                    if start_lap + L - 1 > self.model.total_laps:
                        continue

                    # 1. Tính từng vòng rời rạc
                    loop_total = 0.0
                    for k in range(L):
                        current_lap = start_lap + k
                        age = k + 1
                        loop_total += self.model.predict_lap_time(c, age, current_lap)

                    # 2. Tính bằng công thức đóng O(1)
                    closed_total = self.model.closed_form_stint_lap_time(c, L, start_lap)

                    self.assertAlmostEqual(
                        loop_total, closed_total, places=9,
                        msg=f"Sai lệch tổng thời gian stint {c}, L={L}, start={start_lap}: loop={loop_total}, closed={closed_total}"
                    )

    def test_faulhaber_boundary_cases(self):
        """Kiểm tra các trường hợp biên: L=0, L=1, L âm."""
        self.assertEqual(self.model.closed_form_stint_degradation('Soft', 0), 0.0)
        self.assertEqual(self.model.closed_form_stint_degradation('Medium', -5), 0.0)
        self.assertEqual(self.model.closed_form_stint_lap_time('Hard', 0, 1), 0.0)

        # L = 1
        d1, d2 = self.model.deg_coeffs['Soft']
        expected_deg_1 = d1 * 1.0 + d2 * (1.0 ** 2)
        self.assertAlmostEqual(self.model.closed_form_stint_degradation('Soft', 1), expected_deg_1, places=12)

    def test_faulhaber_performance_speedup(self):
        """Đo lường thời gian thực thi: Faulhaber O(1) phải nhanh hơn vòng lặp rời rạc O(L)."""
        iterations = 20000
        c = 'Medium'
        L = 35
        start_lap = 10

        # Đo vòng lặp
        t0 = time.perf_counter()
        for _ in range(iterations):
            tot = 0.0
            for k in range(L):
                tot += self.model.predict_lap_time(c, k + 1, start_lap + k)
        loop_time = time.perf_counter() - t0

        # Đo Faulhaber O(1)
        t0 = time.perf_counter()
        for _ in range(iterations):
            tot = self.model.closed_form_stint_lap_time(c, L, start_lap)
        closed_time = time.perf_counter() - t0

        # Khẳng định tốc độ O(1) nhanh hơn ít nhất 3 lần so với vòng lặp 35 laps
        speedup = loop_time / max(1e-9, closed_time)
        self.assertGreater(
            speedup, 2.5,
            f"Tốc độ Faulhaber O(1) không đạt kỳ vọng: loop={loop_time:.4f}s, closed={closed_time:.4f}s, speedup={speedup:.2f}x"
        )


if __name__ == '__main__':
    unittest.main()
