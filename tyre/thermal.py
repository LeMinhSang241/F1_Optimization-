from typing import Dict, Tuple, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

THERMAL_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    "Soft": {"kappa1": 0.30, "kappa2": 1.80, "theta2": 1.20},
    "Medium": {"kappa1": 0.25, "kappa2": 1.20, "theta2": 0.80},
    "Hard": {"kappa1": 0.15, "kappa2": 0.60, "theta2": 0.30}
}

T_REF: float = 42.0

def relative_temperature_delta(t_track: float, t_ref: float = T_REF) -> float:
    return (t_track - t_ref) / t_ref

def adjust_degradation_parameters(
    compound: str,
    d1_nominal: float,
    d2_nominal: float,
    t_track: float,
    t_ref: float = T_REF
) -> Tuple[float, float]:
    delta_t = relative_temperature_delta(t_track, t_ref)
    coeffs = THERMAL_COEFFICIENTS.get(compound, {"kappa1": 0.20, "kappa2": 1.00, "theta2": 0.50})
    k1 = coeffs["kappa1"]
    k2 = coeffs["kappa2"]
    th2 = coeffs["theta2"]
    
    d1_adj = d1_nominal * (1.0 + k1 * delta_t)
    thermal_runaway = max(0.0, delta_t) ** 2
    d2_adj = d2_nominal * (1.0 + k2 * delta_t + th2 * thermal_runaway)
    
    return max(0.0, d1_adj), max(0.0, d2_adj)

def plot_temperature_sensitivity(
    base_params: Dict[str, Dict[str, float]],
    temperatures: Tuple[float, float, float] = (32.0, 42.0, 54.0),
    save_path: str = "tyre/figures/fig_tyre_temperature_sensitivity.png"
) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    colors = {"Soft": "#e10600", "Medium": "#ffd100", "Hard": "#ffffff"}
    linestyles = {32.0: ":", 42.0: "-", 54.0: "--"}
    
    for compound, p in base_params.items():
        c_color = colors.get(compound, "#333333")
        l_max = int(p.get("l_max", 30))
        ages = np.arange(1, l_max + 1)
        
        for t_val in temperatures:
            d1_t, d2_t = adjust_degradation_parameters(compound, p["d1"], p["d2"], t_val)
            delta_t_tyre = d1_t * ages + d2_t * (ages ** 2)
            grad_t_deg = d1_t + 2.0 * d2_t * ages
            
            ls = linestyles.get(t_val, "-")
            label = f"{compound} ({int(t_val)}°C)"
            
            ax1.plot(ages, delta_t_tyre, label=label, color=c_color, linestyle=ls, linewidth=2.0)
            ax2.plot(ages, grad_t_deg, label=label, color=c_color, linestyle=ls, linewidth=2.0)

    fig.patch.set_facecolor("#15151e")
    for ax, title, ylabel in [
        (ax1, "(A) Tyre Degradation Delta t_tyre (s)", "Delta t_tyre (s)"),
        (ax2, "(B) Instantaneous Marginal Wear grad t_deg (s/lap)", "grad t_deg (s/lap)")
    ]:
        ax.set_facecolor("#1e1e2d")
        ax.set_title(title, color="#ffffff", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("Tyre Age a (laps)", color="#ffffff", fontsize=11)
        ax.set_ylabel(ylabel, color="#ffffff", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.3, color="#888888")
        ax.tick_params(colors="#cccccc")
        for spine in ax.spines.values():
            spine.set_color("#444455")
            
    ax1.legend(facecolor="#1e1e2d", edgecolor="#444455", labelcolor="#ffffff", fontsize=8, loc="upper left")
    ax2.legend(facecolor="#1e1e2d", edgecolor="#444455", labelcolor="#ffffff", fontsize=8, loc="upper left")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
