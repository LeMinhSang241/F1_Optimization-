from typing import List, Dict, Any, Union
import numpy as np

def marginal_degradation(age: Union[float, np.ndarray], d1: float, d2: float) -> Union[float, np.ndarray]:
    return d1 + 2.0 * d2 * age

def degradation_acceleration(d2: float) -> float:
    return 2.0 * d2

def discrete_step_jump(age: Union[float, np.ndarray], d1: float, d2: float) -> Union[float, np.ndarray]:
    return d1 + 2.0 * d2 * age + d2

def closed_form_stint_degradation(length: int, d1: float, d2: float) -> float:
    if length <= 0:
        return 0.0
    l_val = float(length)
    sum_a = l_val * (l_val + 1.0) / 2.0
    sum_a2 = l_val * (l_val + 1.0) * (2.0 * l_val + 1.0) / 6.0
    return d1 * sum_a + d2 * sum_a2

def closed_form_stint_lap_time(
    length: int,
    start_lap: int,
    total_race_laps: int,
    t_base: float,
    d1: float,
    d2: float,
    alpha_fuel: float,
    gamma_track: float
) -> float:
    if length <= 0:
        return 0.0
    l_val = float(length)
    sum_i = l_val * float(start_lap) + l_val * (l_val - 1.0) / 2.0
    deg = closed_form_stint_degradation(length, d1, d2)
    fuel_term = alpha_fuel * (l_val * float(total_race_laps) - sum_i)
    track_term = gamma_track * sum_i
    return l_val * t_base + deg + fuel_term - track_term

def fix_total_laps(
    stint_lengths: List[int],
    compounds: List[str],
    target_laps: int,
    compound_params: Dict[str, Dict[str, float]],
    l_min: int = 4
) -> List[int]:
    lengths = list(stint_lengths)
    k = len(lengths)
    if k == 0:
        return lengths

    delta_n = target_laps - sum(lengths)

    while delta_n > 0:
        best_score = float("inf")
        best_idx = 0
        for j in range(k):
            c = compounds[j]
            cp = compound_params[c]
            a = lengths[j]
            grad = marginal_degradation(a, cp["d1"], cp["d2"])
            l_max = cp["l_max"]
            if a < l_max:
                score = grad - 0.05 * (l_max - a)
            else:
                score = grad + 1000.0
            if score < best_score:
                best_score = score
                best_idx = j
        lengths[best_idx] += 1
        delta_n -= 1

    while delta_n < 0:
        best_score = -float("inf")
        best_idx = -1
        for j in range(k):
            if lengths[j] > l_min:
                c = compounds[j]
                cp = compound_params[c]
                a = lengths[j]
                grad = marginal_degradation(a, cp["d1"], cp["d2"])
                if grad > best_score:
                    best_score = grad
                    best_idx = j
        if best_idx == -1:
            best_idx = int(np.argmax(lengths))
        lengths[best_idx] -= 1
        delta_n += 1

    return lengths
