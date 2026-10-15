# THÀNH VIÊN 1: GIẢI THUẬT DI TRUYỀN THÍCH NGHI ĐỘNG (DAGA-F1)
## Dynamic Adaptive Genetic Algorithm for F1 Pit-Stop & Tyre Strategy Optimization
**Đơn vị:** Nhóm Đề án DS106 — Khoa Khoa học Dữ liệu, Trường ĐH Công nghệ Thông tin (UIT - ĐHQG-HCM)  
**Phân công:** Thành viên 1 (Algorithm & GA Lead)  
**Tích hợp:** Tiếp nhận mô hình lốp giải tích WLS-Tikhonov & Thermal Dynamics từ Thành viên 3 (Tyre Modeler)

---

## 1. TỔNG QUAN HỆ THỐNG
Dự án của Thành viên 1 giải quyết bài toán tối ưu hóa chiến lược pit-stop và lựa chọn hợp chất lốp F1 trong điều kiện động lực học phi tuyến, ràng buộc thể thao FIA và biến cố xe an toàn (Safety Car) bất định.

### Các đóng góp mới cốt lõi (Novelties):
1. **Biểu diễn nhiễm sắc thể biến thiên mốc pit (Variable-Length Stint Representation):**
   * Mã hóa chiến lược dưới dạng danh sách stint linh hoạt $[(c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1})]$.
   * Cho phép quần thể tự do tiến hóa và cạnh tranh giữa các chiến lược 1-stop, 2-stop và 3-stop đồng thời.
2. **Cơ chế thích nghi động kép (Dual-Level Dynamic Adaptation):**
   * Lịch làm mát phi tuyến cho xác suất lai ghép $P_c(g)$ và đột biến $P_m(g)$.
   * Giám sát liên tục độ đa dạng kiểu gen quần thể $\mathcal{D}_{\text{pop}} \in [0.0, 1.0]$.
3. **Tiêm gen hỗn loạn (Cataclysmic Chaos Injection):**
   * Tự động nhân đột biến $P_m$ lên $2.5\times$ khi độ đa dạng sụt giảm ($\mathcal{D}_{\text{pop}} < 0.15$) ở $70\%$ số thế hệ đầu để phá vỡ bẫy cực tiểu địa phương.
4. **Toán tử đột biến đa hình thái 3 cấp độ (Tri-Level Polymorphic Mutation):**
   * **Micro-mutation (60%):** Dịch chuyển vi mô mốc pit ($\pm 1 \sim 2$ vòng) tinh chỉnh đáy cực tiểu.
   * **Meso-mutation (25%):** Hoán đổi hợp chất lốp thông minh tuân thủ luật FIA.
   * **Macro-mutation (15%):** Đột biến biến thiên số chiều cấu trúc qua cơ chế **Split Stint** ($K \to K+1$) và **Merge Stint** ($K \to K-1$).
5. **Tích hợp đồng bộ tài liệu mô hình lốp TV3:**
   * **Mô hình nhiệt bán thực nghiệm $T_{\text{track}}$:** Hiệu chỉnh $d_1, d_2$ theo $\delta_T$ kèm số hạng phạt ReLU bình phương $\theta_2 \cdot (\max(0, \delta_T))^2$ khi mặt đường quá nhiệt ($> 45^\circ\text{C}$).
   * **Công thức tổng đóng Faulhaber $O(1)$:** Chuyển đổi toàn bộ quá trình đánh giá stint từ vòng lặp $O(L)$ thành phép tính giải tích $O(1)$, tăng tốc độ đánh giá fitness lên nhiều lần.
   * **Toán tử sửa chữa định hướng vật lý (Physics-Guided Repair):** Dựa trên đạo hàm suy giảm lốp $\nabla t_{\text{deg}}(a) = d_1 + 2 d_2 a$ và khoảng cách an toàn vách lốp $(L_{\max} - a)$.
   * **Kiểm soát vách lốp an toàn $L_{\max}$ (Tyre Cliff Control):** Cưỡng chế tái cân bằng số vòng khi vượt $L_{\max}$ và áp dụng hàm phạt bậc hai mô tả sự sụp đổ ma sát.
6. **Tái tối ưu hóa thời gian thực (Safety Car Warm-Start Pivot):**
   * Đóng băng các vòng đã đua $[1, L_{\text{sc}}]$, tái sử dụng gen ưu tú để giải bài toán ra quyết định kép: **Vào pit khẩn cấp (Box under SC)** hay **Tiếp tục chạy (Stay Out)**.
   * Thời gian phản hồi tái hội tụ cực nhanh: **$< 0.02$ giây**, đáp ứng hoàn hảo cửa sổ tác chiến $3 - 5$ giây tại Pit-wall.

---

## 2. KẾT QUẢ ĐỐI CHUẨN THỰC NGHIỆM (BENCHMARK RESULTS)

### Bảng so sánh hiệu năng qua các random seeds (Monza GP - 53 vòng):

