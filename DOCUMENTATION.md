# ĐỒ ÁN MÔN HỌC DS106: TỐI ƯU HÓA VÀ ỨNG DỤNG
## TỐI ƯU HÓA CHIẾN LƯỢC PIT-STOP & QUẢN LÝ LỐP XE ĐUA CÔNG THỨC 1 (F1)

---

## 1. TỔNG QUAN BÀI TOÁN & Ý NGHĨA KỸ THUẬT

Trong các cuộc đua Công thức 1 (F1 Grand Prix), chiến lược dừng pit và quản lý lốp đóng vai trò quyết định đến hơn 60% cơ hội chiến thắng của một đội đua. Kể từ năm 2010, FIA cấm tiếp nhiên liệu trong cuộc đua (Refuelling Ban), do đó xe phải mang toàn bộ tải trọng xăng (khoảng $110\text{ kg}$) ngay từ vạch xuất phát.  
Mục tiêu là tìm kiếm một vector chiến lược dừng pit hoàn chỉnh (số lần pit, thời điểm vào pit và lựa chọn hợp chất lốp) sao cho **tổng thời gian hoàn thành chặng đua là nhỏ nhất**, đồng thời tuân thủ nghiêm ngặt các quy định an toàn và thể thao của FIA.

```
                      ┌──────────────────────────────────────────┐
                      │        KHUNG ĐỐI CHUẨN HAI TRỤ CỘT       │
                      └─────────────────────┬────────────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
     ┌─────────────────────────────┐                 ┌─────────────────────────────┐
     │  TRỤ CỘT 1: BELLMAN DP      │                 │  TRỤ CỘT 2: DAGA-F1         │
     │  (Chuẩn Đối Chứng Toàn Cục) │                 │  (Tiến Hóa Thích Nghi Động) │
     ├─────────────────────────────┤                 ├─────────────────────────────┤
     │ • Quy nạp ngược 30.088 state│                 │ • Khởi tạo có trọng số 65/30/5│
     │ • Nghiệm tối ưu toàn cục     │                 │ • Sửa nghiệm theo gradient  │
     │ • Nghiệm chuẩn: 4497.997s   │                 │ • Đột biến Split/Merge      │
     │ • Không gian bài toán tĩnh  │                 │ • Tái tối ưu SC: 5.2 - 8.6ms│
     └─────────────────────────────┘                 └─────────────────────────────┘
```

---

## 2. HỆ THỐNG KÝ HIỆU & Ý NGHĨA VẬT LÝ

| Ký hiệu | Tên gọi | Đơn vị | Miền giá trị | Ý nghĩa vật lý |
| :--- | :--- | :---: | :---: | :--- |
| $c$ | Hợp chất lốp | – | $\{\text{Soft}, \text{Medium}, \text{Hard}\}$ | Mã hợp chất theo quy định của FIA và Pirelli |
| $a$ | Tuổi lốp (Tyre Age) | vòng | $[1, L_{\max}(c) + 10]$ | Số vòng lăn bánh liên tục trên bộ lốp hiện tại |
| $i$ | Thứ tự vòng đua | vòng | $\{1, \dots, N_{\text{total}}\}$ | Vị trí vòng trong diễn biến chặng đua |
| $N_{\text{total}}$ | Tổng cự ly chặng | vòng | Monza: 53; Silverstone: 52 | Chiều dài danh nghĩa tiêu chuẩn của Grand Prix |
| $t_{\text{base}}(c)$ | Thời gian cơ sở | giây | 81.0 – 91.0 | Thời gian lý thuyết: xe cạn xăng, lốp mới, đường bám |
| $d_1(c)$ | Hệ số mài mòn tuyến tính | s/vòng | 0.040 – 0.145 | Mài mòn cơ học tự nhiên bề mặt (Graining) |
| $d_2(c)$ | Hệ số suy giảm phi tuyến | s/vòng$^2$ | 0.0010 – 0.0065 | Suy thoái nhiệt kết cấu polymer, hiện tượng Tyre Cliff |
| $\alpha_{\text{fuel}}$ | Hệ số giảm tải nhiên liệu | s/vòng | Monza: 0.058; Silverstone: 0.062 | Xe nhanh hơn qua từng vòng do đốt cháy nhiên liệu |
| $\gamma_{\text{track}}$ | Hệ số tiến hóa mặt đường | s/vòng | Monza: 0.022; Silverstone: 0.025 | Mặt đường bám hơn do cao su từ lốp miết xuống đường |
| $L_{\max}(c)$ | Ngưỡng tuổi thọ an toàn | vòng | Soft: 18–22; Med: 30–35; Hard: 42–48 | Giới hạn khuyến cáo Pirelli tránh rủi ro sụt giảm độ bám |
| $T_{\text{pit}}$ | Tổn thất thời gian vào pit | giây | Monza: 23.2; Silverstone: 21.5 | Thời gian tiêu tốn do giới hạn tốc độ $80\text{ km/h}$ trong pit lane |

