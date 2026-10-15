# ĐẶC TẢ TOÁN HỌC & CƠ SỞ GIẢI THUẬT TIẾN HÓA (AGA)
## Đề án DS106: Tối ưu hóa Chiến lược Pit-Stop F1 (Monza GP - 53 Vòng)
**Phân công:** Thành viên 1 - Trưởng nhóm Thuật toán Tiến hóa (Algorithm & GA Lead)  
**Tiêu chuẩn Học thuật:** Báo cáo khoa học Elsevier 2 cột (Overleaf)  

---

### 1. Mô Hình Hóa Bài Toán Tối Ưu Hóa (Problem Formulation)
Bài toán tối ưu hóa chiến lược dừng pit và lựa chọn hợp chất lốp trong F1 được mô hình hóa dưới dạng bài toán **Tối ưu hóa tổ hợp phi tuyến nguyên hỗn hợp có ràng buộc** (*Constrained Non-linear Combinatorial Optimization*) với không gian tìm kiếm có số chiều biến thiên.

#### 1.1. Cấu Trúc Biểu Diễn Nhiễm Sắc Thể (Chromosome Representation)
Nhiễm sắc thể của một chiến lược đua được biểu diễn dưới dạng mảng các đoạn đua liên tục (*Stint Array*):
$$S = [ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) ]$$
Trong đó:
- $K \in \{1, 2, 3\}$: Số lần dừng pit trong chặng đua ($K+1$ stints).
- $c_k \in \{\text{Soft}, \text{Medium}, \text{Hard}\}$: Hợp chất lốp sử dụng trong stint thứ $k$.
- $l_k \in \mathbb{Z}^+$: Độ dài (số vòng đua) của stint thứ $k$, thỏa mãn $l_k \ge 4$.

#### 1.2. Hệ Thống Ràng Buộc (Constraints)
1. **Ràng buộc bảo toàn tổng số vòng đua ($R_1$ - Conservation Invariant):**
   $$\sum_{k=1}^{K+1} l_k = N_{\text{total}} = 53 \quad (\text{Monza GP})$$
2. **Luật lốp FIA ($R_2$ - Hard Legal Constraint):**
   Mỗi xe phải sử dụng ít nhất hai loại hợp chất lốp khô khác nhau trong cuộc đua:
   $$|\{c_1, c_2, \dots, c_{K+1}\}| \ge 2$$
3. **Ngưỡng an toàn cơ học vách lốp Pirelli ($R_3$ - Soft Mechanical Cliff Constraint):**
   $$l_k \le L_{\max}(c_k), \quad \forall k \in [1, K+1]$$
   Với các ngưỡng vách lốp: $L_{\max}(\text{Soft}) = 22$, $L_{\max}(\text{Medium}) = 35$, $L_{\max}(\text{Hard}) = 48$.

#### 1.3. Hàm Mục Tiêu & Hàm Phạt (Objective Function & Penalties)
Mục tiêu là tìm kiếm chiến lược $S^*$ cực tiểu hóa tổng thời gian hoàn thành toàn bộ chặng đua:
$$\min_{S} f(S) = T_{\text{race}}(S) + \Phi_{\text{FIA}}(S) + \Phi_{\text{cliff}}(S)$$
Trong đó:
- **Thời gian chạy thuần túy:**
  $$T_{\text{race}}(S) = \sum_{k=1}^{K+1} \sum_{a=1}^{l_k} t_{\text{lap}}(c_k, a, i) + K \cdot T_{\text{pit}}$$
  Với $i$ là thứ tự vòng đua toàn cục ($i \in [1, N_{\text{total}}]$), $a$ là tuổi lốp cơ học của stint, $T_{\text{pit}} = 23.2$ giây (tổn thất thời gian qua làn pit tại Monza).
- **Hàm phạt vi phạm luật FIA (Hard Penalty):**
  $$\Phi_{\text{FIA}}(S) = \begin{cases} 0 & \text{nếu } |\{c_k\}| \ge 2 \\ 100,000 & \text{ngược lại} \end{cases}$$
- **Hàm phạt rủi ro vách lốp Pirelli (Soft Penalty):**
  $$\Phi_{\text{cliff}}(S) = \sum_{k=1}^{K+1} \beta_{\text{risk}} \cdot \max(0, l_k - L_{\max}(c_k)) \quad (\beta_{\text{risk}} = 50.0 \text{ s/vòng})$$

