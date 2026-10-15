"""Ứng dụng Web Dashboard tương tác mô phỏng và tối ưu hóa chiến lược F1 bằng Giải thuật Di truyền.
Phân công: Thành viên 5 (Scientific Paper & UI Lead).
Chạy bằng lệnh: streamlit run app.py
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import time

from src.tyre_model.pirelli_physics import PirelliPhysicsTyreModel
from src.simulator.race_sim import F1RaceSimulator
from src.ga_strategy.optimizer import F1StrategyGAOptimizer

st.set_page_config(
    page_title="F1 Pit-Stop Strategy Optimizer (GA)",
    page_icon="🏎️",
    layout="wide"
)

st.title("🏎️ F1 Pit-Stop & Tyre Strategy Optimization (Genetic Algorithm)")
st.markdown("""
**Đồ án môn học DS106: Tối ưu hóa và Ứng dụng** | *Khoa Khoa học Dữ liệu - UIT (ĐHQG-HCM)*  
Hệ thống ứng dụng **Giải thuật Di truyền Thích nghi Động (DAGA-F1)** và **Mô hình suy giảm lốp giải tích Pirelli & Động lực học nhiệt TV3** để tìm kiếm chiến lược dừng pit tối ưu nhất.
""")

st.sidebar.header("⚙️ Cấu hình Chặng đua & Thuật toán")

race_choice = st.sidebar.selectbox(
    "Chọn Chặng đua (Grand Prix)",
    ["Monza GP (Ý - 53 vòng)", "Silverstone GP (Anh - 52 vòng)"]
)

circuit_name = "Silverstone" if "Silverstone" in race_choice else "Monza"
total_laps = 53 if circuit_name == "Monza" else 52
default_pit_loss = 23.2 if circuit_name == "Monza" else 21.5
default_t_ref = 30.0 if circuit_name == "Monza" else 28.0

pit_loss = st.sidebar.slider(
    "Tổn thất thời gian vào Pit (Pit Loss - Giây)",
    min_value=15.0, max_value=32.0, value=default_pit_loss, step=0.5
)

track_temp = st.sidebar.slider(
    "Nhiệt độ mặt đường T_track (°C)",
    min_value=15.0, max_value=60.0, value=default_t_ref, step=1.0
)

pop_size = st.sidebar.slider("Kích thước Quần thể (Population Size)", 20, 150, 60, step=10)
generations = st.sidebar.slider("Số Thế hệ Tiến hóa (Generations)", 20, 120, 50, step=10)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🏁 Thiết lập & Khởi chạy")
    st.info(f"""
    - **Chặng đua:** {circuit_name} GP
    - **Tổng số vòng đua:** {total_laps} vòng
    - **Tổn thất Pit:** {pit_loss} s/lần dừng
    - **Nhiệt độ mặt đường:** {track_temp}°C (Tham chiếu: {default_t_ref}°C)
    - **Ràng buộc FIA:** Bắt buộc dùng tối thiểu 2 loại lốp khô khác nhau.
    - **Giải thuật:** DAGA-F1 (Tách/Gộp Stint + Faulhaber O(1) + Kiểm soát vách lốp L_max)
    """)

    run_btn = st.button("🚀 BẮT ĐẦU TỐI ƯU HÓA CHIẾN LƯỢC", type="primary", use_container_width=True)

if run_btn:
    with st.spinner("Đang chạy Giải thuật Di truyền qua các thế hệ..."):
        start_time = time.time()
        tyre_model = PirelliPhysicsTyreModel(track=circuit_name, t_track=track_temp, t_ref=default_t_ref)
        simulator = F1RaceSimulator(total_laps=total_laps, pit_loss=pit_loss, tyre_model=tyre_model)
        optimizer = F1StrategyGAOptimizer(
            simulator=simulator,
            pop_size=pop_size,
            generations=generations
        )
        best_strategy, best_time, details = optimizer.optimize()
        exec_duration = time.time() - start_time

    st.success(f"Tối ưu hoàn tất trong {exec_duration:.2f} giây!")

    with col1:
        st.subheader("🏆 Chiến lược Tối ưu Nhất")
        st.metric("Tổng Thời Gian Đua Dự Kiến", f"{best_time / 60:.2f} phút", f"{best_time:.1f} s")
        st.write(f"**Số lần dừng Pit:** {details['num_stops']} lần dừng")
        st.write(f"**Tuân thủ Luật lốp FIA:** {'✅ Hợp lệ' if details['is_valid_fia'] else '❌ Vi phạm'}")

        st.write("**Chi tiết từng chặng lốp (Stints):**")
        cum_lap = 1
        for i, (comp, length) in enumerate(best_strategy, 1):
            st.write(f"- **Stint {i}:** Lốp **{comp}** | Chạy từ vòng {cum_lap} đến {cum_lap + length - 1} ({length} vòng)")
            cum_lap += length

    with col2:
        st.subheader("📊 Trực quan hóa Tiến trình Hội tụ & Phân bổ Lốp")
        
        # Biểu đồ hội tụ
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(optimizer.history['best_time'], label='Best Race Time', color='crimson', lw=2)
        ax.plot(optimizer.history['avg_time'], label='Population Average', color='gray', linestyle='--', alpha=0.7)
        ax.set_xlabel("Thế hệ (Generation)")
        ax.set_ylabel("Thời gian (giây)")
        ax.set_title("Đồ thị Hội tụ của Giải thuật Di truyền (Convergence Curve)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        # Biểu đồ phân bổ lốp (Timeline)
        fig2, ax2 = plt.subplots(figsize=(8, 1.8))
        color_map = {'Soft': '#E10600', 'Medium': '#FFD100', 'Hard': '#FFFFFF'}
        edge_map = {'Soft': '#B00000', 'Medium': '#D4AF37', 'Hard': '#444444'}
        
        left = 0
        for comp, length in best_strategy:
            ax2.barh(0, length, left=left, color=color_map.get(comp, 'gray'),
                     edgecolor=edge_map.get(comp, 'black'), height=0.6, label=comp)
            ax2.text(left + length / 2, 0, f"{comp}\n({length} laps)", ha='center', va='center',
                     fontweight='bold', color='black')
            left += length

        ax2.set_xlim(0, total_laps)
        ax2.set_yticks([])
        ax2.set_xlabel("Vòng đua (Laps)")
        ax2.set_title("Timeline Chiến lược Lốp Tối ưu")
        st.pyplot(fig2)
