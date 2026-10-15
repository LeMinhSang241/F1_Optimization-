# Workspace Guidelines for F1_Optimization

## LaTeX & Mathematical Expression Formatting
Để ngăn chặn tình trạng lỗi phân tích cú pháp hoặc vỡ giao diện hiển thị LaTeX trong chat và tài liệu Markdown:

1. **Không lạm dụng `$ ... $` nội dòng (inline math) chứa dấu gạch dưới `_`, dấu mũ `^`, hoặc `\text{...}`**:
   - Sử dụng khối mã nội dòng (inline code) cho các biến và biểu thức ngắn: ví dụ `T_race(S)`, `sum(l_k) = N_total`, `nabla t_deg(a) = d1 + 2*d2*a`, `D_pop < 0.15`, `K in {1, 2, 3}`, `L_max = 35`.
   - Hoặc sử dụng ký tự Unicode trực tiếp: `∇t_deg`, `ΔN`, `α_fuel`, `γ_track`, `≥`, `≤`, `∈`.

2. **Khối công thức toán độc lập (Display Math)**:
   - Luôn sử dụng `$$ ... $$` trên các dòng riêng biệt với dòng trống ở trước và sau.
   - Giữ văn giải thích bằng tiếng Việt hoặc nhãn chữ dài ở bên ngoài khối toán thay vì nhồi nhét vào `\text{...}`.
   - Sử dụng `\le`, `\ge`, `\lt`, `\gt` thay cho `<` và `>`.

3. **Cân bằng cú pháp**:
   - Mọi cặp dấu `{ }`, `( )`, `[ ]`, `$`, `$$` phải luôn đóng mở chính xác và cân bằng.
