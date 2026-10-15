# BẢNG PHÂN CHIA NHIỆM VỤ CHI TIẾT CHO NHÓM 5 NGƯỜI
## ĐỒ ÁN DS106: TỐI ƯU HÓA CHIẾN LƯỢC PIT-STOP & QUẢN LÝ LỐP F1 BẰNG GIẢI THUẬT DI TRUYỀN

---

### TỔNG QUAN KIẾN TRÚC GIAO TIẾP DỮ LIỆU GIỮA CÁC THÀNH VIÊN

Để 5 thành viên có thể làm việc song song mà không bị phụ thuộc hay gây xung đột code (merge conflict), dự án được phân chia theo hợp đồng giao diện dữ liệu (Data Contract) rõ ràng:

```
[ TV2: Data Engineer ]
   │
   ▼ (Tạo ra: clean_laps.parquet)
[ TV3: Tyre Modeler ]
   │
   ▼ (Tạo ra: tyre_ensemble.pkl - cung cấp hàm predict_lap_time)
[ TV4: Simulator Engine ] ◄──► [ TV1: GA Core Lead ]
   │                                   │
   └───────────────┬───────────────────┘
                   ▼ (Tạo ra: metrics.json, logs, pareto charts)
           [ TV5: Paper & UI ]
```

---

### THÀNH VIÊN 1: TRƯỞNG NHÓM & KIẾN TRÚC SƯ GIẢI THUẬT (GA CORE LEAD)

* **Vai trò:** Chịu trách nhiệm thiết kế toán học, cấu trúc nhiễm sắc thể và cài đặt toàn bộ lõi Giải thuật Di truyền cải tiến (Improved GA kế thừa từ bài báo Zhao et al., 2024).
* **Kiến thức môn học phụ trách:** Chương 6 (Tối ưu phi tuyến có ràng buộc, Phương pháp hàm phạt, Tối ưu toàn cục Metaheuristics).
* **Nhiệm vụ cụ thể từng tuần:**
  - **Tuần 1–2:** Viết tài liệu đặc tả toán học chi tiết (`docs/math_formulation.md`), định nghĩa không gian tìm kiếm cá thể $\mathbf{X} = [(c_1, \Delta l_1), \dots, (c_{K+1}, \Delta l_{K+1})]$.
  - **Tuần 3–4:** Lập trình module `src/ga_strategy/operators.py` gồm: Khởi tạo có trọng số (Weighted Initialization), Toán tử lai ghép (Crossover) kèm Repair Operator bảo toàn tổng số vòng $\sum \Delta l_k = N_{total}$.
  - **Tuần 5–6:** Cài đặt toán tử đột biến thích nghi động (Fitness-based Dynamic Mutation), cơ chế hàm phạt vi phạm luật lốp FIA ($\Phi_{FIA} = 10^5$), và hoàn thiện bộ tối ưu hóa `src/ga_strategy/optimizer.py`.
  - **Tuần 7 (Buffer):** Phụ trách thí nghiệm bóc tách (Ablation Study 1): Chạy so sánh hiệu năng giữa *Standard GA* (tỷ lệ cố định, khởi tạo ngẫu nhiên) vs *Improved GA* (thích nghi động, khởi tạo có trọng số).
  - **Tuần 8:** Viết mục *3. Methodology (Improved Genetic Algorithm)* trong bài báo khoa học.
* **Đầu ra (Deliverables):**
  - File mã nguồn: `src/ga_strategy/optimizer.py`, `src/ga_strategy/operators.py`.
  - Unit test: `tests/test_ga_constraints.py`.

---

### THÀNH VIÊN 2: KỸ SƯ DỮ LIỆU F1 & TIỀN XỬ LÝ (DATA PIPELINE SPECIALIST)

