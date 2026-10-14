from typing import Dict, List, Tuple, Any, Optional
import itertools
import numpy as np
from tyre.derivatives import (
    marginal_degradation,
    closed_form_stint_lap_time,
    fix_total_laps
)

class RaceSimulator:
    def __init__(
        self,
        circuit_params: Dict[str, Any],
        total_laps: int = 53,
        alpha_fuel: float = 0.058,
        gamma_track: float = 0.022,
        t_pit: float = 23.2
    ) -> None:
        self.circuit_params = circuit_params
        self.total_laps = total_laps
        self.alpha_fuel = alpha_fuel
        self.gamma_track = gamma_track
        self.t_pit = t_pit

    def lap_time(
        self,
        compound: str,
        age: int,
        lap_idx: int,
        dirty_air: bool = False
    ) -> float:
        p = self.circuit_params[compound]
        base = p["t_base"]
        deg = p["d1"] * age + p["d2"] * (age ** 2)
        fuel = self.alpha_fuel * (self.total_laps - lap_idx)
        track = self.gamma_track * lap_idx
        traffic_penalty = 0.35 if dirty_air else 0.0
        return base + deg + fuel - track + traffic_penalty

    def evaluate_stint(self, compound: str, length: int, start_lap: int) -> float:
        p = self.circuit_params[compound]
        return closed_form_stint_lap_time(
            length=length,
            start_lap=start_lap,
            total_race_laps=self.total_laps,
            t_base=p["t_base"],
            d1=p["d1"],
            d2=p["d2"],
            alpha_fuel=self.alpha_fuel,
            gamma_track=self.gamma_track
        )

    def evaluate_strategy(
        self,
        compounds: List[str],
        stint_lengths: List[int]
    ) -> float:
        if sum(stint_lengths) != self.total_laps:
            return float("inf")
        if len(set(compounds)) < 2:
            return float("inf")
            
        total_time = 0.0
        curr_lap = 1
        num_stops = len(stint_lengths) - 1
        
        for c, l_len in zip(compounds, stint_lengths):
            total_time += self.evaluate_stint(c, l_len, curr_lap)
            curr_lap += l_len
            
        total_time += num_stops * self.t_pit
        return total_time

    def solve_bellman_dp(self, max_stops: int = 2) -> Dict[str, Any]:
        available_compounds = list(self.circuit_params.keys())
        best_time = float("inf")
        best_strategy = {}

        for k in range(1, max_stops + 1):
            for c_seq in itertools.product(available_compounds, repeat=k + 1):
                if len(set(c_seq)) < 2:
                    continue
                
                valid_bounds = True
                for c in c_seq:
                    if self.circuit_params[c]["l_max"] < 4:
                        valid_bounds = False
                        break
                if not valid_bounds:
                    continue
                    
                if k == 1:
                    c1, c2 = c_seq
                    l1_max = min(self.total_laps - 4, int(self.circuit_params[c1]["l_max"]))
                    l2_max = int(self.circuit_params[c2]["l_max"])
                    for l1 in range(4, l1_max + 1):
                        l2 = self.total_laps - l1
                        if 4 <= l2 <= l2_max:
                            t = self.evaluate_strategy([c1, c2], [l1, l2])
                            if t < best_time:
                                best_time = t
                                best_strategy = {
                                    "stops": 1,
                                    "compounds": [c1, c2],
                                    "stint_lengths": [l1, l2],
                                    "pit_laps": [l1],
                                    "total_time": t
                                }
                elif k == 2:
                    c1, c2, c3 = c_seq
                    l1_max = min(self.total_laps - 8, int(self.circuit_params[c1]["l_max"]))
                    l2_max = int(self.circuit_params[c2]["l_max"])
                    l3_max = int(self.circuit_params[c3]["l_max"])
                    
                    for l1 in range(4, l1_max + 1):
                        rem1 = self.total_laps - l1
                        cur_l2_max = min(rem1 - 4, l2_max)
                        for l2 in range(4, cur_l2_max + 1):
                            l3 = rem1 - l2
                            if 4 <= l3 <= l3_max:
                                t = self.evaluate_strategy([c1, c2, c3], [l1, l2, l3])
                                if t < best_time:
                                    best_time = t
                                    best_strategy = {
                                        "stops": 2,
                                        "compounds": [c1, c2, c3],
                                        "stint_lengths": [l1, l2, l3],
                                        "pit_laps": [l1, l1 + l2],
                                        "total_time": t
                                    }

        return best_strategy

    def solve_greedy(self) -> Dict[str, Any]:
        c1 = "Medium"
        c2 = "Hard"
        l_max_m = self.circuit_params[c1]["l_max"]
        l1 = int(round(0.80 * l_max_m))
        l2 = self.total_laps - l1
        t = self.evaluate_strategy([c1, c2], [l1, l2])
        return {
            "stops": 1,
            "compounds": [c1, c2],
            "stint_lengths": [l1, l2],
            "pit_laps": [l1],
            "total_time": t
        }

    def solve_adaptive_ga(
        self,
        generations: int = 150,
        pop_size: int = 50,
        seed: int = 42
    ) -> Dict[str, Any]:
        rng = np.random.default_rng(seed)
        compounds_pool = ["Medium", "Soft", "Medium"]
        
        population: List[List[int]] = []
        for _ in range(pop_size):
            cuts = sorted(rng.choice(np.arange(10, self.total_laps - 10), size=2, replace=False))
            l1 = int(cuts[0])
            l2 = int(cuts[1] - cuts[0])
            l3 = int(self.total_laps - cuts[1])
            repaired = fix_total_laps([l1, l2, l3], compounds_pool, self.total_laps, self.circuit_params)
            population.append(repaired)
            
        best_lengths = population[0]
        best_time = self.evaluate_strategy(compounds_pool, best_lengths)
        
        for _ in range(generations):
            fitness = [1.0 / self.evaluate_strategy(compounds_pool, ind) for ind in population]
            fit_probs = np.array(fitness) / sum(fitness)
            
            new_pop: List[List[int]] = []
            elite_idx = int(np.argmax(fitness))
            new_pop.append(list(population[elite_idx]))
            
            while len(new_pop) < pop_size:
                p1_idx, p2_idx = rng.choice(pop_size, size=2, p=fit_probs)
                parent1, parent2 = population[p1_idx], population[p2_idx]
                
                alpha = rng.uniform(0.2, 0.8)
                child = [
                    int(round(alpha * parent1[0] + (1 - alpha) * parent2[0])),
                    int(round(alpha * parent1[1] + (1 - alpha) * parent2[1])),
                    int(round(alpha * parent1[2] + (1 - alpha) * parent2[2]))
                ]
                
                if rng.random() < 0.2:
                    m_idx = rng.integers(0, 3)
                    child[m_idx] += int(rng.choice([-2, -1, 1, 2]))
                    
                child = [max(4, val) for val in child]
                repaired = fix_total_laps(child, compounds_pool, self.total_laps, self.circuit_params)
                new_pop.append(repaired)
                
            population = new_pop
            for ind in population:
                val = self.evaluate_strategy(compounds_pool, ind)
                if val < best_time:
                    best_time = val
                    best_lengths = list(ind)
                    
        return {
            "stops": 2,
            "compounds": compounds_pool,
            "stint_lengths": best_lengths,
            "pit_laps": [best_lengths[0], best_lengths[0] + best_lengths[1]],
            "total_time": best_time
        }

    def simulate_monte_carlo_sc(
        self,
        num_simulations: int = 500,
        poisson_rate: float = 0.3,
        seed: int = 42
    ) -> Dict[str, Any]:
        rng = np.random.default_rng(seed)
        
        def run_sim(compounds: List[str], lengths: List[int]) -> np.ndarray:
            times = np.zeros(num_simulations, dtype=np.float64)
            pit_laps = np.cumsum(lengths)[:-1]
            nominal_total = self.evaluate_strategy(compounds, lengths)
            
            for s in range(num_simulations):
                num_sc = rng.poisson(poisson_rate)
                total_time = nominal_total
                
                if num_sc > 0:
                    sc_starts = rng.integers(1, self.total_laps - 5, size=num_sc)
                    for sc_start in sc_starts:
                        sc_duration = rng.integers(3, 6)
                        sc_window = set(range(sc_start, sc_start + sc_duration))
                        
                        total_time += sc_duration * 18.0
                        
                        for p_lap in pit_laps:
                            if p_lap in sc_window:
                                total_time -= 11.7
                            elif abs(p_lap - sc_start) <= 2:
                                total_time += 14.5
                                
                times[s] = total_time
            return times

        times_1stop = run_sim(["Medium", "Hard"], [26, 27])
        times_2stop = run_sim(["Soft", "Medium", "Hard"], [13, 13, 27])
        
        def summarize(arr: np.ndarray) -> Dict[str, float]:
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "p5": float(np.percentile(arr, 5)),
                "p95": float(np.percentile(arr, 95)),
                "max": float(np.max(arr))
            }

        return {
            "1_stop": summarize(times_1stop),
            "2_stop": summarize(times_2stop)
        }

    def simulate_dirty_air_impact(
        self,
        clean_strategy: Tuple[List[str], List[int]],
        traffic_laps: int = 10
    ) -> Dict[str, float]:
        compounds, lengths = clean_strategy
        clean_time = self.evaluate_strategy(compounds, lengths)
        dirty_time = clean_time + traffic_laps * 0.35
        return {
            "clean_time": clean_time,
            "dirty_time": dirty_time,
            "delta": dirty_time - clean_time
        }
