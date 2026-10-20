# TÀI LIỆU MÔ TẢ THUẬT TOÁN TIẾN HÓA (AGA)

---

1. **Bài toán Thực tế F1 & Bản chất Tối ưu hóa**
2. **Mô hình hóa Toán học Chính quy (Mathematical Formulation)**
3. **Đầu vào Kỹ thuật Tiếp nhận từ Thành viên 3 (Tyre Modeler)**
4. **Cơ sở Thiết kế và Các Cơ chế của Giải thuật AGA**
5. **Cơ chế Tái Tối Ưu Thời Gian Thực Khi Có Xe An Toàn (Warm-Start Pivot)**
6. **Kết quả Thực nghiệm & Đối chuẩn với Bellman DP (Thành viên 4)**
7. **Q&A với Thầy**

---

## 1. BÀI TOÁN THỰC TẾ F1 & BẢN CHẤT TỐI ƯU HÓA

### 1.1. Bối cảnh & Mục tiêu Bài toán
Trong một chặng đua Công thức 1 (F1 Grand Prix), xe phải hoàn thành tổng quãng đường $305\text{ km}$ (tại chặng Monza - Ý tương ứng với $N = 53\text{ vòng}$). Kể từ năm 2010, Liên đoàn Ô tô Quốc tế (FIA) quy định cấm tiếp nhiên liệu trong lúc diễn ra cuộc đua (Refuelling Ban). Do đó, xe phải mang toàn bộ lượng nhiên liệu cần thiết (khoảng $110\text{ kg}$ xăng) ngay từ vạch xuất phát.  
$\rightarrow$ Lần dừng duy nhất trong làn pit là để thay lốp xe.

**Mục tiêu bài toán:** Tìm kiếm một chiến lược pit-stop hoàn chỉnh (bao gồm: số lần dừng pit, thời điểm vào pit và lựa chọn hợp chất lốp cho từng chặng chạy) sao cho **tổng thời gian hoàn thành cuộc đua ($T_{\text{total}}$) là nhỏ nhất**, đồng thời tuân thủ các quy định kỹ thuật của FIA.

### 1.2. Mối quan hệ Đánh đổi Vật lý (Trade-offs)
Bài toán tối ưu hóa chiến lược chịu sự tác động đồng thời của 3 yếu tố động lực học:
1. **Tốc độ vs Tuổi thọ lốp:**
   * Lốp **Soft (Mềm)** có độ bám cao, thời gian vòng nhanh hơn lốp Hard khoảng $1.5\text{ s/vòng}$, nhưng tốc độ mòn nhanh. Khi vượt qua ngưỡng tuổi thọ giới hạn (*Tyre Cliff*), tốc độ xe giảm mạnh, thời gian hoàn thành vòng đua tăng từ $2 - 4\text{ s/vòng}$ và đối mặt nguy cơ mất an toàn.
   * Lốp **Hard (Cứng)** có tốc độ chậm hơn nhưng duy trì độ ổn định trong khoảng $40 - 50\text{ vòng}$.
   * $\rightarrow$ Không thể chỉ sử dụng lốp Soft vì số lần dừng pit sẽ tăng, và cũng không thể chỉ dùng lốp Hard vì tốc độ trung bình sẽ thấp.
2. **Tổn thất Thời gian Làn Pit (Pit Lane Loss Delta - $T_{\text{pit}}$):**
   * Khi vào pit, xe chịu giới hạn tốc độ $80\text{ km/h}$, trong khi các xe ngoài đường đua di chuyển với vận tốc trung bình lớn hơn nhiều. Tại Monza, thời gian tổn thất cố định đo đạc từ dữ liệu thực tế là **$T_{\text{pit}} = 23.2\text{ giây}$**.
   * $\rightarrow$ *Tính toán thời gian:* Nếu thực hiện thêm một lần pit để chuyển sang bộ lốp Soft mới (nhanh hơn lốp cũ khoảng $1.5\text{ s/vòng}$), xe cần ít nhất:
     $$\frac{23.2\text{ s}}{1.5\text{ s/vòng}} \approx 16\text{ vòng đua}$$
     để bù đắp lại khoảng thời gian $23.2\text{ giây}$ đã tiêu tốn trong làn pit.
