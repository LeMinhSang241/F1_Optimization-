# BẢN ĐẶC TẢ LÝ THUYẾT THUẬT TOÁN TOÀN DIỆN CHO CẢ NHÓM (MASTER ALGORITHM SPECIFICATION)

---

1. **Bài toán Thực tế F1 & Bản chất Tối ưu hóa**
2. **Mô hình hóa Toán học Chính quy (Mathematical Formulation)**
3. **Đầu vào Kỹ thuật Tiếp nhận từ Thành viên 3 (Tyre Modeler)**
4. **Kiến trúc & 5 Cơ chế Đột phá của Giải thuật AGA (Thành viên 1)**
5. **Cơ chế Phản xạ Xe An Toàn Thời gian Thực (Safety Car Warm-Start Pivot)**
6. **Kết quả Thực nghiệm & Đối chuẩn với Bellman DP (Thành viên 4)**
7. **Q&A với Thầy**

---

## 1. BÀI TOÁN THỰC TẾ F1 & BẢN CHẤT TỐI ƯU HÓA

### 1.1. Bối cảnh & Mục tiêu Bài toán
Trong một chặng đua Công thức 1 (F1 Grand Prix), xe phải hoàn thành tổng quãng đường $305\text{ km}$ (tại Monza - Ý là $N = 53\text{ vòng}$). Kể từ năm 2010, Liên đoàn Ô tô Quốc tế (FIA) **nghiêm cấm tiếp nhiên liệu trong lúc đua** (Refuelling Ban). Do đó, xe phải mang toàn bộ khoảng $110\text{ kg}$ xăng ngay từ vạch xuất phát.  
$\rightarrow$ Lần dừng duy nhất trong làn pit là để **thay lốp xe**.

**Mục tiêu bài toán:** Tìm một chiến lược pit-stop hoàn chỉnh (bao gồm: *dừng bao nhiêu lần, vào pit ở vòng nào, và mỗi chặng chạy loại lốp gì*) sao cho **Tổng thời gian hoàn thành toàn bộ cuộc đua ($T_{\text{total}}$) là nhỏ nhất**, đồng thời tuân thủ tuyệt đối các quy định kỹ thuật nghiêm ngặt của FIA.

### 1.2. Tam giác Nghịch lý Vật lý Đối kháng (Trade-offs)
Bài toán này không thể giải theo cách suy nghĩ thông thường ("chọn lốp nhanh nhất mà chạy") vì nó bị chi phối bởi 3 mâu thuẫn vật lý đối kháng:
1. **Tốc độ vs Tuổi thọ lốp:**
   * Lốp **Soft (Mềm)** rất bám đường, nhanh hơn lốp Hard khoảng $1.5\text{ s/vòng}$, nhưng mòn rất nhanh. Khi chạm tới ngưỡng tuổi thọ giới hạn (*Tyre Cliff*), tốc độ xe giảm mạnh, thời gian hoàn thành vòng đua tăng từ $2 - 4\text{ s/vòng}$ và có nguy cơ nổ lốp.
   * Lốp **Hard (Cứng)** chạy chậm hơn nhưng bền bỉ suốt $40 - 50\text{ vòng}$.
   * $\rightarrow$ *Mâu thuẫn:* Không thể chỉ chọn Soft (vì phải vào pit quá nhiều lần), cũng không thể chỉ chọn Hard (vì tốc độ trung bình quá chậm).
2. **Chi phí Thời gian Làn Pit (Pit Lane Loss Delta - $T_{\text{pit}}$):**
   * Khi vào pit, xe bị giới hạn tốc độ $80\text{ km/h}$, trong khi xe trên đường đua chạy $330\text{ km/h}$. Tại Monza, thời gian tổn thất cố định này đo đạc thực tế là **$T_{\text{pit}} = 23.2\text{ giây}$**.
   * $\rightarrow$ *Tính toán thời gian:* Nếu muốn vào pit thêm 1 lần để đổi sang bộ lốp Soft mới (nhanh hơn lốp cũ $1.5\text{ s/vòng}$), xe phải còn ít nhất:
     $$\frac{23.2\text{ s}}{1.5\text{ s/vòng}} \approx 16\text{ vòng đua}$$
     để bù lại được $23.2\text{ giây}$ đã mất trong pit.
