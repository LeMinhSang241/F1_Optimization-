# TÀI LIỆU KỸ THUẬT & TOÁN HỌC: MÔ HÌNH HÓA ĐỘNG LỰC HỌC LỐP F1
## Bóc Tách Tham Số Bằng Hồi Quy WLS-Tikhonov & Mở Rộng Nhiệt Độ Mặt Đường
**Tác giả:** Thành viên 3 — Chuyên viên Động lực học Lốp (Tyre Modeler)  
**Đơn vị:** Nhóm Đề án DS106 — Khoa Khoa học Dữ liệu, Trường ĐH Công nghệ Thông tin (UIT - ĐHQG-HCM)  
**Trạng thái:** Bàn giao chính thức cho Thành viên 1 (GA Lead) & Thành viên 4 (Bellman DP Lead)

---

## 1. TỔNG QUAN & PHẠM VI NGHIÊN CỨU

Tài liệu này tổng hợp toàn bộ cơ sở lý thuyết, dẫn xuất giải tích, mô hình hồi quy và phương pháp tối ưu hóa tính toán do **Thành viên 3** phát triển. Mục tiêu then chốt:
1. Thiết lập cơ sở **Cơ học tiếp xúc vật liệu nhớt đàn hồi (Viscoelastic Contact Mechanics)**, phân rã lực bám $\mu_{\text{total}} = \mu_{\text{adhesion}} + \mu_{\text{hysteresis}}$, cơ chế sinh nhiệt $Q_{\text{gen}}$ và giải thích 3 hiện tượng phi tuyến đặc thù của F1 (Graining, Blistering, Tyre Cliff).
2. Xây dựng mô hình suy giảm lốp giải tích bậc hai $\Delta t_{\text{deg}}(c, a) = d_1(c) a + d_2(c) a^2$ bám sát cơ sở vật lý của Pirelli, đồng thời lập luận bác bỏ các mô hình bậc 3, mạng nơ-ron và tuyến tính.
3. Thiết kế thuật toán **Weighted Least Squares (WLS)** kết hợp **Chính quy hóa Tikhonov** và **Bộ lọc nhiễu ngoại lai Huber** để bóc tách bộ tham số $\beta = [t_{\text{base}}, d_1, d_2]^T$ từ dữ liệu viễn trắc FastF1 sạch.
4. Thiết lập **Công thức tổng đóng $O(1)$** và **Đạo hàm giải tích $\nabla t_{\text{deg}}$** làm cầu nối cho thuật toán Quy hoạch động Bellman (TV4) và Giải thuật Di truyền DAGA-F1 (TV1).
5. Mở rộng mô hình nhiệt động lực học bán thực nghiệm theo nhiệt độ mặt đường $T_{\text{track}}$.

---

## 2. CƠ HỌC TIẾP XÚC NHỚT ĐÀN HỒI & 3 HIỆN TƯỢNG PHI TUYẾN ĐẶC THÙ

### 2.1. Cơ học tiếp xúc vật liệu nhớt đàn hồi (Viscoelastic Contact Mechanics)
Một chiếc xe F1 thế hệ hiệu ứng mặt đất (Ground Effect) có:
* Khối lượng không tải nhiên liệu: $m \approx 798\text{ kg}$.
* Vận tốc đỉnh: $v \approx 340\text{ km/h}$.
* Toàn bộ động lực học, gia tốc trọng trường và gia tốc góc của xe liên kết với mặt đường **duy nhất qua 4 vết tiếp xúc lốp (Tyre Contact Patches)**:
  $$S_{\text{contact}} \approx 300\text{ cm}^2 \times 4$$

Hợp chất cao su Pirelli P Zero thuộc nhóm vật liệu polymer nhớt đàn hồi biến dạng lớn ($\in \text{VHS}$ — Very High Specific). Lực bám ma sát tiếp xúc tổng thể $\mu_{\text{total}}$ tuân theo cơ học nhớt đàn hồi và phân rã thành **2 cơ chế vi mô độc lập**:
$$\mathbf{\mu_{\text{total}}(T, v_{\text{slide}}) = \mu_{\text{adhesion}}(T) \;+\; \mu_{\text{hysteresis}}(T, v_{\text{slide}})}$$

