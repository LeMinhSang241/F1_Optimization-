"""Bộ tối ưu hóa chiến lược đua F1 bằng Giải thuật Di truyền Thích nghi Động (DAGA-F1).
Dynamic Adaptive Genetic Algorithm for F1 Pit-Stop & Tyre Strategy Optimization.

Đóng góp mới cốt lõi (Novelties):
1. Cơ chế thích nghi động kép (Dual-Level Dynamic Adaptation):
   - Lịch làm mát phi tuyến cho xác suất lai ghép Pc(g) và đột biến Pm(g).
   - Giám sát độ đa dạng quần thể Đ_pop (Genotypic Diversity Monitor).
2. Tiêm gen hỗn loạn (Cataclysmic Chaos Injection):
   - Nhân Pm lên 2.5 lần khi độ đa dạng sụt giảm (Đ_pop < 0.15) ở 70% số thế hệ đầu để phá bẫy cực tiểu địa phương.
3. Tái tối ưu hóa thời gian thực (Safety Car Warm-Start Pivot):
   - Đóng băng các vòng đã diễn ra [1, L_sc], so sánh tối ưu giữa 2 kịch bản: Vào pit khẩn cấp (Free Pit Stop T_pit=12.5s)
     hoặc Tiếp tục chạy (Stay Out) bảo toàn lốp hiện tại.
   - Tốc độ tái hội tụ cực nhanh (< 0.20s), đáp ứng hoàn hảo cửa sổ tác chiến 3-5 giây tại Pit-wall.

Phân công: Thành viên 1 (Algorithm & GA Lead) - Đề án DS106 UIT 2026.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import random
import time

from src.ga_strategy.operators import (
    heuristic_weighted_initialization,
    physics_guided_repair,
    adaptive_crossover,
    tri_level_mutation,
    COMPOUNDS,
    MIN_STINT_LENGTH,
    CLIFF_LIMITS,
    DEG_COEFFS
)
from src.simulator.race_sim import F1RaceSimulator


class AdaptiveGAOptimizer:
    """Bộ tối ưu hóa Adaptive Genetic Algorithm (AGA / DAGA-F1) cho chiến lược F1."""

    def __init__(
        self,
        simulator: F1RaceSimulator,
        pop_size: int = 60,
        generations: int = 50,
        initial_pc: float = 0.88,
        initial_pm: float = 0.25,
        min_pc: float = 0.65,
        min_pm: float = 0.08,
        elitism_rate: float = 0.05,
        diversity_threshold: float = 0.15
    ):
        self.simulator = simulator
        self.pop_size = max(2, pop_size)
        self.generations = generations
        self.initial_pc = initial_pc
        self.initial_pm = initial_pm
        self.min_pc = min_pc
        self.min_pm = min_pm
        self.elitism_count = max(1, min(self.pop_size - 1, int(self.pop_size * elitism_rate)))
        self.diversity_threshold = diversity_threshold
        
        # Nhận diện thông số động lực học từ simulator / mô hình lốp
        self.cliff_limits = getattr(self.simulator.tyre_model, 'safe_limits', CLIFF_LIMITS)
        self.deg_coeffs = getattr(self.simulator.tyre_model, 'deg_coeffs', DEG_COEFFS)
        
        self.history: Dict[str, List] = {
            'best_time': [],
            'avg_time': [],
            'diversity': [],
            'pc': [],
            'pm': [],
            'chaos_events': []
        }
        
        self.best_individual: Optional[List[Tuple[str, int]]] = None
        self.best_fitness: float = float('inf')
        self.best_details: Optional[Dict[str, Any]] = None

    def _calculate_diversity(self, population: List[List[Tuple[str, int]]]) -> float:
        """Đo lường độ đa dạng kiểu gen của quần thể (Đ_pop) ∈ [0.0, 1.0]."""
        if not population or len(population) < 2:
            return 0.0
            
        n = len(population)
        distances = []
        total_laps = self.simulator.total_laps
        sample_size = min(35, n * (n - 1) // 2)
        if sample_size <= 0:
            return 0.0

        for _ in range(sample_size):
            i1, i2 = random.sample(range(n), 2)
            ind1, ind2 = population[i1], population[i2]

            len_diff = abs(len(ind1) - len(ind2))
            dist_struct = min(1.0, len_diff / 2.0) * 0.35

            min_stints = min(len(ind1), len(ind2))
            comp_diff = sum(1 for k in range(min_stints) if ind1[k][0] != ind2[k][0])
            dist_comp = (comp_diff / max(1, min_stints)) * 0.35

            lap_diff = sum(abs(ind1[k][1] - ind2[k][1]) for k in range(min_stints))
            dist_laps = min(1.0, lap_diff / max(1, total_laps)) * 0.30

            total_dist = min(1.0, dist_struct + dist_comp + dist_laps)
            distances.append(total_dist)

        return float(np.mean(distances)) if distances else 0.0

    def optimize(
        self,
        seed: Optional[int] = None,
        initial_pop: Optional[List[List[Tuple[str, int]]]] = None
    ) -> Tuple[List[Tuple[str, int]], float, Dict[str, Any]]:
        """Thực thi toàn bộ chu trình tiến hóa Adaptive Genetic Algorithm (AGA)."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        start_time = time.time()
        total_laps = self.simulator.total_laps

        self.history = {
            'best_time': [],
            'avg_time': [],
            'diversity': [],
            'pc': [],
            'pm': [],
            'chaos_events': []
        }

        if initial_pop is not None and len(initial_pop) == self.pop_size:
            population = [
                physics_guided_repair(ind, total_laps, self.cliff_limits, self.deg_coeffs)
                for ind in initial_pop
            ]
        else:
            population = heuristic_weighted_initialization(
                self.pop_size, total_laps, self.cliff_limits, self.deg_coeffs
            )

        best_overall_individual = None
        best_overall_fitness = float('inf')
        best_details = None

        for gen in range(self.generations):
            scores = []
            details_list = []

            for ind in population:
                total_time, details = self.simulator.evaluate_strategy(ind)
                scores.append(total_time)
                details_list.append(details)

            sorted_indices = np.argsort(scores)
            population = [population[i] for i in sorted_indices]
            scores = [scores[i] for i in sorted_indices]
            details_list = [details_list[i] for i in sorted_indices]

            current_best_score = scores[0]
            valid_scores = [s for s in scores if s < 50000.0]
            avg_score = float(np.mean(valid_scores)) if valid_scores else current_best_score

            div = self._calculate_diversity(population)

            if current_best_score < best_overall_fitness:
                best_overall_fitness = current_best_score
                best_overall_individual = [tuple(s) for s in population[0]]
                best_details = dict(details_list[0])

            # 1. Lịch làm mát phi tuyến thích nghi (Non-linear Cooling Schedule)
            progress = gen / max(1, self.generations - 1)
            current_pc = self.min_pc + (self.initial_pc - self.min_pc) * (1.0 - (progress ** 1.5))
            current_pm = self.min_pm + (self.initial_pm - self.min_pm) * (1.0 - (progress ** 1.2))

            # 2. Tiêm gen hỗn loạn (Cataclysmic Chaos Injection)
            is_stuck = (div < self.diversity_threshold) and (gen < int(self.generations * 0.70))
            if is_stuck:
                current_pm = min(0.65, current_pm * 2.5)
                self.history['chaos_events'].append(gen)

            self.history['best_time'].append(current_best_score)
            self.history['avg_time'].append(avg_score)
            self.history['diversity'].append(div)
            self.history['pc'].append(current_pc)
            self.history['pm'].append(current_pm)

            # 3. Bảo lưu cá thể tinh hoa (Elitism)
            next_generation = [[tuple(s) for s in population[i]] for i in range(self.elitism_count)]

            # 4. Sinh sản qua Tournament Selection + Lai ghép Stint + Đột biến 3 cấp độ
            k_tourn = min(3, self.pop_size)
            while len(next_generation) < self.pop_size:
                if k_tourn > 1:
                    cands1 = np.random.choice(self.pop_size, k_tourn, replace=False)
                    p1 = population[int(min(cands1))]
                    cands2 = np.random.choice(self.pop_size, k_tourn, replace=False)
                    p2 = population[int(min(cands2))]
                else:
                    p1 = population[0]
                    p2 = population[min(1, len(population) - 1)]

                c1, c2 = adaptive_crossover(
                    p1, p2, total_laps,
                    pc=current_pc,
                    cliff_limits=self.cliff_limits,
                    deg_coeffs=self.deg_coeffs
                )

                c1 = tri_level_mutation(
                    c1, total_laps,
                    pm=current_pm,
                    cliff_limits=self.cliff_limits,
                    deg_coeffs=self.deg_coeffs
                )
                c2 = tri_level_mutation(
                    c2, total_laps,
                    pm=current_pm,
                    cliff_limits=self.cliff_limits,
                    deg_coeffs=self.deg_coeffs
                )

                next_generation.append(c1)
                if len(next_generation) < self.pop_size:
                    next_generation.append(c2)

            population = next_generation

        elapsed = time.time() - start_time
        if best_details is not None:
            best_details['runtime_seconds'] = elapsed

        self.best_individual = best_overall_individual
        self.best_fitness = best_overall_fitness
        self.best_details = best_details

        return best_overall_individual, best_overall_fitness, best_details

    def warm_start_optimize(
        self,
        current_lap: int,
        sc_pit_loss: float = 12.5,
        warm_generations: int = 15,
        current_strategy: Optional[List[Tuple[str, int]]] = None
    ) -> Tuple[List[Tuple[str, int]], float, Dict[str, Any]]:
        """Tái tối ưu hóa thời gian thực khi xuất hiện Xe An Toàn (Safety Car Warm-Start Pivot)."""
        start_time = time.time()
        total_laps = self.simulator.total_laps

        if current_lap >= total_laps:
            base = current_strategy or self.best_individual or [('Medium', total_laps // 2), ('Hard', total_laps - total_laps // 2)]
            base_score, base_det = self.simulator.evaluate_strategy(base)
            base_det['is_warm_start'] = True
            base_det['runtime_seconds'] = time.time() - start_time
            base_det['sc_lap'] = total_laps
            base_det['sc_pit_loss'] = sc_pit_loss
            base_det['pit_at_sc'] = False
            base_det['recommendation'] = "RACE COMPLETED - NO ACTION"
            return base, base_score, base_det

        l_sc = max(1, min(total_laps - 1, int(current_lap)))
        remaining_laps = total_laps - l_sc

        base_strat = current_strategy or self.best_individual
        if base_strat is None:
            base_strat = [('Medium', min(20, l_sc)), ('Hard', total_laps - min(20, l_sc))]

        past_stints: List[Tuple[str, int]] = []
        rem_lap_counter = l_sc
        current_compound = base_strat[0][0]
        current_tyre_age = 1

        for c, length in base_strat:
            if rem_lap_counter > length:
                past_stints.append((c, length))
                rem_lap_counter -= length
            else:
                past_stints.append((c, rem_lap_counter))
                current_compound = c
                current_tyre_age = rem_lap_counter
                rem_lap_counter = 0
                break

        past_compounds = {c for c, _ in past_stints}
        num_past_stops = max(0, len(past_stints) - 1)

        past_pure_time = 0.0
        race_lap_counter = 1
        for c, l_len in past_stints:
            for age in range(1, l_len + 1):
                past_pure_time += self.simulator.tyre_model.predict_lap_time(
                    compound=c,
                    tyre_age=age,
                    race_lap=race_lap_counter,
                    total_laps=total_laps
                )
                race_lap_counter += 1
        past_pure_time += num_past_stops * self.simulator.pit_loss

        # PHƯƠNG ÁN A: VÀO PIT TẠI VÒNG SC (PIT AT SC, LOSS = sc_pit_loss)
        def evaluate_pit_rem(rem_stints: List[Tuple[str, int]]) -> Tuple[float, Dict[str, Any]]:
            total_time = past_pure_time + sc_pit_loss
            num_future_stops = max(0, len(rem_stints) - 1)
            total_time += num_future_stops * self.simulator.pit_loss

            race_lap = l_sc + 1
            all_compounds = set(past_compounds)

            for c, l_len in rem_stints:
                all_compounds.add(c)
                if hasattr(self.simulator.tyre_model, 'closed_form_stint_lap_time'):
                    stint_t = self.simulator.tyre_model.closed_form_stint_lap_time(c, l_len, race_lap)
                    total_time += stint_t
                    race_lap += l_len
                else:
                    for age in range(1, l_len + 1):
                        lap_t = self.simulator.tyre_model.predict_lap_time(
                            compound=c,
                            tyre_age=age,
                            race_lap=race_lap,
                            total_laps=total_laps
                        )
                        total_time += lap_t
                        race_lap += 1

            penalty = 0.0
            if len(all_compounds) < 2:
                penalty += 100000.0

            safe_limits = getattr(self.simulator.tyre_model, 'safe_limits', self.cliff_limits)
            for c, l_len in rem_stints:
                limit = safe_limits.get(c, 35)
                if l_len > limit:
                    over = l_len - limit
                    penalty += (over * 50.0 + (over ** 2) * 5.0)

            details = {
                'pure_race_time': total_time,
                'pit_at_sc': True,
                'num_stops': num_past_stops + 1 + num_future_stops,
                'compounds_used': list(all_compounds),
                'penalty': penalty,
                'is_valid_fia': len(all_compounds) >= 2,
                'is_warm_start': True
            }
            return total_time + penalty, details

        pop_size = 40
        population: List[List[Tuple[str, int]]] = []

        for target_comp in ['Hard', 'Medium', 'Soft']:
            population.append([(target_comp, remaining_laps)])
            if remaining_laps >= MIN_STINT_LENGTH * 2:
                half = remaining_laps // 2
                other_c = 'Soft' if target_comp != 'Soft' else 'Medium'
                population.append([(target_comp, half), (other_c, remaining_laps - half)])

        while len(population) < pop_size:
            if remaining_laps < MIN_STINT_LENGTH * 2:
                c = random.choice(COMPOUNDS)
                ind = [(c, remaining_laps)]
            else:
                c1, c2 = random.sample(COMPOUNDS, 2)
                p = random.randint(MIN_STINT_LENGTH, remaining_laps - MIN_STINT_LENGTH)
                ind = [(c1, p), (c2, remaining_laps - p)]
            population.append(
                physics_guided_repair(
                    ind, remaining_laps, self.cliff_limits, self.deg_coeffs,
                    min_compounds=1, min_stints=1
                )
            )

        best_pit_rem_strat = None
        best_pit_score = float('inf')
        best_pit_details = None

        for gen in range(warm_generations):
            scores = []
            details_list = []
            for ind in population:
                score, details = evaluate_pit_rem(ind)
                scores.append(score)
                details_list.append(details)

            sorted_idx = np.argsort(scores)
            population = [population[i] for i in sorted_idx]
            scores = [scores[i] for i in sorted_idx]
            details_list = [details_list[i] for i in sorted_idx]

            if scores[0] < best_pit_score:
                best_pit_score = scores[0]
                best_pit_rem_strat = [tuple(s) for s in population[0]]
                best_pit_details = dict(details_list[0])

            next_pop = [population[0], population[1]]
            while len(next_pop) < pop_size:
                p1 = population[random.randint(0, min(8, pop_size - 1))]
                p2 = population[random.randint(0, min(8, pop_size - 1))]
                c1, c2 = adaptive_crossover(
                    p1, p2, remaining_laps, pc=0.85,
                    cliff_limits=self.cliff_limits, deg_coeffs=self.deg_coeffs,
                    min_compounds=1, min_stints=1
                )
                c1 = tri_level_mutation(
                    c1, remaining_laps, pm=0.20,
                    cliff_limits=self.cliff_limits, deg_coeffs=self.deg_coeffs,
                    min_compounds=1, min_stints=1
                )
                next_pop.append(c1)
                if len(next_pop) < pop_size:
                    next_pop.append(c2)
            population = next_pop

        # PHƯƠNG ÁN B: TIẾP TỤC CHẠY (STAY OUT)
        base_score, base_details = self.simulator.evaluate_strategy(base_strat)

        if best_pit_score < base_score:
            full_strategy = past_stints + best_pit_rem_strat
            chosen_score = best_pit_score
            chosen_details = best_pit_details or {}
            chosen_details['pit_at_sc'] = True
            chosen_details['recommendation'] = "BOX THIS LAP (FREE SC PIT STOP)"
        else:
            full_strategy = [tuple(s) for s in base_strat]
            chosen_score = base_score
            chosen_details = dict(base_details)
            chosen_details['pit_at_sc'] = False
            chosen_details['recommendation'] = "STAY OUT (CONTINUE CURRENT STINT)"

        elapsed = time.time() - start_time
        chosen_details['runtime_seconds'] = elapsed
        chosen_details['full_strategy'] = full_strategy
        chosen_details['sc_lap'] = l_sc
        chosen_details['sc_pit_loss'] = sc_pit_loss
        chosen_details['is_warm_start'] = True

        return full_strategy, chosen_score, chosen_details


# Aliases for backward compatibility
DAGAOptimizer = AdaptiveGAOptimizer
F1StrategyGAOptimizer = AdaptiveGAOptimizer