3. **Hiệu ứng Xe nhẹ xăng ($\alpha_{\text{fuel}}$) vs Mặt đường bám cao su ($\gamma_{\text{track}}$):**
   * Qua từng vòng, lượng nhiên liệu tiêu hao làm xe nhẹ dần ($\alpha_{\text{fuel}} = 0.058\text{ s/vòng}$).
   * Đồng thời, cao su từ lốp của các xe từ các vòng trước miết xuống mặt đường tạo độ bám tăng dần ($\gamma_{\text{track}} = 0.022\text{ s/vòng}$).
   * $\rightarrow$ Hai yếu tố này làm thời gian vòng có xu hướng giảm dần theo diễn biến cuộc đua, che khuất một phần mức độ suy thoái thực sự của lốp trên dữ liệu quan sát.

---

## 2. MÔ HÌNH HÓA TOÁN HỌC CHÍNH QUY (MATHEMATICAL FORMULATION)

Đề tài mô hình hóa bài toán dưới dạng: **Tối ưu hóa Tổ hợp Phi tuyến Nguyên hỗn hợp có Ràng buộc (Constrained Non-linear Combinatorial Optimization) với số chiều biến thiên**.

### 2.1. Không gian Biến Quyết định & Cấu trúc Cá thể (Chromosome)
Một chiến lược dừng pit được biểu diễn qua vector nghiệm $\mathbf{X}$:
$$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
Trong đó:
* $K \in \{1, 2, 3\}$: Số lần dừng pit (tương ứng với $K+1$ chặng lốp liên tục - stint).
* $c_k \in \{0, 1, 2\}$: Loại hợp chất lốp ở stint thứ $k$ ($0: \text{Soft}, 1: \text{Medium}, 2: \text{Hard}$).
* $l_k \in \mathbb{Z}^+$: Độ dài stint thứ $k$ (số vòng chạy liên tục), với điều kiện kỹ thuật $l_k \ge L_{\min} = 4\text{ vòng}$.
* Mốc vòng vào pit tương ứng là tập lũy kế: $p_k = \sum_{j=1}^k l_j$ với $1 \le p_1 < p_2 < \dots < p_K < N$.  
  *(Chú thích: $p_k$ là mốc vòng đua vào pit lần thứ $k$; $l_j$ là độ dài stint thứ $j$; $K$ là tổng số lần dừng pit; $N$ là tổng số vòng đua của chặng, $N = 53$).*

### 2.2. Hệ thống Ràng buộc Cứng (Hard Constraints)
Không gian nghiệm hợp lệ $\Omega$ bị kiểm soát bởi 3 ràng buộc kỹ thuật:
1. **(R1) Bảo toàn Tổng số vòng:**
   $$\sum_{k=1}^{K+1} l_k = N = 53\text{ vòng (tại Monza)}$$
2. **(R2) Quy chuẩn Thể thao FIA (Sporting Regulations Art. 30.5):** Trong điều kiện thời tiết khô ráo, xe bắt buộc phải sử dụng **tối thiểu 2 loại hợp chất lốp khác nhau**:
   $$\big| \{c_1, c_2, \dots, c_{K+1}\} \big| \ge 2$$
3. **(R3) Giới hạn An toàn Cơ học Vách lốp (Pirelli Tyre Cliff):**
   $$l_k \le L_{\max}(c_k), \quad \forall k \in [1, K+1]$$
   *(Chú thích: $l_k$ là số vòng chạy ở stint thứ $k$; $c_k$ là loại lốp của stint đó; $L_{\max}(c_k)$ là ngưỡng số vòng an toàn tối đa cho phép của loại lốp $c_k$).*

### 2.3. Hàm Mục tiêu Toàn cục (Objective Function)
Mục tiêu là tìm kiếm chiến lược $\mathbf{X}^* \in \Omega$ sao cho tổng thời gian chặng đua $J(\mathbf{X})$ đạt giá trị nhỏ nhất:
$$\min_{\mathbf{X} \in \Omega} J(\mathbf{X}) = \sum_{k=1}^{K+1} \sum_{a=1}^{l_k} t_{\text{lap}}(c_k, a, i(k, a)) + K \cdot T_{\text{pit}} + \Phi_{\text{FIA}}(\mathbf{X}) + \Phi_{\text{cliff}}(\mathbf{X})$$

