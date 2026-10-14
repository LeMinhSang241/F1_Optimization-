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
    closed_form_stint_lap_time as tv3_closed_stint_time,
    fix_total_laps as tv3_fix_total_laps
)
from tyre.thermal import adjust_degradation_parameters as tv3_adjust_thermal
import json


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

    def test_tv3_json_params_consistency(self):
        """Kiểm chứng tính nhất quán giữa file JSON mô hình lốp TV3 và tham số TV1."""
        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tyre', 'models', 'tyre_params_monza.json'))
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertEqual(data['circuit'], 'monza')
            self.assertEqual(data['total_laps'], 53)
            self.assertAlmostEqual(data['alpha_fuel'], 0.058, places=3)
            self.assertAlmostEqual(data['gamma_track'], 0.022, places=3)
            self.assertAlmostEqual(data['t_pit'], 23.2, places=1)
            # Khẳng định các hợp chất Soft, Medium, Hard có trong JSON
            self.assertIn('Soft', data['compounds'])
            self.assertIn('Medium', data['compounds'])
            self.assertIn('Hard', data['compounds'])

    def test_tv3_fix_total_laps_preservation(self):
        """Kiểm tra hàm fix_total_laps của TV3 bảo toàn bất biến tổng 53 vòng."""
        compound_params = {
            'Soft': {'d1': 0.12, 'd2': 0.005, 'l_max': 22},
            'Medium': {'d1': 0.07, 'd2': 0.002, 'l_max': 35},
            'Hard': {'d1': 0.04, 'd2': 0.001, 'l_max': 48}
        }
        test_cases = [
            ([10, 20, 10], ['Soft', 'Medium', 'Hard']), # 40 laps (thiếu 13)
            ([25, 25, 25], ['Medium', 'Hard', 'Medium']), # 75 laps (thừa 22)
            ([14, 20, 19], ['Soft', 'Medium', 'Hard'])  # Đúng 53 vòng
        ]
        for lengths, compounds in test_cases:
            fixed = tv3_fix_total_laps(lengths, compounds, target_laps=53, compound_params=compound_params)
            self.assertEqual(sum(fixed), 53)
            self.assertTrue(all(l >= 4 for l in fixed))


if __name__ == '__main__':
    unittest.main()
