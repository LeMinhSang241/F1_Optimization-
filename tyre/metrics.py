from typing import Dict, Any
import numpy as np

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, num_params: int = 3) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    m = len(y_true)
    residuals = y_true - y_pred
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    if m > num_params + 1:
        r2_adj = 1.0 - (1.0 - r2) * ((m - 1) / (m - num_params - 1))
    else:
        r2_adj = r2
        
    rmse = float(np.sqrt(ss_res / m))
    mae = float(np.mean(np.abs(residuals)))
    mape = float(np.mean(np.abs(residuals / y_true)) * 100.0)
    
    eps = 1e-12
    aic = float(m * np.log(max(ss_res / m, eps)) + 2 * num_params)
    bic = float(m * np.log(max(ss_res / m, eps)) + num_params * np.log(m))
    
    return {
        "r2": r2,
        "r2_adj": r2_adj,
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "aic": aic,
        "bic": bic,
        "ss_res": ss_res,
        "sample_size": m
    }