---

### 2. Mô Hình Động Lực Học Lốp Giải Tích Pirelli (Tyre Physics Model)
Thời gian hoàn thành vòng đua tại vòng thứ $i$ trên bộ lốp hợp chất $c$ có tuổi $a$:
$$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) + \Delta t_{\text{deg}}(c, a) + \Delta t_{\text{fuel}}(i) - \Delta t_{\text{track}}(i)$$
- **Thời gian cơ sở:** $t_{\text{base}}(\text{Soft}) = 81.50$s, $t_{\text{base}}(\text{Medium}) = 82.20$s, $t_{\text{base}}(\text{Hard}) = 83.00$s.
- **Suy giảm lốp bậc hai:** $\Delta t_{\text{deg}}(c, a) = d_1(c) \cdot a + d_2(c) \cdot a^2$.
  - Soft: $d_1 = 0.120, d_2 = 0.0050$
  - Medium: $d_1 = 0.070, d_2 = 0.0020$
  - Hard: $d_1 = 0.040, d_2 = 0.0010$
- **Hiệu ứng xe nhẹ xăng:** $\Delta t_{\text{fuel}}(i) = \alpha_{\text{fuel}} \cdot (N_{\text{total}} - i)$ với $\alpha_{\text{fuel}} = 0.058$ s/vòng.
- **Hiệu ứng đường bám cao su:** $\Delta t_{\text{track}}(i) = \gamma_{\text{track}} \cdot i$ với $\gamma_{\text{track}} = 0.022$ s/vòng.

#### Đạo Hàm Giải Tích Suy Giảm Hiệu Suất Lốp ($\nabla t_{\text{deg}}$)
$$\nabla t_{\text{deg}}(c, a) = \frac{\partial \Delta t_{\text{deg}}}{\partial a} = d_1(c) + 2 \cdot d_2(c) \cdot a$$
Đạo hàm này biểu diễn tốc độ gia tăng thời gian vòng đua tại tuổi lốp $a$, là cơ sở định hướng cho Toán tử Sửa chữa Vật lý.

---

### 3. Các Toán Tử Di Truyền Thích Nghi Đột Phá (Novel GA Operators)

#### 3.1. Khởi Tạo Quần Thể Định Hướng Tri Thức Chuyên Gia (Heuristic Weighted Initialization)
Quần thể kích thước $P = 60$ được sinh theo phân phối xác suất thực tiễn F1:
- **65% Cá thể 1-stop:** Chọn 2 hợp chất khác nhau, điểm vào pit phân bố từ 25% đến 68% chặng đua.
- **30% Cá thể 2-stop:** Phân bổ 3 stints cân đối thỏa mãn luật FIA.
- **5% Cá thể 3-stop:** Chiến lược tấn công sprint stints.
- 100% cá thể khởi tạo đều được kiểm soát thỏa mãn ngay luật FIA.

#### 3.2. Toán Tử Sửa Chữa Định Hướng Vật Lý (Physics-Guided Repair Operator)
Triệt tiêu **100% nghiệm bất khả thi** sau khi lai ghép và đột biến:
1. **Kiểm tra luật FIA:** Nếu chỉ có 1 loại lốp, thay thế hợp chất của stint ngắn nhất bằng loại lốp khác để bảo toàn tính ổn định của các stint chính.
2. **Cân bằng số vòng $\Delta N = N_{\text{total}} - \sum l_k$:**
   - **Khi thiếu vòng ($\Delta N > 0$):** Dựa vào đạo hàm $\nabla t_{\text{deg}}(c_k, l_k)$ và dung sai an toàn vách lốp $(L_{\max}(c_k) - l_k)$, ưu tiên bù thêm vòng vào stint có dung sai an toàn lớn nhất và đạo hàm suy giảm thấp nhất (Hard/Medium).
   - **Khi thừa vòng ($\Delta N < 0$):** Khấu trừ vòng từ stint có đạo hàm suy giảm cao nhất ($\nabla t_{\text{deg}}$ cao nhất, lốp Soft hoặc stint vượt cliff), bảo đảm luôn duy trì $l_k \ge 4$.
3. **Bảo tồn bất biến:** Cam kết $\sum l_k = 53$ tuyệt đối.

