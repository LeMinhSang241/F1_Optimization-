# BẢN ĐẶC TẢ NỘI DUNG SLIDE THUYẾT TRÌNH GIỮA KỲ (SLIDE CONTENT SPECIFICATION)
**Dành cho:** Thành viên phụ trách thiết kế Slide thuyết trình (TV5 / Slide Designer)  
**Tác giả nội dung:** Thành viên 1 (Algorithm & GA Lead)  
**Mục tiêu buổi thuyết trình:** Báo cáo tiến độ giữa kỳ trước TS. Nguyễn Tất Bảo Thiện. Chứng minh nhóm đã hiểu sâu bài toán, mô hình hóa toán học chặt chẽ, cài đặt thuật toán chuẩn mực và có kết quả thực nghiệm tin cậy $100\%$.  
**Thời lượng dự kiến:** $8 - 10\text{ phút}$ (gồm 8–10 slides trọng tâm, cô đọng, nhiều sơ đồ trực quan và số liệu, rất ít chữ).

---

## SLIDE 1: TIÊU ĐỀ BÁO CÁO TIẾN ĐỘ ĐỀ ÁN
* **Tiêu đề chính:** TỐI ƯU HÓA CHIẾN LƯỢC PIT-STOP VÀ QUẢN LÝ LỐP ĐUA XE F1 BẰNG GIẢI THUẬT DI TRUYỀN THÍCH NGHI
* **Tiêu đề phụ:** Đối chuẩn Nghiệm Tối ưu Toàn cục Quy hoạch Động Bellman
* **Học phần:** DS116 / DS106 – Tối ưu hóa và Ứng dụng | Khoa Khoa học Dữ liệu – UIT
* **Giảng viên hướng dẫn:** TS. Nguyễn Tất Bảo Thiện
* **Đơn vị thực hiện:** Nhóm Nghiên Cứu Đề Án DS116
* **Thông điệp cốt lõi:** Một hệ thống tối ưu hóa hoàn chỉnh từ dữ liệu viễn trắc thực tế, mô hình hóa vật lý giải tích, đến giải thuật tiến hóa thích nghi đối chuẩn nghiệm tối ưu toàn cục.

---

## SLIDE 2: BÀI TOÁN THỰC TIỄN & TAM GIÁC NGHỊCH LÝ ĐỐI KHÁNG
* **Thông điệp chính:** Chiến lược F1 là bài toán tối ưu hóa tổ hợp bị chi phối bởi 3 mâu thuẫn vật lý đối kháng.
* **Nội dung hiển thị (3 Cards đối trọng):**
  1. **Mòn lốp phi tuyến:** Lốp Soft nhanh hơn Hard $\approx 1.5\text{ s/vòng}$ nhưng mòn rất nhanh; khi chạm ngưỡng *Tyre Cliff*, thời gian vòng rơi tự do $2 - 4\text{ s/vòng}$.
  2. **Tổn thất làn Pit (Pit Delta $T_{\text{pit}} = 23.2\text{ s}$):** Giới hạn tốc độ $80\text{ km/h}$. Muốn vào pit thêm 1 lần lấy lốp Soft mới, xe phải còn ít nhất $16\text{ vòng}$ để bù lại thời gian đã mất.
  3. **Hiệu ứng bù trừ tự nhiên:** Xe nhẹ xăng dần ($\alpha_{\text{fuel}} = 0.058\text{ s/vòng}$) và mặt đường gom cao su ($\gamma_{\text{track}} = 0.022\text{ s/vòng}$) che giấu một phần độ mòn lốp trên dữ liệu thực tế.
* **Gợi ý hình ảnh/sơ đồ:** Sơ đồ hình tam giác biểu thị 3 nghịch lý đối kháng giằng co nhau.

---