3. **Xe nhẹ xăng ($\alpha_{\text{fuel}}$) vs Mặt đường bám cao su ($\gamma_{\text{track}}$):**
   * Qua từng vòng, xe đốt cháy $\approx 1.6\text{ kg}$ xăng, xe nhẹ đi sẽ chạy nhanh hơn ($\alpha_{\text{fuel}} = 0.058\text{ s/vòng}$).
   * Đồng thời, cao su từ lốp của các xe từ các vòng trước miết xuống mặt đường tạo độ bám tăng dần ($\gamma_{\text{track}} = 0.022\text{ s/vòng}$).
   * $\rightarrow$ Hai yếu tố này làm thời gian vòng giảm dần theo thời gian, che giấu và triệt tiêu một phần độ mòn của lốp trên dữ liệu quan sát.

---

## 2. MÔ HÌNH HÓA TOÁN HỌC CHÍNH QUY (MATHEMATICAL FORMULATION)

Đề tài mô hình hóa bài toán thành: **Bài toán Tối ưu hóa Tổ hợp Phi tuyến Nguyên hỗn hợp có Ràng buộc (Constrained Non-linear Combinatorial Optimization) với số chiều biến thiên**.

### 2.1. Không gian Biến Quyết định & Cấu trúc Cá thể (Chromosome)
Một chiến lược dừng pit hoàn chỉnh được biểu diễn bởi một cá thể $\mathbf{X}$:
$$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
Trong đó:
* $K \in \{1, 2, 3\}$: Số lần dừng pit (tương ứng với $K+1$ chặng lốp liên tục - stint).
* $c_k \in \{0, 1, 2\}$: Loại hợp chất lốp ở stint thứ $k$ ($0: \text{Soft}, 1: \text{Medium}, 2: \text{Hard}$).
* $l_k \in \mathbb{Z}^+$: Độ dài stint thứ $k$ (số vòng chạy liên tục), với điều kiện vật lý $l_k \ge L_{\min} = 4\text{ vòng}$.
* Mốc vòng vào pit tương ứng là tập lũy kế: $p_k = \sum_{j=1}^k l_j$ với $1 \le p_1 < p_2 < \dots < p_K < N$.  
  *(Chú thích: $p_k$ là mốc vòng đua vào pit lần thứ $k$; $l_j$ là độ dài stint thứ $j$; $K$ là tổng số lần dừng pit; $N$ là tổng số vòng đua của chặng, $N = 53$).*

### 2.2. Hệ thống Ràng buộc Cứng (Hard Constraints)
Không gian nghiệm hợp lệ $\Omega$ bị kiểm soát nghiêm ngặt bởi 3 ràng buộc:
1. **(R1) Bảo toàn Tổng số vòng:**
   $$\sum_{k=1}^{K+1} l_k = N = 53\text{ vòng (tại Monza)}$$
2. **(R2) Quy chuẩn Thể thao FIA (Sporting Regulations Art. 30.5):** Trong điều kiện khô ráo, bắt buộc phải sử dụng **tối thiểu 2 loại hợp chất lốp khác nhau**:
   $$\big| \{c_1, c_2, \dots, c_{K+1}\} \big| \ge 2$$
   *(Vi phạm luật này sẽ bị truất quyền thi đấu - Disqualification).*
3. **(R3) Giới hạn An toàn Cơ học Vách lốp (Pirelli Tyre Cliff):**
   $$l_k \le L_{\max}(c_k), \quad \forall k \in [1, K+1]$$
   *(Chú thích: $l_k$ là số vòng chạy ở stint thứ $k$; $c_k$ là loại lốp của stint đó; $L_{\max}(c_k)$ là ngưỡng số vòng an toàn tối đa cho phép của loại lốp $c_k$).*

### 2.3. Hàm Mục tiêu Toàn cục (Objective Function)
Mục tiêu là tìm kiếm chiến lược $\mathbf{X}^* \in \Omega$ sao cho tổng thời gian chặng đua $J(\mathbf{X})$ đạt cực tiểu:
$$\min_{\mathbf{X} \in \Omega} J(\mathbf{X}) = \sum_{k=1}^{K+1} \sum_{a=1}^{l_k} t_{\text{lap}}(c_k, a, i(k, a)) + K \cdot T_{\text{pit}} + \Phi_{\text{FIA}}(\mathbf{X}) + \Phi_{\text{cliff}}(\mathbf{X})$$

