"""Mô hình Động lực học & Suy giảm Hiệu suất Lốp Giải tích Pirelli (Pirelli Physics Tyre Model).
Chuẩn hóa vật lý theo dữ liệu thực nghiệm F1 2023 và tài liệu kỹ thuật TV3 (WLS-Tikhonov & Thermal Dynamics).
Tích hợp:
1. Mô hình nhiệt động lực học bán thực nghiệm theo nhiệt độ mặt đường T_track.
2. Công thức tổng đóng giải tích Faulhaber O(1) cho stint.
3. Đạo hàm giải tích mài mòn bậc 1 nabla t_deg(a) và bậc 2 nabla^2 t_deg(a).
4. Kiểm soát vách mòn lốp an toàn L_max (Tyre Cliff).

Phân công: Thành viên 1 (GA Lead) tích hợp bàn giao kỹ thuật từ Thành viên 3 (Tyre Modeler).
"""

from typing import Dict, Tuple, Optional, Union
import numpy as np


# Hệ số nhạy nhiệt độ bán thực nghiệm từ TV3 (Mục 7.2 tài liệu kỹ thuật)
THERMAL_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    'Soft': {'kappa1': 0.30, 'kappa2': 1.80, 'theta2': 1.20},
    'Medium': {'kappa1': 0.25, 'kappa2': 1.20, 'theta2': 0.80},
    'Hard': {'kappa1': 0.15, 'kappa2': 0.60, 'theta2': 0.30}
}