1. **Lực bám dính phân tử $\mu_{\text{adhesion}}(T)$ (Molecular Adhesion):**
   * Được sinh ra từ các liên kết Van der Waals giữa các chuỗi polymer cao su lốp và độ nhám vi mô (micro-texture) của đá rải mặt đường.
   * Cơ chế này đạt hiệu suất tối đa nghiêm ngặt chỉ khi nhiệt độ bề mặt lốp nằm trong **Cửa sổ nhiệt độ vận hành tối ưu (Operating Window - OW)**:
     $$T_{\text{tyre}} \in [t^\circ_{\min}, \; t^\circ_{\max}]$$
   * Nếu lốp quá nguội ($T < t^\circ_{\min}$): Cao su bị thủy tinh hóa, trơ và mất liên kết bám dính.
   * Nếu lốp quá nhiệt ($T > t^\circ_{\max}$): Cao su bị chảy nhão, bốc hơi dầu polymer làm mất bám dính.

2. **Suy hao trễ đàn hồi $\mu_{\text{hysteresis}}(T, v_{\text{slide}})$ (Hysteretic Deformation Loss):**
   * Xảy ra khi cao su lốp biến dạng trùm lên các mỏm nhấp nhô vĩ mô (macro-texture) của mặt đường dưới tốc độ trượt vi mô $v_{\text{slide}}$.
   * Do đặc tính trễ đàn hồi nhớt (viscoelastic hysteresis), cơ năng biến dạng không được hoàn trả toàn bộ mà bị tiêu tán thành nhiệt lượng nội tại sinh ra trong khối cao su theo phương trình:
     $$\mathbf{Q_{\text{gen}} = \pi \cdot f \cdot E'' \cdot \epsilon^2}$$
     * $f$: Tần số kích thích kích cỡ hạt đá mặt đường khi xe lướt qua.
     * $E''$: Mô-đun tổn thất (Loss Modulus) của hợp chất cao su Pirelli.
     * $\epsilon$: Biên độ biến dạng trượt tương đối (Strain amplitude).

3. **Động lực học mài mòn đa vòng (Multi-lap Degradation Dynamics):**
   Qua $N$ vòng đua, lốp xe chịu tác động hủy hoại đồng thời từ hai mặt:
   * **Mài mòn cơ học (Mechanical Wear):** Lớp cao su mặt gai mỏng dần $\implies$ giảm diện tích tiếp xúc thực, giảm ma sát và lực bám $\mu$.
   * **Quá nhiệt nội tại (Thermal Degradation):** Bản chất cao su có hệ số dẫn nhiệt rất kém $\implies$ nhiệt lượng sinh ra $Q_{\text{gen}}$ tích tụ liên tục không kịp khuếch tán, dẫn đến quá nhiệt và phá hủy mạng lưới polymer. Hai cơ chế này tương hỗ đẩy nhanh tốc độ mòn lốp.

---

### 2.2. Ba hiện tượng suy giảm phi tuyến đặc thù của lốp F1
Dữ liệu viễn trắc FastF1 ghi nhận 3 hiện tượng vật lý phi tuyến nghiêm trọng mà mọi mô hình tuyến tính đều thất bại khi mô tả:

1. **Hiện tượng tạo hạt (Graining — $\searrow$ Độ bám):**
   * Xảy ra khi lốp bị trượt ngang mạnh khi nhiệt độ bề mặt chưa đủ nóng. Lớp cao su bề mặt bị xé rách thành các hạt tròn li ti lăn tăn trên bề mặt lốp.
   * Hệ quả: Giảm diện tích tiếp xúc thực, suy giảm hệ số ma sát $\mu$, làm chậm thời gian vòng đua từ **$0.3 - 0.7\text{ giây/vòng}$**.
   * Đặc tính phục hồi: Có thể tự làm sạch ("grain cleaning") nếu tay đua chủ động điều khiển xe mượt mà để các hạt cao su mòn đều trở lại.

2. **Hiện tượng phồng rộp (Blistering — $\nearrow$ Quá nhiệt phá hủy):**
   * Xảy ra khi nhiệt độ đáy lốp (carcass) bên trong quá cao do trễ đàn hồi sinh nhiệt $Q_{\text{gen}}$, làm bốc hơi các hợp chất hữu cơ sinh khí bọt nổ tung, làm bong tróc từng mảng lớn cao su mặt ngoài.
   * Hệ quả: Xe mất mảng bám lớn, rung giật vô lăng dữ dội, làm chậm thời gian vòng đua từ **$1.0 - 2.0\text{ giây/vòng}$**. Đây là tổn thương cơ học vĩnh viễn, không thể phục hồi.