Trong đó:
* $t_{\text{lap}}(c, a, i)$: Thời gian hoàn thành vòng đua thứ $i$ trên lốp $c$ ở tuổi thọ $a$.
* $K \cdot T_{\text{pit}}$: Tổng tổn thất thời gian di chuyển qua làn pit ($K \times 23.2\text{ s}$), với $K$ là số lần dừng pit ($K \in \{1, 2, 3\}$), $T_{\text{pit}}$ là thời gian tổn thất qua làn pit ($23.2\text{ s}$ tại Monza).
* $\Phi_{\text{FIA}}(\mathbf{X})$: Hàm phạt đối với trường hợp vi phạm quy định hợp chất lốp của FIA:
  $$\Phi_{\text{FIA}}(\mathbf{X}) = \begin{cases} 0 & \text{nếu } |\{c_k\}| \ge 2 \\ 100,000\text{ giây} & \text{nếu chỉ dùng duy nhất 1 loại lốp} \end{cases}$$
* $\Phi_{\text{cliff}}(\mathbf{X})$: Hàm phạt đối với các stint vượt quá tuổi thọ an toàn của lốp:
  $$\Phi_{\text{cliff}}(\mathbf{X}) = 50.0 \times \sum_{k=1}^{K+1} \max\big(0, l_k - L_{\max}(c_k)\big)$$

---

## 3. ĐẦU VÀO KỸ THUẬT TIẾP NHẬN TỪ THÀNH VIÊN 3 (TYRE MODELER)

Thuật toán tối ưu hóa tiếp nhận các thông số và đạo hàm giải tích từ mô hình mòn lốp do Thành viên 3 xây dựng:

### 3.1. Phương trình Suy giảm Lốp Giải tích Bậc hai Pirelli (WLS Regression)
Thời gian vòng đua thứ $i$ được phân rã thành 4 thành phần giải tích:
$$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) + \big[ d_1(c) a + d_2(c) a^2 \big] + \alpha_{\text{fuel}} (N - i) - \gamma_{\text{track}} i$$

*(Chú thích tham số: $c$ là loại hợp chất lốp; $a$ là số vòng lốp đã lăn bánh liên tục ($a \in [1, l_k]$); $i$ là số thứ tự vòng đua hiện tại ($i \in [1, N]$); $t_{\text{base}}(c)$ là thời gian cơ sở của lốp $c$; $d_1(c)$ là hệ số suy giảm tuyến tính; $d_2(c)$ là hệ số suy giảm phi tuyến bậc hai; $\alpha_{\text{fuel}} = 0.058\text{ s/vòng}$ là hệ số độ trễ do tải trọng nhiên liệu; $N = 53$ là tổng số vòng; $\gamma_{\text{track}} = 0.022\text{ s/vòng}$ là hệ số bám cao su mặt đường).*

* Ý nghĩa vật lý:
  - $d_1(c) a$: Mài mòn cơ học tự nhiên bề mặt (*Graining*). Do sự cọ xát với mặt đường, các hạt cao su nhỏ bong tróc làm giảm diện tích tiếp xúc, dẫn tới suy giảm độ bám theo từng vòng.
  - $d_2(c) a^2$: Suy thoái nhiệt bên trong kết cấu lốp (*Blistering* và *Tyre Cliff*). Khi xe vận hành ở cường độ cao, nhiệt sinh ra do biến dạng trễ đàn hồi nhớt ($Q_{\text{gen}} = \pi f E'' \epsilon^2$) tích tụ bên trong khung lốp, gây phồng rộp và làm độ bám suy giảm nhanh sau một ngưỡng tuổi thọ nhất định.

**Bảng tham số hiệu chuẩn tại Monza (53 vòng, $T_{\text{pit}} = 23.2\text{ s}$):**  
*(Nguồn: Dữ liệu viễn trắc FastF1 chặng Italian GP 2023, ước lượng bằng hồi quy Weighted Least Squares bởi Thành viên 3 kết hợp tài liệu kỹ thuật Pirelli Motorsport)*
| Hợp chất lốp ($c$) | Thời gian cơ sở $t_{\text{base}}$ | Hệ số $d_1$ (s/vòng) | Hệ số $d_2$ (s/vòng$^2$) | Tuổi thọ an toàn $L_{\max}$ |
| :--- | :---: | :---: | :---: | :---: |
| **Soft (C4)** | $81.50\text{ s}$ | $0.120$ | $0.0050$ | $22\text{ vòng}$ |
| **Medium (C3)** | $82.20\text{ s}$ | $0.070$ | $0.0020$ | $35\text{ vòng}$ |
| **Hard (C2)** | $83.00\text{ s}$ | $0.040$ | $0.0010$ | $48\text{ vòng}$ |

