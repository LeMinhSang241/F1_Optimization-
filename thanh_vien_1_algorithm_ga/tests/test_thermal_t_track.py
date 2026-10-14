"""Kiểm thử tính đúng đắn của mô hình nhiệt động lực học bán thực nghiệm theo T_track.
Bảo đảm 100% tuân thủ công thức Mục 7.2 từ tài liệu TV3.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import numpy as np

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel, THERMAL_COEFFICIENTS


class TestThermalTrackTemperature(unittest.TestCase):
    """Kiểm thử mô hình độ nhạy nhiệt độ mặt đường T_track."""

    def test_nominal_temperature_preserves_coefficients(self):
        """Khi T_track == T_ref (30°C tại Monza), hệ số d1, d2 phải bằng giá trị danh định."""
        model = PirelliPhysicsTyreModel(track="Monza", t_track=30.0, t_ref=30.0)
        self.assertAlmostEqual(model.delta_t, 0.0, places=9)

        for c in ['Soft', 'Medium', 'Hard']:
            d1_adj, d2_adj = model.deg_coeffs[c]
            d1_nom, d2_nom = model.nominal_deg_coeffs[c]
            self.assertAlmostEqual(d1_adj, d1_nom, places=9)
            self.assertAlmostEqual(d2_adj, d2_nom, places=9)
            self.assertEqual(model.safe_limits[c], model.nominal_safe_limits[c])

    def test_cool_track_no_thermal_runaway(self):
        """Khi trời mát (T_track < T_ref, ví dụ 24°C): delta_T < 0, hàm phạt ReLU bình phương = 0."""
        model = PirelliPhysicsTyreModel(track="Monza", t_track=24.0, t_ref=30.0)
        delta_t_expected = (24.0 - 30.0) / 30.0  # -0.20
        self.assertAlmostEqual(model.delta_t, delta_t_expected, places=9)

        for c in ['Soft', 'Medium', 'Hard']:
            d1_adj, d2_adj = model.deg_coeffs[c]
            d1_nom, d2_nom = model.nominal_deg_coeffs[c]
            k1 = THERMAL_COEFFICIENTS[c]['kappa1']
            k2 = THERMAL_COEFFICIENTS[c]['kappa2']

            expected_d1 = d1_nom * (1.0 + k1 * delta_t_expected)
            expected_d2 = d2_nom * (1.0 + k2 * delta_t_expected)  # relu term = 0

            self.assertAlmostEqual(d1_adj, expected_d1, places=9)
            self.assertAlmostEqual(d2_adj, expected_d2, places=9)
            # Lốp mát hơn -> mòn ít hơn danh định
            self.assertLess(d1_adj, d1_nom)
            self.assertLess(d2_adj, d2_nom)

    def test_hot_track_quadratic_thermal_runaway(self):
        """Khi mặt đường quá nhiệt (T_track = 48°C > 30°C): kích hoạt ReLU bình phương mô tả rộp lốp (blistering)."""
        model = PirelliPhysicsTyreModel(track="Monza", t_track=48.0, t_ref=30.0)
        delta_t_expected = (48.0 - 30.0) / 30.0  # +0.60
        self.assertAlmostEqual(model.delta_t, delta_t_expected, places=9)

        for c in ['Soft', 'Medium', 'Hard']:
            d1_adj, d2_adj = model.deg_coeffs[c]
            d1_nom, d2_nom = model.nominal_deg_coeffs[c]
            k1 = THERMAL_COEFFICIENTS[c]['kappa1']
            k2 = THERMAL_COEFFICIENTS[c]['kappa2']
            th2 = THERMAL_COEFFICIENTS[c]['theta2']

            expected_d1 = d1_nom * (1.0 + k1 * delta_t_expected)
            expected_d2 = d2_nom * (1.0 + k2 * delta_t_expected + th2 * (delta_t_expected ** 2))

            self.assertAlmostEqual(d1_adj, expected_d1, places=9)
            self.assertAlmostEqual(d2_adj, expected_d2, places=9)
            # Tốc độ mòn tăng vọt (Hard tăng > 1.45x, Medium tăng > 2.0x, Soft tăng > 2.5x)
            self.assertGreater(d1_adj, d1_nom)
            self.assertGreater(d2_adj, d2_nom * 1.45)

    def test_heat_induced_cliff_reduction(self):
        """Khi nhiệt độ mặt đường tăng quá cao, tuổi thọ an toàn L_max phải bị co ngắn lại."""
        model_nominal = PirelliPhysicsTyreModel(track="Monza", t_track=30.0)
        model_hot = PirelliPhysicsTyreModel(track="Monza", t_track=45.0)  # delta_T = 0.50

        for c in ['Soft', 'Medium', 'Hard']:
            self.assertLess(
                model_hot.safe_limits[c],
                model_nominal.safe_limits[c],
                f"L_max của {c} không giảm khi mặt đường quá nhiệt!"
            )

    def test_dynamic_temperature_update(self):
        """Kiểm tra hàm set_track_temperature cập nhật động trạng thái."""
        model = PirelliPhysicsTyreModel(track="Monza", t_track=30.0)
        d1_30, d2_30 = model.deg_coeffs['Soft']

        model.set_track_temperature(42.0)
        d1_42, d2_42 = model.deg_coeffs['Soft']

        self.assertGreater(d1_42, d1_30)
        self.assertGreater(d2_42, d2_30)

    def test_extreme_cold_track_las_vegas_night(self):
        """Kiểm tra điều kiện rét buốt cực đoan (Las Vegas GP đêm, T_track = 12°C < T_ref = 30°C).
        delta_T = -0.60. Đảm bảo d1, d2 giữ chặn dưới vật lý strictly positive, không bị triệt tiêu về 0 hoặc âm.
        """
        model = PirelliPhysicsTyreModel(track="Monza", t_track=12.0, t_ref=30.0)
        self.assertAlmostEqual(model.delta_t, -0.60, places=5)

        for c in ['Soft', 'Medium', 'Hard']:
            d1_adj, d2_adj = model.deg_coeffs[c]
            d1_nom, d2_nom = model.nominal_deg_coeffs[c]

            # Phải duy trì mài mòn dương vật lý
            self.assertGreater(d1_adj, 0.0)
            self.assertGreater(d2_adj, 0.0)
            self.assertGreaterEqual(d1_adj, d1_nom * 0.20)
            self.assertGreaterEqual(d2_adj, d2_nom * 0.10)
            # Lốp lạnh mòn chậm hơn danh định
            self.assertLess(d1_adj, d1_nom)
            self.assertLess(d2_adj, d2_nom)

    def test_extreme_hot_track_scorching_desert(self):
        """Kiểm tra điều kiện mặt đường quá nhiệt cực đoan (T_track = 62°C, delta_T = +1.067).
        Kích hoạt bùng nổ nhiệt rộp lốp phi tuyến và suy giảm mạnh vách an toàn L_max.
        """
        model = PirelliPhysicsTyreModel(track="Monza", t_track=62.0, t_ref=30.0)
        self.assertGreater(model.delta_t, 1.0)

        for c in ['Soft', 'Medium', 'Hard']:
            d1_adj, d2_adj = model.deg_coeffs[c]
            d1_nom, d2_nom = model.nominal_deg_coeffs[c]
            nom_limit = model.nominal_safe_limits[c]
            curr_limit = model.safe_limits[c]

            self.assertGreater(d1_adj, d1_nom * 1.15)
            # Rộp lốp bùng nổ: Soft/Medium tăng > 2.5x, Hard chống chịu tốt hơn tăng > 1.8x
            min_mult = 2.5 if c in ['Soft', 'Medium'] else 1.8
            self.assertGreater(d2_adj, d2_nom * min_mult)
            self.assertLess(curr_limit, nom_limit)
            self.assertGreaterEqual(curr_limit, 8)    # Không vi phạm sàn an toàn tối thiểu 8 vòng


if __name__ == '__main__':
    unittest.main()
