# TÀI LIỆU KHỞI TẠO BỐI CẢNH & NHIỆM VỤ THÀNH VIÊN 1 (TV1 CONTEXT INIT)
**Học phần:** DS116 / DS106 – Tối ưu hóa và Ứng dụng  
**Giảng viên phụ trách:** TS. Nguyễn Tất Bảo Thiện (Khoa Khoa học Dữ liệu, Trường ĐH Công nghệ Thông tin - UIT, ĐHQG-HCM)  
**Đề tài:** Tối ưu hóa Đơn Mục tiêu Chiến lược Pit-stop và Quản lý Lốp trong Đua xe Công thức 1 (F1 Pit-Stop & Tyre Strategy Optimization)  
**Tiêu chí đánh giá của Giảng viên:** Đánh giá định tính chuyên sâu ("feeling"), tập trung kiểm tra:
1. Sinh viên có thực sự thấu hiểu bản chất bài toán thực tế hay không?
2. Bài toán có được mô hình hóa toán học chính quy, hợp lý và logic không?
3. Sinh viên có nắm vững bản chất của Tối ưu hóa không (Search Space, Constraints, Objective Function, Trade-offs, Local vs Global Optima)?

---

## 1. VỊ TRÍ & RANH GIỚI TRÁCH NHIỆM CỦA THÀNH VIÊN 1 (TV1)
* **Chức danh:** Trưởng nhóm Thuật toán Tiến hóa (Algorithm & GA Lead).
* **Trách nhiệm cốt lõi:**
  - Thiết kế cấu trúc nhiễm sắc thể (Chromosome Representation) mảng stint với số chiều biến thiên: $\mathbf{S} = [(c_1, l_1), \dots, (c_{K+1}, l_{K+1})]$.
  - Xây dựng giải thuật Di truyền Thích nghi (Adaptive Genetic Algorithm - AGA).
  - Thiết kế Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair Operator) bảo toàn số vòng đua $\sum l_k = 53$ và tuân thủ luật FIA ($\ge 2$ hợp chất).
  - Thiết kế Toán tử Đột biến Đa hình thái 3 cấp độ (Micro-Meso-Macro với cơ chế Split/Merge Stint tự tiến hóa số lần dừng pit $K$).
  - Thiết lập Lịch làm mát thích nghi phi tuyến $P_c(g), P_m(g)$ và cơ chế Tiêm gen hỗn loạn (Cataclysmic Chaos Injection).
  - Phát triển tính năng Tái tối ưu hóa thời gian thực khi có Xe An Toàn (Safety Car Warm-Start Pivot).
  - Soạn thảo Section 3 (Methodology: AGA) cho bài báo theo chuẩn Elsevier.

## 2. GIAO DIỆN PHỐI HỢP VỚI CÁC THÀNH VIÊN KHÁC
* **Nhận từ Thành viên 3 (Tyre Modeler):**
  - Mô hình suy giảm lốp giải tích bậc hai Pirelli: $\Delta t_{\text{deg}}(c, a) = d_1(c) a + d_2(c) a^2$.
  - Bộ tham số đã hiệu chuẩn tại Monza:
    - Soft: $t_{\text{base}} = 81.50\text{ s}, d_1 = 0.120, d_2 = 0.0050, L_{\max} = 22\text{ laps}$.
    - Medium: $t_{\text{base}} = 82.20\text{ s}, d_1 = 0.070, d_2 = 0.0020, L_{\max} = 35\text{ laps}$.
    - Hard: $t_{\text{base}} = 83.00\text{ s}, d_1 = 0.040, d_2 = 0.0010, L_{\max} = 48\text{ laps}$.
  - Đạo hàm suy giảm lốp giải tích: $\nabla t_{\text{deg}}(a) = d_1(c) + 2 d_2(c) a$ (dùng làm la bàn định hướng cho toán tử Repair).
  - Công thức Faulhaber $O(1)$ tính tổng thời gian mòn lốp cả stint: $D_{\text{stint}}(c, L) = d_1 \frac{L(L+1)}{2} + d_2 \frac{L(L+1)(2L+1)}{6}$.
* **Chuyển giao cho Thành viên 4 (Simulation & Bellman DP):**
  - Đã chuyển giao Trình mô phỏng chặng đua (Race Simulator) và Bộ giải Quy hoạch động Bellman (Ground Truth).
  - Nhận lại từ TV4 kết quả đối chứng: Bellman DP tìm ra nghiệm tối ưu toàn cục tuyệt đối là $4497.997\text{ s}$ (`[Medium 20v -> Soft 14v -> Medium 19v]`). AGA của TV1 đạt Optimality Gap = $0.0000\%$.
* **Chuyển giao cho Thành viên 5 (Paper Lead & Slide Designer):**
  - Bản thảo lý thuyết thuật toán, bảng tham số, công thức toán và các KPI đối chuẩn khoa học để đưa vào bài báo Elsevier và Slide thuyết trình.

---

## 3. BẢNG TRA CỨU CÁC CON SỐ THỰC NGHIỆM ĐÃ ĐƯỢC KIỂM ĐỊNH (ZERO HALLUCINATION)
* **Số trạng thái Bellman DP:** $30,088$ trạng thái khả thi.
* **Thời gian đua tối ưu toàn cục (Ground Truth):** $4497.997\text{ s}$ (tương đương 1h 14m 57.997s).
* **Chiến lược tối ưu lý thuyết:** 2-stop: Medium 20 vòng $\to$ Soft 14 vòng $\to$ Medium 19 vòng.
* **Optimality Gap của AGA:** $0.0000\%$ qua 30 random seeds độc lập.
* **Kiểm định phi tham số Wilcoxon Signed-Rank Test:** $p = 3.59 \times 10^{-7} < 0.001$ (vượt trội hoàn toàn so với Standard GA).
* **Thời gian phản xạ tái tối ưu Safety Car:** $4.1 - 5.5\text{ ms}$ (nhanh gấp 15 lần Bellman DP giải lại từ đầu $\approx 65-85\text{ ms}$, nằm gọn trong cửa sổ quyết định $3\text{ s}$ tại Pit-wall).
* **Số lượng Unit Test tự động:** $48/48$ tests PASSED trong $11.7\text{ s} - 12.4\text{ s}$.