* **Vai trò:** Trích xuất, làm sạch và chuẩn hóa toàn bộ dữ liệu telemetry từ API FastF1 của 2 chặng đua mục tiêu (Monza 2023 & Silverstone 2023).
* **Kiến thức môn học phụ trách:** Chương 4 (Phân tích đặc trưng dữ liệu, xử lý dị biệt, lọc nhiễu thực nghiệm).
* **Nhiệm vụ cụ thể từng tuần:**
  - **Tuần 1–2:** Cài đặt môi trường `fastf1`, cấu hình hệ thống cache cục bộ để tránh lỗi timeout mạng; tải thử dữ liệu mẫu.
  - **Tuần 3–4:** Viết pipeline tự động cào dữ liệu Monza và Silverstone:
    - Lọc bỏ vòng cờ vàng/Safety Car (`TrackStatus != '1'`).
    - Lọc bỏ In-lap, Out-lap.
    - Lọc bỏ các vòng bị khóa bánh hoặc kẹt xe bất thường ($t_{lap} > 1.07 \times \text{median}$).
    - Tính toán chính xác thời gian tổn thất vào pit: $T_{pit\_loss} = (t_{lap}^{in} + t_{lap}^{out}) - 2 \cdot \bar{t}_{clean}$.
    - Khử ảnh hưởng tiêu hao nhiên liệu ($\Delta t_{fuel}$) và độ bám cao su mặt đường ($\Delta t_{track}$).
  - **Tuần 5–6:** Đóng gói toàn bộ tập dữ liệu đã làm sạch thành tệp `data/clean_laps.parquet` và tạo bản sao lưu trên Google Drive nhóm.
  - **Tuần 7 (Buffer):** Hỗ trợ TV4 trích xuất chiến thuật đua thực tế của Max Verstappen, Charles Leclerc, Lando Norris làm Ground Truth đối soát.
  - **Tuần 8:** Viết mục *2. Materials & Data Preprocessing* trong bài báo khoa học.
* **Đầu ra (Deliverables):**
  - File mã nguồn: `src/data/fastf1_loader.py`, `src/data/cleaner.py`.
  - Dữ liệu: `data/clean_laps.parquet`.
  - Unit test: `tests/test_data_pipeline.py`.

---

### THÀNH VIÊN 3: CHUYÊN VIÊN MÔ HÌNH HÓA MÒN LỐP (TYRE DEGRADATION MODELER)

* **Vai trò:** Xây dựng mô hình suy giảm hiệu suất lốp theo số vòng và tối ưu hóa trọng số kết hợp (Ensemble Weights) bằng Real-valued GA (kế thừa bài báo Kaya et al., 2024).
* **Kiến thức môn học phụ trách:** Chương 4 (Hồi quy đa biến, hồi quy phi tuyến) và Chương 6 (Tối ưu trọng số liên tục).
* **Nhiệm vụ cụ thể từng tuần:**
  - **Tuần 1–2:** Nghiên cứu các phương trình vật lý suy giảm lốp bậc 2 (Quadratic Tyre Degradation) của Pirelli.
  - **Tuần 3–4:** Nhận dữ liệu sạch từ TV2. Huấn luyện 4 mô hình hồi quy cơ sở:
    1. Ridge Regression (hồi quy tuyến tính có hiệu chuẩn L2).
    2. Polynomial Regression bậc 2 (mô hình hóa hiện tượng cliff tụt độ bám).
    3. Support Vector Regression (SVR).
    4. XGBoost Regressor.
  - **Tuần 5–6:** Lập trình thuật toán **Real-valued Genetic Algorithm (RCGA)** theo phương pháp Kaya et al. (2024) để tìm véc-tơ $\mathbf{\beta}^* = [\beta_1, \beta_2, \beta_3, \beta_4]$ thỏa $\sum \beta_i = 1$ nhằm tối thiểu hóa sai số RMSE trên tập Validation.
  - **Tuần 7 (Buffer):** Phụ trách thí nghiệm bóc tách (Ablation Study 2): So sánh sai số RMSE giữa *Từng mô hình đơn lẻ* vs *Mô hình Ensemble trung bình* vs *Mô hình Ensemble tối ưu bằng RCGA*.
  - **Tuần 8:** Viết mục *3. Tyre Performance Modeling via RCGA Ensemble* trong bài báo khoa học.
* **Đầu ra (Deliverables):**
  - File mã nguồn: `src/tyre_model/rcga_ensemble.py`.
  - Mô hình đóng gói: `models/tyre_ensemble.pkl` (chứa hàm `predict_lap_time(compound, age, race_lap)`).

---

### THÀNH VIÊN 4: KỸ SƯ MÔ PHỎNG & ĐỐI SOÁT CHIẾN THUẬT (RACE SIMULATOR & BENCHMARK LEAD)