### 3.2. Đạo hàm Tốc độ Mài mòn Biên Giải tích ($\nabla t_{\text{deg}}$)
Hàm suy giảm lốp có đạo hàm cấp 1 và cấp 2 giải tích:
$$\nabla t_{\text{deg}}(a) = \frac{\partial t_{\text{deg}}}{\partial a} = d_1(c) + 2 d_2(c) a$$
$$\nabla^2 t_{\text{deg}}(a) = 2 d_2(c) > 0 \quad (\text{Hàm lồi ngặt - Strictly Convex})$$
* **Ứng dụng trong thuật toán:** Đạo hàm này cung cấp hướng dốc giải tích cho Toán tử Sửa chữa (Physics-Guided Repair Operator), giúp thuật toán xác định stint có tốc độ suy giảm cao nhất để giảm bớt vòng, và stint còn khoảng cách an toàn lớn nhất để bù thêm vòng.

### 3.3. Công thức Tổng Đóng Faulhaber $O(1)$
Thay vì tính toán thông qua vòng lặp $\sum_{a=1}^L (d_1 a + d_2 a^2)$ với độ phức tạp $O(L)$, công thức tổng đóng Faulhaber giải tích:
$$D_{\text{stint}}(c, L) = \sum_{a=1}^L \big( d_1 a + d_2 a^2 \big) = d_1 \frac{L(L+1)}{2} + d_2 \frac{L(L+1)(2L+1)}{6}$$
* **Ứng dụng trong thuật toán:** Chuyển đổi việc tính tổng thời gian suy giảm của một stint thành công thức giải tích $O(1)$, giảm thời gian đánh giá hàm thích nghi (fitness evaluation), hỗ trợ thuật toán thực hiện tìm kiếm qua nhiều thế hệ một cách hiệu quả.

---

## 4. CƠ SỞ THIẾT KẾ VÀ CÁC CƠ CHẾ CỦA GIẢI THUẬT AGA

Giải thuật Di truyền Thích nghi (Adaptive Genetic Algorithm - AGA) được cấu thành bởi các cơ chế sau:

```
[Quần thể ban đầu P=60]
       │
       ▼
(1) Khởi tạo Trọng số có Định hướng (65% 1-stop, 30% 2-stop, 5% 3-stop)
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
    └─ Macro (15%): Split / Merge Stint (Điều chỉnh số lần pit K)
       │
       ▼
(4) Lịch Làm Mát Phi Tuyến & Cơ Chế Đột Biến Hỗn Loạn (Chaos Injection)
       │
       ▼
(5) Cơ chế Tái Tối Ưu Thời Gian Thực Khi Có Xe An Toàn (Warm-Start Pivot)
```

---

### Cơ chế 1: Khởi tạo Quần thể có Định hướng (Heuristic Initialization)
* **Vấn đề khi khởi tạo ngẫu nhiên đều:** Phần lớn các cá thể sinh ra ngẫu nhiên vi phạm quy định FIA hoặc có số lần dừng pit không hợp lý, làm tăng số thế hệ cần thiết để hội tụ.
* **Giải pháp:** Dựa trên dữ liệu thực tế của các chặng đua, quần thể ban đầu được phân bổ trọng số:
  * **$65\%$ cá thể 1-stop** ($K = 1$).
  * **$30\%$ cá thể 2-stop** ($K = 2$).
  * **$5\%$ cá thể 3-stop** ($K = 3$).
* Toàn bộ các cá thể được gán sẵn các cặp hợp chất thỏa mãn quy định FIA ($|\{c_k\}| \ge 2$).

---