---

## 3. MÔ HÌNH HÓA TOÁN HỌC CHÍNH QUY (MATHEMATICAL FORMULATION)

### 3.1. Cấu trúc Không gian Nghiệm (Chromosome Representation)
Một chiến lược đua được biểu diễn dưới dạng vector các đoạn đua liên tục (*Stint Array*):
$$\mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
Trong đó:
- $K \in \{1, 2, 3\}$: Số lần dừng pit trong chặng đua ($K+1$ stints).
- $c_k \in \{\text{Soft}, \text{Medium}, \text{Hard}\}$: Hợp chất lốp ở stint thứ $k$.
- $l_k \in \mathbb{Z}^+$: Số vòng chạy liên tục ở stint thứ $k$ ($l_k \ge 4$).

### 3.2. Hệ thống Ràng buộc
1. **(R1) Bảo toàn Tổng số vòng:** $\sum_{k=1}^{K+1} l_k = N_{\text{total}}$ (Monza: 53; Silverstone: 52).
2. **(R2) Luật lốp FIA (Sporting Regulations Art. 30.5):** Trong điều kiện khô ráo, bắt buộc sử dụng ít nhất 2 loại hợp chất lốp khác nhau:
   $$\big| \{c_1, c_2, \dots, c_{K+1}\} \big| \ge 2$$
3. **(R3) Giới hạn Cơ học Vách lốp (Pirelli Tyre Cliff):** Khuyến cáo $l_k \le L_{\max}(c_k)$.

### 3.3. Hàm Mục tiêu Toàn cục
$$\min_{\mathbf{S} \in \Omega} J(\mathbf{S}) = \sum_{k=1}^{K+1} \left( \sum_{a=1}^{l_k} t_{\text{lap}}(c_k, a, i) \right) + K \cdot T_{\text{pit}} + \Phi_{\text{FIA}}(\mathbf{S}) + \Phi_{\text{cliff}}(\mathbf{S})$$
Trong đó:
- **Phương trình phân rã thời gian vòng đua:**
  $$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) + \big[ d_1(c) a + d_2(c) a^2 \big] + \alpha_{\text{fuel}} (N_{\text{total}} - i) - \gamma_{\text{track}} i$$
- **Hàm phạt vi phạm luật FIA:**
  $$\Phi_{\text{FIA}}(\mathbf{S}) = \begin{cases} 0 & \text{nếu } |\{c_k\}| \ge 2 \\ 100,000\text{ s} & \text{ngược lại} \end{cases}$$
- **Hàm phạt vượt vách mòn lốp:**
  $$\Phi_{\text{cliff}}(\mathbf{S}) = \sum_{k=1}^{K+1} \Big[ 50.0 \cdot \max(0, l_k - L_{\max}(c_k)) + 5.0 \cdot \big(\max(0, l_k - L_{\max}(c_k))\big)^2 \Big]$$

---

## 4. HAI KHÁM PHÁ TOÁN HỌC & ĐÓNG GÓP THUẬT TOÁN

### 4.1. Đạo hàm Tốc độ Mài mòn Biên Giải tích ($\nabla t_{\text{deg}}$)
$$\nabla t_{\text{deg}}(c, a) = \frac{\partial \Delta t_{\text{deg}}}{\partial a} = d_1(c) + 2 d_2(c) a$$
$$\nabla^2 t_{\text{deg}}(c, a) = 2 d_2(c) > 0 \quad (\text{Hàm lồi ngặt - Strictly Convex})$$
* **Ứng dụng:** Đạo hàm cung cấp hướng dốc giải tích cho Toán tử Sửa chữa (Physics-Guided Repair Operator). Khi cá thể bị thừa/thiếu vòng sau lai ghép, thuật toán ưu tiên cắt giảm vòng ở stint có $\nabla t_{\text{deg}}$ cao nhất và bù vòng vào stint có dung sai an toàn lớn nhất.

### 4.2. Dạng đóng Giải tích Faulhaber $O(1)$
Tổng thời gian suy giảm tích lũy của một stint dài $L$ vòng được giải tích hóa triệt tiêu vòng lặp:
$$D_{\text{stint}}(c, L) = \sum_{a=1}^L \big( d_1 a + d_2 a^2 \big) = d_1 \frac{L(L+1)}{2} + d_2 \frac{L(L+1)(2L+1)}{6}$$
* **Ứng dụng:** Giảm độ phức tạp từ $O(L)$ về $O(1)$, tăng tốc độ đánh giá hàm thích nghi hơn 50 lần.

---

## 5. KẾT QUẢ THỰC NGHIỆM ĐỐI CHUẨN (MONZA - 53 VÒNG)