* **Vai trò:** Xây dựng bộ mô phỏng tính toán thời gian toàn bộ chặng đua từ chiến lược lốp, tích hợp hàm đánh giá thích nghi cho GA và thực hiện các thí nghiệm đối soát thực tế.
* **Kiến thức môn học phụ trách:** Chương 6 (Đánh giá hàm mục tiêu, hàm phạt) và Chuẩn đầu ra G3, G4.
* **Nhiệm vụ cụ thể từng tuần:**
  - **Tuần 1–2:** Thiết kế cấu trúc lớp `F1RaceSimulator` tiếp nhận cấu hình chặng đua (tổng số vòng, pit loss).
  - **Tuần 3–4:** Lập trình hàm tính toán thời gian từng vòng, kết nối với hàm dự đoán của TV3 và cộng dồn tổn thất pit:
    $$T_{total} = \sum_{k=1}^{K+1} \left( \sum_{a=1}^{\Delta l_k} t_{lap}(c_k, a, lap) \right) + K \cdot T_{pit\_loss}$$
  - **Tuần 5–6:** Ghép nối Trình mô phỏng với Lõi GA của TV1 đóng vai trò là hàm đánh giá thích nghi (Fitness Function). Chạy thử nghiệm chặng Monza (53 vòng) và Silverstone (52 vòng).
  - **Tuần 7 (Buffer):** Thực hiện thí nghiệm phân tích độ nhạy (Sensitivity Analysis):
    - Thử nghiệm $T_{pit\_loss} \pm 3\text{s}$ (mô phỏng thợ thay lốp chậm).
    - Thử nghiệm biến thiên nhiệt độ mặt đường $+5^\circ\text{C}$ (lốp mòn nhanh hơn).
    - So sánh chiến lược GA tìm ra với kết quả thực tế của tay đua vô địch (Max Verstappen).
  - **Tuần 8:** Viết mục *4. Experimental Results & Discussion* trong bài báo khoa học.
* **Đầu ra (Deliverables):**
  - File mã nguồn: `src/simulator/race_sim.py`.
  - Notebook kết quả thực nghiệm: `notebooks/benchmark_and_sensitivity.ipynb`.

---

### THÀNH VIÊN 5: TRƯỞNG NHÓM BÀI BÁO KHOA HỌC & UI DEMO (SCIENTIFIC PAPER & UI LEAD)

* **Vai trò:** Chủ trì biên soạn toàn văn bài báo khoa học định dạng Elsevier/IEEE, xây dựng ứng dụng Web Dashboard tương tác (Streamlit) và chuẩn bị slide thuyết trình Seminar cuối kỳ.
* **Kiến thức môn học phụ trách:** Chuẩn đầu ra G4 (Báo cáo seminar, trình bày kết quả nghiên cứu khoa học).
* **Nhiệm vụ cụ thể từng tuần:**
  - **Tuần 1–2:** Thiết lập template bài báo 2 cột chuẩn LaTeX/Word (Elsevier template giống bài của thầy); phác thảo mục lục và khung bài báo.
  - **Tuần 3–4:** Bắt đầu dựng giao diện Web Dashboard bằng **Streamlit** (`app.py`): Giao diện cho phép chọn chặng đua, kéo chọn số lần pit tối đa, chọn nhiệt độ mặt đường.
  - **Tuần 5–6:** Tích hợp bộ mô phỏng của TV4 và bộ tối ưu GA của TV1 lên Web UI. Khi bấm nút "Tối ưu hóa chiến lược", giao diện vẽ đồ thị hội tụ GA và biểu đồ thanh (Gantt chart) thể hiện các stint lốp.
  - **Tuần 7 (Buffer):** Thu thập toàn bộ biểu đồ, bảng số liệu Ablation Study từ TV1, TV3, TV4 để đưa vào bài báo khoa học. Hoàn thiện bộ slide Seminar (20–25 slide).
  - **Tuần 8:** Rà soát văn phong, kiểm tra lỗi trích dẫn tài liệu tham khảo (format IEEE/APA); tổ chức buổi diễn tập thuyết trình (Mock Seminar) cho nhóm.
* **Đầu ra (Deliverables):**
  - Bài báo hoàn chỉnh: `paper/F1_Strategy_Optimization_DS106.pdf`.
  - Web UI: `app.py`.
  - Slide báo cáo: `slides/DS106_Seminar_Presentation.pptx`.
