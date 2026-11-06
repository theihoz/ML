# Báo cáo tiểu luận – Đề tài 4

- `BaoCao_TieuLuan_De4_LuongCNTT.docx`: báo cáo Word (A4, Times New Roman 13, giãn dòng 1,5, lề trái 3,5 cm, phải 2 cm, trên 2,5 cm, dưới 3 cm). Khi mở, Word hỏi cập nhật trường: chọn **Yes** để điền mục lục, danh mục hình và danh mục bảng (hoặc nhấn Ctrl+A rồi F9). Họ tên, MSSV, lớp, giảng viên và tỷ lệ đóng góp để trống cho nhóm tự điền.
- `diagrams/*.drawio`: tám sơ đồ đen trắng, mở và chỉnh bằng draw.io (app.diagrams.net hoặc bản desktop); `*.png` là ảnh xuất dùng trong báo cáo.
- `figures/`: biểu đồ Matplotlib/Seaborn sinh từ `job_market/src/career_market/salary_charts.py` và ảnh chụp giao diện.

- `SlideThuyetTrinh_De4_v2.pptx`: 37 slide cho người nghe không chuyên, có lời nói trong Speaker Notes.
- `KichBan_ThuyetTrinh_De4.docx`: kịch bản đọc cho một người thuyết trình, bảng ghi nhớ và câu hỏi thường gặp.
- Sáu notebook `job_market/notebooks/tinh_nang_*.ipynb` giải thích từng tính năng; xem README trong thư mục notebook.

## Sinh lại tài liệu

Chạy từ thư mục gốc của repo, với Node.js có `docx` và `pptxgenjs` (có thể đặt `NODE_PATH` trỏ đến thư mục cài riêng), và môi trường Python của `job_market`:

```sh
PYTHONPATH=job_market/src python report/scripts/render_figures.py
node report/scripts/build_report.js . report/BaoCao_TieuLuan_De4_LuongCNTT.docx
node report/scripts/build_slides_v2.js . report/SlideThuyetTrinh_De4_v2.pptx
node report/scripts/build_kich_ban.js report/KichBan_ThuyetTrinh_De4.docx
```

Biểu đồ dữ liệu được sinh lại và không commit. Ảnh giao diện trong `figures/ui-*.png` được lưu trong repo. Các sơ đồ draw.io chưa được xuất lại trong đợt cập nhật này. Báo cáo và slide ghi rõ mô hình chưa đạt chuẩn production; rà soát nhãn do AI thực hiện, chưa thay thế thẩm định của con người.
- `TeamWork_PP_Nhom3.ipynb`: notebook báo cáo nhóm (bản thăm dò Ridge/Linear Regression ban đầu), giữ làm hồ sơ.
