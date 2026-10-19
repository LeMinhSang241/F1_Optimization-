# NỘI DUNG SLIDE THUYẾT TRÌNH – PHẦN THUẬT TOÁN TIẾN HÓA (AGA)
**Tệp:** `main GA algorithm (slide).md`  
**Dành cho:** Người thiết kế Slide  
**Định dạng:** Visual-First (Tối giản chữ, nhấn mạnh công thức, số liệu và vị trí chèn hình ảnh/biểu đồ).

---

## SLIDE 1: MÃ HÓA NHIỄM SẮC THỂ & TOÁN TỬ SỬA CHỮA ĐỊNH HƯỚNG VẬT LÝ

### 1. Thông điệp cốt lõi
Mã hóa mảng stint biến thiên và triệt tiêu $100\%$ nghiệm bất khả thi nhờ đạo hàm suy giảm biên $\nabla t_{\text{deg}}$.

### 2. Nội dung hiển thị (Cột văn bản)
* **Mã hóa Nhiễm sắc thể (Chromosome):**
  $$\mathbf{X} = \langle K, \mathbf{S} \rangle, \quad \mathbf{S} = \big[ (c_1, l_1), (c_2, l_2), \dots, (c_{K+1}, l_{K+1}) \big]$$
  * $K \in \{1, 2, 3\}$: Số lần pit (chiều dài mảng thay đổi).
  * $c_k \in \{\text{Soft, Medium, Hard}\}$: Hợp chất lốp.
  * $l_k \ge 4$: Độ dài stint (số vòng chạy liên tục).

* **Khởi tạo Quần thể Tri thức:**
  * $65\%$ 1-stop | $30\%$ 2-stop | $5\%$ 3-stop (Thỏa ngay luật FIA).

* **Toán tử Sửa chữa Vật lý (Physics-Guided Repair):**
  * Sử dụng đạo hàm suy giảm biên: $\nabla t_{\text{deg}}(a) = d_1 + 2d_2 a$.
  * **Thiếu vòng ($\sum l_k < 53$):** Bù vào stint có dư địa an toàn lớn nhất ($L_{\max} - l_k$).
  * **Thừa vòng ($\sum l_k > 53$):** Cắt bớt ở stint có tốc độ mòn $\nabla t_{\text{deg}}$ cao nhất.

### 3. Khung Chỉ số KPI (Stat Cards)
* `100% Nghiệm khả thi` (Không loại bỏ cá thể)
* `Bảo toàn số vòng:` $\sum l_k = 53$

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 1: figures/diagram_chromosome_and_repair.png]`  
*(Mô tả sơ đồ cần tạo: Nửa trên vẽ mảng nhiễm sắc thể gồm các block màu Soft/Med/Hard; Nửa dưới vẽ lưu đồ: Cá thể lệch vòng $\to$ Tính đạo hàm $\nabla t_{\text{deg}} \to$ Bù/Trừ vòng $\to$ Đạt chuẩn 53 vòng).*

---

## SLIDE 2: ĐỘT BIẾN ĐA HÌNH THÁI 3 CẤP ĐỘ & TIÊM GEN HỖN LOẠN

### 1. Thông điệp cốt lõi
Toán tử Split/Merge giúp số lần pit $K$ tự tiến hóa tối ưu; cơ chế Chaos Injection phá vỡ bẫy cực tiểu địa phương.

### 2. Nội dung hiển thị (Cột văn bản)
* **Đột biến Đa hình thái 3 Cấp độ:**
  * **Micro ($60\%$):** Tinh chỉnh vi mô $\pm 1$ vòng giữa 2 stint liền kề (Khai thác sâu).
  * **Meso ($25\%$):** Hoán đổi ngẫu nhiên loại lốp (Bảo toàn luật FIA).
  * **Macro ($15\%$) – Biến thiên Cấu trúc:**
    * **Split Stint ($K \to K+1$):** Cắt đôi stint dài $\to$ Tránh sụp vách lốp (*Tyre Cliff*).
    * **Merge Stint ($K \to K-1$):** Gộp 2 stint ngắn $\to$ Tiết kiệm trọn vẹn **$23.2\text{ s}$** vào pit.

* **Tiêm Gen Hỗn loạn (Chaos Injection):**
  * Lịch làm mát phi tuyến $P_c(g), P_m(g)$ giảm dần theo thế hệ.
  * Giám sát độ đa dạng quần thể $\bar{D}_{\text{pop}}$:
    $$\bar{D}_{\text{pop}} < 0.15 \;\Longrightarrow\; P_m \leftarrow P_m \times 2.5 \quad \text{(trong 3 thế hệ)}$$

### 3. Khung Chỉ số KPI (Stat Cards)
* `Tự tiến hóa số lần pit:` $K \in \{1, 2, 3\}$
* `Phá bẫy cực tiểu:` Tăng cường độ biến dị cục bộ

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 2: figures/diagram_split_merge_mutation.png]`  
*(Mô tả sơ đồ cần tạo: Hai thanh stint trực quan: Thanh 1 dài bị kéo cắt đôi thành 2 stint có màu lốp khác nhau [Split: 1-stop $\to$ 2-stop]; Thanh 2 gồm hai đoạn ngắn ghép lại thành một thanh dài [Merge: 2-stop $\to$ 1-stop]).*