Trong đó:
* $t_{\text{lap}}(c, a, i)$: Thời gian hoàn thành vòng đua thứ $i$ trên lốp $c$ ở tuổi thọ $a$.
* $K \cdot T_{\text{pit}}$: Tổng tổn thất thời gian di chuyển qua làn pit ($K \times 23.2\text{ s}$), trong đó $K$ là số lần dừng pit ($K \in \{1, 2, 3\}$), $T_{\text{pit}}$ là tổn thất thời gian cố định khi xe di chuyển qua làn pit ($23.2\text{ s}$ tại Monza).
* $\Phi_{\text{FIA}}(\mathbf{X})$: Hàm phạt cực đại đối với vi phạm luật FIA:
  $$\Phi_{\text{FIA}}(\mathbf{X}) = \begin{cases} 0 & \text{nếu } |\{c_k\}| \ge 2 \\ 100,000\text{ giây} & \text{nếu chỉ dùng duy nhất 1 loại lốp} \end{cases}$$
* $\Phi_{\text{cliff}}(\mathbf{X})$: Hàm phạt quá tải vách lốp:
  $$\Phi_{\text{cliff}}(\mathbf{X}) = 50.0 \times \sum_{k=1}^{K+1} \max\big(0, l_k - L_{\max}(c_k)\big)$$

---

## 3. ĐẦU VÀO KỸ THUẬT TIẾP NHẬN TỪ THÀNH VIÊN 3 (TYRE MODELER)

Để thuật toán tối ưu hóa chạy chính xác và có cơ sở khoa học, thuật toán tiếp nhận trực tiếp 3 kết quả nghiên cứu giải tích từ TV3:

### 3.1. Phương trình Suy giảm Lốp Giải tích Bậc hai Pirelli (WLS Regression)
Thời gian vòng đua thứ $i$ được phân rã thành 4 thành phần giải tích:
$$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) + \big[ d_1(c) a + d_2(c) a^2 \big] + \alpha_{\text{fuel}} (N - i) - \gamma_{\text{track}} i$$

*(Chú thích tham số: $c$ là loại hợp chất lốp; $a$ là số vòng lốp đã chạy liên tục ($a \in [1, l_k]$); $i$ là số thứ tự vòng đua hiện tại ($i \in [1, N]$); $t_{\text{base}}(c)$ là thời gian cơ sở của lốp $c$; $d_1(c)$ là hệ số suy giảm tuyến tính; $d_2(c)$ là hệ số suy giảm phi tuyến bậc hai; $\alpha_{\text{fuel}} = 0.058\text{ s/vòng}$ là hệ số độ trễ do tải trọng nhiên liệu; $N = 53$ là tổng số vòng chặng đua; $\gamma_{\text{track}} = 0.022\text{ s/vòng}$ là hệ số bám cao su mặt đường).*

* Ý nghĩa vật lý:
  - $d_1(c) a$: Hiện tượng mài mòn cơ học tự nhiên bề mặt (*Graining*). Khi cao su cọ xát liên tục với mặt đường nhựa, các hạt cao su nhỏ bị bong tróc làm diện tích tiếp xúc giảm dần, khiến xe mất dần độ bám đường theo từng vòng đua.
  - $d_2(c) a^2$: Hiện tượng suy thoái nhiệt phi tuyến tính bên trong kết cấu lốp (*Blistering* và *Tyre Cliff*). Khi xe chạy ở tốc độ cao và phanh gấp liên tục, nhiệt sinh ra do biến dạng trễ đàn hồi nhớt ($Q_{\text{gen}} = \pi f E'' \epsilon^2$) tích tụ bên trong khung lốp mà không kịp tản ra ngoài. Nhiệt độ quá cao làm sôi cao su, phồng rộp bề mặt và làm độ bám suy giảm rất nhanh sau khi vượt qua một ngưỡng tuổi thọ nhất định.

