# Hệ thống ký hiệu, đơn vị và ý nghĩa vật lý

| Ký hiệu | Tên gọi | Đơn vị | Miền giá trị | Ý nghĩa vật lý |
| :--- | :--- | :--- | :--- | :--- |
| $c$ | Hợp chất lốp | – | {Soft, Medium, Hard} | Mã định danh theo chuẩn FIA |
| $a$ | Tuổi lốp | vòng | $[1, L_{\text{max}}(c) + 10]$ | Số vòng tích lũy trên bộ lốp hiện tại |
| $i$ | Thứ tự vòng đua | vòng | $\{1, \dots, N\}$ | Vị trí vòng trong chặng đua |
| $N$ | Tổng cự ly | vòng | Monza: 53; Silverstone: 52 | Chiều dài danh nghĩa của Grand Prix |
| $t_{\text{base}}(c)$ | Thời gian cơ sở | s | 81.0 – 92.0 | Tốc độ lý thuyết: lốp mới, cạn xăng, đường bám |
| $d_1(c)$ | Hệ số suy giảm tuyến tính | s/vòng | 0.030 – 0.160 | Mài mòn cơ học theo quy luật Archard |
| $d_2(c)$ | Hệ số suy giảm phi tuyến | s/vòng$^2$ | 0.0008 – 0.0070 | Gia tốc thoái hóa nhiệt, Tyre Cliff |
| $\alpha_{\text{fuel}}$ | Hệ số tiêu hao nhiên liệu | s/vòng | 0.055 – 0.065 | Xe nhẹ đi do đốt 1.6 kg/vòng |
| $\gamma_{\text{track}}$ | Hệ số cao su bám đường | s/vòng | 0.020 – 0.028 | Mặt đường bám hơn do bám dính cao su |
| $L_{\text{max}}(c)$ | Ngưỡng tuổi thọ giới hạn | vòng | 18 – 48 | Khuyến cáo Pirelli, vượt ngưỡng đối mặt nổ lốp |
| $T_{\text{pit}}$ | Thời gian mất khi vào pit | s | 20.0 – 25.0 | Thời gian tổn hao trong pit lane và thay lốp |



---# So sánh các thuật toán tối ưu chiến lược (30 random seeds độc lập tại Monza)

| Tiêu chí | Bellman DP | Greedy Baseline | Standard GA | Adaptive GA (TV3) |
| :--- | :--- | :--- | :--- | :--- |
| **Chiến lược** | M(20) $\to$ S(14) $\to$ M(19) | M(28) $\to$ H(25) | M(20) $\to$ S(14) $\to$ M(19) | M(20) $\to$ S(14) $\to$ M(19) |
| **Số lần pit $K$** | 2 | 1 | 2 | 2 |
| **Vòng vào pit** | 20, 34 | 28 | 20, 34 | 20, 34 |
| **Thời gian tốt nhất (s)** | 4497.997 | 4510.615 | 4497.997 | 4497.997 |
| **Thời gian trung bình (s)**| 4497.997 | 4510.615 | 4497.997 | 4497.997 |
| **Mean gap (%)** | 0.0000 | +0.2805 | $8.09 \times 10^{-15}$ | $2.43 \times 10^{-14}$ |
| **Thời gian chạy** | 506.5 ms | < 1.0 ms | 1214.3 ms | 1296.5 ms |

**Nhận xét**:
1. **DP và AGA vượt Greedy 12.618 s**: Kỹ sư bảo thủ theo trực giác chọn 1-stop Medium(28) $\to$ Hard(25) mất 4510.615 s. Mô hình giải tích của TV3 chứng minh rằng dừng 2 lần (Medium 20 $\to$ Soft 14 $\to$ Medium 19) dù mất thêm 23.2 s pit-loss vẫn về đích sớm hơn 12.618 s (hơn nửa vòng đua).
2. **AGA tiệm cận tối ưu tuyệt đối**: Nhờ toán tử sửa chữa dẫn hướng bằng gradient vật lý $\nabla t_{\text{deg}}$, AGA đạt đúng nghiệm toàn cục của DP ở cả 30/30 seed với sai số dấu phẩy động chỉ $10^{-14}\%$.

# Phân bố rủi ro Monte Carlo với Safety Car (500 lượt, quá trình Poisson $\lambda = 0.3$)

| Chỉ số | 1-Stop (M-H: 26-27) | 2-Stop (S-M-H: 13-13-27) | Nhận định kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Trung bình (s)** | 4547.246 | 4621.292 | 1-Stop nhanh hơn 74.046 s trên bình diện xác suất |
| **Độ lệch chuẩn $\sigma$ (s)**| 113.803 | 159.675 | 1-Stop ổn định hơn, ít biến động |
| **P5, Best case (s)** | 4508.864 | 4509.015 | Tương đương khi SC xuất hiện đúng cửa sổ pit |
| **P95, Worst case (s)**| 4857.048 | 4875.909 | 1-Stop có rủi ro đuôi (tail risk) thấp hơn |
| **Tối đa (s)** | 4964.512 | 5171.141 | 2-Stop chậm hơn tới 206.6 s khi SC rơi vào thời điểm bất lợi |