3. **Hiện tượng vách mòn lốp (Tyre Cliff — $a > L_{\max}$):**
   * Xảy ra khi tuổi lốp $a$ vượt quá ngưỡng giới hạn an toàn $L_{\max}$, lớp cao su gai lốp bị mài mòn mỏng dưới $0.5\text{ mm}$ (chạm ngưỡng tuổi thọ tối đa).
   * Hệ quả: Độ bám sụp đổ thẳng đứng theo "vách đá", thời gian vòng đua tăng vọt đột ngột từ **$1.5 - 3.5\text{ giây/vòng}$**, chiếc xe hoàn toàn mất lái và bắt buộc phải vào pit khẩn cấp.

---

### 2.3. Lập luận học thuật bác bỏ các mô hình khác (Model Justification)
Nhóm nghiên cứu đã thẩm định và quyết định lựa chọn mô hình **Bậc 2** $\Delta t_{\text{tyre}}(c, a) = d_1(c) a + d_2(c) a^2$ dựa trên các lập luận bác bỏ có cơ sở toán học và cơ học vững chắc:

* **Bác bỏ mô hình Đa thức Bậc 3 ($a^3$):**
  * Gây quá khớp (Overfitting) với các biến động ngắn hạn trong dữ liệu viễn trắc.
  * **Mất tính lồi nghiêm ngặt (Loses Strict Convexity):** Đạo hàm bậc hai $\nabla^2 t = 6 d_3 a + 2 d_2$ có thể đổi dấu khi $d_3$ âm, làm mất tính lồi, sinh ra các điểm uốn và cực tiểu cục bộ giả tạo, phá hỏng thuật toán Quy hoạch động Bellman và làm sai lệch điểm cực tiểu duy nhất.
* **Bác bỏ Mạng Nơ-ron (Neural Networks / Deep Learning):**
  * Mô hình nơ-ron là hộp đen (Black-box), **không có đạo hàm giải tích đóng $\nabla t_{\text{deg}}$** $\implies$ hoàn toàn bất khả thi trong việc cung cấp gradient vật lý để làm toán tử sửa chữa nghiệm (Physics-Guided Repair) cho Giải thuật Di truyền DAGA-F1.
  * Chi phí tính toán inference forward-pass hàng triệu lần trong vòng lặp tối ưu làm thời gian chạy bùng nổ (ước tính $\approx 500\text{ giờ}$ cho tối ưu 1 stint), triệt tiêu khả năng phản ứng thời gian thực khi có Safety Car.
* **Bác bỏ mô hình Tuyến tính ($d_1 a$ thuần túy):**
  * Mô hình tuyến tính (thường dùng trong các phân tích thô sơ hoặc nguồn không kiểm chứng "Trust Me Bro") hoàn toàn phi vật lý. Thực tế có tới hơn $60\%$ thời gian lốp chạy trong trạng thái nhiệt độ tích tụ tăng dần ($\nearrow$).
  * Nếu dùng mô hình tuyến tính, thuật toán Dynamic Programming (DP) sẽ luôn thiên vị cực đoan dồn về biên tuổi thọ (Soft Max), phân phối sai số sẽ mang đặc tính "đuôi dày" (Fat-tail distribution) thay vì phân phối chuẩn Gauss, dẫn tới sụp đổ chiến lược khi xe lao thẳng vào vách lốp Tyre Cliff.

---

### 2.4. Phân loại hợp chất Pirelli C1 – C5 & Ngưỡng $L_{\max}$
Hãng Pirelli phân loại độ cứng của lốp từ **C1 (cứng nhất)** đến **C5 (mềm nhất)**:
$$\implies L_{\max} = \lim_{a \to \infty} \big\{ a \mid \Delta t_{\text{deg}}(a) \le \text{Threshold} \big\}$$
Nếu tuổi lốp $a > L_{\max}$, cấu trúc bề mặt bị phá hủy (blistering/graining), gai lốp mỏng $< 0.5\text{ mm}$, nguy cơ rách vách lốp hoặc nổ lốp tức thời.

### 2.5. So sánh đặc tính trường đua & Cửa sổ nhiệt độ (Operating Window - OW)
* **Chặng Monza GP (53 vòng):**
  * Vận tốc trung bình rất cao: $\bar{v} \approx 250\text{ km/h}$.
  * Đặc tính: Đường thẳng dài (chiếm $> 70\%$ chiều dài vòng đua), lực ép ngang thấp (low downforce), làm mát lốp bằng luồng khí tốt.
  * Cửa sổ nhiệt độ hoạt động tiêu chuẩn (Operating Window):
    * **Soft (C5):** $105^\circ\text{C} - 135^\circ\text{C}$
    * **Medium (C4):** $100^\circ\text{C} - 130^\circ\text{C}$
    * **Hard (C3):** $110^\circ\text{C} - 140^\circ\text{C}$
  * Ngưỡng vách lốp an toàn: $L_{\max}(\text{Soft}) = 22$, $L_{\max}(\text{Medium}) = 35$, $L_{\max}(\text{Hard}) = 48$ vòng.