**Bảng tham số chuẩn hóa tại Monza (53 vòng, $T_{\text{pit}} = 23.2\text{ s}$):**  
*(Nguồn: Dữ liệu viễn trắc chính thức FastF1 chặng Italian GP 2023, ước lượng bằng hồi quy Weighted Least Squares bởi Thành viên 3 kết hợp tài liệu kỹ thuật Pirelli Motorsport)*
| Hợp chất lốp ($c$) | Thời gian cơ sở $t_{\text{base}}$ | Hệ số $d_1$ (s/vòng) | Hệ số $d_2$ (s/vòng$^2$) | Tuổi thọ an toàn $L_{\max}$ |
| :--- | :---: | :---: | :---: | :---: |
| **Soft (C4)** | $81.50\text{ s}$ | $0.120$ | $0.0050$ | $22\text{ vòng}$ |
| **Medium (C3)** | $82.20\text{ s}$ | $0.070$ | $0.0020$ | $35\text{ vòng}$ |
| **Hard (C2)** | $83.00\text{ s}$ | $0.040$ | $0.0010$ | $48\text{ vòng}$ |

### 3.2. Đạo hàm Tốc độ Mài mòn Biên Giải tích ($\nabla t_{\text{deg}}$)
Hàm suy giảm lốp có đạo hàm cấp 1 và cấp 2 giải tích:
$$\nabla t_{\text{deg}}(a) = \frac{\partial t_{\text{deg}}}{\partial a} = d_1(c) + 2 d_2(c) a$$
$$\nabla^2 t_{\text{deg}}(a) = 2 d_2(c) > 0 \quad (\text{Hàm lồi ngặt - Strictly Convex})$$
* **Ứng dụng trong thuật toán:** Đạo hàm này cung cấp hướng dốc giải tích cho Toán tử Sửa chữa (Physics-Guided Repair Operator), giúp thuật toán xác định chính xác stint nào có tốc độ suy giảm cao nhất để khấu trừ bớt vòng, và stint nào còn khoảng cách an toàn lớn nhất để bù thêm vòng.

### 3.3. Công thức Tổng Đóng Faulhaber $O(1)$
Thay vì phải dùng vòng lặp $\sum_{a=1}^L (d_1 a + d_2 a^2)$ mất độ phức tạp $O(L)$, công thức tổng đóng Faulhaber giải tích:
$$D_{\text{stint}}(c, L) = \sum_{a=1}^L \big( d_1 a + d_2 a^2 \big) = d_1 \frac{L(L+1)}{2} + d_2 \frac{L(L+1)(2L+1)}{6}$$
* **Ứng dụng trong thuật toán:** Chuyển đổi việc tính tổng thời gian suy giảm của một stint từ độ phức tạp $O(L)$ thành công thức giải tích $O(1)$, rút ngắn thời gian đánh giá hàm thích nghi (fitness evaluation) xuống mức micro-giây, bảo đảm tốc độ tính toán cho toàn bộ quần thể qua nhiều thế hệ.

---

## 4. KIẾN TRÚC & 5 CƠ CHẾ ĐỘT PHÁ CỦA GIẢI THUẬT AGA (THÀNH VIÊN 1)

Giải thuật Di truyền Thích nghi (Adaptive Genetic Algorithm - AGA) sở hữu **5 cải tiến then chốt**:

```
[Quần thể ban đầu P=60]
       │
       ▼
(1) Khởi tạo Trọng số Tri thức (65% 1-stop, 30% 2-stop, 5% 3-stop)
       │
       ▼
(2) Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair via ∇t_deg)
       │
       ▼
   Lai ghép Stint Crossover
       │
       ▼
(3) Đột biến Đa hình thái 3 Cấp độ
    ├─ Micro (60%): Tinh chỉnh vi mô ±1 vòng
    ├─ Meso  (25%): Hoán đổi hợp chất lốp
    └─ Macro (15%): Split / Merge Stint (Tự tiến hóa số lần dừng K)
       │
       ▼
(4) Lịch làm mát Thích nghi Pc(g), Pm(g) & Tiêm gen Hỗn loạn (Chaos Injection)
       │
       ▼
(5) Cơ chế Tái tối ưu Safety Car Thời gian thực (Warm-Start Pivot < 5ms)
```

---

### Cơ chế 1: Khởi tạo Quần thể Định hướng Tri thức Chuyên gia (Heuristic Weighted Initialization)
* **Vấn đề của GA cổ điển:** Khởi tạo ngẫu nhiên đều khiến $90\%$ cá thể sinh ra vi phạm luật FIA (chỉ dùng 1 loại lốp) hoặc chọn số lần pit vô lý (4–5 lần pit), làm lãng phí hàng trăm thế hệ đầu tiên chỉ để học lại các quy tắc hiển nhiên.
* **Giải pháp:** Dựa trên phân tích dữ liệu lịch sử các chặng đua F1 hiện đại, phân bổ trọng số khởi tạo:
  * **$65\%$ cá thể 1-stop** ($K = 1$, ví dụ: Medium $\to$ Hard).
  * **$30\%$ cá thể 2-stop** ($K = 2$, ví dụ: Medium $\to$ Soft $\to$ Medium).
  * **$5\%$ cá thể 3-stop** ($K = 3$, chiến thuật tấn công đặc biệt).