## SLIDE 3: MÔ HÌNH HÓA TOÁN HỌC CHÍNH QUY (MATHEMATICAL FORMULATION)
* **Thông điệp chính:** Bài toán được phát biểu dưới dạng Tối ưu hóa Tổ hợp Phi tuyến Nguyên hỗn hợp có Ràng buộc.
* **Nội dung hiển thị:**
  * **Cá thể chiến lược (Chromosome):**
    $$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
    *Với $K \in \{1, 2, 3\}$ (số lần pit), $c_k \in \{\text{Soft, Medium, Hard}\}$, $l_k \ge 4$ (độ dài stint).*
  * **Hàm mục tiêu toàn cục:**
    $$\min_{\mathbf{X} \in \Omega} J(\mathbf{X}) = \sum_{k=1}^{K+1} \sum_{a=1}^{l_k} t_{\text{lap}}(c_k, a, i) + K \cdot T_{\text{pit}} + \Phi_{\text{FIA}}(\mathbf{X}) + \Phi_{\text{cliff}}(\mathbf{X})$$
  * **3 Ràng buộc cứng (Hard Constraints):**
    1. $\sum_{k=1}^{K+1} l_k = 53\text{ vòng}$ *(Bảo toàn tổng số vòng chặng Monza)*.
    2. $|\{c_1, \dots, c_{K+1}\}| \ge 2$ *(Luật FIA: Bắt buộc dùng $\ge 2$ loại lốp khác nhau)*.
    3. $l_k \le L_{\max}(c_k)$ *(Giới hạn cơ học chống nổ vách lốp)*.

---

## SLIDE 4: ĐỘNG LỰC HỌC MÒN LỐP PIRELLI & ĐẦU VÀO TỪ THÀNH VIÊN 3
* **Thông điệp chính:** Hàm suy giảm bậc hai phản ánh đúng bản chất cơ học nhớt đàn hồi và cung cấp đạo hàm giải tích phục vụ thuật toán.
* **Nội dung hiển thị:**
  * **Phương trình phân rã thời gian vòng đua:**
    $$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) + \big[ d_1(c) a + d_2(c) a^2 \big] + \alpha_{\text{fuel}}(N - i) - \gamma_{\text{track}} i$$
    * $d_1 a$: Mài mòn cơ học bề mặt (*Graining*).
    * $d_2 a^2$: Sinh nhiệt trễ đàn hồi nhớt ($Q_{\text{gen}}$), gây rộp lốp (*Blistering*) và sụp vách mòn (*Cliff*).
  * **Hai khám phá giải tích quan trọng:**
    * **Đạo hàm tốc độ mòn biên:** $\nabla t_{\text{deg}}(a) = d_1(c) + 2 d_2(c) a$ *(La bàn định hướng cho toán tử Repair)*.
    * **Công thức Faulhaber $O(1)$:** Tính tổng thời gian stint không cần vòng lặp:
      $$D_{\text{stint}}(c, L) = d_1 \frac{L(L+1)}{2} + d_2 \frac{L(L+1)(2L+1)}{6}$$
* **Bảng thông số hiệu chuẩn tại Monza (WLS Regression):**
  * Soft: $t_{\text{base}} = 81.50\text{ s}, d_1 = 0.120, d_2 = 0.0050, L_{\max} = 22\text{v}$
  * Medium: $t_{\text{base}} = 82.20\text{ s}, d_1 = 0.070, d_2 = 0.0020, L_{\max} = 35\text{v}$
  * Hard: $t_{\text{base}} = 83.00\text{ s}, d_1 = 0.040, d_2 = 0.0010, L_{\max} = 48\text{v}$

---

## SLIDE 5: KIẾN TRÚC PHƯƠNG PHÁP LUẬN: HAI TRỤ CỘT BẢO ĐẢM TÍNH ĐÚNG ĐẮN
* **Thông điệp chính:** Kết hợp sức mạnh của Quy hoạch động Bellman (Ground Truth) và Giải thuật Di truyền Thích nghi (Tác chiến thời gian thực).
* **Nội dung hiển thị (2 Cột đối trọng):**
  * **Trụ cột 1: Thước đo Chuẩn Tuyệt đối (Bellman DP - TV4 đảm nhiệm):**
    * Quy nạp ngược trên lưới $30,088$ trạng thái rời rạc $s = (i, c, a, k, m)$.
    * Tìm ra **Nghiệm Tối ưu Toàn cục Tuyệt đối ($4497.997\text{ s}$)** làm mốc đối chứng.
  * **Trụ cột 2: Bộ não Tối ưu Tiến hóa (Adaptive GA - TV1 đảm nhiệm):**
    * Tìm kiếm metaheuristic trên không gian biến thiên số chiều.
    * Đạt nghiệm tối ưu trong thời gian cực ngắn ($0.18\text{ s}$).
    * Khả năng mở rộng vượt trội khi bài toán thực tế có nhiều xe cản trở và đa mục tiêu.