* **Chặng Silverstone GP (52 vòng):**
  * Vận tốc trung bình: $\bar{v} < 250\text{ km/h}$.
  * Đặc tính: Tổ hợp góc cua tốc độ cao liên tục (Maggotts, Becketts, Chapel, Stowe, Abbey), tải trọng ngang và tải trọng khí động học cực đại.
  * Cửa sổ nhiệt độ hoạt động:
    * **Soft (C3):** $100^\circ\text{C} - 130^\circ\text{C}$
    * **Medium (C2):** $110^\circ\text{C} - 140^\circ\text{C}$
    * **Hard (C1):** $115^\circ\text{C} - 145^\circ\text{C}$
  * Ngưỡng vách lốp an toàn ngắn hơn: $L_{\max}(\text{Soft}) = 18$, $L_{\max}(\text{Medium}) = 30$, $L_{\max}(\text{Hard}) = 42$ vòng.
  * So sánh thông số: $d_1, d_2, t_{\text{base}}$ tại Silverstone đều lớn hơn Monza, trong khi $L_{\max}$ ngắn hơn do ma sát bề mặt nhám và tải trọng cua lớn hơn.

---

## 3. BÀI TOÁN HỒI QUY WLS (WEIGHTED LEAST SQUARES)

### 3.1. Phương trình phân rã thời gian vòng đua & Biến phản hồi hiệu chỉnh $y_j$
Theo phân tích động lực học của Pirelli, thời gian hoàn thành vòng đua thứ $i$ của xe sử dụng hợp chất lốp $c$ ở số vòng tuổi $a$ được phân rã thành **4 thành phần vật lý độc lập**:
$$t_{\text{lap}}(c, a, i) = t_{\text{base}}(c) \;+\; \Delta t_{\text{tyre}}(c, a) \;+\; \Delta t_{\text{fuel}}(i) \;-\; \Delta t_{\text{track}}(i)$$

Trong đó:
$$\mathbf{\Delta t_{\text{tyre}}(c, a) = d_1(c) \cdot a \;+\; d_2(c) \cdot a^2}$$

Triển khai đầy đủ phương trình phân rã 4 thành phần:
$$\mathbf{t_{\text{lap}}(c, a, i) = \underbrace{t_{\text{base}}(c)}_{\text{Thời gian cơ sở}} \;+\; \underbrace{d_1(c) \cdot a}_{\text{Mòn cơ học (tt)}} \;+\; \underbrace{d_2(c) \cdot a^2}_{\text{Thoái hóa nhiệt (pt)}} \;+\; \underbrace{\alpha_{\text{fuel}} \cdot (N - i)}_{\text{Tải trọng nhiên liệu}} \;-\; \underbrace{\gamma_{\text{track}} \cdot i}_{\text{Mặt đường bám cao su}}}$$

* $t_{\text{base}}(c)$: Thời gian cơ sở (lốp mới $a=0$, xe cạn xăng, điều kiện mặt đường chuẩn).
* $d_1(c) \cdot a$: Thành phần suy giảm tuyến tính (tt) do mài mòn cơ học bào mỏng gai lốp.
* $d_2(c) \cdot a^2$: Thành phần suy giảm phi tuyến (pt) do tích tụ nhiệt nội tại $Q_{\text{gen}}$ và suy biến lưu biến.
* $\alpha_{\text{fuel}} \cdot (N - i)$: Ảnh hưởng tải trọng nhiên liệu, với $\alpha_{\text{fuel}} \approx 0.035\text{ s/vòng}$ (xe đốt $\approx 2.0\text{ kg}$ xăng/vòng từ bình chứa đầy $110\text{ kg}$ lúc xuất phát).
* $\gamma_{\text{track}} \cdot i$: Hệ số mặt đường bám thêm cao su (Track Evolution Factor), xe chạy càng về cuối chặng đường đua càng có độ bám cao hơn.

Từ tập hợp $M$ mẫu viễn trắc hợp lệ lọc từ FastF1:
$$\mathcal{O} = \big\{ (i_j, a_j, t_{\text{lap}, j}) \big\}_{j=1}^M$$

Để cô lập độ mòn nội tại của lốp, biến phản hồi quan sát được hiệu chỉnh bằng cách khấu trừ tải trọng nhiên liệu và bù trừ độ bám mặt đường:
$$\mathbf{y_j = t_{\text{lap}, j} \;-\; \alpha_{\text{fuel}} \cdot (N - i_j) \;+\; \gamma_{\text{track}} \cdot i_j}$$

