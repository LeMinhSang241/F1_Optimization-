"""Module mô hình hóa sự suy giảm hiệu suất lốp (Tyre Degradation Modeling).
Tối ưu hóa trọng số kết hợp (Ensemble Weights) bằng Real-valued Genetic Algorithm (RCGA).
Kế thừa phương pháp luận từ bài báo Kaya & Çetin-Kaya (Elsevier EAAI, 2024).
Phân công: Thành viên 3 (Tyre Degradation Modeler).
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline


class RealValuedGATyreEnsemble:
    """Mô hình Ensemble dự đoán thời gian vòng dựa trên hợp chất lốp, số vòng đã chạy và lượng nhiên liệu.
    Ứng dụng RCGA để tối ưu hóa véc-tơ trọng số liên tục beta thỏa mãn sum(beta) = 1.
    """

    def __init__(self, base_models: Optional[List] = None):
        self.base_models = base_models or [
            make_pipeline(PolynomialFeatures(degree=1), Ridge()),
            make_pipeline(PolynomialFeatures(degree=2), Ridge()),
        ]
        self.weights = np.ones(len(self.base_models)) / len(self.base_models)
        self.is_fitted = False

    def optimize_weights_rcga(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        pop_size: int = 50,
        generations: int = 40,
        mutation_rate: float = 0.15,
    ) -> np.ndarray:
        """Tối ưu hóa véc-tơ trọng số beta bằng Real-valued GA theo Kaya et al. (2024).
        
        Nhiễm sắc thể: véc-tơ số thực [beta_1, beta_2, ..., beta_M] với beta_i in [0, 1] và sum(beta) = 1.
        Mục tiêu: Tối thiểu hóa RMSE trên tập kiểm định.
        """
        num_models = len(self.base_models)
        # Sinh dự đoán từ từng mô hình cơ sở
        preds = np.array([model.predict(X_val) for model in self.base_models])  # shape: (M, N)
        
        # Khởi tạo quần thể ngẫu nhiên thỏa ràng buộc Dirichlet
        population = np.random.dirichlet(np.ones(num_models), size=pop_size)
        best_weights = population[0]
        best_rmse = float('inf')

        for gen in range(generations):
            # Đánh giá độ thích nghi (RMSE)
            rmses = []
            for indiv in population:
                combined_pred = np.tensordot(indiv, preds, axes=(0, 0))
                rmse = np.sqrt(np.mean((y_val - combined_pred) ** 2))
                rmses.append(rmse)
                if rmse < best_rmse:
                    best_rmse = rmse
                    best_weights = indiv.copy()

            # Chọn lọc Tournament
            new_pop = []
            for _ in range(pop_size):
                i1, i2 = np.random.choice(pop_size, 2, replace=False)
                winner = population[i1] if rmses[i1] < rmses[i2] else population[i2]
                new_pop.append(winner.copy())
            new_pop = np.array(new_pop)

            # Lai ghép số thực (Arithmetic Crossover)
            for i in range(0, pop_size - 1, 2):
                if np.random.rand() < 0.8:
                    alpha = np.random.uniform(0.2, 0.8)
                    p1, p2 = new_pop[i].copy(), new_pop[i+1].copy()
                    new_pop[i] = alpha * p1 + (1 - alpha) * p2
                    new_pop[i+1] = (1 - alpha) * p1 + alpha * p2

            # Đột biến Gaussian + Chuẩn hóa bảo toàn tổng bằng 1
            for i in range(pop_size):
                if np.random.rand() < mutation_rate:
                    noise = np.random.normal(0, 0.05, size=num_models)
                    mutated = np.clip(new_pop[i] + noise, 0.01, 1.0)
                    new_pop[i] = mutated / np.sum(mutated)

            # Elitism: giữ cá thể tốt nhất
            new_pop[0] = best_weights.copy()
            population = new_pop

        self.weights = best_weights
        return self.weights

    def predict_lap_time(self, compound: str, tyre_age: int, race_lap: int, total_laps: int = 53) -> float:
        """Dự đoán thời gian hoàn thành vòng đua giải tích cơ bản (được calibrate từ số liệu Pirelli):
        LapTime = BaseTime(c) + Deg(c, a) + Fuel(lap) - TrackRubber(lap)
        """
        # Base time khi xe nhẹ xăng (Monza chuẩn ~81.5s)
        base_times = {'Soft': 81.5, 'Medium': 82.2, 'Hard': 83.0}
        base = base_times.get(compound, 82.5)

        # Hệ số mòn lốp bậc hai: d1 * a + d2 * a^2
        deg_coeffs = {
            'Soft': (0.12, 0.005),
            'Medium': (0.07, 0.002),
            'Hard': (0.04, 0.001)
        }
        d1, d2 = deg_coeffs.get(compound, (0.08, 0.003))
        deg_delta = d1 * tyre_age + d2 * (tyre_age ** 2)

        # Hiệu ứng tiêu hao xăng (~0.06s/vòng)
        fuel_delta = 0.058 * (total_laps - race_lap)

        # Hiệu ứng mặt đường gom cao su (~0.02s/vòng)
        track_delta = 0.022 * race_lap

        return float(base + deg_delta + fuel_delta - track_delta)
