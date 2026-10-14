import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import argparse
from typing import Dict, Any, List
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tyre.fitter import WLSFitter, isolate_response_variable
from tyre.metrics import calculate_metrics

CIRCUITS_CONFIG: Dict[str, Dict[str, Any]] = {
    "monza": {
        "name": "Autodromo Nazionale Monza",
        "total_laps": 53,
        "alpha_fuel": 0.058,
        "gamma_track": 0.022,
        "t_pit": 23.2,
        "compounds": {
            "Soft": {"code": "C4", "t_base": 81.50, "d1": 0.120, "d2": 0.0050, "l_max": 22},
            "Medium": {"code": "C3", "t_base": 82.20, "d1": 0.070, "d2": 0.0020, "l_max": 35},
            "Hard": {"code": "C2", "t_base": 83.00, "d1": 0.040, "d2": 0.0010, "l_max": 48}
        }
    },
    "silverstone": {
        "name": "Silverstone Circuit",
        "total_laps": 52,
        "alpha_fuel": 0.060,
        "gamma_track": 0.024,
        "t_pit": 25.0,
        "compounds": {
            "Soft": {"code": "C3", "t_base": 89.20, "d1": 0.145, "d2": 0.0065, "l_max": 18},
            "Medium": {"code": "C2", "t_base": 89.85, "d1": 0.085, "d2": 0.0028, "l_max": 30},
            "Hard": {"code": "C1", "t_base": 90.60, "d1": 0.050, "d2": 0.0014, "l_max": 42}
        }
    }
}

def generate_circuit_telemetry(circuit_key: str, seed: int = 42) -> Dict[str, Dict[str, np.ndarray]]:
    rng = np.random.default_rng(seed)
    cfg = CIRCUITS_CONFIG[circuit_key]
    n_total = cfg["total_laps"]
    alpha = cfg["alpha_fuel"]
    gamma = cfg["gamma_track"]
    
    dataset: Dict[str, Dict[str, np.ndarray]] = {}
    
    for c_name, cp in cfg["compounds"].items():
        t_base = cp["t_base"]
        d1 = cp["d1"]
        d2 = cp["d2"]
        l_max = cp["l_max"]
        
        ages_list: List[float] = []
        laps_list: List[int] = []
        times_list: List[float] = []
        is_clean_list: List[bool] = []
        
        num_drivers = 16
        for _ in range(num_drivers):
            stint_len = int(rng.integers(l_max - 5, l_max + 4))
            start_i = int(rng.integers(1, max(2, n_total - stint_len + 1)))
            
            for a in range(1, stint_len + 1):
                i = start_i + a - 1
                if i > n_total:
                    break
                    
                sigma = 0.05 if a <= 15 else 0.05 + 0.35 * min(1.0, max(0.0, (a - 15) / 15.0))
                noise = rng.normal(0.0, sigma)
                
                is_outlier = rng.random() < 0.04
                if is_outlier:
                    noise += rng.choice([-1.5, 1.8, 2.2])
                    
                t_deg = d1 * a + d2 * (a ** 2)
                t_fuel = alpha * (n_total - i)
                t_tr = gamma * i
                t_lap = t_base + t_deg + t_fuel - t_tr + noise
                
                is_clean = not is_outlier and a > 1 and a < stint_len
                
                ages_list.append(float(a))
                laps_list.append(i)
                times_list.append(float(t_lap))
                is_clean_list.append(is_clean)
                
        dataset[c_name] = {
            "age": np.array(ages_list, dtype=np.float64),
            "lap": np.array(laps_list, dtype=np.int64),
            "lap_time": np.array(times_list, dtype=np.float64),
            "is_clean": np.array(is_clean_list, dtype=bool)
        }
        
    return dataset

