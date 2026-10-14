"""Kiểm thử tính tương thích liên module giữa Thành viên 1 (DAGA-F1) và Thành viên 3 (Tyre Package).
Chứng minh mã nguồn của TV1 và TV3 khớp chính xác 100% về mặt toán học và vật lý.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import unittest

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
from tyre.derivatives import (
    marginal_degradation as tv3_marginal_deg,
    closed_form_stint_degradation as tv3_closed_deg,
    closed_form_stint_lap_time as tv3_closed_stint_time
)
from tyre.thermal import adjust_degradation_parameters as tv3_adjust_thermal


class TestTV3Interoperability(unittest.TestCase):
    """Kiểm thử đồng bộ hóa giữa TV1 và TV3."""

    def setUp(self):
        self.tv1_model = PirelliPhysicsTyreModel(track="Monza", t_track=30.0, t_ref=30.0)

    def test_marginal_degradation_matches_tv3(self):
        """So sánh đạo hàm mài mòn marginal_degradation giữa TV1 và TV3."""
        for c in ['Soft', 'Medium', 'Hard']:
            d1, d2 = self.tv1_model.deg_coeffs[c]
            for age in [1, 5, 12, 20, 30]:
                tv1_val = self.tv1_model.marginal_degradation(c, age)
                tv3_val = tv3_marginal_deg(float(age), d1, d2)
                self.assertAlmostEqual(tv1_val, tv3_val, places=10)

    def test_closed_form_stint_degradation_matches_tv3(self):
        """So sánh tổng mài mòn stint closed_form_stint_degradation giữa TV1 và TV3."""
        for c in ['Soft', 'Medium', 'Hard']:
            d1, d2 = self.tv1_model.deg_coeffs[c]
            for length in [5, 14, 20, 28]:
                tv1_val = self.tv1_model.closed_form_stint_degradation(c, length)
                tv3_val = tv3_closed_deg(length, d1, d2)
                self.assertAlmostEqual(tv1_val, tv3_val, places=10)

    def test_closed_form_stint_lap_time_matches_tv3(self):
        """So sánh thời gian stint closed_form_stint_lap_time giữa TV1 và TV3."""
        for c in ['Soft', 'Medium', 'Hard']:
            d1, d2 = self.tv1_model.deg_coeffs[c]
            t_base = self.tv1_model.base_times[c]
            alpha = self.tv1_model.alpha_fuel
            gamma = self.tv1_model.gamma_track

            for length, start_lap in [(20, 1), (14, 21), (19, 35)]:
                tv1_val = self.tv1_model.closed_form_stint_lap_time(c, length, start_lap)
                tv3_val = tv3_closed_stint_time(
                    length=length,
                    start_lap=start_lap,
                    total_race_laps=53,
                    t_base=t_base,
                    d1=d1,
                    d2=d2,
                    alpha_fuel=alpha,
                    gamma_track=gamma
                )
                self.assertAlmostEqual(tv1_val, tv3_val, places=9)

    def test_thermal_model_matches_tv3_equations(self):
        """So sánh điều chỉnh nhiệt độ mặt đường giữa TV1 và TV3."""
        for c in ['Soft', 'Medium', 'Hard']:
            d1_nom, d2_nom = self.tv1_model.nominal_deg_coeffs[c]
            for t_track in [30.0, 36.0, 45.0]:
                tv3_d1, tv3_d2 = tv3_adjust_thermal(c, d1_nom, d2_nom, t_track, t_ref=30.0)
                # Khởi tạo mô hình TV1 với nhiệt độ này
                tv1_m = PirelliPhysicsTyreModel(track="Monza", t_track=t_track, t_ref=30.0)
                tv1_d1, tv1_d2 = tv1_m.deg_coeffs[c]

                self.assertAlmostEqual(tv1_d1, tv3_d1, places=9)
                self.assertAlmostEqual(tv1_d2, tv3_d2, places=9)


if __name__ == '__main__':
    unittest.main()