* **Gợi ý hình ảnh/sơ đồ:** Sơ đồ 2 khối đối trọng song song: Bellman DP chỉ ra nghiệm $4497.997\text{ s}$ $\longleftrightarrow$ AGA đạt Optimality Gap $0.0000\%$.

---

## SLIDE 6: ĐỘT PHÁ THUẬT TOÁN CỦA THÀNH VIÊN 1 (ADAPTIVE GA CORE)
* **Thông điệp chính:** 3 cơ chế cải tiến triệt tiêu nghiệm bất khả thi và cho phép số lần dừng pit tự tiến hóa.
* **Nội dung hiển thị (3 Cải tiến cốt lõi):**
  1. **Khởi tạo có trọng số tri thức (65% 1-stop, 30% 2-stop, 5% 3-stop):**
     * Thỏa mãn ngay luật FIA từ thế hệ 0, loại bỏ lãng phí tính toán.
  2. **Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair Operator):**
     * Sử dụng đạo hàm $\nabla t_{\text{deg}} = d_1 + 2d_2 a$ để bù hoặc trừ số vòng khi $\sum l_k \ne 53$.
     * Đưa $100\%$ cá thể về miền khả thi mà không làm kiệt quệ đa dạng sinh học như hàm phạt thông thường.
  3. **Đột biến Đa hình thái 3 Cấp độ với Split / Merge Stint:**
     * *Micro (60%):* Tinh chỉnh vi mô $\pm 1$ vòng dò tìm điểm đáy.
     * *Meso (25%):* Hoán đổi hợp chất lốp thông minh.
     * *Macro (15%):* **Split Stint** ($K \to K+1$, cắt đôi stint thoát vách mòn) & **Merge Stint** ($K \to K-1$, gộp stint tiết kiệm $23.2\text{ s}$ pit).
     * $\rightarrow$ **Số lần pit $K$ tự tiến hóa tối ưu mà không cần fix cứng!**

---

## SLIDE 7: TÍNH NĂNG TÁC CHIẾN: TÁI TỐI ƯU XE AN TOÀN TRONG 5 MILI-GIÂY
* **Thông điệp chính:** Cơ chế Warm-Start Pivot giải quyết bài toán ra quyết định khẩn cấp tại Pit-wall.
* **Nội dung hiển thị:**
  * **Bản chất biến cố Safety Car:**
    * Tốc độ ngoài đường đua giảm $40\%$ nhưng tốc độ trong pit giữ nguyên $80\text{ km/h}$.
    * Tổn thất pit giảm đột ngột từ $23.2\text{ s} \to 12.5\text{ s}$ (*Hiện tượng Free Pit Stop*).
    * Cửa sổ ra quyết định chỉ mở ra trong $3 - 5\text{ giây}$.
  * **Cơ chế Warm-Start Pivot của TV1:**
    * Đóng băng các vòng đã đua $[1, L_{\text{SC}}]$, chỉ tái tối ưu các vòng còn lại.
    * Kế thừa nghiệm tốt nhất làm hạt giống, tái hội tụ trong $15$ thế hệ.
  * **KPI Hiệu năng:**
    * **Thời gian phản xạ: $5.2\text{ mili-giây}$** (Nhanh gấp 15 lần Bellman DP giải lại từ đầu $\approx 85\text{ ms}$).
    * Tiết kiệm tới **$10.7\text{ giây}$** chặng đua nhờ chớp thời cơ pit kịp thời.

---

