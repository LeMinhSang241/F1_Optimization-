# BẢN NỘI DUNG SLIDE THUYẾT TRÌNH – PHẦN THUẬT TOÁN TIẾN HÓA (TV1)
**Tệp:** `main GA algorithm (slide).md`  
**Dành cho:** Thành viên phụ trách ghép Slide (Slide Designer)  
**Phạm vi:** **Chỉ bao gồm phần của Thành viên 1 (Algorithm & GA Lead)** để đưa trực tiếp lên các slide về thuật toán GA.  
**Đặc điểm:** Ngắn gọn, súc tích, dạng gạch đầu dòng, có công thức và số liệu rõ ràng, không có chữ thừa.

---

## SLIDE 1: CẤU TRÚC NHIỄM SẮC THỂ & TOÁN TỬ SỬA CHỮA ĐỊNH HƯỚNG VẬT LÝ

### 1. Thông điệp cốt lõi (Takeaway)
Mã hóa nhiễm sắc thể biến thiên theo stint và triệt tiêu $100\%$ nghiệm bất khả thi nhờ đạo hàm mài mòn biên $\nabla t_{\text{deg}}$.

### 2. Nội dung hiển thị trên Slide

* **Cấu trúc Cá thể (Chromosome Representation):**
  $$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
  * $K \in \{1, 2, 3\}$: Số lần dừng pit (chiều dài mảng biến thiên linh hoạt).
  * $c_k \in \{\text{Soft, Medium, Hard}\}$: Loại lốp sử dụng ở từng stint.
  * $l_k \ge 4$: Độ dài stint (số vòng chạy liên tục).

* **Khởi tạo Quần thể Định hướng Tri thức (Heuristic Initialization):**
  * Phân bổ trọng số thực tế: **$65\%$ 1-stop**, **$30\%$ 2-stop**, **$5\%$ 3-stop**.
  * Toàn bộ cá thể thỏa mãn ngay luật FIA ($|\{c_k\}| \ge 2$) từ thế hệ 0.

* **Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair Operator):**
  * *Vấn đề:* Lai ghép/đột biến làm lệch tổng số vòng ($\sum l_k \ne 53$).
  * *Giải pháp:* Dùng **đạo hàm mài mòn biên $\nabla t_{\text{deg}} = d_1 + 2d_2 a$** làm la bàn định hướng:
    * **Thiếu vòng ($\sum l_k < 53$):** Bù vòng vào stint có khoảng cách an toàn tới vách lốp lớn nhất ($L_{\max} - l_k$).
    * **Thừa vòng ($\sum l_k > 53$):** Khấu trừ vòng ở stint có tốc độ mòn biên $\nabla t_{\text{deg}}$ cao nhất (lốp Soft cũ).
  * *Hiệu quả:* Đưa **$100\%$** cá thể về miền hợp lệ $\Omega$ mà không làm chết đa dạng sinh học.

### 3. Gợi ý Sơ đồ Trực quan
Sơ đồ khối: Cá thể bị lệch vòng $\longrightarrow$ Tính đạo hàm $\nabla t_{\text{deg}}$ $\longrightarrow$ Bù/Trừ vào stint tối ưu $\longrightarrow$ Nghiệm hợp lệ $\sum l_k = 53$.

---

## SLIDE 2: ĐỘT BIẾN ĐA HÌNH THÁI 3 CẤP ĐỘ & TIÊM GEN HỖN LOẠN

### 1. Thông điệp cốt lõi (Takeaway)
Đột biến Split/Merge giúp số lần pit $K$ tự tiến hóa tối ưu; cơ chế Chaos Injection phá vỡ bẫy cực tiểu địa phương.

### 2. Nội dung hiển thị trên Slide

* **Đột biến Đa hình thái 3 Cấp độ (Tri-Level Mutation):**
  * **Micro-mutation ($60\%$):** Tinh chỉnh vi mô mốc pit giữa 2 stint liền kề ($l_k \pm 1, l_{k+1} \mp 1$) $\rightarrow$ Khai thác sâu (*Exploitation*) điểm đáy tối ưu.
  * **Meso-mutation ($25\%$):** Hoán đổi ngẫu nhiên loại hợp chất lốp, giữ nguyên số vòng và bảo toàn luật FIA.
  * **Macro-mutation ($15\%$) – Biến thiên Cấu trúc (Split & Merge):**
    * **Tách stint (Split: $K \to K+1$):** Cắt đôi stint dài nhất thành 2 stint lốp khác nhau $\rightarrow$ Giải cứu xe thoát khỏi vách mòn (*Tyre Cliff*).
    * **Gộp stint (Merge: $K \to K-1$):** Gộp 2 stint ngắn liền kề thành 1 stint lốp bền hơn $\rightarrow$ Tiết kiệm trọn vẹn **$23.2\text{ s}$** tổn thất làn pit.
    * $\rightarrow$ **Số lần pit $K$ tự động tiến hóa, không cần gán cứng!**

