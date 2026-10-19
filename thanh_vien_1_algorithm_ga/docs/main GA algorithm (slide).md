# NỘI DUNG SLIDE THUYẾT TRÌNH – PHẦN THUẬT TOÁN TIẾN HÓA (AGA)
**Tệp:** `main GA algorithm (slide).md`  
**Dành cho:** Người thiết kế Slide  
**Định dạng:** Visual-First (Tối giản chữ, sử dụng thuật ngữ chính quy, khiêm tốn, nhấn mạnh số liệu và vị trí chèn sơ đồ).

---

## SLIDE 1: MÃ HÓA NHIỄM SẮC THỂ & TOÁN TỬ SỬA CHỮA ĐỊNH HƯỚNG VẬT LÝ

### 1. Thông điệp cốt lõi
Mã hóa mảng stint biến thiên và bảo đảm tính khả thi của cá thể nhờ đạo hàm suy giảm biên $\nabla t_{\text{deg}}$.

### 2. Nội dung hiển thị (Cột văn bản)
* **Mã hóa Nhiễm sắc thể (Chromosome):**
  $$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
  * $K \in \{1, 2, 3\}$: Số lần dừng pit (chiều dài mảng thay đổi).
  * $c_k \in \{\text{Soft, Medium, Hard}\}$: Hợp chất lốp.
  * $l_k \ge 4$: Độ dài stint (số vòng chạy liên tục).

* **Khởi tạo Quần thể có Định hướng:**
  * Phân bổ: $65\%$ 1-stop | $30\%$ 2-stop | $5\%$ 3-stop (Thỏa mãn quy chuẩn FIA).

* **Toán tử Sửa chữa Vật lý (Physics-Guided Repair):**
  * Hướng dốc giải tích: $\nabla t_{\text{deg}}(a) = d_1 + 2d_2 a$.
  * **Thiếu vòng ($\sum l_k < 53$):** Bù vào stint có khoảng cách an toàn lớn nhất ($L_{\max} - l_k$).
  * **Thừa vòng ($\sum l_k > 53$):** Giảm bớt ở stint có tốc độ suy giảm $\nabla t_{\text{deg}}$ cao nhất.

### 3. Khung Chỉ số KPI (Stat Cards)
* `Tỷ lệ nghiệm khả thi: 100%` (Không cần loại bỏ cá thể)
* `Bảo toàn số vòng:` $\sum l_k = 53$

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 1: figures/diagram_chromosome_and_repair.png]`  
*(Mô tả sơ đồ: Nửa trên vẽ mảng nhiễm sắc thể gồm các khối màu đại diện cho Soft/Medium/Hard; Nửa dưới vẽ lưu đồ: Cá thể lệch vòng $\to$ Tính đạo hàm $\nabla t_{\text{deg}} \to$ Điều chỉnh độ dài stint $\to$ Đạt chuẩn 53 vòng).*

---

## SLIDE 2: ĐỘT BIẾN ĐA HÌNH THÁI 3 CẤP ĐỘ & CƠ CHẾ CHAOS INJECTION

### 1. Thông điệp cốt lõi
Toán tử Split/Merge hỗ trợ tìm kiếm số lần pit $K$ phù hợp; cơ chế Chaos Injection hỗ trợ thoát khỏi cực tiểu địa phương.

### 2. Nội dung hiển thị (Cột văn bản)
* **Đột biến Đa hình thái 3 Cấp độ:**
  * **Micro ($60\%$):** Tinh chỉnh vi mô $\pm 1$ vòng giữa 2 stint liền kề (Khai thác cục bộ).
  * **Meso ($25\%$):** Thay đổi hợp chất lốp (Bảo toàn quy chuẩn FIA).
  * **Macro ($15\%$) – Biến thiên Cấu trúc:**
    * **Split Stint ($K \to K+1$):** Phân tách stint dài $\to$ Hạn chế suy thoái lốp quá mức (*Tyre Cliff*).
    * **Merge Stint ($K \to K-1$):** Hợp nhất 2 stint ngắn $\to$ Giảm $23.2\text{ s}$ tổn thất thời gian làn pit.

* **Cơ chế Đột biến Hỗn loạn (Chaos Injection):**
  * Lịch làm mát thích nghi $P_c(g), P_m(g)$ giảm dần theo thế hệ.
  * Giám sát độ đa dạng quần thể $\bar{D}_{\text{pop}}$:
    $$\bar{D}_{\text{pop}} < 0.15 \;\Longrightarrow\; P_m \leftarrow P_m \times 2.5 \quad \text{(trong 3 thế hệ)}$$

### 3. Khung Chỉ số KPI (Stat Cards)
* `Linh hoạt số lần pit:` $K \in \{1, 2, 3\}$
* `Hỗ trợ duy trì độ đa dạng di truyền`

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 2: figures/diagram_split_merge_mutation.png]`  
*(Mô tả sơ đồ: Hai minh họa dạng thanh: (1) Một stint dài được phân tách thành hai stint [Split: $K \to K+1$]; (2) Hai stint ngắn được hợp nhất thành một stint [Merge: $K \to K-1$]).*