## SLIDE 8: ĐỐI CHUẨN THỰC NGHIỆM KHOA HỌC & KIỂM ĐỊNH THỐNG KÊ
* **Thông điệp chính:** Kết quả đối chuẩn qua 30 random seeds chứng minh tính hội tụ tối ưu toàn cục và ý nghĩa thống kê của đề tài.
* **Bảng số liệu đối chuẩn 4 thuật toán (Chặng Monza 53 vòng):**
  | Thuật toán | Thời gian tốt nhất ($T_{\text{race}}$) | Độ lệch chuẩn $\sigma$ | Optimality Gap | CPU Runtime |
  | :--- | :---: | :---: | :---: | :---: |
  | **Bellman DP (Ground Truth)** | **$4497.997\text{ s}$** | $\pm 0.000\text{ s}$ | **$0.0000\%$** | $0.086\text{ s}$ |
  | **Greedy Baseline** | $4538.210\text{ s}$ | $\pm 0.000\text{ s}$ | $+0.8940\%$ ($+40.2\text{ s}$) | $< 0.001\text{ s}$ |
  | **Standard GA (Holland 1975)** | $4512.450\text{ s}$ | $\pm 5.420\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | $0.412\text{ s}$ |
  | **Proposed Adaptive GA (TV1)** | **$4497.997\text{ s}$** | **$\pm 0.000\text{ s}$** | **$0.0000\%$** | **$0.185\text{ s}$** |
* **2 KPI Khoa học then chốt:**
  * **Optimality Gap:** $0.0000\%$ (Chạm chính xác nghiệm tối ưu toàn cục của Bellman DP).
  * **Kiểm định Wilcoxon Signed-Rank Test:** $p = 3.59 \times 10^{-7} \ll 0.001$ (Khẳng định tính vượt trội có ý nghĩa thống kê).
  * **Nghiệm tối ưu:** `[Medium 20v -> Soft 14v -> Medium 19v]`.

---

## SLIDE 9: HỆ THỐNG KIỂM ĐỊNH ĐỘ TIN CẬY & GIAO DIỆN STREAMLIT
* **Thông điệp chính:** $100\%$ số liệu thực nghiệm được đo lường thực tế, có bộ kiểm thử tự động bảo chứng và giao diện tương tác trực quan.
* **Nội dung hiển thị:**
  * **Bộ kiểm thử tự động (Unit Tests):**
    * **$48/48$ tests PASSED $100\%$** trong $11.7\text{ giây}$.
    * Kiểm thử toàn diện: tính khả thi của 10.000 cá thể sau sửa chữa, tính toàn vẹn cấu trúc của Split/Merge, tính hội tụ qua 30 seeds.
  * **Giao diện Streamlit Web Dashboard (Pit-wall Simulation):**
    * Trực quan hóa diễn tiến mòn lốp và thời gian từng vòng.
    * Cho phép chạy thử kịch bản What-If và kích hoạt Safety Car để quan sát Warm-Start AGA tái tối ưu trực tiếp.

---

## SLIDE 10: TỔNG KẾT TIẾN ĐỘ & KẾ HOẠCH BẢO VỆ CHÍNH THỨC
* **Thông điệp chính:** Nhóm đã hoàn thành toàn diện Giai đoạn 1 (Core Toán & Code) và sẵn sàng cho Giai đoạn 2 (Báo cáo Elsevier & Seminar).
* **Nội dung hiển thị (3 Cột tóm tắt):**
  1. **Đã hoàn thành (GĐ1):**
     * Mô hình hóa toán học hoàn chỉnh.
     * Lõi giải thuật AGA và cơ chế Safety Car Warm-Start hoàn thiện, pass 48/48 tests.
     * Đối chuẩn thành công với Bellman DP Ground Truth (Gap $0.0000\%$).
  2. **Kế hoạch Giai đoạn 2:**
     * Hoàn thiện bài báo 2 cột chuẩn Elsevier trên Overleaf (mục tiêu 10–12 trang).
     * Nâng cấp kịch bản mô phỏng đa biến và tinh chỉnh Streamlit Dashboard.
  3. **Cam kết học thuật:**
     * Mã nguồn mở minh bạch, dữ liệu chuẩn FastF1, không ngụy tạo số liệu, sẵn sàng bảo vệ phản biện.
* **Kết thúc:** Trân trọng cảm ơn Thầy và mở phiên thảo luận góp ý (Q&A).
