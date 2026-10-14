"""Các toán tử của Giải thuật Di truyền Thích nghi Động (DAGA-F1).
Dynamic Adaptive Genetic Algorithm for F1 Pit-Stop & Tyre Strategy Optimization.

Đóng góp mới cốt lõi (Novelties):
1. Biểu diễn nhiễm sắc thể biến thiên mốc pit (Variable-Length Stint Representation).
2. Toán tử sửa chữa định hướng vật lý (Physics-Guided Repair Operator) dựa trên đạo hàm giải tích
   suy giảm hiệu suất lốp ∇t_deg(a) = d1(c) + 2*d2(c)*a và ngưỡng vách lốp L_max bàn giao từ TV3.
3. Toán tử đột biến đa hình thái 3 cấp độ (Tri-Level Polymorphic Mutation: Micro, Meso, Macro)
   với cơ chế Split Stint / Merge Stint tự động tiến hóa số lần dừng pit K ∈ {1, 2, 3}.
4. Khởi tạo quần thể định hướng tri thức chuyên gia (Heuristic Weighted Initialization: 65% 1-stop, 30% 2-stop, 5% 3-stop).

Phân công: Thành viên 1 (Algorithm & GA Lead) tích hợp hoàn chỉnh tài liệu mô hình lốp TV3.
"""

from typing import List, Tuple, Dict, Optional, Union
import random
import numpy as np


COMPOUNDS: List[str] = ['Soft', 'Medium', 'Hard']

# Pirelli 2023 Physical Degradation Coefficients (d1, d2) - Monza GP Default
# Formula: Delta_t_deg = d1 * a + d2 * a^2
# Derivative: nabla_t_deg(a) = d1 + 2 * d2 * a
DEG_COEFFS: Dict[str, Tuple[float, float]] = {
    'Soft': (0.120, 0.0050),
    'Medium': (0.070, 0.0020),
    'Hard': (0.040, 0.0010)
}

# Pirelli Mechanical Safety Cliff Limits (L_max) - Monza GP Default
CLIFF_LIMITS: Dict[str, int] = {
    'Soft': 22,
    'Medium': 35,
    'Hard': 48
}

# Base lap times for unladen car at Monza (s)
BASE_TIMES: Dict[str, float] = {
    'Soft': 81.50,
    'Medium': 82.20,
    'Hard': 83.00
}

MIN_STINT_LENGTH: int = 4


def tyre_deg_derivative(
    compound: str,
    age: int,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None
) -> float:
    """Tính đạo hàm giải tích của sự suy giảm hiệu suất lốp theo tuổi lốp a:
    ∇t_deg(a) = d1(c) + 2 * d2(c) * a
    """
    coeffs = deg_coeffs or DEG_COEFFS
    d1, d2 = coeffs.get(compound, (0.080, 0.0030))
    return float(d1 + 2.0 * d2 * max(1, age))


def degradation_acceleration(
    compound: str,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None
) -> float:
    """Đạo hàm bậc hai (Gia tốc mòn lốp): ∇^2 t_deg(a) = 2 * d2(c) > 0 (Hàm lồi nghiêm ngặt)."""
    coeffs = deg_coeffs or DEG_COEFFS
    _, d2 = coeffs.get(compound, (0.080, 0.0030))
    return float(2.0 * d2)


def closed_form_stint_degradation(
    length: int,
    compound: str,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None
) -> float:
    """Tổng độ mòn của stint dài L vòng bằng công thức đóng Faulhaber O(1):
    D_stint = d1 * L*(L+1)/2 + d2 * L*(L+1)*(2L+1)/6
    """
    if length <= 0:
        return 0.0
    coeffs = deg_coeffs or DEG_COEFFS
    d1, d2 = coeffs.get(compound, (0.080, 0.0030))
    l_val = float(length)
    sum_a = l_val * (l_val + 1.0) / 2.0
    sum_a2 = l_val * (l_val + 1.0) * (2.0 * l_val + 1.0) / 6.0
    return float(d1 * sum_a + d2 * sum_a2)