* Toàn bộ các cá thể được gán sẵn các cặp hợp chất thỏa mãn ngay luật FIA ($|\{c_k\}| \ge 2$).

---

### Cơ chế 2: Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair Operator)
* **Vấn đề của GA cổ điển:** Khi lai ghép hoặc đột biến, các cá thể con thường xuyên bị lệch tổng số vòng ($\sum l_k \ne 53$). Nếu dùng phương pháp truyền thống là "phạt nặng để loại bỏ" (*Death Penalty*), quần thể sẽ bị cạn kiệt đa dạng sinh học và rơi vào bế tắc.
* **Giải pháp:** Thiết kế toán tử sửa chữa định hướng vật lý không phá vỡ cấu trúc:
  1. Tính độ lệch số vòng: $\Delta N = 53 - \sum_{k=1}^{K+1} l_k$.
  2. **Nếu thiếu vòng ($\Delta N > 0$):** Dựa vào đạo hàm $\nabla t_{\text{deg}}$, thuật toán tìm stint nào có *khoảng cách an toàn tới vách lốp lớn nhất* $\big(L_{\max}(c_k) - l_k\big)$ để bù thêm vòng vào đó (ưu tiên lốp Hard hoặc Medium).
  3. **Nếu thừa vòng ($\Delta N < 0$):** Khấu trừ số vòng từ stint có *tốc độ mòn biên lớn nhất* ($\nabla t_{\text{deg}}$ cao nhất - lốp Soft đã cũ) hoặc stint dài nhất, bảo đảm luôn duy trì $l_k \ge 4$.
  4. **Kiểm tra luật FIA:** Nếu sau lai ghép cá thể bị trùng lặp lốp ($|\{c_k\}| = 1$), tự động chuyển đổi hợp chất của stint ngắn nhất sang loại lốp hợp lệ khác.
* **Kết quả:** Triệt tiêu **$100\%$** nghiệm bất khả thi, đưa mọi cá thể về không gian nghiệm hợp lệ $\Omega$.
* **Lưu ý đánh giá:** Cơ chế sửa chữa này hiện tại được cài đặt theo các quy tắc logic điều kiện (thuần if-else) dựa trên đạo hàm mòn biên. Phương pháp này đã giải quyết tốt việc bảo toàn tính khả thi của cá thể, tuy nhiên mới chỉ tối ưu hóa được một phần và chưa phải là phép chiếu tối ưu toán học tuyệt đối, còn tiềm năng phát triển sâu hơn trong tương lai.

---

### Cơ chế 3: Đột biến Đa hình thái 3 Cấp độ (Tri-Level Mutation) với Split / Merge Stint
* **Vấn đề lớn nhất của bài toán:** Số lần dừng pit $K$ là một biến nguyên rời rạc ($K \in \{1, 2, 3\}$). Nếu cố định chiều dài nhiễm sắc thể, thuật toán không thể so sánh được giữa chiến lược 1-stop và 2-stop.
* **Giải pháp:** Thiết kế nhiễm sắc thể biến thiên chiều dài và đột biến 3 cấp độ:
  1. **Micro-mutation ($60\%$):** Tinh chỉnh vi mô mốc pit giữa 2 stint liền kề:
     $$l_k \leftarrow l_k \pm 1, \quad l_{k+1} \leftarrow l_{k+1} \mp 1$$
     Bảo toàn chính xác $\sum l_k = 53$, giúp thuật toán khai thác sâu (*Exploitation*) dò tìm chính xác điểm đáy tối ưu.
  2. **Meso-mutation ($25\%$):** Hoán đổi ngẫu nhiên hợp chất lốp của một stint sang loại khác, giữ nguyên độ dài stint và bảo toàn luật FIA.
  3. **Macro-mutation ($15\%$) - Biến thiên Cấu trúc (Split & Merge):**
     * **Cơ chế Tách stint (Split Stint - Chuyển $K \to K+1$):**
       - Chọn stint dài nhất ($l_k \ge 8$).
       - Cắt đôi stint đó tại điểm ngẫu nhiên thành 2 stint: $(c_k, l_{\text{part1}})$ và $(c_{\text{new}}, l_k - l_{\text{part1}})$.
       - *Ý nghĩa vật lý:* Giải cứu xe khỏi hiện tượng vách mòn (*Tyre Cliff*) bằng cách chèn thêm một lần pit để lấy lốp mới nhanh hơn.
     * **Cơ chế Gộp stint (Merge Stint - Chuyển $K \to K-1$):**
       - Chọn 2 stint liền kề ngắn, gộp lại thành 1 stint duy nhất: $l_{\text{merged}} = l_k + l_{k+1}$.
       - Tự động gán hợp chất bền hơn (nếu $l_{\text{merged}} > 25\text{v}$ gán Hard; nếu $> 18\text{v}$ gán Medium) để không bị nổ lốp.
       - *Ý nghĩa vật lý:* Tiết kiệm trọn vẹn $23.2\text{ giây}$ tổn thất làn pit.
     * $\rightarrow$ **Nhờ cơ chế này, số lần dừng pit $K$ tự động tiến hóa để tìm ra chiến lược tối ưu mà người lập trình không cần can thiệp gán cứng!**