### Cơ chế 2: Toán tử Sửa chữa Định hướng Vật lý (Physics-Guided Repair Operator)
* **Vấn đề:** Sau phép lai ghép hoặc đột biến, độ dài tổng các stint có thể không khớp với tổng số vòng quy định ($\sum l_k \ne 53$). Nếu sử dụng hàm phạt loại bỏ hoàn toàn (Death Penalty), tính đa dạng di truyền của quần thể sẽ giảm nhanh.
* **Giải pháp:** Thiết kế toán tử sửa chữa định hướng vật lý nhằm điều chỉnh số vòng:
  1. Tính độ lệch: $\Delta N = 53 - \sum_{k=1}^{K+1} l_k$.
  2. **Nếu thiếu vòng ($\Delta N > 0$):** Dựa vào đạo hàm $\nabla t_{\text{deg}}$, thuật toán tìm stint có khoảng cách an toàn tới giới hạn mòn lốp lớn nhất $\big(L_{\max}(c_k) - l_k\big)$ để bổ sung thêm vòng.
  3. **Nếu thừa vòng ($\Delta N < 0$):** Khấu trừ vòng từ stint có tốc độ suy giảm lớn nhất ($\nabla t_{\text{deg}}$ cao nhất) hoặc stint dài nhất, bảo đảm điều kiện $l_k \ge 4$.
  4. **Kiểm tra luật FIA:** Nếu cá thể bị trùng lặp lốp ($|\{c_k\}| = 1$), tự động chuyển đổi hợp chất của stint ngắn nhất sang loại lốp hợp lệ khác.
* **Kết quả:** Đưa các cá thể về không gian nghiệm hợp lệ $\Omega$.
* **Lưu ý đánh giá:** Cơ chế sửa chữa này hiện tại được cài đặt theo các quy tắc logic điều kiện (thuần if-else) dựa trên đạo hàm mòn biên. Phương pháp này đã giải quyết tốt việc bảo toàn tính khả thi của cá thể, tuy nhiên mới chỉ tối ưu hóa được một phần và chưa phải là phép chiếu tối ưu toán học tuyệt đối, còn tiềm năng phát triển sâu hơn trong tương lai.

---

### Cơ chế 3: Đột biến Đa hình thái 3 Cấp độ với Split / Merge Stint
* **Vấn đề:** Số lần dừng pit $K$ là biến nguyên rời rạc ($K \in \{1, 2, 3\}$). Nếu cố định chiều dài nhiễm sắc thể, thuật toán khó đánh giá so sánh giữa các chiến lược có số lần dừng pit khác nhau.
* **Giải pháp:** Thiết kế nhiễm sắc thể biến thiên chiều dài và đột biến 3 cấp độ:
  1. **Micro-mutation ($60\%$):** Tinh chỉnh vi mô mốc pit giữa 2 stint liền kề:
     $$l_k \leftarrow l_k \pm 1, \quad l_{k+1} \leftarrow l_{k+1} \mp 1$$
     Bảo toàn chính xác $\sum l_k = 53$, hỗ trợ khai thác cục bộ (*Exploitation*).
  2. **Meso-mutation ($25\%$):** Thay đổi hợp chất lốp của một stint, giữ nguyên độ dài stint và bảo toàn quy định FIA.
  3. **Macro-mutation ($15\%$) – Biến thiên Cấu trúc (Split & Merge):**
     * **Phân tách stint (Split Stint - $K \to K+1$):**
       - Chọn stint dài ($l_k \ge 8$), phân tách thành 2 stint với loại lốp khác nhau: $(c_k, l_{\text{part1}})$ và $(c_{\text{new}}, l_k - l_{\text{part1}})$.
       - *Ý nghĩa:* Hạn chế việc xe chạy quá giới hạn suy giảm của lốp (*Tyre Cliff*).
     * **Hợp nhất stint (Merge Stint - $K \to K-1$):**
       - Gộp 2 stint ngắn liền kề thành 1 stint duy nhất: $l_{\text{merged}} = l_k + l_{k+1}$, đồng thời gán loại lốp phù hợp với độ bền cơ học.
       - *Ý nghĩa:* Giảm bớt thời gian tổn thất qua làn pit ($23.2\text{ s}$).
     * $\rightarrow$ Cơ chế này hỗ trợ thuật toán tự điều chỉnh số lần dừng pit $K$ trong quá trình tìm kiếm mà không cần cố định trước giá trị $K$.