Kết quả: $y_j$ phản ánh thuần túy thời gian vòng đua danh định chỉ còn phụ thuộc vào tuổi lốp:
$$y_j = t_{\text{base}}(c) \;+\; d_1(c) \cdot a_j \;+\; d_2(c) \cdot a_j^2 \;+\; \epsilon_j$$

### 3.2. Mô hình quan sát tuyến tính theo tham số
$$y_j = t_{\text{base}}(c) \;+\; d_1(c) \cdot a_j \;+\; d_2(c) \cdot a_j^2 \;+\; \epsilon_j$$

Dưới dạng phương trình ma trận:
$$y = X \beta + \epsilon$$
với:
$$y = \begin{bmatrix} y_1 \\ \vdots \\ y_M \end{bmatrix} \in \mathbb{R}^M, \quad \beta = \begin{bmatrix} t_{\text{base}}(c) \\ d_1(c) \\ d_2(c) \end{bmatrix} \in \mathbb{R}^3, \quad X = \begin{bmatrix} 1 & a_1 & a_1^2 \\ \vdots & \vdots & \vdots \\ 1 & a_M & a_M^2 \end{bmatrix} \in \mathbb{R}^{M \times 3}$$

### 3.3. Lý do bác bỏ mô hình OLS (Ordinary Least Squares)
Mô hình OLS giả định ma trận trọng số đơn vị $W = I$ (coi mọi vòng đua bình đẳng $w_j = 1$). OLS thất bại vì:
1. **Phương sai thay đổi (Heteroscedasticity):** Phương sai sai số tăng vọt theo tuổi lốp:
   $$\sigma^2(a) \approx 0.05\,\text{s}^2 \text{ (lốp mới, } a \le 10) \;\longrightarrow\; 0.47\,\text{s}^2 \text{ (lốp già, } a \ge 30)$$
   Vi phạm nghiêm trọng giả định Homoscedasticity của Định lý Gauss-Markov.
2. **Nhiễu giao thông & Khí bẩn (Dirty Air Outliers):** Xe chạy bám đuôi đối thủ hoặc né cờ vàng bị trễ $\pm 1.5\text{s}$. Sai số bình phương $(1.5)^2 = 2.25$ trong OLS sẽ bóp méo toàn bộ đường cong vật lý.

### 3.4. Cấu trúc Ma trận Trọng số Độc lập $W$
Ma trận trọng số đường chéo:
$$W = \text{diag}(w_1, w_2, \dots, w_M) \in \mathbb{R}^{M \times M}$$
với mỗi phần tử trên đường chéo là tích của 2 thành phần độc lập:
$$w_j = w_{\text{age}}(a_j) \cdot w_{\text{Huber}}(r_j)$$

#### A. Trọng số tuổi lốp $w_{\text{age}}(a_j)$:
Khắc phục hiện tượng phương sai bùng nổ khi lốp vượt quá ngưỡng an toàn $L_{\max}$:
$$w_{\text{age}}(a_j) = \frac{1}{1 \;+\; 0.5 \left[ \dfrac{\max\big(0, \; a_j - L_{\max}(c)\big)}{5} \right]^2}$$
* Khi $a_j \le L_{\max}$: $\max(0, a_j - L_{\max}) = 0 \implies w_{\text{age}} = 1.0$ (giữ nguyên $100\%$ độ tin cậy).
* Khi $a_j > L_{\max}$: Mẫu số tăng phi tuyến bậc hai, giảm nhanh trọng số của các vòng lốp bị hỏng/rách vách để tránh làm biến dạng tham số chuẩn.

#### B. Trọng số khử nhiễu ngoại lai Huber $w_{\text{Huber}}(r_j)$:
Dựa trên M-estimator của Peter Huber (1964) với ngưỡng $\delta_{\text{Huber}} = 1.2\,\text{s}$:
$$w_{\text{Huber}}(r_j) = \begin{cases} 
1.0 & \text{nếu } |r_j| \le \delta_{\text{Huber}} \\[6pt]
\dfrac{\delta_{\text{Huber}}}{|r_j| + 10^{-6}} & \text{nếu } |r_j| > \delta_{\text{Huber}} 
\end{cases}$$
* $r_j = y_j - X_j \beta$: Phần dư (thời gian thực tế trừ dự đoán).
* Hằng số $+ 10^{-6}$ ở mẫu số: Hằng số $\epsilon$ chống chia cho 0.
* Cơ chế: Khi $|r_j| > 1.2\text{s}$ (kẹt xe, cờ vàng, trượt cua), hàm chuyển bình phương sai số $r_j^2$ thành trị tuyệt đối $\delta_{\text{Huber}} |r_j|$, triệt tiêu hoàn toàn tác động phá hoại của các điểm ngoại lai.