---

## SLIDE 3: TÁI TỐI ƯU THỜI GIAN THỰC KHI CÓ XE AN TOÀN (WARM-START PIVOT)

### 1. Thông điệp cốt lõi
Cơ chế Warm-Start Pivot tái tối ưu chiến lược trong $5.2\text{ ms}$, phù hợp với cửa sổ thời gian ra quyết định tại Pit-wall.

### 2. Nội dung hiển thị (Cột văn bản)
* **Bối cảnh Xe An Toàn (Safety Car – SC):**
  * Tốc độ ngoài đường đua giảm $40\%$, tốc độ trong làn pit giữ nguyên $80\text{ km/h}$.
  * Tổn thất thời gian qua làn pit giảm: **$23.2\text{ s} \longrightarrow 12.5\text{ s}$** (*Free Pit Stop*).
  * Cửa sổ thời gian ra quyết định: Khoảng **$3 - 5\text{ giây}$** trước lối vào làn pit.

* **Quy trình Tái Tối Ưu Rút Gọn (Warm-Start):**
  1. **Cố định quá khứ:** Giữ nguyên các vòng đã đua $[1, L_{\text{SC}}]$.
  2. **Kế thừa nghiệm:** Sử dụng cá thể tốt nhất hiện tại làm nghiệm khởi đầu.
  3. **Tái hội tụ:** Tối ưu hóa các vòng còn lại ($53 - L_{\text{SC}}$) với $G = 15$ thế hệ.

### 3. Khung Chỉ số KPI (Stat Cards)
* `Thời gian tính toán: 5.2 ms` (So với giải lại bằng Bellman DP: ~85 ms)
* `Chênh lệch thời gian ước tính: ~10.7 s` (So với vào pit ở điều kiện cờ xanh)

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 3: figures/diagram_safety_car_warm_start.png]`  
*(Mô tả sơ đồ: Trục thời gian 53 vòng đua: Vòng 1 đến 20 được đánh dấu "Cố định"; Vạch cờ vàng SC tại vòng 20; Mũi tên "Warm-Start Pivot (5.2 ms)" định hướng cho các vòng còn lại).*

---

## SLIDE 4: ĐỐI CHUẨN THỰC NGHIỆM & KIỂM TRA ĐỘ TIN CẬY

### 1. Thông điệp cốt lõi
Thuật toán AGA đạt kết quả tiệm cận nghiệm tối ưu Bellman DP, có ý nghĩa thống kê ($p < 0.001$) và được kiểm thử qua 48 trường hợp thử nghiệm.

### 2. Bảng Đối chuẩn Thực nghiệm (Monza GP – 53 vòng)
| Thuật toán | Thời gian tốt nhất | Sai số tối ưu (Gap) | Runtime |
| :--- | :---: | :---: | :---: |
| **Bellman DP (Ground Truth)** | **$4497.997\text{ s}$** | **$0.0000\%$** (Mốc chuẩn) | $0.086\text{ s}$ |
| **Standard GA (Holland 1975)** | $4512.450\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | $0.412\text{ s}$ |
| **Adaptive GA (Đề xuất)** | **$4497.997\text{ s}$** | **$0.0000\%$** | **$0.185\text{ s}$** |

### 3. Khung Chỉ số KPI (Stat Cards)
* `Optimality Gap:` **$0.0000\%$** (Nghiệm tìm được: `[Med 20v -> Soft 14v -> Med 19v]`)
* `Kiểm định Wilcoxon (30 seeds):` **$p = 3.59 \times 10^{-7} < 0.001$** (Bác bỏ giả thuyết $H_0$)
* `Kiểm thử tự động:` Đạt **$48/48$** trường hợp thử nghiệm ($11.7\text{ s}$)

### 4. Vị trí chèn Hình ảnh / Biểu đồ Thực nghiệm
* `[CHÈN BIỂU ĐỒ 4A: paper/figures/seed_distribution_boxplot.png]`  
  *(Biểu đồ hộp Boxplot so sánh độ phân tán thời gian đua qua 30 random seeds giữa AGA và Standard GA).*
* `[CHÈN BIỂU ĐỒ 4B: paper/figures/convergence_comparison.png]`  
  *(Đồ thị đường cong hội tụ qua các thế hệ thể hiện ảnh hưởng của cơ chế Chaos Injection lên quá trình tìm kiếm).*