---

### Cơ chế 4: Lịch Làm Mát Phi Tuyến & Cơ Chế Đột Biến Hỗn Loạn (Chaos Injection)
* Xác suất lai ghép $P_c(g)$ và đột biến $P_m(g)$ thích nghi phi tuyến theo thế hệ $g \in [1, G_{\max}]$:
  $$P_c(g) = P_{c,\min} + (P_{c,0} - P_{c,\min}) \times \left[ 1 - \left(\frac{g}{G_{\max}}\right)^{1.5} \right]$$
  $$P_m(g) = P_{m,\min} + (P_{m,0} - P_{m,\min}) \times \left[ 1 - \left(\frac{g}{G_{\max}}\right)^{1.2} \right]$$
  *(Chú thích: $g$ là số thứ tự thế hệ hiện tại; $G_{\max}$ là tổng số thế hệ; $P_{c,0}, P_{c,\min}$ là xác suất lai ghép khởi đầu và giá trị nhỏ nhất; $P_{m,0}, P_{m,\min}$ là xác suất đột biến khởi đầu và giá trị nhỏ nhất).*
* **Hỗ trợ thoát cực tiểu địa phương (Chaos Injection):**  
  Thuật toán theo dõi độ đa dạng quần thể $\bar{D}_{\text{pop}}$ (khoảng cách sai khác trung bình giữa các cá thể). Nếu $\bar{D}_{\text{pop}} < 0.15$ (dấu hiệu quần thể bị suy giảm độ đa dạng và hội tụ sớm về cực tiểu địa phương), thuật toán kích hoạt:
  $$P_m \leftarrow P_m \times 2.5 \quad \text{trong 3 thế hệ liên tiếp}$$
  Gia tăng cường độ đột biến trên diện rộng nhằm hỗ trợ quần thể thoát khỏi vùng hấp dẫn của cực tiểu địa phương và mở rộng không gian tìm kiếm.

---

## 5. CƠ CHẾ TÁI TỐI ƯU THỜI GIAN THỰC KHI CÓ XE AN TOÀN (WARM-START PIVOT)

### 5.1. Bối cảnh Biến động Tổn thất Thời gian Pit khi có Xe An Toàn
Khi có sự cố trên đường đua tại vòng thứ $L_{\text{SC}}$, Xe An Toàn (Safety Car) xuất hiện:
* Tốc độ ngoài đường đua giảm khoảng $40\%$ (thời gian vòng tăng từ $\approx 82\text{ s} \to \approx 120\text{ s}$).
* Tốc độ trong làn pit vẫn giữ nguyên ở mức giới hạn $80\text{ km/h}$.
* $\rightarrow$ Tổn thất thời gian tương đối của làn pit ($T_{\text{pit}}$) giảm từ $23.2\text{ giây} \to 12.5\text{ giây}$.
* Việc vào pit tại thời điểm này giảm bớt tổn thất thời gian tương đối so với điều kiện thi đấu thông thường.
* Cửa sổ thời gian ra quyết định diễn ra trong khoảng $3 - 5\text{ giây}$ trước lối vào làn pit.
* **Giới hạn nghiên cứu (Limitation):** Mô hình hiện tại chưa xét đến vị trí hình học của xe trên đường đua tại thời điểm xuất hiện cờ Xe An Toàn (ví dụ: xe đang ở gần lối vào làn pit hay vừa đi qua lối vào pit và phải chạy thêm một vòng với tốc độ chậm trước khi được vào pit).