def heuristic_weighted_initialization(
    pop_size: int,
    total_laps: int = 53,
    cliff_limits: Optional[Dict[str, int]] = None,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None
) -> List[List[Tuple[str, int]]]:
    """Khởi tạo quần thể đa dạng cấu trúc theo phân phối thực tế chuyên gia F1:
    - 65% cá thể 1-stop (2 stints)
    - 30% cá thể 2-stop (3 stints)
    - 5% cá thể 3-stop (4 stints)
    
    100% cá thể sinh ra đều thỏa mãn ngay luật FIA (dùng ít nhất 2 loại lốp khô khác nhau).
    Hỗ trợ linh hoạt mọi độ dài cuộc đua (Monza 53 vòng, Silverstone 52 vòng, v.v.).
    """
    if pop_size <= 0:
        return []

    population: List[List[Tuple[str, int]]] = []
    
    if pop_size < 3:
        n_1stop = pop_size
        n_2stop = 0
        n_3stop = 0
    else:
        n_1stop = int(pop_size * 0.65)
        n_2stop = int(pop_size * 0.30)
        n_3stop = pop_size - n_1stop - n_2stop

    # 1. Nhóm 1-stop: 2 stints (Medium-Hard, Soft-Hard, Hard-Medium, etc.)
    for _ in range(n_1stop):
        c1, c2 = random.sample(COMPOUNDS, 2)
        min_p = max(MIN_STINT_LENGTH, int(total_laps * 0.25))
        max_p = max(min_p, min(total_laps - MIN_STINT_LENGTH, int(total_laps * 0.68)))
        pit_lap = random.randint(min_p, max_p) if max_p >= min_p else total_laps // 2
        stints = [(c1, pit_lap), (c2, total_laps - pit_lap)]
        population.append(physics_guided_repair(stints, total_laps, cliff_limits, deg_coeffs))

    # 2. Nhóm 2-stop: 3 stints (Medium-Hard-Medium, Soft-Hard-Soft, Soft-Medium-Hard, etc.)
    for _ in range(n_2stop):
        c1 = random.choice(['Soft', 'Medium'])
        c2 = random.choice(['Medium', 'Hard'])
        c3 = random.choice(['Soft', 'Medium', 'Hard'])
        if len({c1, c2, c3}) < 2:
            c3 = 'Hard' if c1 != 'Hard' else 'Medium'

        base_third = max(MIN_STINT_LENGTH, total_laps // 3)
        l1 = random.randint(MIN_STINT_LENGTH, max(MIN_STINT_LENGTH + 2, base_third + 3))
        l2 = random.randint(MIN_STINT_LENGTH, max(MIN_STINT_LENGTH + 2, base_third + 3))
        l3 = total_laps - (l1 + l2)
        if l3 < MIN_STINT_LENGTH:
            l3 = MIN_STINT_LENGTH
            l2 = max(MIN_STINT_LENGTH, total_laps - l1 - l3)
        stints = [(c1, l1), (c2, l2), (c3, l3)]
        population.append(physics_guided_repair(stints, total_laps, cliff_limits, deg_coeffs))

    # 3. Nhóm 3-stop: 4 stints (Chiến lược tấn công tốc lực ngắn)
    for _ in range(n_3stop):
        c1, c2 = 'Soft', 'Medium'
        c3 = random.choice(['Soft', 'Medium'])
        c4 = random.choice(['Soft', 'Medium', 'Hard'])
        base_fourth = max(MIN_STINT_LENGTH, total_laps // 4)
        l1 = random.randint(MIN_STINT_LENGTH, max(MIN_STINT_LENGTH + 1, base_fourth + 2))
        l2 = random.randint(MIN_STINT_LENGTH, max(MIN_STINT_LENGTH + 1, base_fourth + 2))
        l3 = random.randint(MIN_STINT_LENGTH, max(MIN_STINT_LENGTH + 1, base_fourth + 2))
        l4 = total_laps - (l1 + l2 + l3)
        if l4 < MIN_STINT_LENGTH:
            l4 = MIN_STINT_LENGTH
            l3 = max(MIN_STINT_LENGTH, total_laps - (l1 + l2 + l4))
        stints = [(c1, l1), (c2, l2), (c3, l3), (c4, l4)]
        population.append(physics_guided_repair(stints, total_laps, cliff_limits, deg_coeffs))

    return population


def physics_guided_repair(
    individual: List[Tuple[str, int]],
    total_laps: int = 53,
    cliff_limits: Optional[Dict[str, int]] = None,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None,
    min_compounds: int = 2,
    min_stints: int = 2
) -> List[Tuple[str, int]]:
    """Toán tử sửa chữa định hướng vật lý (Physics-Guided Repair Operator).
    
    Giải quyết triệt để 3 ràng buộc khắt khe của FIA và Pirelli:
    (R1) Bảo toàn bất biến tổng số vòng: sum(l_k) == total_laps.
    (R2) Luật lốp FIA: Sử dụng ít nhất min_compounds loại hợp chất khô khác nhau (|{c_k}| >= min_compounds).
    (R3) Độ an toàn cơ học vách lốp: Tối ưu dung sai an toàn (L_max - l_k) dựa trên
         đạo hàm giải tích suy giảm lốp ∇t_deg(a) = d1(c) + 2*d2(c)*a.
    """
    if total_laps <= 0:
        return []

    c_limits = cliff_limits or CLIFF_LIMITS
    d_coeffs = deg_coeffs or DEG_COEFFS

    if total_laps < 2 * MIN_STINT_LENGTH:
        effective_min_stints = 1
        effective_min_compounds = 1
        effective_min_len = 1
    else:
        effective_min_stints = min_stints
        effective_min_compounds = min_compounds
        effective_min_len = MIN_STINT_LENGTH

    if not individual:
        if effective_min_stints >= 2:
            c1, c2 = random.sample(COMPOUNDS, 2)
            mid = max(effective_min_len, min(total_laps - effective_min_len, total_laps // 2))
            return [(c1, mid), (c2, total_laps - mid)]
        else:
            return [(random.choice(COMPOUNDS), total_laps)]

    # Bước 1: Chuẩn hóa dữ liệu đầu vào
    repaired: List[List] = []
    for s in individual:
        c = s[0] if s[0] in COMPOUNDS else random.choice(COMPOUNDS)
        try:
            l = int(s[1])
        except (ValueError, TypeError):
            l = effective_min_len
        repaired.append([c, max(effective_min_len, l)])

    # Gộp stint nếu số lượng stint nhân độ dài tối thiểu vượt quá total_laps
    while len(repaired) > 1 and len(repaired) * effective_min_len > total_laps:
        idx = 0
        min_sum = repaired[0][1] + repaired[1][1]
        for i in range(1, len(repaired) - 1):
            if repaired[i][1] + repaired[i + 1][1] < min_sum:
                min_sum = repaired[i][1] + repaired[i + 1][1]
                idx = i
        c_m = repaired[idx][0] if repaired[idx][0] in ['Medium', 'Hard'] else repaired[idx + 1][0]
        repaired = repaired[:idx] + [[c_m, repaired[idx][1] + repaired[idx + 1][1]]] + repaired[idx + 2:]

    # Nếu sau khi lọc ít hơn số stint tối thiểu yêu cầu -> Tách stint
    if len(repaired) < effective_min_stints:
        c_orig, l_orig = repaired[0]
        other_comp = random.choice([c for c in COMPOUNDS if c != c_orig])
        half = max(effective_min_len, min(total_laps - effective_min_len, l_orig // 2))
        repaired = [[c_orig, half], [other_comp, max(effective_min_len, total_laps - half)]]

    # Bước 2: Cưỡng chế Luật lốp FIA
    if effective_min_compounds >= 2 and len(repaired) >= 2:
        compounds = [c for c, _ in repaired]
        if len(set(compounds)) < effective_min_compounds:
            shortest_idx = min(range(len(repaired)), key=lambda i: repaired[i][1])
            cur_comp = repaired[shortest_idx][0]
            s_len = repaired[shortest_idx][1]
            available = [c for c in COMPOUNDS if c != cur_comp]
            if s_len <= 18 and 'Soft' in available:
                new_comp = 'Soft'
            elif s_len >= 30 and 'Hard' in available:
                new_comp = 'Hard'
            elif 'Medium' in available:
                new_comp = 'Medium'
            else:
                new_comp = random.choice(available)
            repaired[shortest_idx][0] = new_comp

    # Bước 2b: Tái cân bằng vách lốp (Tyre Cliff Rebalancing)
    # Nếu có stint vượt quá L_max, điều chuyển các vòng vượt ngưỡng sang stint có dung sai an toàn
    for i in range(len(repaired)):
        c, l = repaired[i]
        cliff = c_limits.get(c, 35)
        if l > cliff:
            excess = l - cliff
            for _ in range(excess):
                best_target = -1
                best_score = -float('inf')
                for j in range(len(repaired)):
                    if j != i:
                        cj, lj = repaired[j]
                        cliff_j = c_limits.get(cj, 35)
                        cap_j = cliff_j - lj
                        if cap_j > 0:
                            grad_j = tyre_deg_derivative(cj, lj, d_coeffs)
                            score_j = cap_j * 2.0 - grad_j * 10.0
                            if score_j > best_score:
                                best_score = score_j
                                best_target = j
                if best_target != -1:
                    repaired[i][1] -= 1
                    repaired[best_target][1] += 1
                else:
                    break

    # Bước 3: Cân bằng tổng số vòng chặng đua (Lap Conservation Balance)
    current_sum = sum(l for _, l in repaired)
    diff = total_laps - current_sum

    if diff > 0:
        # THIẾU VÒNG (ΔN > 0): Bù thêm vòng vào stint có tốc độ mòn thấp nhất và xa vách lốp nhất
        for _ in range(diff):
            best_idx = 0
            best_score = -float('inf')
            for i, (c, l) in enumerate(repaired):
                cliff = c_limits.get(c, 35)
                capacity = cliff - l
                grad = tyre_deg_derivative(c, l, d_coeffs)
                if capacity > 0:
                    score = capacity * 2.0 - grad * 10.0
                else:
                    score = capacity * 10.0 - grad * 20.0
                if score > best_score:
                    best_score = score
                    best_idx = i
            repaired[best_idx][1] += 1

    elif diff < 0:
        # THỪA VÒNG (ΔN < 0): Khấu trừ vòng ở stint có tốc độ mòn nguy hiểm nhất
        abs_diff = abs(diff)
        for _ in range(abs_diff):
            valid_indices = [i for i in range(len(repaired)) if repaired[i][1] > effective_min_len]
            if not valid_indices:
                break
            worst_idx = valid_indices[0]
            worst_score = -float('inf')
            for i in valid_indices:
                c, l = repaired[i]
                cliff = c_limits.get(c, 35)
                over_cliff = max(0, l - cliff)
                grad = tyre_deg_derivative(c, l, d_coeffs)
                score = over_cliff * 20.0 + grad * 5.0 + (l / total_laps)
                if score > worst_score:
                    worst_score = score
                    worst_idx = i
            repaired[worst_idx][1] -= 1

    # Bước 4: Bảo đảm nghiêm ngặt bất biến tổng số vòng
    final_sum = sum(l for _, l in repaired)
    if final_sum != total_laps:
        discrepancy = total_laps - final_sum
        if discrepancy > 0:
            max_idx = max(range(len(repaired)), key=lambda i: repaired[i][1])
            repaired[max_idx][1] += discrepancy
        else:
            to_remove = abs(discrepancy)
            while to_remove > 0:
                valid_idx = [i for i in range(len(repaired)) if repaired[i][1] > effective_min_len]
                if valid_idx:
                    target_i = max(valid_idx, key=lambda i: repaired[i][1])
                    repaired[target_i][1] -= 1
                    to_remove -= 1
                else:
                    if len(repaired) > 1:
                        repaired[0][1] += repaired[1][1] - to_remove
                        repaired.pop(1)
                        to_remove = 0
                    else:
                        repaired[0][1] = total_laps
                        to_remove = 0

    # Bước 5: Kiểm tra lần cuối luật FIA
    if effective_min_compounds >= 2 and len(repaired) >= 2:
        final_comps = [c for c, _ in repaired]
        if len(set(final_comps)) < 2:
            repaired[0][0] = 'Hard' if repaired[-1][0] != 'Hard' else 'Medium'

    return [(str(c), int(l)) for c, l in repaired]


def adaptive_crossover(
    parent1: List[Tuple[str, int]],
    parent2: List[Tuple[str, int]],
    total_laps: int = 53,
    pc: float = 0.85,
    cliff_limits: Optional[Dict[str, int]] = None,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None,
    min_compounds: int = 2,
    min_stints: int = 2
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """Toán tử lai ghép mốc pit chuẩn hóa (Normalized Stint Crossover)."""
    if random.random() > pc:
        return [tuple(s) for s in parent1], [tuple(s) for s in parent2]

    len1 = len(parent1)
    len2 = len(parent2)

    if len1 == len2 and len1 > 1:
        pt = random.randint(1, len1 - 1)
        c1 = parent1[:pt] + parent2[pt:]
        c2 = parent2[:pt] + parent1[pt:]
    else:
        c1 = [list(s) for s in parent1]
        c2 = [list(s) for s in parent2]
        if random.random() < 0.5:
            c1[0][0] = parent2[0][0]
            c2[0][0] = parent1[0][0]
        else:
            c1[-1][0] = parent2[-1][0]
            c2[-1][0] = parent1[-1][0]

    return (
        physics_guided_repair(c1, total_laps, cliff_limits, deg_coeffs, min_compounds, min_stints),
        physics_guided_repair(c2, total_laps, cliff_limits, deg_coeffs, min_compounds, min_stints)
    )


def tri_level_mutation(
    individual: List[Tuple[str, int]],
    total_laps: int = 53,
    pm: float = 0.20,
    cliff_limits: Optional[Dict[str, int]] = None,
    deg_coeffs: Optional[Dict[str, Tuple[float, float]]] = None,
    min_compounds: int = 2,
    min_stints: int = 2
) -> List[Tuple[str, int]]:
    """Toán tử Đột biến Đa hình thái 3 Cấp độ (Tri-Level Polymorphic Mutation: Micro, Meso, Macro)."""
    if random.random() > pm:
        return [tuple(s) for s in individual]

    if not individual:
        return physics_guided_repair([], total_laps, cliff_limits, deg_coeffs, min_compounds, min_stints)

    mutated = [list(s) for s in individual]
    rand_choice = random.random()

    # CẤP ĐỘ 1: Micro-mutation (60%)
    if rand_choice < 0.60:
        if len(mutated) > 1:
            idx = random.randint(0, len(mutated) - 2)
            delta = random.choice([-2, -1, 1, 2])
            if (mutated[idx][1] + delta >= MIN_STINT_LENGTH and 
                mutated[idx + 1][1] - delta >= MIN_STINT_LENGTH):
                mutated[idx][1] += delta
                mutated[idx + 1][1] -= delta
        else:
            idx = 0
            current_comp = mutated[idx][0]
            other_comps = [c for c in COMPOUNDS if c != current_comp]
            mutated[idx][0] = random.choice(other_comps)

    # CẤP ĐỘ 2: Meso-mutation (25%)
    elif rand_choice < 0.85:
        idx = random.randint(0, len(mutated) - 1)
        current_comp = mutated[idx][0]
        other_comps = [c for c in COMPOUNDS if c != current_comp]
        mutated[idx][0] = random.choice(other_comps)

    # CẤP ĐỘ 3: Macro-mutation (15%) - Split / Merge Stint
    else:
        num_stints = len(mutated)

        if num_stints == 1:
            orig_comp, orig_len = mutated[0]
            if orig_len >= MIN_STINT_LENGTH * 2:
                split_pt = random.randint(MIN_STINT_LENGTH, orig_len - MIN_STINT_LENGTH)
                new_comp = random.choice([c for c in COMPOUNDS if c != orig_comp])
                mutated = [[orig_comp, split_pt], [new_comp, orig_len - split_pt]]
            else:
                other_comps = [c for c in COMPOUNDS if c != orig_comp]
                mutated[0][0] = random.choice(other_comps)

        elif num_stints == 2:
            longest_idx = max(range(len(mutated)), key=lambda i: mutated[i][1])
            orig_comp, orig_len = mutated[longest_idx]
            if orig_len >= MIN_STINT_LENGTH * 2:
                split_pt = random.randint(MIN_STINT_LENGTH, orig_len - MIN_STINT_LENGTH)
                new_comp = random.choice([c for c in COMPOUNDS if c != orig_comp])
                new_stints = [
                    [orig_comp, split_pt],
                    [new_comp, orig_len - split_pt]
                ]
                mutated = mutated[:longest_idx] + new_stints + mutated[longest_idx + 1:]

        elif num_stints == 3:
            if random.random() < 0.5:
                longest_idx = max(range(len(mutated)), key=lambda i: mutated[i][1])
                orig_comp, orig_len = mutated[longest_idx]
                if orig_len >= MIN_STINT_LENGTH * 2:
                    split_pt = random.randint(MIN_STINT_LENGTH, orig_len - MIN_STINT_LENGTH)
                    new_comp = random.choice([c for c in COMPOUNDS if c != orig_comp])
                    new_stints = [
                        [orig_comp, split_pt],
                        [new_comp, orig_len - split_pt]
                    ]
                    mutated = mutated[:longest_idx] + new_stints + mutated[longest_idx + 1:]
            else:
                idx = 0 if (mutated[0][1] + mutated[1][1] <= mutated[1][1] + mutated[2][1]) else 1
                c1, l1 = mutated[idx]
                c2, l2 = mutated[idx + 1]
                merged_len = l1 + l2
                if merged_len > 25:
                    merged_comp = 'Hard'
                elif merged_len > 18:
                    merged_comp = 'Medium'
                else:
                    merged_comp = c1 if c1 in ['Medium', 'Hard'] else c2
                mutated = mutated[:idx] + [[merged_comp, merged_len]] + mutated[idx + 2:]

        else:
            idx = random.randint(0, len(mutated) - 2)
            c1, l1 = mutated[idx]
            c2, l2 = mutated[idx + 1]
            merged_len = l1 + l2
            merged_comp = 'Hard' if merged_len > 25 else ('Medium' if merged_len > 18 else c1)
            mutated = mutated[:idx] + [[merged_comp, merged_len]] + mutated[idx + 2:]

    return physics_guided_repair(mutated, total_laps, cliff_limits, deg_coeffs, min_compounds, min_stints)


# Aliases for backward compatibility
repair_operator = physics_guided_repair
adaptive_mutation = tri_level_mutation