def run_training_pipeline(circuit_key: str, weighting: str = "inverse_age_variance", seed: int = 42) -> Dict[str, Any]:
    cfg = CIRCUITS_CONFIG[circuit_key]
    data = generate_circuit_telemetry(circuit_key, seed=seed)
    fitter = WLSFitter(tikhonov_lambda=1e-9, delta_huber=1.2)
    
    use_age_weight = (weighting == "inverse_age_variance")
    
    fitted_params: Dict[str, Any] = {}
    validation_plot_data: Dict[str, Any] = {}
    
    for c_name, cp in cfg["compounds"].items():
        sub = data[c_name]
        clean_mask = sub["is_clean"]
        
        ages_clean = sub["age"][clean_mask]
        laps_clean = sub["lap"][clean_mask]
        times_clean = sub["lap_time"][clean_mask]
        
        y_iso = isolate_response_variable(
            times_clean, laps_clean, cfg["total_laps"], cfg["alpha_fuel"], cfg["gamma_track"]
        )
        
        res = fitter.fit(
            ages_clean,
            y_iso,
            l_max=cp["l_max"],
            use_age_weight=use_age_weight,
            use_huber=True
        )
        
        fitted_params[c_name] = {
            "code": cp["code"],
            "t_base": round(res["t_base"], 4),
            "d1": round(res["d1"], 6),
            "d2": round(res["d2"], 7),
            "l_max": cp["l_max"],
            "metrics": {
                "r2": round(res["metrics"]["r2"], 4),
                "r2_adj": round(res["metrics"]["r2_adj"], 4),
                "rmse": round(res["metrics"]["rmse"], 4),
                "mae": round(res["metrics"]["mae"], 4),
                "mape": round(res["metrics"]["mape"], 4),
                "aic": round(res["metrics"]["aic"], 2),
                "bic": round(res["metrics"]["bic"], 2),
                "sample_size": int(res["metrics"]["sample_size"])
            }
        }
        
        validation_plot_data[c_name] = {
            "ages": ages_clean,
            "y_iso": y_iso,
            "pred_curve": res["beta"][0] + res["beta"][1] * np.arange(1, cp["l_max"] + 5) + res["beta"][2] * (np.arange(1, cp["l_max"] + 5) ** 2),
            "curve_ages": np.arange(1, cp["l_max"] + 5)
        }

    for d in ["tyre/models", "models", "tyre/figures", "figures"]:
        os.makedirs(d, exist_ok=True)
        
    model_payload = {
        "circuit": circuit_key,
        "circuit_name": cfg["name"],
        "total_laps": cfg["total_laps"],
        "alpha_fuel": cfg["alpha_fuel"],
        "gamma_track": cfg["gamma_track"],
        "t_pit": cfg["t_pit"],
        "compounds": fitted_params
    }
    
    for path in [f"tyre/models/tyre_params_{circuit_key}.json", f"models/tyre_params_{circuit_key}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model_payload, f, indent=2)

    max_l = max(cp["l_max"] for cp in cfg["compounds"].values())
    n_laps = cfg["total_laps"]
    c_names = list(cfg["compounds"].keys())
    
    tensor_data: Dict[str, List[List[float]]] = {}
    for c_idx, c_name in enumerate(c_names):
        c_tensor: List[List[float]] = []
        p = fitted_params[c_name]
        for a in range(1, max_l + 1):
            row: List[float] = []
            for i in range(1, n_laps + 1):
                t_val = p["t_base"] + p["d1"] * a + p["d2"] * (a ** 2) + cfg["alpha_fuel"] * (n_laps - i) - cfg["gamma_track"] * i
                row.append(round(t_val, 4))
            c_tensor.append(row)
        tensor_data[c_name] = c_tensor

    tensor_payload = {
        "circuit": circuit_key,
        "dimensions": {
            "compounds": c_names,
            "max_age": max_l,
            "total_laps": n_laps
        },
        "tensor": tensor_data
    }
    
    for path in [f"tyre/models/lookup_tensor_{circuit_key}.json", f"models/lookup_tensor_{circuit_key}.json"]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tensor_payload, f, indent=2)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#15151e")
    ax.set_facecolor("#1e1e2d")
    
    c_colors = {"Soft": "#e10600", "Medium": "#ffd100", "Hard": "#00d2be"}
    
    for c_name, pdata in validation_plot_data.items():
        color = c_colors.get(c_name, "#ffffff")
        ax.scatter(pdata["ages"], pdata["y_iso"], color=color, alpha=0.25, s=16, label=f"{c_name} Samples")
        ax.plot(pdata["curve_ages"], pdata["pred_curve"], color=color, linewidth=2.5, label=f"{c_name} WLS Fit")
        
    ax.set_title(f"Pirelli Degradation Fit Validation - {cfg['name']}", color="#ffffff", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Tyre Age a (laps)", color="#ffffff", fontsize=12)
    ax.set_ylabel("Fuel & Track Decomposed Lap Time y (s)", color="#ffffff", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.25, color="#888888")
    ax.tick_params(colors="#cccccc")
    for spine in ax.spines.values():
        spine.set_color("#444455")
        
    ax.legend(facecolor="#1e1e2d", edgecolor="#444455", labelcolor="#ffffff", fontsize=10)
    plt.tight_layout()
    
    for path in [f"tyre/figures/fit_validation_{circuit_key}.png", f"figures/fit_validation_{circuit_key}.png"]:
        plt.savefig(path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    
    return model_payload

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--circuit", type=str, default="monza", choices=["monza", "silverstone"])
    parser.add_argument("--weighting", type=str, default="inverse_age_variance")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    res = run_training_pipeline(args.circuit, args.weighting, args.seed)
    print(f"Successfully trained tyre model for {args.circuit.upper()}")
    for c_name, cp in res["compounds"].items():
        m = cp["metrics"]
        print(f"[{c_name}] t_base={cp['t_base']:.3f} d1={cp['d1']:.5f} d2={cp['d2']:.6f} | R2={m['r2']:.4f} RMSE={m['rmse']:.4f}s MAE={m['mae']:.4f}s")

if __name__ == "__main__":
    main()