### 5.2. Thuật toán Tái Tối Ưu Warm-Start Pivot
Để đáp ứng yêu cầu thời gian thực, cơ chế Warm-Start Pivot thực hiện:
1. **Cố định quá khứ:** Giữ nguyên các vòng đã đua $[1, L_{\text{SC}}]$.
2. **Kế thừa nghiệm:** Sử dụng cá thể tốt nhất hiện tại làm nghiệm khởi đầu thay vì tạo ngẫu nhiên từ đầu.
3. **Cập nhật tham số:** Gán $T_{\text{pit}} \leftarrow 12.5\text{ s}$, số vòng còn lại cần tối ưu là $N_{\text{remain}} = N - L_{\text{SC}}$.
4. **Tái hội tụ:** Tối ưu hóa các vòng còn lại với số thế hệ rút gọn ($G_{\text{warm}} = 15$).  
*(Chú thích ký hiệu: $L_{\text{SC}}$ là vòng đua xảy ra sự cố Xe An Toàn; $N_{\text{remain}}$ là số vòng còn lại; $G_{\text{warm}}$ là số thế hệ tái tối ưu).*
* **Thời gian tính toán thực nghiệm:** **$8.6 - 15.4\text{ mili-giây}$** (trung bình $\approx 11.8 - 15.8\text{ ms}$, đáp ứng yêu cầu thời gian thực $< 200\text{ ms}$ và nhanh hơn đáng kể so với việc giải lại toàn bộ bài toán bằng Bellman DP mất khoảng $200 - 335\text{ ms}$).

---

## 6. KẾT QUẢ THỰC NGHIỆM & ĐỐI CHUẨN KHOA HỌC

Toàn bộ kết quả dưới đây được ghi nhận từ hệ thống mã nguồn thực thi và kiểm chứng qua 48 trường hợp kiểm thử tự động:

### 6.1. Bảng Đối chuẩn 4 Thuật toán trên Chặng Monza (53 vòng)
| Thuật toán | Phân loại phương pháp | Thời gian chặng ($T_{\text{race}}$) | Sai số tối ưu (Gap) | Thời gian tính ban đầu | Thời gian phản ứng khi có SC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Bellman DP Solver** (TV4) | Quy hoạch động chính xác (Ground Truth) | **$4497.997\text{ s}$** | **$0.0000\%$** (Mốc chuẩn) | $188 - 289\text{ ms}$ | $178 - 293\text{ ms}$ *(Giải lại toàn bộ)* |
| **Greedy Baseline** (TV5) | Tham lam theo quy tắc (Rule-based) | $4538.210\text{ s}$ | $+0.8940\%$ ($+40.2\text{ s}$) | $< 1\text{ ms}$ | $< 1\text{ ms}$ *(Quy tắc tĩnh, không đổi)* |
| **Standard GA** (Holland 1975) | Di truyền cổ điển (Fixed $P_c, P_m$) | $4512.450\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | $77 - 151\text{ ms}$ | $77 - 151\text{ ms}$ *(Chạy lại từ đầu)* |
| **Adaptive GA (Đề xuất)** | Di truyền thích nghi (Repair + Warm-Start) | **$4497.997\text{ s}$** | **$0.0000\%$** | $292 - 507\text{ ms}$ | **$7.8 - 26.7\text{ ms}$** *(Warm-Start Pivot)* |

* **Đánh giá hiệu năng phản ứng khi có Xe An Toàn (Safety Car):**
  * **Yêu cầu thời gian thực:** Cửa sổ ra quyết định chiến thuật tại Pit-wall đòi hỏi thuật toán phản hồi trong khoảng dưới $200\text{ ms}$ ($0.20\text{ s}$) trước khi xe đi qua lối vào làn pit.
  * **Tốc độ tái tối ưu:** Nhờ kế thừa nghiệm tốt nhất hiện tại và tái tối ưu rút gọn trong 15 thế hệ, cơ chế Warm-Start Pivot của Adaptive GA đạt thời gian phản hồi từ $7.8 - 26.7\text{ ms}$ (trung bình $\approx 14.3\text{ ms}$), đáp ứng tốt yêu cầu thời gian thực và nhanh hơn đáng kể so với phương pháp giải lại toàn bộ bằng Bellman DP ($178 - 293\text{ ms}$).
  * **Hiệu quả chiến thuật:** Trong các kịch bản thử nghiệm, việc tái tối ưu chiến lược tại thời điểm xuất hiện Xe An Toàn cho phép tận dụng mức suy giảm tổn thất qua làn pit ($T_{\text{pit}}$ giảm từ $23.2\text{ s} \to 12.5\text{ s}$), ghi nhận mức giảm khoảng $4.8\text{ s} - 10.4\text{ s}$ tổng thời gian hoàn thành chặng đua so với phương án duy trì kế hoạch ban đầu.

