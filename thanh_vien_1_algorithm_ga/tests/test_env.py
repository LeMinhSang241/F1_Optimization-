import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import pytest
except ImportError:
    pytest = None

from src.tyre_model.rcga_ensemble import RealValuedGATyreEnsemble
from src.simulator.race_sim import F1RaceSimulator
from src.ga_strategy.operators import (
    heuristic_weighted_initialization,
    repair_operator,
    adaptive_crossover,
    adaptive_mutation
)
from src.ga_strategy.optimizer import F1StrategyGAOptimizer


def test_tyre_model_prediction():
    """Kiểm tra mô hình dự đoán mòn lốp."""
    model = RealValuedGATyreEnsemble()
    t_soft_new = model.predict_lap_time('Soft', tyre_age=1, race_lap=1, total_laps=53)
    t_soft_old = model.predict_lap_time('Soft', tyre_age=15, race_lap=15, total_laps=53)
    assert t_soft_old > t_soft_new, "Lốp cũ phải chạy chậm hơn lốp mới"


def test_simulator_fia_rule():
    """Kiểm tra cơ chế phạt khi vi phạm luật FIA (chỉ dùng 1 loại lốp)."""
    sim = F1RaceSimulator(total_laps=53, pit_loss=23.2)
    # Chiến lược phạm luật: chỉ dùng Soft
    illegal_strat = [('Soft', 53)]
    total_time, details = sim.evaluate_strategy(illegal_strat)
    assert not details['is_valid_fia'], "Chiến lược 1 loại lốp phải vi phạm luật FIA"
    assert details['penalty'] >= 100000.0, "Phải bị phạt 10^5 giây"

    # Chiến lược hợp lệ: Soft + Hard
    legal_strat = [('Soft', 20), ('Hard', 33)]
    total_time_legal, details_legal = sim.evaluate_strategy(legal_strat)
    assert details_legal['is_valid_fia'], "Chiến lược dùng 2 loại lốp phải hợp lệ"
    assert details_legal['penalty'] == 0.0, "Không được bị phạt"


def test_repair_operator():
    """Kiểm tra toán tử sửa chữa luôn bảo toàn tổng số vòng đua."""
    strat = [('Soft', 15), ('Hard', 30)]  # Tổng 45 vòng, thiếu 8 vòng
    repaired = repair_operator(strat, total_laps=53)
    total_laps = sum(length for _, length in repaired)
    assert total_laps == 53, f"Tổng số vòng sau khi sửa phải đúng 53, nhưng nhận được {total_laps}"


def test_ga_optimizer_run():
    """Kiểm tra chạy nhanh bộ tối ưu hóa GA trong 3 thế hệ."""
    sim = F1RaceSimulator(total_laps=53, pit_loss=23.2)
    opt = F1StrategyGAOptimizer(simulator=sim, pop_size=10, generations=3)
    best_strat, best_time, details = opt.optimize()

    assert best_strat is not None
    assert sum(l for _, l in best_strat) == 53
    assert details['is_valid_fia']
    assert best_time < 50000  # Nghiệm hợp lệ không bị dính penalty lớn


if __name__ == '__main__':
    print("Running test_tyre_model_prediction()...")
    test_tyre_model_prediction()
    print("Running test_simulator_fia_rule()...")
    test_simulator_fia_rule()
    print("Running test_repair_operator()...")
    test_repair_operator()
    print("Running test_ga_optimizer_run()...")
    test_ga_optimizer_run()
    print("--> ALL 4 UNIT TESTS PASSED SUCCESSFULLY! <--")