---

### Cơ chế 4: Lịch Làm mát Phi tuyến & Tiêm Gen Hỗn loạn (Cataclysmic Chaos Injection)
* Xác suất lai ghép $P_c(g)$ và đột biến $P_m(g)$ thích nghi phi tuyến theo thế hệ $g \in [1, G_{\max}]$:
  $$P_c(g) = P_{c,\min} + (P_{c,0} - P_{c,\min}) \times \left[ 1 - \left(\frac{g}{G_{\max}}\right)^{1.5} \right]$$
  $$P_m(g) = P_{m,\min} + (P_{m,0} - P_{m,\min}) \times \left[ 1 - \left(\frac{g}{G_{\max}}\right)^{1.2} \right]$$
  *(Chú thích: $g$ là số thứ tự thế hệ hiện tại; $G_{\max}$ là tổng số thế hệ; $P_{c,0}, P_{c,\min}$ là xác suất lai ghép khởi đầu và giá trị nhỏ nhất; $P_{m,0}, P_{m,\min}$ là xác suất đột biến khởi đầu và giá trị nhỏ nhất. Đầu quá trình: $P_c, P_m$ cao để khám phá không gian; Cuối quá trình: giảm dần để hội tụ ổn định).*
* **Phá bẫy Cực tiểu Địa phương (Chaos Injection):**  
  Thuật toán liên tục đo độ đa dạng kiểu gen quần thể $\bar{D}_{\text{pop}}$ (khoảng cách sai khác trung bình giữa các cá thể trong quần thể). Nếu $\bar{D}_{\text{pop}} < 0.15$ (dấu hiệu quần thể bị suy giảm độ đa dạng và hội tụ sớm về cực tiểu địa phương), thuật toán tự động kích hoạt **Cataclysmic Chaos Injection**:
  $$\text{Nhân } P_m \times 2.5 \quad \text{trong 3 thế hệ liên tiếp}$$
  Gia tăng cường độ đột biến trên diện rộng nhằm hỗ trợ quần thể thoát khỏi vùng hấp dẫn của cực tiểu địa phương và mở rộng không gian tìm kiếm.

---

## 5. CƠ CHẾ PHẢN XẠ XE AN TOÀN THỜI GIAN THỰC (SAFETY CAR WARM-START PIVOT)

### 5.1. Bản chất Vật lý của Hiện tượng "Free Pit Stop"
Khi có tai nạn trên đường đua tại vòng thứ $L_{\text{SC}}$, Giám đốc cuộc đua kích hoạt Xe An Toàn (Safety Car):
* Tốc độ ngoài đường đua bị khống chế giảm $40\%$ (thời gian vòng tăng từ $\approx 82\text{ s} \to \approx 120\text{ s}$).
* Tuy nhiên, tốc độ trong làn pit vẫn giữ nguyên tối đa $80\text{ km/h}$.
* $\rightarrow$ **Tổn thất thời gian tương đối của làn pit ($T_{\text{pit}}$) giảm đột ngột từ $23.2\text{ giây} \to 12.5\text{ giây}$!**
* Đội đua nào vào pit ngay thời điểm này sẽ được lợi hơn $10\text{ giây}$ so với đối thủ vào pit ở điều kiện cờ xanh.
* Tuy nhiên, **Cửa sổ ra quyết định chỉ mở ra trong $3 - 5\text{ giây}$** trước khi xe chạy qua lối vào pit.
* **Giới hạn nghiên cứu (Limitation):** Mô hình hiện tại chưa xét đến vị trí hình học của xe trên đường đua tại thời điểm xuất hiện cờ Xe An Toàn (ví dụ: xe đang chạy ở gần lối vào làn pit hay vừa đi qua lối vào pit và phải chạy thêm một vòng với tốc độ chậm trước khi được vào pit).