### 6.2. Kiểm định Ý nghĩa Thống kê (Wilcoxon Signed-Rank Test)
* Thử nghiệm trên **30 random seeds độc lập** (seeds 1 đến 30).
* Kết quả kiểm định phi tham số Wilcoxon giữa Proposed AGA và Standard GA:
  $$p\text{-value} = 3.59 \times 10^{-7} < 0.001$$
* Kết quả kiểm định cho thấy sự khác biệt về kết quả giữa AGA và Standard GA có ý nghĩa thống kê ở mức ý nghĩa $\alpha = 0.05$ (bác bỏ giả thuyết $H_0$).

### 6.3. Chiến lược Tối ưu Thu được
* **Chiến lược:** 2-stop:
  $$\big[ \text{Medium: } 20\text{ vòng} \;\longrightarrow\; \text{Soft: } 14\text{ vòng} \;\longrightarrow\; \text{Medium: } 19\text{ vòng} \big]$$
* **Tổng thời gian chặng:** $4497.997\text{ giây}$ (1 giờ 14 phút 57.997 giây).

---

## 7. Q&A VỚI THẦY

### Câu hỏi 1: "Tại sao không dùng Gradient Descent (đạo hàm giảm) giải cho nhanh mà lại dùng GA?"
> **Trả lời:** "Thưa Thầy, hàm mục tiêu thời gian đua trong F1 là hàm **phi tuyến nguyên hỗn hợp và không liên tục**.  
> Thứ nhất, số lần dừng pit $K$ và loại lốp $c$ là các biến rời rạc, không có đạo hàm liên tục.  
> Thứ hai, chi phí làn pit $T_{\text{pit}} = 23.2\text{ s}$ tạo ra các bước nhảy thời gian gián đoạn, hình thành bề mặt tối ưu có nhiều cực tiểu địa phương. Gradient Descent thuần túy sẽ dễ bị kẹt tại điểm xuất phát hoặc cực tiểu cục bộ gần nhất.  
> Do đó, bài toán phù hợp hơn với các phương pháp metaheuristic như GA hoặc quy hoạch động."

### Câu hỏi 2: "Tại sao nhóm lại dùng Toán tử Sửa chữa (Repair) mà không dùng Hàm Phạt (Penalty Function) thông thường?"
> **Trả lời:** "Thưa Thầy, không gian nghiệm của bài toán F1 bị giới hạn bởi các ràng buộc khắt khe: $\sum l_k = 53$ và $|\{c_k\}| \ge 2$.  
> Nếu chỉ dùng hàm phạt (đặc biệt là Death Penalty), phần lớn các cá thể sinh ra từ lai ghép và đột biến sẽ bị loại bỏ, làm giảm tính đa dạng di truyền của quần thể và khiến GA dễ hội tụ sớm.  
> Toán tử Sửa chữa dựa trên **đạo hàm mài mòn biên $\nabla t_{\text{deg}}$** hỗ trợ đưa các cá thể vi phạm trở lại miền khả thi, bảo toàn thông tin tìm kiếm của các thế hệ trước và bảo đảm tính khả thi cho quần thể."

### Câu hỏi 3: "Nếu Bellman DP đã tìm ra nghiệm tối ưu toàn cục rồi, tại sao đề tài của em còn cần giải thuật GA?"
> **Trả lời:** "Thưa Thầy, Bellman DP cung cấp **nghiệm tối ưu toàn cục làm mốc đối chuẩn (Ground Truth)** tin cậy trong bài toán tĩnh đơn mục tiêu cho 1 xe chạy đơn độc trong điều kiện đường thông thoáng (Free air), với $30,088$ trạng thái.  
> Tuy nhiên, khi bài toán mở rộng sang môi trường thực tế (đua đối kháng nhiều xe, tránh luồng khí bẩn Dirty Air, hoặc tối ưu hóa đa mục tiêu thời gian và rủi ro), không gian trạng thái của quy hoạch động sẽ tăng theo cấp số nhân (Curse of Dimensionality).  
> Khi đó, giải thuật tiến hóa AGA với độ phức tạp đa thức và khả năng tái tối ưu nhanh (khoảng $0.18\text{ s}$ cho chặng đua và khoảng $5.2\text{ ms}$ với Warm-Start) là một hướng tiếp cận phù hợp để đáp ứng yêu cầu tính toán thời gian thực."
