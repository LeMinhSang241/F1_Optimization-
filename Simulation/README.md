# Mô phỏng pit-stop

Làm lần lượt các bước sau.

1. Cài pygame nếu máy chưa có: `pip install pygame-ce`
2. Đứng ở thư mục dự án, chạy: `python Simulation/main.py`
3. Cửa sổ mở chặng Monza, nhiệt độ 30 độ, hệ số lốp danh định. Ba xe là GA Optimal (Medium 20, Soft 14, Medium 19), Verstappen (Medium 26, Hard 27) và Holland GA (Medium 24, Hard 29).
4. Cột bên phải hiện hạng, khoảng cách tới xe dẫn đầu, tuổi lốp trên giới hạn an toàn, xăng còn lại, khí bẩn hoặc DRS, số vòng tới pit, thời gian ước tính và thời gian gốc.
5. Thời gian gốc của ba xe Monza lúc mở cửa sổ là 4497.997 giây, 4508.864 giây và 4508.197 giây. Ba số này là lúc chưa có cờ và chưa có khí bẩn.
6. Phím Space tạm dừng hoặc chạy tiếp. Phím mũi tên lên và mũi tên xuống đổi tốc độ tua.
7. Phím C đổi sang Silverstone rồi bấm lại để về Monza. Silverstone có 52 vòng. Ba xe là chiến lược hai lần pit ngắn nhất, một lần pit Medium-Hard, và một lần pit Soft-Hard. Đổi chặng thì đua chạy lại từ đầu.
8. Phím T đổi nhiệt độ mặt đường: mát hơn chuẩn, đúng chuẩn, rồi nóng hơn chuẩn. Đường nóng làm lốp mòn nhanh hơn và có thể hạ giới hạn tuổi lốp. Đua chạy lại từ đầu.
9. Phím F đổi giữa hệ số danh định trong `data/race_configs.py` và hệ số đã fit trong `models/tyre_params_monza.json` hoặc `models/tyre_params_silverstone.json`. Đua chạy lại từ đầu.
10. Lúc bắt đầu chặng, chương trình bốc safety car theo xác suất khoảng 0,3 lần mỗi chặng. Nếu có, cột phải ghi vòng bắt đầu và số vòng kéo dài, từ 3 đến 8 vòng, không trước vòng 5 và không sau 85% chặng.
11. Phím S gọi safety car ngay nếu đang ở cờ xanh và vòng hiện tại còn trong khoảng đó. Xe chạy bằng 60% tốc độ, pit còn 46% thời gian. Phím V gọi virtual safety car: 80% tốc độ, pit còn 68% thời gian. Bấm giữa vòng thì cờ tính từ vòng sau. Safety car đã bốc từ đầu thì tính đúng vòng ghi trên bảng. Cờ đếm theo xe dẫn đầu rồi trả về cờ xanh.
12. Khi một xe cách xe phía trước từ 1,5 giây trở xuống, vòng đó của xe sau cộng 0,35 giây khí bẩn. Từ 1,0 giây trở xuống thì được DRS và trừ 0,5 giây.
13. Đóng cửa sổ để thoát.