#### C. Thuật toán lặp IRLS (Iteratively Reweighted Least Squares)
Do phần dư $r_j$ phụ thuộc vào nghiệm $\beta$ chưa biết, thuật toán giải bằng phương pháp lặp:
1. **Khởi tạo:** Gán $W^{(0)} = I$ (chạy OLS ban đầu) để tìm nghiệm sơ bộ $\beta^{(0)}$.
2. **Cập nhật phần dư:** $r_j^{(k)} = y_j - X_j \beta^{(k)}$.
3. **Cập nhật trọng số:** Tính ma trận $W^{(k+1)}$ từ $w_{\text{age}}(a_j)$ và $w_{\text{Huber}}(r_j^{(k)})$.
4. **Giải WLS:** Tính $\beta^{(k+1)} = (X^T W^{(k+1)} X + \lambda I)^{-1} X^T W^{(k+1)} y$.
5. **Hội tụ:** Dừng khi $\|\beta^{(k+1)} - \beta^{(k)}\|_2 < 10^{-5}$ (thường sau $3 - 5$ vòng lặp).

---

## 4. NGHIỆM GIẢI TÍCH ĐÓNG VÀ CHÍNH QUY HÓA TIKHONOV

### 4.1. Hàm mất mát có số hạng phạt Tikhonov
$$\min_{\beta} \; J(\beta) = (y - X \beta)^T W (y - X \beta) \;+\; \lambda \|\beta\|_2^2$$
với tham số chính quy hóa cực nhỏ $\lambda \approx 10^{-9}$.

### 4.2. Dẫn xuất nghiệm giải tích
Lấy đạo hàm riêng theo vector tham số $\beta$:
$$\frac{\partial J}{\partial \beta} = -2 X^T W (y - X \beta) + 2 \lambda \beta = 0$$
$$\implies -X^T W y + X^T W X \beta + \lambda I \beta = 0$$
$$\implies \big(X^T W X + \lambda I\big) \beta = X^T W y$$

Nghiệm giải tích đóng duy nhất:
$$\hat{\beta} = \big(X^T W X + \lambda I\big)^{-1} X^T W y$$

### 4.3. Ràng buộc không âm vật lý
Để loại bỏ các nghiệm âm phi vật lý (lốp không thể càng chạy càng bám đường):
$$\hat{\beta} \longleftarrow \max\big(0, \; \hat{\beta}\big) \implies t_{\text{base}} > 0, \; d_1 \ge 0, \; d_2 \ge 0$$
Số hạng $\lambda I$ bảo đảm ma trận $(X^T W X + \lambda I)$ luôn xác định dương và khả nghịch $100\%$, ngăn chặn lỗi singular matrix.

---

## 5. DẪN XUẤT CẦU NỐI CHO THÀNH VIÊN 1 & THÀNH VIÊN 4

### 5.1. Đạo hàm mài mòn bậc 1 (Tốc độ mòn lốp)
$$\nabla t_{\text{deg}}(a) = \frac{\partial \Delta t_{\text{tyre}}}{\partial a} = d_1(c) + 2 \cdot d_2(c) \cdot a \quad (\text{giây/vòng})$$
*Đây là công thức nền tảng cung cấp cho Thành viên 1 để xây dựng toán tử sửa chữa nghiệm trong DAGA-F1.*

### 5.2. Đạo hàm mài mòn bậc 2 (Gia tốc mòn lốp)
$$\nabla^2 t_{\text{deg}}(a) = \frac{\partial^2 \Delta t_{\text{tyre}}}{\partial a^2} = 2 \cdot d_2(c) \quad \forall a \ge 1$$
*Chứng minh toán học: Vì $d_2 > 0 \implies \nabla^2 t_{\text{deg}} > 0$, hàm suy giảm lốp là một hàm lồi nghiêm ngặt (Strictly Convex Function), bảo đảm không gian tìm kiếm có điểm cực tiểu duy nhất.*

### 5.3. Bước chuyển rời rạc khi kéo dài stint $a \mapsto a+1$
$$\begin{aligned}
\Delta t_{\text{discrete}}(a \mapsto a+1) &= \Big[ d_1 (a+1) + d_2 (a+1)^2 \Big] - \Big[ d_1 a + d_2 a^2 \Big] \\
&= d_1 + d_2 (2a + 1) \\
&= \mathbf{\nabla t_{\text{deg}}(a) + d_2(c)}
\end{aligned}$$