| Tiêu chí | Bellman DP (Ground Truth) | Greedy Heuristic | Standard GA (Holland) | DAGA-F1 (Nhóm đề xuất) |
| :--- | :--- | :--- | :--- | :--- |
| **Chiến lược tối ưu** | Medium(20) $\to$ Soft(14) $\to$ Medium(19) | Medium(26) $\to$ Hard(27) | Biến động theo seed | Medium(20) $\to$ Soft(14) $\to$ Medium(19) |
| **Số lần dừng pit ($K$)** | 2 | 1 | 1 | 2 |
| **Vòng vào pit** | 20, 34 | 26 | 18 - 28 | 20, 34 (hoặc hoán vị tương đương) |
| **Thời gian đua tốt nhất** | **4497.997 s** | 4508.864 s | 4508.197 s | **4497.997 s** |
| **Thời gian đua trung bình** | **4497.997 s** | 4508.864 s | 4508.197 s | **4497.997 s** |
| **Khoảng cách tối ưu (Mean Gap %)** | **0.0000%** | +0.2416% | +0.2268% | **0.0000%** |
| **Thời gian thực thi (Runtime)** | 0.10 - 0.16 s | < 0.001 s | ~0.08 s | **0.10 - 0.22 s** |
| **Tốc độ phản ứng Safety Car** | Không hỗ trợ động | Không hỗ trợ | Không hỗ trợ | **0.009 - 0.015 s** |

*Kiểm định phi tham số Wilcoxon Signed-Rank Test: $p\text{-value} = 9.77 \times 10^{-4} < 0.001$ (Khẳng định DAGA-F1 vượt trội SGA có ý nghĩa thống kê).*

---

## 3. CẤU TRÚC THƯ MỤC MÃ NGUỒN

```
thanh_vien_1_algorithm_ga/
├── README.md                      # Tài liệu tổng quan & hướng dẫn kỹ thuật
├── requirements.txt               # Danh mục thư viện phụ thuộc
├── app.py                         # Giao diện tương tác trực quan Streamlit
├── src/
│   ├── __init__.py
│   ├── ga_strategy/
│   │   ├── __init__.py
│   │   ├── operators.py           # Toán tử DAGA-F1 (Khởi tạo, Sửa chữa vật lý, Lai ghép, Đột biến 3 cấp)
│   │   └── optimizer.py           # Bộ tối ưu DAGA-F1 (Adaptive cooling, Chaos injection, SC warm-start)
│   ├── simulator/
│   │   ├── __init__.py
│   │   └── race_sim.py            # F1RaceSimulator (Faulhaber O(1), Tyre cliff penalty, FIA constraints)
│   ├── tyre_model/
│   │   ├── __init__.py
│   │   ├── pirelli_physics.py     # Mô hình vật lý Pirelli tích hợp T_track, Faulhaber O(1), nabla t_deg
│   │   └── rcga_ensemble.py       # Mô hình Ensemble RCGA (Kaya et al., Elsevier 2024)
│   ├── benchmark/
│   │   ├── __init__.py
│   │   ├── dp_solver.py           # Bộ giải Quy hoạch Động Bellman (Ground Truth Global Optimum)
│   │   └── run_comparison.py      # Kịch bản thực nghiệm đối chứng học thuật (Greedy vs SGA vs DAGA-F1 vs DP)
│   └── data/
│       ├── __init__.py
│       ├── fastf1_loader.py       # Module nạp dữ liệu FastF1 sẵn sàng kết nối TV2
│       └── benchmark_results.json # Kết quả thực nghiệm đối chuẩn lưu trữ
├── tests/
│   ├── __init__.py
│   ├── test_env.py                # Kiểm thử môi trường và dependencies
│   ├── test_operators.py          # Kiểm thử toán tử GA (Repair, Crossover, Mutation, Diversity)
│   ├── test_mutation_split_merge.py # Kiểm thử đột biến thay đổi số lượng stint K in {1, 2, 3}
│   ├── test_ga_baseline.py        # Kiểm thử hội tụ DAGA-F1 đạt 0.000% gap so với Bellman DP
│   ├── test_faulhaber_o1.py       # Kiểm thử nghiệm giải tích đóng Faulhaber O(1) vs vòng lặp
│   ├── test_thermal_t_track.py    # Kiểm thử mô hình nhiệt độ mặt đường T_track và ReLU-squared
│   ├── test_tyre_cliff_lmax.py    # Kiểm thử kiểm soát vách mòn lốp L_max và tái cân bằng vòng
│   └── test_tv3_interoperability.py # Kiểm thử tương thích liên module với package tyre của TV3
└── docs/
    ├── TV1_Thuyet_Minh_Giai_Thuat_DAGA_F1.md # Báo cáo học thuật chi tiết của Thành viên 1
    └── TV3_Tai_Lieu_Mo_Hinh_Lop_WLS.md       # Tài liệu bàn giao mô hình lốp từ Thành viên 3
```

---

## 4. HƯỚNG DẪN CHẠY KIỂM THỬ VÀ MÔ PHỎNG

### Chạy toàn bộ 49 test cases tự động:
```bash
python -m unittest discover tests
```

### Chạy kịch bản thực nghiệm đối chứng học thuật (10 seeds):
```bash
python src/benchmark/run_comparison.py
```

### Khởi chạy bảng điều khiển tương tác (Streamlit Dashboard):
```bash
streamlit run app.py
```