### 5.2. Thuật toán Tái Tối Ưu Warm-Start Pivot
Nếu chạy lại giải thuật tối ưu từ đầu, thời gian tính toán sẽ không kịp đáp ứng. Cơ chế Warm-Start Pivot giải quyết bài toán này:
1. **Đóng băng quá khứ:** Cố định toàn bộ các vòng đã đua $[1, L_{\text{SC}}]$.
2. **Khởi tạo kế thừa:** Sử dụng chính cá thể tốt nhất hiện tại làm hạt giống (seed) thay vì khởi tạo ngẫu nhiên từ đầu.
3. **Cập nhật tham số:** Giảm $T_{\text{pit}} \leftarrow 12.5\text{ s}$, số vòng còn lại cần tối ưu là $N_{\text{remain}} = N - L_{\text{SC}}$.
4. **Tái hội tụ thần tốc:** Chạy lõi AGA với số thế hệ rút gọn ($G_{\text{warm}} = 15$).  
*(Chú thích ký hiệu: $L_{\text{SC}}$ là vòng đua xảy ra sự cố Xe An Toàn; $N_{\text{remain}}$ là số vòng còn lại cần tính toán; $G_{\text{warm}}$ là số thế hệ tái tối ưu).*
* **Thời gian thực thi:** **$4.1 - 5.5\text{ mili-giây}$** (nhanh hơn gấp 15 lần so với việc giải lại bằng Bellman DP mất $65 - 85\text{ ms}$).

---

## 6. KẾT QUẢ THỰC NGHIỆM & ĐỐI CHUẨN KHOA HỌC

Toàn bộ kết quả dưới đây là số liệu thực tế được đo đạc từ hệ thống mã nguồn và kiểm chứng qua $48/48$ unit tests tự động:

### 6.1. Bảng Đối chuẩn Toàn diện 4 Thuật toán trên Chặng Monza (53 vòng)
| Thuật toán | Phân loại phương pháp | Thời gian đua tốt nhất ($T_{\text{race}}$) | Độ lệch chuẩn $\sigma$ | Sai số tối ưu (Optimality Gap) | CPU Runtime |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Bellman DP Solver** (TV4) | Quy hoạch động chính xác (Ground Truth) | **$4497.997\text{ s}$** | $\pm 0.000\text{ s}$ | **$0.0000\%$** (Mốc chuẩn) | $0.086\text{ s}$ |
| **Greedy Baseline** (TV5) | Tham lam theo quy tắc (Rule-based) | $4538.210\text{ s}$ | $\pm 0.000\text{ s}$ | $+0.8940\%$ ($+40.2\text{ s}$) | $< 0.001\text{ s}$ |
| **Standard GA** (Holland 1975) | Di truyền cổ điển (Fixed $P_c, P_m$) | $4512.450\text{ s}$ | $\pm 5.420\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | $0.412\text{ s}$ |
| **Adaptive GA (TV1 đề xuất)** | Di truyền thích nghi có Repair & Split/Merge | **$4497.997\text{ s}$** | **$\pm 0.000\text{ s}$** | **$0.0000\%$** (Chạm mốc tối ưu) | **$0.185\text{ s}$** |

### 6.2. Kiểm định Ý nghĩa Thống kê (Wilcoxon Signed-Rank Test)
* Chạy thử nghiệm trên **30 random seeds độc lập** (seeds 1 đến 30).
* Kết quả kiểm định phi tham số Wilcoxon giữa Proposed AGA và Standard GA:
  $$p\text{-value} = 3.59 \times 10^{-7} \ll 0.001$$
* Khẳng định sự vượt trội của AGA là có ý nghĩa thống kê tuyệt đối, loại trừ hoàn toàn yếu tố may rủi ngẫu nhiên.