#### 3.3. Đột Biến Đa Hình Thái 3 Cấp Độ (Tri-Level Polymorphic Mutation)
- **Micro-mutation (60%):** Dịch chuyển vi mô mốc pit giữa 2 stint liền kề ($l_k \pm 1, l_{k+1} \mp 1$) để tinh chỉnh điểm tối ưu cục bộ.
- **Meso-mutation (25%):** Hoán đổi hợp chất lốp thông minh.
- **Macro-mutation (15%):** Đột biến thay đổi số lần dừng pit $K$:
  - *Split Stint:* Chia đôi stint dài nhất thành 2 stint lốp khác nhau ($1\text{-stop} \to 2\text{-stop}$ hoặc $2\text{-stop} \to 3\text{-stop}$).
  - *Merge Stint:* Gộp 2 stint ngắn liền kề thành 1 stint lốp bền hơn ($3\text{-stop} \to 2\text{-stop}$ hoặc $2\text{-stop} \to 1\text{-stop}$).
  - Cho phép quần thể **tự động tiến hóa số lần dừng pit tối ưu $K$** một cách tự nhiên.

#### 3.4. Lịch Làm Mát Phi Tuyến & Tiêm Gen Hỗn Loạn (Cataclysmic Chaos Injection)
- **Lịch làm mát phi tuyến:**
  $$P_c(g) = P_{c,\min} + (P_{c,0} - P_{c,\min}) \cdot \left[1 - \left(\frac{g}{G_{\max}}\right)^{1.5}\right]$$
  $$P_m(g) = P_{m,\min} + (P_{m,0} - P_{m,\min}) \cdot \left[1 - \left(\frac{g}{G_{\max}}\right)^{1.2}\right]$$
  Với $P_{c,0} = 0.88, P_{c,\min} = 0.65$; $P_{m,0} = 0.25, P_{m,\min} = 0.08$.
- **Độ đa dạng quần thể $\bar{D}_{\text{pop}}$:** Kết hợp khoảng cách phân kỳ cấu trúc số stint, khoảng cách Hamming hợp chất, và độ lệch biên pit.
- **Tiêm gen hỗn loạn:** Nếu $\bar{D}_{\text{pop}} < 0.15$ tại $g < 0.70 \cdot G_{\max}$, nhân $P_m$ lên 2.5 lần ($P_m \leftarrow \min(0.65, P_m \times 2.5)$) để kích nổ đột biến diện rộng, bứt phá khỏi cực tiểu địa phương.
- **Bảo lưu tinh hoa (Elitism 5%):** Luôn giữ nguyên các cá thể tốt nhất qua từng thế hệ.

#### 3.5. Cơ Chế Tái Tối Ưu Xe An Toàn Thời Gian Thực (Warm-Start Safety Car Pivot)
Khi Xe An Toàn (Safety Car) xuất hiện tại vòng $L_{\text{sc}}$ làm tổn thất pit giảm đột ngột từ 23.2s xuống 12.5s:
1. Đóng băng các vòng đã đua $[1, L_{\text{sc}}]$ cùng hợp chất đã sử dụng.
2. Tái sử dụng các gen ưu tú kết hợp mồi các chiến lược vào pit khẩn cấp (Free Pit Stop).
3. Tái tối ưu hóa các vòng còn lại $[L_{\text{sc}} + 1, N_{\text{total}}]$ trong 15 thế hệ.
4. Thời gian phản hồi đo đạc thực tế: **$\approx 0.015 - 0.020$ giây** ($< 0.20$s), đáp ứng hoàn hảo cửa sổ tác chiến 3–5 giây trên Pit-wall.

---

### 4. Kết Quả Thực Nghiệm & Đối Chuẩn Bellman DP
- **Bellman DP Ground Truth:** $T_{\text{opt}} = 4497.997$s (Chiến lược: Medium [20] - Soft [14] - Medium [19]).
- **Adaptive GA (DAGA-F1):**
  - Đạt chính xác $4497.997$s trên tất cả các random seeds thử nghiệm.
  - **Optimality Gap = 0.0000%** (Tiêu chuẩn đề ra: $\le 0.05\%$).
  - Thời gian thực thi trung bình: **$0.110$ giây** ($< 1.0$ giây).
  - Tỷ lệ nghiệm khả thi sau sửa chữa: **100.000%** qua 10.000 mẫu kiểm thử.
  - Thời gian phản ứng Warm-Start Safety Car Pivot: **$0.015$ giây** ($< 0.20$ giây).
