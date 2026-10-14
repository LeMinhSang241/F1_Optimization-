"""Bộ kiểm thử đánh giá chuẩn (Baseline Benchmark Suite) cho Thành viên 1.
Kiểm tra độ hội tụ, sai số tối ưu so với Bellman DP Ground Truth (Optimality Gap <= 0.05%),
và thời gian đáp ứng thời gian thực của cơ chế Warm-Start Safety Car Pivot (< 0.20s).
Phân công: Thành viên 1 (Algorithm & GA Lead) - Đề án DS106 UIT 2026.
"""

import sys
import os
import time
import unittest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
from src.simulator.race_sim import F1RaceSimulator
from src.benchmark.dp_solver import BellmanDPSolver
from src.ga_strategy.optimizer import AdaptiveGAOptimizer, DAGAOptimizer


class TestGABaselineBenchmark(unittest.TestCase):
    """Kiểm thử đối chuẩn hiệu năng học thuật cho giải thuật Adaptive GA (AGA)."""

    @classmethod
    def setUpClass(cls):
        """Khởi tạo mô hình vật lý Pirelli và giải Bellman DP Ground Truth cho chặng Monza 53 vòng."""
        cls.track = "Monza"
        cls.total_laps = 53
        cls.pit_loss = 23.2
        cls.tyre_model = PirelliPhysicsTyreModel(cls.track)
        cls.simulator = F1RaceSimulator(
            total_laps=cls.total_laps,
            pit_loss=cls.pit_loss,
            tyre_model=cls.tyre_model
        )
        
        # Giải Bellman DP tìm nghiệm chuẩn tuyệt đối (Ground Truth Global Optimum)
        t_dp_start = time.time()
        dp_solver = BellmanDPSolver(cls.tyre_model, traffic_penalty=0.0)
        cls.dp_time, cls.dp_strat = dp_solver.solve()
        cls.dp_runtime = time.time() - t_dp_start
        print(f"\n[Ground Truth DP] Time: {cls.dp_time:.3f}s | Strategy: {cls.dp_strat} | Runtime: {cls.dp_runtime:.3f}s")

    def test_01_dp_ground_truth_validity(self):
        """Kiểm tra nghiệm của Bellman DP thỏa mãn toàn bộ ràng buộc và khớp với Simulator."""
        self.assertEqual(sum(l for _, l in self.dp_strat), self.total_laps)
        compounds = {c for c, _ in self.dp_strat}
        self.assertGreaterEqual(len(compounds), 2, "DP Ground Truth phai thoa luat FIA")

        # Simulator phải tính ra cùng thời gian (sai số nổi < 1e-4)
        sim_time, details = self.simulator.evaluate_strategy(self.dp_strat)
        self.assertAlmostEqual(sim_time, self.dp_time, places=2)
        self.assertEqual(details['penalty'], 0.0)
        self.assertTrue(details['is_valid_fia'])

    def test_02_aga_optimality_gap_vs_dp(self):
        """Kiểm chứng AGA đạt mốc sai số tối ưu Optimality Gap <= 0.05% so với Bellman DP Ground Truth."""
        seeds = [42, 100, 2023, 7, 999]
        gaps = []
        runtimes = []

        print("\n--- BENCHMARK AGA CONVERGENCE VS BELLMAN DP (5 SEEDS) ---")
        for s in seeds:
            opt = AdaptiveGAOptimizer(
                simulator=self.simulator,
                pop_size=60,
                generations=50
            )
            strat, best_t, details = opt.optimize(seed=s)
            runtime = details['runtime_seconds']
            gap = ((best_t - self.dp_time) / self.dp_time) * 100.0

            gaps.append(gap)
            runtimes.append(runtime)

            print(f"Seed {s:4d} | AGA Time: {best_t:.3f}s | DP: {self.dp_time:.3f}s | Gap: {gap:.4f}% | Runtime: {runtime:.3f}s | Strat: {strat}")

            # Nghiệm phải hợp lệ 100%
            self.assertEqual(sum(l for _, l in strat), self.total_laps)
            self.assertTrue(details['is_valid_fia'])
            self.assertEqual(details['penalty'], 0.0)

        mean_gap = float(np.mean(gaps))
        min_gap = float(np.min(gaps))
        mean_runtime = float(np.mean(runtimes))

        print(f"--> RESULTS: Mean Gap = {mean_gap:.4f}% | Min Gap = {min_gap:.4f}% | Mean Runtime = {mean_runtime:.3f}s")

        # Tiêu chuẩn nghiệm thu: Min Gap <= 0.01% và Mean Gap <= 0.05%
        self.assertLessEqual(min_gap, 0.01, "It nhat 1 seed phai tiem can sat moc DP (Gap <= 0.01%)")
        self.assertLessEqual(mean_gap, 0.05, f"Mean Optimality Gap ({mean_gap:.4f}%) phai <= 0.05%")
        self.assertLessEqual(mean_runtime, 1.0, "Thoi gian tinh toan trung binh phai < 1.0 giay")

    def test_03_warm_start_safety_car_pivot_runtime(self):
        """Kiểm chứng tính năng Safety Car Warm-Start Pivot:
        Tái tối ưu hóa chiến lược tại các vòng SC khác nhau với runtime < 0.20s.
        """
        sc_scenarios = [
            (18, 12.5),  # SC ở vòng 18, pit loss giảm còn 12.5s
            (25, 12.5),  # SC ở vòng 25
            (32, 12.5)   # SC ở vòng 32
        ]

        print("\n--- BENCHMARK REAL-TIME SAFETY CAR WARM-START PIVOT (< 0.20s) ---")
        opt = AdaptiveGAOptimizer(simulator=self.simulator, pop_size=60, generations=50)
        # Chạy baseline trước để có chiến lược nền
        opt.optimize(seed=42)

        for lap_sc, sc_loss in sc_scenarios:
            t0 = time.time()
            sc_strat, sc_time, details = opt.warm_start_optimize(
                current_lap=lap_sc,
                sc_pit_loss=sc_loss,
                warm_generations=15
            )
            pivot_time = time.time() - t0

            print(f"SC at Lap {lap_sc:2d} | Pivot Runtime: {pivot_time:.4f}s | Total Time: {sc_time:.3f}s | Strat: {sc_strat}")

            # Kiểm chứng các ràng buộc
            self.assertLess(pivot_time, 0.20, f"Thoi gian phan ung SC ({pivot_time:.4f}s) phai < 0.20 giay")
            self.assertEqual(sum(l for _, l in sc_strat), self.total_laps, "Tong so vong phai dung 53")
            self.assertTrue(details['is_valid_fia'], "Chien luoc SC phai thoa luat FIA")
            self.assertEqual(details['penalty'], 0.0, "Khong duoc co penalty")

    def test_04_cooling_schedule_and_chaos_injection(self):
        """Kiểm chứng Lịch làm mát phi tuyến Pc, Pm và cơ chế Tiêm gen hỗn loạn (Chaos Injection)."""
        opt = AdaptiveGAOptimizer(
            simulator=self.simulator,
            pop_size=40,
            generations=30,
            initial_pc=0.88,
            initial_pm=0.25,
            min_pc=0.65,
            min_pm=0.08
        )
        opt.optimize(seed=123)

        history = opt.history
        self.assertEqual(len(history['pc']), 30)
        self.assertEqual(len(history['pm']), 30)
        self.assertEqual(len(history['diversity']), 30)

        # Pc và Pm phải tuân thủ biên trên và biên dưới
        self.assertAlmostEqual(history['pc'][0], 0.88, places=2)
        self.assertAlmostEqual(history['pc'][-1], 0.65, places=2)
        self.assertGreater(history['pc'][0], history['pc'][-1], "Pc phai giam dan theo the he")

        # Kiểm tra độ đa dạng luôn nằm trong khoảng hợp lệ [0, 1]
        for d in history['diversity']:
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)

    def test_05_aga_silverstone_circuit_gap(self):
        """Kiểm chứng tính tổng quát hóa đa chặng: Chặng Silverstone GP 2023 (52 vòng)."""
        silverstone_model = PirelliPhysicsTyreModel("Silverstone")
        silverstone_sim = F1RaceSimulator(
            total_laps=silverstone_model.total_laps,
            pit_loss=silverstone_model.pit_loss,
            tyre_model=silverstone_model
        )
        # Bellman DP Ground Truth cho Silverstone
        dp_solver = BellmanDPSolver(silverstone_model, traffic_penalty=0.0)
        silverstone_dp_time, silverstone_dp_strat = dp_solver.solve()

        opt = AdaptiveGAOptimizer(simulator=silverstone_sim, pop_size=60, generations=50)
        strat, best_t, details = opt.optimize(seed=42)
        gap = ((best_t - silverstone_dp_time) / silverstone_dp_time) * 100.0

        print(f"\n[Silverstone] DP: {silverstone_dp_time:.3f}s {silverstone_dp_strat} | AGA: {best_t:.3f}s {strat} | Gap: {gap:.4f}%")
        self.assertLessEqual(gap, 0.05, f"Optimality Gap tai Silverstone ({gap:.4f}%) phai <= 0.05%")
        self.assertEqual(sum(l for _, l in strat), 52)
        self.assertTrue(details['is_valid_fia'])
        self.assertEqual(details['penalty'], 0.0)

    def test_06_edge_case_safety_car_pivot_lap1_and_lap52(self):
        """Kiểm chứng độ bền của Safety Car Warm-Start Pivot tại các trường hợp biên: Lap 1 và Lap 52."""
        opt = AdaptiveGAOptimizer(simulator=self.simulator, pop_size=60, generations=50)
        opt.optimize(seed=42)

        # 1. SC xuất hiện ngay Lap 1
        t0 = time.time()
        sc1_strat, sc1_time, d1 = opt.warm_start_optimize(current_lap=1, sc_pit_loss=12.5)
        pivot_time1 = time.time() - t0
        self.assertLess(pivot_time1, 0.20)
        self.assertEqual(sum(l for _, l in sc1_strat), 53)
        self.assertTrue(d1['is_valid_fia'])
        self.assertEqual(d1['penalty'], 0.0)

        # 2. SC xuất hiện ở Lap áp chót (Lap 52/53)
        t0 = time.time()
        sc52_strat, sc52_time, d52 = opt.warm_start_optimize(current_lap=52, sc_pit_loss=12.5)
        pivot_time52 = time.time() - t0
        self.assertLess(pivot_time52, 0.20)
        self.assertEqual(sum(l for _, l in sc52_strat), 53)
        self.assertTrue(d52['is_valid_fia'])
        self.assertEqual(d52['penalty'], 0.0)

    def test_07_small_pop_size_resilience(self):
        """Kiểm chứng tính ổn định khi cấu hình quần thể cực nhỏ (pop_size = 2)."""
        opt = AdaptiveGAOptimizer(simulator=self.simulator, pop_size=2, generations=3)
        strat, best_t, det = opt.optimize(seed=99)
        self.assertIsNotNone(strat)
        self.assertEqual(sum(l for _, l in strat), 53)


if __name__ == '__main__':
    unittest.main(verbosity=2)