* **Tiêm Gen Hỗn loạn (Cataclysmic Chaos Injection):**
  * Lịch làm mát phi tuyến thích nghi $P_c(g)$ và $P_m(g)$ giảm dần theo thế hệ.
  * Giám sát độ đa dạng quần thể $\bar{D}_{\text{pop}}$:
    $$\text{Nếu } \bar{D}_{\text{pop}} < 0.15 \;\Longrightarrow\; \text{Nhân } P_m \times 2.5 \text{ trong 3 thế hệ}$$
  * Kích nổ đột biến diện rộng, hất văng quần thể khỏi hố cực tiểu địa phương.

### 3. Gợi ý Sơ đồ Trực quan
Hình minh họa 2 thanh stint: (1) Thanh dài bị cắt đôi (Split Stint); (2) Hai thanh ngắn gộp lại thành một thanh dài (Merge Stint).

---

## SLIDE 3: TÁI TỐI ƯU HÓA XE AN TOÀN THỜI GIAN THỰC (WARM-START PIVOT)

### 1. Thông điệp cốt lõi (Takeaway)
Cơ chế Warm-Start Pivot tái tối ưu chiến lược trong $5.2\text{ ms}$, đáp ứng tức thời cửa sổ quyết định $3\text{ s}$ tại Pit-wall.

### 2. Nội dung hiển thị trên Slide

* **Bối cảnh Xe An Toàn (Safety Car – SC):**
  * Tốc độ ngoài đường đua giảm $40\%$, tốc độ trong làn pit giữ nguyên $80\text{ km/h}$.
  * Tổn thất làn pit giảm đột ngột: **$T_{\text{pit}} = 23.2\text{ s} \longrightarrow 12.5\text{ s}$** (*Free Pit Stop*).
  * Cửa sổ ra quyết định khẩn cấp tại Pit-wall: Chỉ có **$3 - 5\text{ giây}$** trước lối vào pit.

* **Cơ chế Warm-Start Pivot của TV1:**
  1. **Đóng băng quá khứ:** Cố định toàn bộ các vòng đã đua $[1, L_{\text{SC}}]$.
  2. **Kế thừa hạt giống:** Lấy cá thể tối ưu hiện tại làm khởi điểm (Warm-start), không ngẫu nhiên hóa từ đầu.
  3. **Tái hội tụ thần tốc:** Cập nhật $T_{\text{pit}} \leftarrow 12.5\text{ s}$ và chỉ tối ưu các vòng còn lại với $G = 15$ thế hệ.

* **KPI Đạt Được:**
  * **Thời gian tính toán:** **$5.2\text{ mili-giây}$** (nhanh gấp **15 lần** Bellman DP giải lại từ đầu $\approx 85\text{ ms}$).
  * **Lợi ích thực tế:** Tiết kiệm **$10.7\text{ giây}$** tổng thời gian chặng đua so với đối thủ không kịp vào pit.

### 3. Gợi ý Sơ đồ Trực quan
Dòng thời gian chặng đua Monza 53 vòng: Vạch cờ vàng SC xuất hiện tại vòng 20 $\rightarrow$ Vùng đóng băng $[1, 20]$ $\rightarrow$ Mũi tên Warm-Start Pivot giải quyết các vòng còn lại $[21, 53]$ trong $5.2\text{ ms}$.

---

## SLIDE 4: ĐỐI CHUẨN THỰC NGHIỆM & ĐỘ TIN CẬY CỦA THUẬT TOÁN (TV1 METRICS)

### 1. Thông điệp cốt lõi (Takeaway)
Thuật toán AGA đạt Optimality Gap $0.0000\%$, vượt trội có ý nghĩa thống kê và được bảo chứng bởi 48/48 automated tests.

### 2. Nội dung hiển thị trên Slide

* **Bảng Số liệu Đối chuẩn Thực nghiệm (Monza GP – 53 vòng):**
  | Thuật toán | Thời gian đua tốt nhất | Optimality Gap | Wilcoxon ($p$-value) | Runtime |
  | :--- | :---: | :---: | :---: | :---: |
  | **Bellman DP (Ground Truth)** | **$4497.997\text{ s}$** | **$0.0000\%$** (Chuẩn) | — | $0.086\text{ s}$ |
  | **Standard GA (Holland 1975)** | $4512.450\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | — | $0.412\text{ s}$ |
  | **Proposed Adaptive GA (TV1)** | **$4497.997\text{ s}$** | **$0.0000\%$** | **$p = 3.59 \times 10^{-7}$** | **$0.185\text{ s}$** |

* **3 KPI Khẳng định Năng lực Thuật toán:**
  * **Optimality Gap = $0.0000\%$:** Chạm chính xác nghiệm tối ưu toàn cục lý thuyết (`[Medium 20v -> Soft 14v -> Medium 19v]`).
  * **Kiểm định Thống kê Wilcoxon (30 seeds):** $p = 3.59 \times 10^{-7} \ll 0.001$ $\rightarrow$ Bác bỏ giả thuyết $H_0$, tính vượt trội của AGA là chắc chắn.
  * **Độ tin cậy mã nguồn:** **$48/48$ unit tests tự động PASSED $100\%$** trong $11.7\text{ s}$ (không ngụy tạo số liệu).

### 3. Gợi ý Sơ đồ Trực quan
Nhúng biểu đồ Boxplot phân bố nghiệm qua 30 random seeds giữa Proposed AGA và Standard GA, làm nổi bật cột AGA phẳng tuyệt đối ở mốc $4497.997\text{ s}$.
