from typing import Tuple, Dict, Any, Optional
import numpy as np
from tyre.metrics import calculate_metrics

def isolate_response_variable(
    t_lap: np.ndarray,
    lap_index: np.ndarray,
    n_total: int,
    alpha_fuel: float,
    gamma_track: float
) -> np.ndarray:
    return t_lap - alpha_fuel * (n_total - lap_index) + gamma_track * lap_index

def compute_age_weights(tyre_age: np.ndarray, l_max: float) -> np.ndarray:
    ratio = np.maximum(0.0, (tyre_age - l_max) / 5.0)
    return 1.0 / (1.0 + 0.5 * (ratio ** 2))

def compute_huber_weights(residuals: np.ndarray, delta_huber: float = 1.2) -> np.ndarray:
    abs_res = np.abs(residuals)
    weights = np.ones_like(abs_res)
    mask = abs_res > delta_huber
    weights[mask] = delta_huber / (abs_res[mask] + 1e-6)
    return weights

class WLSFitter:
    def __init__(
        self,
        tikhonov_lambda: float = 1e-9,
        delta_huber: float = 1.2,
        max_irls_iter: int = 25,
        tol: float = 1e-7
    ) -> None:
        self.tikhonov_lambda = tikhonov_lambda
        self.delta_huber = delta_huber
        self.max_irls_iter = max_irls_iter
        self.tol = tol

    def fit(
        self,
        tyre_age: np.ndarray,
        y_isolated: np.ndarray,
        l_max: float,
        use_age_weight: bool = True,
        use_huber: bool = True
    ) -> Dict[str, Any]:
        age = np.asarray(tyre_age, dtype=np.float64)
        y = np.asarray(y_isolated, dtype=np.float64)
        m = len(age)
        
        x_mat = np.column_stack([np.ones(m), age, age ** 2])
        eye3 = np.eye(3, dtype=np.float64)
        
        w_age = compute_age_weights(age, l_max) if use_age_weight else np.ones(m, dtype=np.float64)
        w_huber = np.ones(m, dtype=np.float64)
        
        beta = np.zeros(3, dtype=np.float64)
        
        for _ in range(self.max_irls_iter):
            w = w_age * w_huber
            x_w = x_mat.T * w
            xtwx = x_w @ x_mat + self.tikhonov_lambda * eye3
            xtwy = x_w @ y
            
            new_beta = np.linalg.solve(xtwx, xtwy)
            new_beta = np.maximum(0.0, new_beta)
            
            diff = np.linalg.norm(new_beta - beta)
            beta = new_beta
            
            if not use_huber or diff < self.tol:
                break
                
            residuals = y - x_mat @ beta
            w_huber = compute_huber_weights(residuals, self.delta_huber)
            
        y_pred = x_mat @ beta
        metrics = calculate_metrics(y, y_pred, num_params=3)
        
        return {
            "t_base": float(beta[0]),
            "d1": float(beta[1]),
            "d2": float(beta[2]),
            "beta": beta,
            "weights": w,
            "metrics": metrics,
            "y_pred": y_pred
        }