**Giải thích hiện tượng**: Trong điều kiện lý tưởng đường trống không SC, 2-stop nhanh hơn 1-stop. Nhưng khi có Safety Car ngẫu nhiên, 2-stop phải pit hai lần nên rủi ro "mình pit lúc cờ xanh còn đối thủ pit lúc cờ vàng" cao gấp đôi. Điều này giải thích vì sao Red Bull của Max Verstappen tại Monza 2023 ưu tiên 1-stop để triệt tiêu tail risk.

### Mô phỏng đa xe: Dirty Air và Strategy Flipping
Khi bám đuôi đối thủ trong khoảng cách $\Delta t_{\text{gap}} < 1.5\text{ s}$, xe bị mất downforce, trượt bánh nhiều hơn và bị phạt $+0.35\text{ s/vòng}$ (dirty air penalty).
- Khi chạy một mình (clean air): Chiến lược 2-stop nhanh hơn 1-stop 3.421 s nhờ độ bám lốp mới.
- Khi bị kẹt trong đoàn xe (DRS train): Việc pit 2 lần đẩy xe rơi ngược lại vào đoàn xe chậm 2 lần. Chỉ cần bị kẹt 10 vòng ($10 \times 0.35 = 3.5\text{ s}$) là toàn bộ lợi thế 3.4 s của lốp mới bị triệt tiêu hoàn toàn. Do đó, mô hình mòn lốp phải luôn phối hợp chặt chẽ với mô hình vị trí đường đua (track position).

---

# Cấu trúc Thư mục và Hướng dẫn Sử dụng Mã nguồn

### Sơ đồ cấu trúc thư mục:
```
F1_Optimization-/
├── tyre/
│   ├── __init__.py                # Package root exports
│   ├── metrics.py                 # R2, R2_adj, RMSE, MAE, MAPE, AIC, BIC (zero comments)
│   ├── fitter.py                  # WLS, Tikhonov lambda=1e-9, Huber IRLS, Age weights (zero comments)
│   ├── derivatives.py             # Marginal wear, 2nd deriv, discrete jump, O(1) stint sum, GA fix (zero comments)
│   ├── thermal.py                 # Semi-empirical temperature model, sensitivity curves (zero comments)
│   ├── simulator.py               # Race simulator, Bellman DP, Adaptive GA, Monte Carlo, Dirty air (zero comments)
│   ├── train.py                   # Automated 7-step CLI pipeline (zero comments)
│   ├── DOCUMENTATION.md           # Master technical & mathematical documentation
│   ├── models/
│   │   ├── tyre_params_monza.json
│   │   ├── tyre_params_silverstone.json
│   │   ├── lookup_tensor_monza.json
│   │   └── lookup_tensor_silverstone.json
│   ├── figures/
│   │   ├── fig_tyre_temperature_sensitivity.png
│   │   ├── fit_validation_monza.png
│   │   └── fit_validation_silverstone.png
│   └── docs/
│       ├── tyre_physics_spec.md
│       ├── tyre_sensitivity_analysis.md
│       ├── section_3_1_and_4_1_elsevier.md
│       └── slide_seminar_tv3.md
├── src/
│   ├── tyre_model/                # Direct module compatibility bridges (zero comments)
│   └── simulation/                # Simulation compatibility bridges (zero comments)
└── DOCUMENTATION.md               # Root master document
```

### Hướng dẫn chạy nhanh:
1. **Huấn luyện mô hình lốp qua CLI**:
   ```bash
   python tyre/train.py --circuit monza --weighting inverse_age_variance --seed 42
   python tyre/train.py --circuit silverstone --weighting inverse_age_variance --seed 42
   ```

2. **Chạy mô phỏng đối chuẩn (DP, Greedy, AGA, Monte Carlo, Dirty Air)**:
   ```bash
   python -c "
   from tyre.simulator import RaceSimulator
   import json
   with open('tyre/models/tyre_params_monza.json') as f:
       cfg = json.load(f)
   sim = RaceSimulator(cfg['compounds'])
   print('DP:', sim.solve_bellman_dp())
   print('Greedy:', sim.solve_greedy())
   print('AGA:', sim.solve_adaptive_ga())
   "
   ```

3. **Vẽ biểu đồ độ nhạy nhiệt độ**:
   ```bash
   python -c "
   from tyre.thermal import plot_temperature_sensitivity
   params = {'Soft': {'d1': 0.12, 'd2': 0.005, 'l_max': 22}, 'Medium': {'d1': 0.07, 'd2': 0.002, 'l_max': 35}, 'Hard': {'d1': 0.04, 'd2': 0.001, 'l_max': 48}}
   plot_temperature_sensitivity(params)
   "
   ```