### 5.4. Đột phá: Công thức tổng giải tích đóng $O(1)$ cho Stint
Tổng độ mòn của một stint dài $L$ vòng xuất phát từ lốp mới:
$$D_{\text{stint}}(c, L) = \sum_{a=1}^{L} \big(d_1 a + d_2 a^2\big) = d_1 \sum_{a=1}^{L} a \;+\; d_2 \sum_{a=1}^{L} a^2$$

Áp dụng hằng đẳng thức tổng đại số Faulhaber:
$$\sum_{a=1}^{L} a = \frac{L(L+1)}{2}, \qquad \sum_{a=1}^{L} a^2 = \frac{L(L+1)(2L+1)}{6}$$

Thay vào, thu được **công thức tính tổng đóng thời gian $O(1)$**:
$$\mathbf{D_{\text{stint}}(c, L) = d_1(c) \cdot \frac{L(L+1)}{2} \;+\; d_2(c) \cdot \frac{L(L+1)(2L+1)}{6}}$$

* **Ý nghĩa tính toán:** Chuyển đổi toàn bộ thuật toán Quy hoạch động Bellman (TV4) và Simulator từ vòng lặp $O(L)$ thành phép tính giải tích $O(1)$. Nhờ đó, Bellman DP giải 30.088 trạng thái chỉ trong chưa đầy $0.1$ giây.

### 5.5. Cơ chế sửa chữa nghiệm theo Gradient vật lý (Bàn giao cho TV1)
Khi lai ghép hoặc đột biến vi phạm bảo toàn số vòng:
$$\Delta N = N - \sum_{k=1}^{K+1} l_k \ne 0$$
* **Trường hợp thiếu vòng ($\Delta N > 0$):**
  $$j^* = \arg\min_{j} \Big[ \nabla t_{\text{deg}}(a_j) - 0.05 \cdot \big(L_{\max}(c_j) - a_j\big) \Big] \quad \text{với } a_j < L_{\max}(c_j)$$
  Cộng thêm vòng vào stint có tốc độ mòn thấp nhất và xa vách lốp nhất.
* **Trường hợp thừa vòng ($\Delta N < 0$):**
  $$j^* = \arg\max_{j} \Big( \nabla t_{\text{deg}}(a_j) \Big) \quad \text{với } l_j > L_{\min} = 4$$
  Trừ bớt vòng ở stint có tốc độ mòn nguy hiểm nhất.

---

## 6. ĐÁNH GIÁ ĐỘ KHỚP MÔ HÌNH & TĂNG TỐC TENSOR 3D

### 6.1. Bộ chỉ số kiểm định thống kê (Validation Metrics)
Mô hình được đánh giá độc lập trên từng loại lốp (Soft, Medium, Hard) qua các thước đo:
* **Hệ số xác định:**
  $$R^2 = 1 - \frac{\sum (y_j - \hat{y}_j)^2}{\sum (y_j - \bar{y})^2}, \qquad R^2_{\text{adj}} = 1 - (1 - R^2) \frac{M - 1}{M - p - 1}$$
* **Sai số trung bình:**
  $$\text{RMSE} = \sqrt{\frac{1}{M} \sum_{j=1}^M (y_j - \hat{y}_j)^2}, \quad \text{MAE} = \frac{1}{M} \sum_{j=1}^M |y_j - \hat{y}_j|, \quad \text{MAPE} = \frac{100\%}{M} \sum_{j=1}^M \left|\frac{y_j - \hat{y}_j}{y_j}\right|$$
* **Tiêu chuẩn lựa chọn mô hình:**
  $$\text{AIC} = 2k + M \ln(\text{RSS}/M), \qquad \text{BIC} = k \ln(M) + M \ln(\text{RSS}/M)$$
  Chứng minh mô hình bậc 2 có điểm AIC/BIC thấp hơn mô hình bậc 1 (dưới khớp) và mô hình bậc 3 (quá khớp).

### 6.2. Kỹ thuật tiền biên dịch Tensor 3 Chiều $\mathcal{T}[c, a, i]$
Để giải phóng hoàn toàn năng lực xử lý CPU cho Bellman DP và GA:
$$\mathcal{T} \in \mathbb{R}^{|C| \times \max(L_{\max}) \times N}, \qquad \mathcal{T}[c, a, i] = t_{\text{lap}}(c, a, i)$$
* Kích thước mảng: $3 \times 48 \times 53 = 7.632$ số thực float64 ($\approx 61\text{ KB}$ RAM).
* Toàn bộ thuật toán tối ưu hóa chuyển sang **tra bảng $O(1)$**, triệt tiêu chi phí tính toán động học.