class PirelliPhysicsTyreModel:
    """Mô hình suy giảm hiệu suất lốp giải tích bậc hai Pirelli kết hợp tiêu hao xăng,
    cao su mặt đường và hiệu chỉnh nhiệt độ mặt đường T_track.
    """

    def __init__(
        self,
        track: str = "Monza",
        t_track: Optional[float] = None,
        t_ref: Optional[float] = None
    ):
        self.track = track

        if track == "Monza":
            self.total_laps = 53
            self.pit_loss = 23.2
            self.alpha_fuel = 0.058   # Giảm ~0.058s/vòng khi xe nhẹ xăng
            self.gamma_track = 0.022  # Nhanh thêm ~0.022s/vòng khi mặt đường bám cao su
            self.t_ref = t_ref if t_ref is not None else 30.0  # Nhiệt độ tham chiếu tiêu chuẩn Monza (°C)
            self.base_times = {'Soft': 81.50, 'Medium': 82.20, 'Hard': 83.00}
            self.nominal_deg_coeffs = {
                'Soft': (0.120, 0.0050),    # d1, d2
                'Medium': (0.070, 0.0020),
                'Hard': (0.040, 0.0010)
            }
            self.nominal_safe_limits = {'Soft': 22, 'Medium': 35, 'Hard': 48}
        else:  # Silverstone
            self.total_laps = 52
            self.pit_loss = 21.5
            self.alpha_fuel = 0.062
            self.gamma_track = 0.025
            self.t_ref = t_ref if t_ref is not None else 28.0  # Nhiệt độ tham chiếu tiêu chuẩn Silverstone (°C)
            self.base_times = {'Soft': 89.20, 'Medium': 89.85, 'Hard': 90.60}
            self.nominal_deg_coeffs = {
                'Soft': (0.145, 0.0065),
                'Medium': (0.085, 0.0028),
                'Hard': (0.050, 0.0014)
            }
            self.nominal_safe_limits = {'Soft': 18, 'Medium': 30, 'Hard': 42}

        self.t_track = t_track if t_track is not None else self.t_ref
        self._update_thermal_coefficients()

    def set_track_temperature(self, t_track: float) -> None:
        """Cập nhật nhiệt độ mặt đường và tính toán lại toàn bộ hệ số suy giảm."""
        self.t_track = float(t_track)
        self._update_thermal_coefficients()

    def _update_thermal_coefficients(self) -> None:
        """Hiệu chỉnh tham số d1, d2 và vách lốp L_max theo phương trình bán thực nghiệm TV3:
        delta_T = (T_track - T_ref) / T_ref
        d1(c, T_track) = d1_nominal * (1 + kappa1 * delta_T)
        d2(c, T_track) = d2_nominal * (1 + kappa2 * delta_T + theta2 * (max(0, delta_T))^2)
        """
        self.delta_t = (self.t_track - self.t_ref) / self.t_ref
        self.deg_coeffs: Dict[str, Tuple[float, float]] = {}
        self.safe_limits: Dict[str, int] = {}

        for c, (d1_nom, d2_nom) in self.nominal_deg_coeffs.items():
            thermal = THERMAL_COEFFICIENTS.get(c, {'kappa1': 0.20, 'kappa2': 1.00, 'theta2': 0.50})
            k1 = thermal['kappa1']
            k2 = thermal['kappa2']
            th2 = thermal['theta2']

            d1_adj = d1_nom * (1.0 + k1 * self.delta_t)
            thermal_runaway = max(0.0, self.delta_t) ** 2
            d2_adj = d2_nom * (1.0 + k2 * self.delta_t + th2 * thermal_runaway)

            # Đảm bảo chặn dưới vật lý ngay cả khi trời rét cực đoan (Las Vegas đêm < 15°C)
            # Ngăn ngừa d2 bị triệt tiêu về 0 hoặc âm do k2 * delta_T < -1
            self.deg_coeffs[c] = (
                max(d1_nom * 0.20, float(d1_adj)),
                max(d2_nom * 0.10, float(d2_adj))
            )

            # Giảm tuổi thọ an toàn nếu mặt đường quá nhiệt (nhiệt độ tăng làm rộp lốp sớm)
            nom_limit = self.nominal_safe_limits[c]
            if self.delta_t > 0.20:
                heat_reduction = int(round(nom_limit * 0.20 * min(1.5, self.delta_t)))
                self.safe_limits[c] = max(8, nom_limit - heat_reduction)
            else:
                self.safe_limits[c] = nom_limit

    def predict_lap_time(
        self,
        compound: str,
        tyre_age: int,
        race_lap: int,
        total_laps: Optional[int] = None,
        **kwargs
    ) -> float:
        """Tính toán chính xác thời gian hoàn thành vòng đua:
        t_lap = t_base + (d1*a + d2*a^2) + alpha_fuel*(N - lap) - gamma_track*lap
        """
        base = self.base_times.get(compound, 82.50)
        d1, d2 = self.deg_coeffs.get(compound, (0.080, 0.0030))
        deg_delta = d1 * tyre_age + d2 * (tyre_age ** 2)
        n_laps = total_laps if total_laps is not None else kwargs.get('total_laps', self.total_laps)
        fuel_delta = self.alpha_fuel * (n_laps - race_lap)
        track_delta = self.gamma_track * race_lap

        return float(base + deg_delta + fuel_delta - track_delta)

    def marginal_degradation(self, compound: str, age: Union[int, float]) -> float:
        """Đạo hàm mài mòn bậc 1 (Tốc độ mòn tức thời tại tuổi lốp a):
        nabla t_deg(a) = d1(c) + 2 * d2(c) * a
        """
        d1, d2 = self.deg_coeffs.get(compound, (0.080, 0.0030))
        return float(d1 + 2.0 * d2 * max(1.0, float(age)))

    def degradation_acceleration(self, compound: str) -> float:
        """Đạo hàm mài mòn bậc 2 (Gia tốc mòn lốp):
        nabla^2 t_deg(a) = 2 * d2(c)
        """
        _, d2 = self.deg_coeffs.get(compound, (0.080, 0.0030))
        return float(2.0 * d2)

    def discrete_step_jump(self, compound: str, age: int) -> float:
        """Gia số thời gian vòng đua khi kéo dài thêm 1 vòng (a -> a+1):
        Delta t_discrete = nabla t_deg(a) + d2(c)
        """
        _, d2 = self.deg_coeffs.get(compound, (0.080, 0.0030))
        return float(self.marginal_degradation(compound, age) + d2)

    def closed_form_stint_degradation(self, compound: str, length: int) -> float:
        """Tổng độ suy giảm lốp tích lũy của stint dài L vòng bằng công thức Faulhaber O(1):
        D_stint(c, L) = d1(c) * L*(L+1)/2 + d2(c) * L*(L+1)*(2L+1)/6
        """
        if length <= 0:
            return 0.0
        d1, d2 = self.deg_coeffs.get(compound, (0.080, 0.0030))
        l_val = float(length)
        sum_a = l_val * (l_val + 1.0) / 2.0
        sum_a2 = l_val * (l_val + 1.0) * (2.0 * l_val + 1.0) / 6.0
        return float(d1 * sum_a + d2 * sum_a2)

    def closed_form_stint_lap_time(
        self,
        compound: str,
        length: int,
        start_lap: int,
        total_laps: Optional[int] = None
    ) -> float:
        """Tổng thời gian hoàn thành toàn bộ stint dài L vòng xuất phát từ vòng start_lap:
        Tính giải tích đóng O(1) triệt tiêu hoàn toàn vòng lặp for.
        """
        if length <= 0:
            return 0.0
        l_val = float(length)
        base = self.base_times.get(compound, 82.50)
        deg = self.closed_form_stint_degradation(compound, length)
        n_laps = total_laps if total_laps is not None else self.total_laps

        sum_i = l_val * float(start_lap) + l_val * (l_val - 1.0) / 2.0
        fuel_term = self.alpha_fuel * (l_val * float(n_laps) - sum_i)
        track_term = self.gamma_track * sum_i

        return float(l_val * base + deg + fuel_term - track_term)

    def get_safe_limit(self, compound: str) -> int:
        """Trả về tuổi thọ an toàn tối đa khuyến nghị của Pirelli để tránh Tyre Cliff."""
        return self.safe_limits.get(compound, 35)