---

## SLIDE 3: TÁI TỐI ƯU XE AN TOÀN THỜI GIAN THỰC (WARM-START PIVOT)

### 1. Thông điệp cốt lõi
Cơ chế Warm-Start Pivot tái tối ưu chiến lược trong $5.2\text{ ms}$, đáp ứng tức thời cửa sổ quyết định $3\text{ s}$ tại Pit-wall.

### 2. Nội dung hiển thị (Cột văn bản)
* **Biến cố Xe An Toàn (Safety Car – SC):**
  * Tốc độ đường đua giảm $40\%$, tốc độ làn pit giữ nguyên $80\text{ km/h}$.
  * Tổn thất làn pit giảm đột ngột: **$23.2\text{ s} \longrightarrow 12.5\text{ s}$** (*Free Pit Stop*).
  * Cửa sổ ra quyết định khẩn cấp: **$3 - 5\text{ giây}$** trước lối vào pit.

* **Quy trình Tái Tối Ưu Thần Tốc:**
  1. **Đóng băng quá khứ:** Cố định toàn bộ các vòng đã đua $[1, L_{\text{SC}}]$.
  2. **Kế thừa hạt giống:** Lấy cá thể tối ưu hiện tại làm khởi điểm (Warm-start).
  3. **Tái hội tụ rút gọn:** Tối ưu các vòng còn lại ($53 - L_{\text{SC}}$) trong $G = 15$ thế hệ.

### 3. Khung Chỉ số KPI (Stat Cards)
* `Thời gian phản xạ: 5.2 ms` (Nhanh gấp 15 lần Bellman DP giải lại: $85\text{ ms}$)
* `Lợi thế thời gian: +10.7 s` (So với đối thủ vào pit ở cờ xanh)

### 4. Vị trí chèn Hình ảnh / Sơ đồ
`[CHÈN HÌNH 3: figures/diagram_safety_car_warm_start.png]`  
*(Mô tả sơ đồ cần tạo: Trục thời gian 53 vòng đua Monza: Vòng 1 đến 20 màu xám có nhãn "Đóng băng"; Vạch đỏ cờ vàng SC tại vòng 20; Mũi tên xanh "Warm-Start Pivot (5.2 ms)" trỏ đến vùng 33 vòng còn lại).*

---

## SLIDE 4: ĐỐI CHUẨN THỰC NGHIỆM & KIỂM ĐỊNH ĐỘ TIN CẬY

### 1. Thông điệp cốt lõi
Thuật toán AGA đạt Optimality Gap $0.0000\%$, vượt trội có ý nghĩa thống kê ($p < 0.001$) và vượt qua $48/48$ unit tests.

### 2. Bảng Đối chuẩn Thực nghiệm (Monza GP – 53 vòng)
| Thuật toán | Thời gian tốt nhất | Sai số tối ưu (Gap) | Runtime |
| :--- | :---: | :---: | :---: |
| **Bellman DP (Ground Truth)** | **$4497.997\text{ s}$** | **$0.0000\%$** (Mốc chuẩn) | $0.086\text{ s}$ |
| **Standard GA (Holland 1975)** | $4512.450\text{ s}$ | $+0.3213\%$ ($+14.5\text{ s}$) | $0.412\text{ s}$ |
| **Proposed Adaptive GA** | **$4497.997\text{ s}$** | **$0.0000\%$** (Chạm mốc) | **$0.185\text{ s}$** |

### 3. Khung Chỉ số KPI (Stat Cards)
* `Optimality Gap:` **$0.0000\%$** (Chiến lược tối ưu: `[Med 20v -> Soft 14v -> Med 19v]`)
* `Wilcoxon Test (30 seeds):` **$p = 3.59 \times 10^{-7} \ll 0.001$**
* `Kiểm thử tự động:` **$48/48$ Unit Tests PASSED $100\%$** ($11.7\text{ s}$)

### 4. Vị trí chèn Hình ảnh / Biểu đồ Thực nghiệm
* `[CHÈN BIỂU ĐỒ 4A: paper/figures/seed_distribution_boxplot.png]`  
  *(Biểu đồ hộp Boxplot so sánh độ phân tán thời gian đua qua 30 random seeds giữa AGA và Standard GA).*
* `[CHÈN BIỂU ĐỒ 4B: paper/figures/convergence_comparison.png]`  
  *(Đồ thị đường cong hội tụ qua các thế hệ thể hiện rõ tác động bứt phá của cơ chế Chaos Injection).*