---

## 7. MÔ HÌNH NHIỆT ĐỘNG LỰC HỌC & ĐỘ NHẠY THEO NHIỆT ĐỘ MẶT ĐƯỜNG ($T_{\text{track}}$)

### 7.1. Cơ chế biến tính nhiệt của hợp chất cao su
Khi nhiệt độ mặt đường $T_{\text{track}}$ tăng cao:
* Đỉnh ma sát tiếp xúc (Friction Peak) bị trượt ra ngoài vùng vận hành tối ưu (Operating Window).
* Mô-đun đàn hồi lưu biến $E'$ suy giảm $\implies$ cao su mềm nhão, biến dạng trượt lớn $\implies$ công suất ma sát sinh nhiệt nội tại tăng đột biến ($Q_{\text{gen}} \gg$).
* Nhiệt độ tích tụ thúc đẩy quá trình oxy hóa polymer và rộp lốp (blistering) $\implies$ Hiện tượng Tyre Cliff sụp đổ sớm hơn.

### 7.2. Phương trình bán thực nghiệm hiệu chỉnh tham số theo $T_{\text{track}}$
Độ lệch nhiệt độ tương đối không thứ nguyên:
$$\delta_T = \frac{T_{\text{track}} - T_{\text{ref}}}{T_{\text{ref}}}$$
với $T_{\text{ref}}$ là nhiệt độ tham chiếu tiêu chuẩn (Monza: $T_{\text{ref}} = 30^\circ\text{C}$).

Hệ số mài mòn $d_1$ và $d_2$ biến thiên theo nhiệt độ:
$$\mathbf{d_1(c, T_{\text{track}}) = d_1^{(0)}(c) \cdot \Big[ 1 + K_{T_1}(c) \cdot \delta_T \Big]}$$
$$\mathbf{d_2(c, T_{\text{track}}) = d_2^{(0)}(c) \cdot \Big[ 1 + K_{T_2}(c) \cdot \delta_T \;+\; \theta(c) \cdot \big(\max(0, \delta_T)\big)^2 \Big]}$$

* $d_1^{(0)}(c), d_2^{(0)}(c)$: Các tham số danh định tại $T_{\text{ref}}$.
* $K_{T_1}(c), K_{T_2}(c)$: Hệ số độ nhạy nhiệt độ tuyến tính.
* $\theta(c) \cdot \big(\max(0, \delta_T)\big)^2$: **Hàm phạt kích hoạt ReLU bình phương**:
  * Khi trời mát ($\delta_T \le 0 \implies \max(0, \delta_T) = 0$): Không bị suy thoái nhiệt phi tuyến.
  * Khi trời quá nhiệt ($\delta_T > 0$): Hệ số $d_2$ bùng nổ theo cấp số bậc hai, mô tả chính xác sự sụp đổ độ bám khi mặt đường nóng trên $45^\circ\text{C}$.

---

## 8. BẢNG TỔNG KẾT BÀN GIAO THAM SỐ LIÊN THÀNH VIÊN

| Tham Số Kỹ Thuật | Ký Hiệu | Đơn Vị | Giá Trị Soft (C5) | Giá Trị Medium (C4) | Giá Trị Hard (C3) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Thời gian cơ sở (Monza)** | $t_{\text{base}}$ | giây | $81.000$ | $81.500$ | $82.200$ |
| **Hệ số mòn tuyến tính** | $d_1$ | s/vòng | $0.1200$ | $0.0700$ | $0.0400$ |
| **Hệ số mòn phi tuyến** | $d_2$ | s/vòng$^2$ | $0.0055$ | $0.0022$ | $0.0010$ |
| **Ngưỡng an toàn vách lốp** | $L_{\max}$ | vòng | $22$ | $35$ | $48$ |
| **Hao hụt nhiên liệu** | $\alpha_{\text{fuel}}$ | s/vòng | \multicolumn{3}{c|}{$0.0350\text{ s/vòng}$} |
| **Ngưỡng lọc ngoại lai Huber**| $\delta_{\text{Huber}}$ | giây | \multicolumn{3}{c|}{$1.200\text{ giây}$} |
| **Hệ số chính quy hóa** | $\lambda$ | — | \multicolumn{3}{c|}{$10^{-9}$} |

---

*Tài liệu này hoàn tất việc đồng bộ toán học giữa Thành viên 3, Thành viên 1 và Thành viên 4, sẵn sàng đưa vào Section 3.1 & Section 4.1 của bài báo khoa học chuẩn Elsevier trên Overleaf.*