### 6.3. Chiến lược Tối ưu Toàn cục Lý thuyết
* **Nghiệm tối ưu:** Chiến lược **2-stop**:
  $$\big[ \text{Medium: } 20\text{ vòng} \;\longrightarrow\; \text{Soft: } 14\text{ vòng} \;\longrightarrow\; \text{Medium: } 19\text{ vòng} \big]$$
* **Tổng thời gian chặng:** $4497.997\text{ giây}$ (1 giờ 14 phút 57.997 giây).

---

## 7. Q&A VỚI THẦY: BẢN CHẤT TỐI ƯU HÓA

### Câu hỏi 1: "Tại sao không dùng Gradient Descent (đạo hàm giảm) giải cho nhanh mà lại dùng GA?"
> **Trả lời:** "Thưa Thầy, hàm mục tiêu thời gian đua trong F1 là hàm **phi tuyến nguyên hỗn hợp và không liên tục**.  
> Thứ nhất, số lần dừng pit $K$ và loại lốp $c$ là các biến rời rạc, không có đạo hàm liên tục.  
> Thứ hai, chi phí làn pit $T_{\text{pit}} = 23.2\text{ s}$ tạo ra các bước nhảy thời gian gián đoạn cực lớn, tạo nên bề mặt tối ưu gồ ghề với vô số hố cực tiểu địa phương. Gradient Descent thuần túy sẽ ngay lập tức bị kẹt tại điểm xuất phát.  
> Vì vậy, bài toán bắt buộc phải dùng các phương pháp tìm kiếm metaheuristic như GA hoặc quy hoạch động."

### Câu hỏi 2: "Tại sao nhóm lại dùng Toán tử Sửa chữa (Repair) mà không dùng Hàm Phạt (Penalty Function) thông thường?"
> **Trả lời:** "Thưa Thầy, không gian nghiệm của bài toán F1 bị giới hạn bởi 2 ràng buộc đẳng thức và bất đẳng thức khắt khe: $\sum l_k = 53$ và $|\{c_k\}| \ge 2$.  
> Nếu chỉ dùng hàm phạt (đặc biệt là Death Penalty), phần lớn các cá thể sinh ra từ lai ghép và đột biến sẽ bị xóa sổ, làm cạn kiệt tính đa dạng sinh học của quần thể và khiến GA hội tụ sớm vào nghiệm hạ đẳng.  
> Ngược lại, việc nhóm thiết kế Toán tử Sửa chữa dựa trên **đạo hàm mài mòn biên $\nabla t_{\text{deg}}$** giúp biến các cá thể bất khả thi trở lại thành cá thể hợp lệ ngay trên biên của miền chấp nhận được, vừa bảo toàn tri thức tìm kiếm của thế hệ trước, vừa bảo đảm $100\%$ nghiệm sinh ra là khả thi."

### Câu hỏi 3: "Nếu Bellman DP đã tìm ra nghiệm tối ưu toàn cục rồi, tại sao đề tài của em còn cần giải thuật GA?"
> **Trả lời:** "Thưa Thầy, đây là luận điểm then chốt của đề tài.  
> Bellman DP là **thước đo chân lý (Ground Truth)** cực kỳ xuất sắc trong bài toán tĩnh đơn mục tiêu cho 1 xe chạy đơn độc trong điều kiện đường thông thoáng (Free air), giải quyết trên $30,088$ trạng thái.  
> Tuy nhiên, trong thực tế đua xe, bài toán sẽ mở rộng sang: (1) Đua đối kháng nhiều xe (Game Theory, tránh khí bẩn Dirty Air); (2) Bài toán đa mục tiêu (vừa tối ưu thời gian vừa né rủi ro mòn lốp); (3) Tái tối ưu tức thời khi có cờ vàng hay thời tiết mưa bất ngờ. Khi thêm các chiều trạng thái này, DP sẽ gặp hiện tượng **Bùng nổ Không gian Trạng thái (Curse of Dimensionality, $> 10^9$ trạng thái)** và hoàn toàn tràn bộ nhớ.  
> Khi đó, giải thuật tiến hóa AGA của em với độ phức tạp đa thức và tốc độ hội tụ nhanh ($0.18\text{ s}$, và $5\text{ ms}$ với Warm-Start) là công cụ duy nhất có thể triển khai thời gian thực tại Pit-wall!"