| Thuật toán | Chiến lược tối ưu | Tổng thời gian (s) | Optimality Gap | Thời gian tính | Thời gian xử lý khi có SC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Bellman DP (Ground Truth)** | Medium (20) $\to$ Soft (14) $\to$ Medium (19) | **4497.997** | **0.0000%** (Chuẩn) | $180\text{--}280\text{ ms}$ | $170\text{--}290\text{ ms}$ *(Giải lại toàn bộ)* |
| **DAGA-F1 (Nhóm đề xuất)** | Medium (20) $\to$ Soft (14) $\to$ Medium (19) | **4497.997** | **0.0000%** | $110\text{--}260\text{ ms}$ | **$5.2\text{--}8.6\text{ ms}$** *(Warm-Start)* |
| **Standard Holland GA** | Soft (17) $\to$ Hard (36) | 4508.197 | +0.2268% (+10.2s) | $90\text{--}150\text{ ms}$ | $90\text{--}150\text{ ms}$ |
| **Greedy Heuristic** | Medium (26) $\to$ Hard (27) | 4508.864 | +0.2416% (+10.8s) | $< 1\text{ ms}$ | Không thể thích nghi |

* **Kiểm định ý nghĩa thống kê:** Kiểm định Wilcoxon Signed-Rank trên 30 random seeds độc lập đạt $p\text{-value} = 3.59 \times 10^{-7} < 0.001$, khẳng định tính vượt trội của DAGA-F1 có ý nghĩa thống kê rõ rệt so với Standard GA.

---

## 6. CẤU TRÚC THƯ MỤC VÀ HƯỚNG DẪN THỰC THI

```
F1_Optimization-/
├── data/
│   ├── race_configs.py            # Cấu hình gốc duy nhất (Single Source of Truth)
│   ├── clean_laps.parquet         # Dữ liệu sạch Monza đã làm sạch
│   └── benchmark_results.json     # Kết quả đối soát thống kê
├── src/
│   └── data/
│       ├── cleaner.py             # Pipeline lọc FastF1, trừ xăng & track rubber
│       ├── collector.py           # Bộ cào dữ liệu FastF1 tự động
│       ├── monza_2023/            # Dữ liệu viễn trắc chặng Monza
│       └── silverstone_2023/      # Dữ liệu viễn trắc chặng Silverstone
├── tyre/
│   ├── fitter.py                  # Thuật toán WLS, Tikhonov lambda=1e-9, Huber IRLS
│   ├── derivatives.py             # Đạo hàm giải tích, Faulhaber O(1), fix_total_laps
│   ├── thermal.py                 # Mô hình nhiệt động bán thực nghiệm T_track
│   ├── simulator.py               # Trình mô phỏng chặng đua và đối soát
│   └── train.py                   # Pipeline huấn luyện mô hình lốp từ dữ liệu FastF1
├── thanh_vien_1_algorithm_ga/
│   ├── app.py                     # Web Dashboard tương tác (Streamlit)
│   ├── src/
│   │   ├── ga_strategy/           # Lõi thuật toán DAGA-F1 (Operators, Optimizer)
│   │   ├── benchmark/             # Bộ giải Bellman DP quy nạp ngược
│   │   ├── tyre_model/            # Mô hình lốp giải tích Pirelli
│   │   └── simulator/             # F1 Race Simulator tích hợp Faulhaber O(1)
│   ├── tests/                     # 48 Unit tests tự động (100% Passed)
│   └── paper/
│       └── presentation_slides.tex# Slide báo cáo Beamer LaTeX 12 trang chuẩn mực
└── Simulation/
    ├── main.py                    # Mô phỏng đồ họa 2D Pygame trực quan
    ├── race.py                    # Động cơ xe chạy theo timeline chiến thuật F1
    ├── track.py                   # Mô hình hình học đường đua
    └── renderer.py                # Hiển thị thông số xe thời gian thực
```

### Lệnh chạy kiểm thử và thực thi:

1. **Làm sạch dữ liệu viễn trắc FastF1:**
   ```bash
   python src/data/cleaner.py
   ```

2. **Huấn luyện mô hình lốp WLS-Tikhonov:**
   ```bash
   python tyre/train.py --circuit monza
   python tyre/train.py --circuit silverstone
   ```

3. **Chạy kiểm thử toàn bộ 48 unit tests:**
   ```bash
   pytest thanh_vien_1_algorithm_ga/tests
   ```

4. **Chạy thực nghiệm đối chuẩn học thuật 4 giải thuật:**
   ```bash
   python thanh_vien_1_algorithm_ga/src/benchmark/run_comparison.py
   ```

5. **Khởi chạy Web Dashboard tương tác (Streamlit):**
   ```bash
   streamlit run thanh_vien_1_algorithm_ga/app.py
   ```

6. **Khởi chạy Mô phỏng 2D trực quan (Pygame):**
   ```bash
   python Simulation/main.py
   ```
   *(Nhấn phím `SPACE` để tạm dừng/tiếp tục, phím `UP`/`DOWN` để điều chỉnh tốc độ mô phỏng).*
