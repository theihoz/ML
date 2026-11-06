# Lương IT Việt Nam 2023–2026: bộ đối chiếu thực tế cho mô hình dự đoán lương

Ngày tra cứu: 2026-11-06. Đơn vị chuẩn hóa trong file: **triệu VND/tháng**. Mọi con số dưới đây đều lấy từ trang hoặc PDF của chính nhà phát hành, trừ những chỗ ghi rõ "thứ cấp". Ký hiệu "–" nghĩa là nguồn để trống ô đó; "không tìm thấy" nghĩa là không tìm được số liệu.

---

## 1. Tóm tắt

- **Ba nguồn sơ cấp đọc được bảng số liệu đầy đủ:**
  1. **ITviec**, IT Salary & Recruitment Market Report, các bản 2023-2024, 2024-2025 và 2025-2026. Đây là khảo sát người lao động tự khai. Số liệu là trung vị, đơn vị triệu VND/tháng, chia theo vị trí và theo năm kinh nghiệm. Trang công khai **không có** bảng theo thành phố hay cấp bậc, cũng **không nêu** lương là gross hay net. Nguồn: https://itviec.com/report/vietnam-it-salary-and-recruitment-market và https://itviec.com/report/vietnam-it-salary-and-recruitment-market-2024-2025
  2. **TopDev**, Vietnam IT Market Report 2023 và 2024-2025. Số liệu kết hợp khảo sát với dữ liệu tin tuyển dụng (JD). Đơn vị là USD, **gross trước thuế**, kèm tỷ giá do chính TopDev công bố. Đây là nguồn **duy nhất** có bảng **cấp bậc × thành phố (HCM / Hà Nội / Đà Nẵng)** và bảng theo vị trí (trung vị và khoảng). Nguồn: https://topdev.vn/TopDev_VietnamITMarketReport2023_VietnamTechTalentsReport.pdf và https://shiftasia.com/wp-content/uploads/2024/12/TopDev_VietnamITMarketReport2024_2025_VietnamITTechTalentLandscape.pdf (bản 2024-2025 lấy từ một bản sao do bên thứ ba lưu, vì trang của TopDev bắt đăng ký mới cho tải: https://topdev.vn/get-report-en).
  3. **Adecco Vietnam Salary Guide 2026.** Đây là khoảng min–max của **lương cơ bản gross**, đơn vị triệu VND/tháng, chia theo HCM và Hà Nội, với hai nhóm kinh nghiệm 1–5 năm và trên 5 năm. Nguồn: https://www.adecco.com/-/jssmedia/project/adecco/adeccovn/pdf/adecco-vietnam-salary-guide-2026.pdf
- **Không lấy được bảng sơ cấp:** TopCV (trang bị chặn 403, chỉ có số thứ cấp), Navigos/VietnamWorks, Robert Walters, Michael Page, Talentnet-Mercer (bảng chi tiết phải gửi form mới tải được), và bản PDF Adecco 2025 (link cũ chuyển hướng về trang chủ). Về số liệu nhà nước, **không tìm thấy** số liệu lương theo nghề IT từ Tổng cục Thống kê. Chỉ có thu nhập bình quân toàn bộ lao động, theo bài báo thứ cấp: 7,7 triệu/tháng năm 2024 (https://mekongasean.vn/nam-2024-thu-nhap-binh-quan-cua-lao-dong-la-77-trieu-dongthang-37256.html). Con số này không dùng được để đối chiếu.
- **Mức tin cậy:** TopDev và Adecco rõ ràng về gross. ITviec có cỡ mẫu công bố (1.839 đến 2.324 người) nhưng mỗi ô chỉ có ít người, nhiều ô bị bỏ trống. TopDev không nêu cỡ mẫu cho từng ô. Cả ba nguồn đều thiên về doanh nghiệp lớn ở hai thành phố lớn và nhóm người dùng của chính nền tảng.

---

## 2. Bảng nguồn

| # | Nguồn | URL | Năm phát hành | Kỳ dữ liệu | Cỡ mẫu | Loại dữ liệu | Gross/Net | Đơn vị | Thống kê | Phân rã |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 | ITviec IT Salary & Recruitment Market Report 2025-2026 | https://itviec.com/report/vietnam-it-salary-and-recruitment-market | 2025 (cuối năm) | 27/05–31/07/2025 và 21/10–11/11/2025 | 1.839 người trả lời (gồm IT professional, freelancer, sinh viên IT, HR, CxO) | Khảo sát online tự khai | **Không nêu** | Triệu VND/tháng | Trung vị | Vị trí × năm KN (<1, 1-2, 3-4, 5-8, >8 năm). Không có thành phố. |
| S2 | ITviec IT Salary & Recruitment Market Report 2024-2025 | https://itviec.com/report/vietnam-it-salary-and-recruitment-market-2024-2025 | 2024 | 10/09–10/10/2024 | 2.324 người | Khảo sát online tự khai | **Không nêu** | VND/tháng | Trung vị (kèm số năm KN trung vị của vị trí) | 31 vị trí. Mỗi vị trí chỉ có 1 số. |
| S3 | ITviec IT Salary Report 2023-2024 (blog tóm tắt) | https://itviec.com/blog/it-salary-report-2023-2024/ | 2023 | 19/09–10/10/2023 | 2.207 người | Khảo sát online tự khai | **Không nêu** | Triệu VND/tháng | Trung vị | Chỉ có 6 vị trí trên trang công khai |
| S4 | TopDev Vietnam IT Market Report 2024-2025 | https://shiftasia.com/wp-content/uploads/2024/12/TopDev_VietnamITMarketReport2024_2025_VietnamITTechTalentLandscape.pdf (bản sao. Trang gốc: https://topdev.vn/get-report-en) | 09/2024 | 01/2022–07/2024 | 45.015 người khảo sát và hơn 90.000 tin tuyển dụng. Đã loại 9,3% dữ liệu không hợp lệ. | Khảo sát kết hợp dữ liệu JD. Phân phối theo thành phố tính theo "ratio of JD". | **Gross trước thuế**, không gồm OT và thưởng | USD/tháng. Tỷ giá TopDev dùng: **1 USD = 25.000 VND** | Trung bình (cấp bậc, thành phố); trung vị kèm khoảng (vị trí) | Cấp bậc × thành phố; năm KN; vị trí |
| S5 | TopDev Vietnam IT Market Report 2023 | https://topdev.vn/TopDev_VietnamITMarketReport2023_VietnamTechTalentsReport.pdf | 2023 | 07/2022–07/2023 | 50.012 người khảo sát và hơn 70.000 tin tuyển dụng. Đã loại 9,5% dữ liệu. | Khảo sát kết hợp JD | **Gross trước thuế** | USD/tháng. Tỷ giá TopDev dùng: **1 USD = 23.300 VND** | Trung bình kèm khoảng | Năm KN; thành phố |
| S6 | Adecco Vietnam Salary Guide 2026 | https://www.adecco.com/-/jssmedia/project/adecco/adeccovn/pdf/adecco-vietnam-salary-guide-2026.pdf | 2026 | Khảo sát cuối năm 2025 | Gửi tới hơn 10.000 người trong cơ sở dữ liệu. Không nêu số phản hồi cho bảng lương. | Dữ liệu khách hàng và ứng viên của Adecco, kết hợp nhận định của chuyên viên tuyển dụng | **Lương cơ bản gross** | Triệu VND/tháng | Khoảng min–max | Vị trí × thành phố (HCM, HN) × KN (1–5 năm, trên 5 năm) |
| S7 | TopCV, Báo cáo thị trường tuyển dụng 2025-2026 (thứ cấp) | Không truy cập được bản gốc. Thứ cấp: https://vietnamnet.vn/en/information-technology-remains-top-paying-profession-in-vietnam-2480607.html | 2026 | Q3/2025 | Hơn 3.000 người phản hồi và gần 300.000 tin tuyển dụng (theo bài báo) | Khảo sát kết hợp tin tuyển dụng | Không rõ | Triệu VND/tháng | Trung vị | Rời rạc, vài vị trí |
| S8 | Navigos / VietnamWorks, Robert Walters, Michael Page, Talentnet-Mercer | Robert Walters: https://vccinews.com/news/62051/robert-walters-salary-survey-2026-vietnam-reaches-new-milestone-with-rising-salaries-and-fierce-ai-talent-race. Talentnet: https://www.talentnetgroup.com/vn/featured-insights/rewards/vietnam-salary-report-labor-market-2025 | 2024–2026 | – | – | – | – | – | – | **Không tìm thấy** bảng lương IT công khai |

---

## 3. Bảng số liệu đối chiếu (chuẩn hóa về triệu VND/tháng)

Quy tắc quy đổi: số USD của TopDev được nhân với **tỷ giá chính TopDev công bố trong từng báo cáo** (S4: 25.000; S5: 23.300), để giữ nhất quán với nhà phát hành. Ký hiệu G = gross; "?" = nguồn không nêu gross hay net.

### 3.1 Cấp bậc × thành phố, TopDev 2024-2025 (S4), trung bình, G

Nguồn: trang 25 của báo cáo, mục "Average salary by level & location". Bảng gốc tính bằng USD.

| Thành phố | Fresher | Junior | Middle | Senior | Leader/Manager | Director/Architect |
|---|---|---|---|---|---|---|
| TP. Hồ Chí Minh | 9,75 ($390) | 20,38 ($815) | 30,40 ($1.216) | 42,70 ($1.708) | 52,08 ($2.083) | 69,28 ($2.771) |
| Hà Nội | 9,50 ($380) | 20,20 ($808) | 28,20 ($1.128) | 37,05 ($1.482) | 41,30 ($1.652) | 55,00 ($2.200) |
| Đà Nẵng | 9,50 ($380) | 20,13 ($805) | 28,15 ($1.126) | 33,18 ($1.327) | 38,75 ($1.550) | không có dữ liệu |

Trung bình chung theo thành phố (S4, trang 25): HCM 33,78 ($1.351), HN 30,53 ($1.221), ĐN 28,15 ($1.126). Trung bình toàn quốc là 32,93 ($1.317, năm 2024).
Bản 2023 (S5, trang 18, tỷ giá 23.300): HCM 32,39 ($1.390), HN 28,99 ($1.244), ĐN 27,24 ($1.169).

TopDev nhận xét rằng ở mức Fresher và Junior, lương gần như không chênh giữa các thành phố, còn từ Middle trở lên thì khác biệt rõ (S4, trang 25).

### 3.2 Cấp bậc theo năm kinh nghiệm, TopDev, trung bình (khoảng), G

| Cấp bậc (định nghĩa của TopDev) | 2024-2025 (S4, trang 26, ×25.000) | 2023 (S5, trang 20, ×23.300) |
|---|---|---|
| Fresher (<1 năm) | 12,0 (10,38–12,75) | 10,60 (10,14–11,98) |
| Junior (1 đến <3 năm; bản 2023 là 1–2 năm) | 19,5 (14,65–23,75) | 17,36 (13,42–20,90) |
| Middle (3 đến <5 năm; bản 2023 là 3–4 năm) | 29,4 (25,13–35,68) | 27,91 (22,90–33,46) |
| Senior (từ 5 năm) | 42,5 (38,03–48,18) | 39,47 (34,60–45,46) |
| Leader/Manager (kỹ thuật) | 45,0 (41,28–50,48) | 41,59 (37,82–54,43) |
| Director/Architect (kỹ thuật) | 53,5 (49,88–64,75) | 52,19 (46,67–62,44) |

Lưu ý: Fresher trong bảng theo năm kinh nghiệm ($480) cao hơn Fresher trong bảng theo thành phố ($380–390) của cùng báo cáo S4. Báo cáo không giải thích chênh lệch này, có thể do hai bảng dùng hai tập dữ liệu khác nhau.

### 3.3 Vị trí × năm kinh nghiệm, ITviec 2025-2026 (S1), trung vị, "?"

Nguồn: https://itviec.com/report/vietnam-it-salary-and-recruitment-market. Không có phân rã theo thành phố. Cột ánh xạ cấp bậc gần đúng: <1 năm ≈ Fresher, 1-2 năm ≈ Junior, 3-4 năm ≈ Middle, 5-8 năm ≈ Senior, >8 năm ≈ Senior+/Lead.

| Vị trí ITviec | Vai trò trong mô hình | Tổng | <1 năm | 1-2 năm | 3-4 năm | 5-8 năm | >8 năm |
|---|---|---|---|---|---|---|---|
| Back-end Developer | Backend | 37,8 | 12,4 | 25,35 | 30,1 | 39,9 | 54,9 |
| Front-end Developer | Frontend | 34,8 | – | – | 30,8 | 41,8 | 46,3 |
| Full-stack Developer | Fullstack | 37,25 | 10,1 | 20,35 | 34,5 | 41,8 | 44,8 |
| Mobile Developer | Mobile | 36,85 | 14,15 | 28,8 | 29,05 | 37,35 | 45,7 |
| Game Developer | Game | 33,35 | – | 26,5 | 40,4 | 57,85 | – |
| Embedded Engineer | Embedded/IoT | 34,35 | 21,4 | 23,9 | 28,4 | 39,4 | 60,65 |
| Product Owner/Product Manager | PM/PO | 50,1 | – | 25,3 | 42,7 | 60,4 | 75 |
| Business Analyst | Business Analyst | 30 | 12,2 | 14 | 28 | 37,4 | 41,35 |
| Project Leader/Project Manager | PM/PO | 50,1 | 17,2 | 29,85 | 48,4 | 58,45 | – |
| Tech Lead | Tech Lead/Architect | 51,8 | – | 45,3 | 53,85 | – | 68,45 |
| IT Manager | IT Manager/CTO | 50,25 | – | 46,4 | – | – | 50,3 |
| CTO/CIO/VPoE | IT Manager/CTO | 101,25 | – | – | 100,3 | – | – |
| Tester | QA/QC | 28,8 | 14,15 | 14,2 | 20,7 | 25,3 | 36,5 |
| QA - QC | QA/QC | 31,2 | – | 18 | 24,4 | 29,75 | 38,5 |
| Data Analyst/Data Scientist/BI Analyst | Data Analyst/BI (lẫn AI/ML) | 40,65 | – | 23,8 | – | 42,5 | – |
| Data Engineer | Data Engineer | 41,3 | – | – | 56,9 | – | – |
| ERP Engineer/ERP Consultant | ERP/SAP | 30,2 | 15,2 | 16,1 | 19,5 | 35,6 | – |
| IT Support/Helpdesk | IT Support | 20 | – | 8,6 | 18,7 | 22,5 | – |

Một số ô có dấu hiệu cỡ mẫu nhỏ, không đơn điệu theo kinh nghiệm: Mobile 1-2 năm (28,8) gần bằng 3-4 năm (29,05); Data Engineer 3-4 năm (56,9) cao hơn tổng (41,3); IT Manager >8 năm (50,3) gần bằng 1-2 năm (46,4); CTO 3-4 năm (100,3).

### 3.4 Vị trí, ITviec 2024-2025 (S2), trung vị kèm số năm kinh nghiệm trung vị, "?"

Nguồn: https://itviec.com/report/vietnam-it-salary-and-recruitment-market-2024-2025. Mỗi vị trí chỉ có một con số, gắn với số năm kinh nghiệm trung vị của người trả lời.

| Vị trí | Năm KN | Trung vị | Vị trí | Năm KN | Trung vị |
|---|---|---|---|---|---|
| Back-end Developer | 6 | 35,6 | Tester | 7 | 25,3 |
| Front-end Developer | 6 | 30,5 | QA-QC | 8,5 | 38,1 |
| Full-stack Developer | 6 | 36,35 | System Engineer/System Admin | 6 | 28,1 |
| Mobile Developer | 7 | 40,1 | DevOps/DevSecOps Engineer | 5 | 43,6 |
| Game Developer | 6 | 36,9 | Cloud Engineer | 3 | 29,2 |
| Embedded Engineer | 8 | 45,6 | Network Engineer | 7 | 30,0 |
| Product Owner/Product Manager | 6 | 50,95 | Security Engineer/Consultant | 8 | 60,6 |
| Business Analyst | 6 | 32,4 | Data Engineer | 6 | 44,1 |
| Project Leader/Project Manager | 6 | 47,35 | Data Analyst/DS/BI | 5,5 | 31,3 |
| Bridge Engineer (BrSE) | 7 | 49,0 | Database Engineer (≈ DBA) | 6 | 40,0 |
| Salesforce Engineer/Consultant | 6 | 33,15 | AI Engineer/Blockchain Engineer | 4 | 37,75 |
| IT Manager | 6 | 45,05 | ERP Engineer/Consultant | 6,5 | 41,0 |
| Tech Lead | 6 | 58,0 | Firmware Engineer | 6 | 45,5 |
| IT Consultant | 6 | 27,35 | Solution Architect | 5,5 | 73,95 |
| CTO/CIO/VPoE | 8 | 96,0 | IT Support/Helpdesk | 6 | 17,3 |
| Designer (≈ UI/UX) | 6,5 | 34,6 | | | |

ITviec 2023-2024 (S3) chỉ công bố 6 vị trí: Solution Architect 63 (2,5 năm KN), Tech Lead 50 (3 năm), Project Leader/PM 48 (5 năm), Cloud Engineer 45 (4 năm), DevOps/DevSecOps 40,5 (2 năm), Data Engineer 30 (2 năm). Nguồn: https://itviec.com/blog/it-salary-report-2023-2024/. Số năm kinh nghiệm thấp như vậy (Solution Architect chỉ 2,5 năm) đáng ngờ, nên chỉ dùng ở mức tham khảo.

### 3.5 Vị trí, TopDev 2024-2025 (S4), trung vị và khoảng, G, ×25.000

Nguồn: trang 28–30 của S4. Không phân rã theo thành phố hay cấp bậc. Báo cáo **không định nghĩa** "Range" là min–max hay p25–p75.

| Vị trí TopDev | Vai trò trong mô hình | Trung vị | Khoảng |
|---|---|---|---|
| Software Developer/Engineer | Software Engineer (chung) | 33,75 | 28,25–49,75 |
| Back-end Developer | Backend | 33,50 | 28,00–50,25 |
| Front-end Developer | Frontend | 32,50 | 27,50–48,75 |
| Full-stack Developer | Fullstack | 38,50 | 33,00–56,25 |
| Mobile Application Developer | Mobile | 30,00 | 25,50–45,75 |
| DevOps Engineer | DevOps/Cloud | 38,50 | 32,50–56,50 |
| Cloud Engineer | DevOps/Cloud | 42,00 | 36,50–59,25 |
| Site Reliability Engineer | DevOps/Cloud | 48,25 | 41,25–64,75 |
| Tester | QA/QC | 24,50 | 21,00–38,25 |
| QA Engineer | QA/QC | 29,50 | 26,00–43,75 |
| QC Engineer | QA/QC | 26,50 | 22,75–41,00 |
| Automation Test Engineer | QA/QC | 34,75 | 29,75–51,75 |
| Data Engineer | Data Engineer | 35,25 | 30,75–51,50 |
| Data Analyst | Data Analyst/BI | 30,75 | 28,25–46,50 |
| BI Developer | Data Analyst/BI | 41,50 | 36,75–59,75 |
| AI Engineer | AI/ML | 34,00 | 27,75–51,50 |
| Machine Learning Engineer | AI/ML | 42,00 | 37,00–59,50 |
| Data Scientist | AI/ML | 41,00 | 37,25–57,75 |
| Business Analyst | Business Analyst | 27,75 | 23,75–42,75 |
| Project Manager | PM/PO | 41,75 | 36,25–58,75 |
| Product Manager | PM/PO | 45,00 | 41,00–61,25 |
| Product Owner | PM/PO | 35,25 | 30,75–53,75 |
| Software Architect | Tech Lead/Architect | 50,75 | 47,00–61,25 |
| Solution Architect | Tech Lead/Architect | 51,50 | 46,25–70,25 |
| Technical Architect | Tech Lead/Architect | 57,25 | 53,75–68,75 |
| Embedded Systems Developer | Embedded/IoT | 35,00 | 28,25–53,75 |
| Firmware Developer | Embedded/IoT | 27,25 | 21,00–46,00 |
| Security Engineer | Security | 29,25 | 25,75–42,75 |
| Cybersecurity Engineer | Security | 26,75 | 23,50–42,50 |
| Penetration Tester | Security | 39,00 | 31,50–55,75 |
| Systems Engineer | System/Network admin | 28,50 | 24,00–44,25 |
| Technical Support Engineer | IT Support | 22,00 | 20,25–33,25 |
| IT Helpdesk | IT Support | 17,00 | 15,50–25,50 |
| ERP Developer | ERP/SAP | 29,00 | 26,75–41,25 |
| SAP Developer | ERP/SAP | 30,50 | 27,25–41,00 |
| Game Developer | Game | 31,75 | 25,25–46,25 |
| Bridge Software Engineer (BrSE) | BrSE | 40,75 | 34,25–60,00 |
| UI/UX Designer | UI/UX | 24,50 | 21,00–37,25 |
| Database Administrator (DBA) | DBA | 32,50 | 25,75–47,75 |

Lưu ý: dòng Security Engineer ($1.030–1.710, trung vị $1.170) trùng hoàn toàn với dòng Security Test Engineer, nên có thể là lỗi sao chép trong báo cáo gốc. TopDev không có dòng riêng cho IT Manager hay CTO trong bản 2024-2025.

### 3.6 Vị trí × thành phố × kinh nghiệm, Adecco 2026 (S6), khoảng min–max, lương cơ bản G

Nguồn: trang 48–49 của S6. Không có Đà Nẵng. Không có trung vị.

| Vị trí Adecco | Vai trò trong mô hình | HCM 1–5 năm | HCM 5+ năm | HN 1–5 năm | HN 5+ năm |
|---|---|---|---|---|---|
| CIO - CTO | IT Manager/CTO | 180–270 | 270–350 | 140–180 | 180–350 |
| IT Director | IT Manager/CTO | 120–150 | 150–240 | 60–120 | 100–200 |
| IT Manager | IT Manager/CTO | 70–90 | 100–180 | 40–70 | 60–100 |
| Software/Solution/Enterprise Architect | Tech Lead/Architect | 80–130 | 130–180 | 60–100 | 80–160 |
| Cyber Security Manager | Security (quản lý) | – | – | 50–80 | 60–120 |
| Product Owner/Project Manager | PM/PO | 50–80 | 70–130 | 45–80 | 60–120 |
| Business Analyst | Business Analyst | 30–60 | 60–80 | 35–45 | 40–65 |
| Software Engineer | Backend/Frontend/Fullstack/SE | 20–70 | 70–130 | 35–45 | 40–80 |
| QA/QC Engineer | QA/QC | 25–45 | 45–70 | 18–40 | 40–50 |
| System Engineer | System/Network admin | 30–50 | 50–80 | 20–40 | 40–60 |
| DevOps/DevSecOps | DevOps/Cloud | 35–70 | 70–135 | 30–60 | 45–90 |
| Data Engineer | Data Engineer | 35–70 | 70–120 | 25–50 | 50–100 |
| Data Scientist | AI/ML | 80–120 | 120–200 | 30–70 | 60–150 |
| AI Engineer | AI/ML | 40–70 | 70–100 | 25–50 | 50–100 |
| Machine Learning Engineer | AI/ML | 30–70 | 70–100 | 30–60 | 50–100 |
| UI/UX Designer | UI/UX | 35–60 | 60–100 | 20–40 | 40–80 |
| IT Support/Helpdesk | IT Support | 20–40 | 40–60 | 15–35 | 25–45 |
| ERP/SAP Consultant | ERP/SAP | 30–40 | 40–80 | 20–40 | 40–70 |

Số của Adecco cao hơn rõ rệt so với ITviec và TopDev, vì Adecco tuyển cho khách hàng là doanh nghiệp lớn và FDI, hồ sơ thiên về cấp cao (S6 nêu phần lớn người trả lời có hơn 10 năm kinh nghiệm).

### 3.7 Số thứ cấp (chưa kiểm chứng bằng bản gốc)

- TopCV 2025-2026, theo VietnamNet (https://vietnamnet.vn/en/information-technology-remains-top-paying-profession-in-vietnam-2480607.html): Solution Architect trên 5 năm KN có trung vị 56,329; Trưởng/phó phòng IT 53,572; AI Engineer và Data Engineer (không quản lý) trên 38,532 triệu/tháng. Báo không nêu gross hay net.
- TopCV 2025-2026, theo một bài trên chính domain TopCV (https://topcv.vn/tong-hop-cv-tham-khao-cho-lap-trinh-vien, chỉ thấy qua đoạn trích của công cụ tìm kiếm, chưa mở được trang): Full-stack <1 năm 14,4; Full-stack khoảng 5 năm 36,504; DevOps 1–3 năm 24,7; DevOps 2–5 năm 28,0; IT Helpdesk <1 năm 9,67 triệu/tháng.

### 3.8 Ô trống so với 23 vai trò × 3 thành phố × 6 cấp bậc

- **Thành phố:** chỉ TopDev có Đà Nẵng, và chỉ ở mức gộp mọi vai trò. **Không tìm thấy** nguồn sơ cấp nào cho vai trò × thành phố × cấp bậc cùng lúc.
- **Cấp Manager:** chỉ có "Leader/Manager" (TopDev), IT Manager và CTO (ITviec, Adecco).
- Vai trò thiếu theo kinh nghiệm ở ITviec 2025-2026: DevOps/Cloud, AI/ML, Security, System/Network admin, UI/UX, DBA, BrSE. Những vai trò này chỉ có một con số (S2, S4) hoặc khoảng (S6).

---

## 4. Khác biệt so với lương chào tuyển

1. **Gross và net.** TopDev ghi rõ "monthly gross salary before tax", không gồm OT và thưởng, kể cả lương tháng 13 (S4, trang 46). Adecco ghi "base salaries… gross monthly wages" (S6, trang 16). ITviec **không nêu** (S1, S2). Theo TopDev 2023 (S5, trang 28), người lao động đóng 10,5% bảo hiểm bắt buộc (BHXH 8%, BHYT 1,5%, BHTN 1%) trước khi tính thuế TNCN. Vì vậy một tin tuyển dụng ghi "net" sẽ tương ứng với mức gross cao hơn đáng kể. Nếu dữ liệu huấn luyện trộn tin gross và tin net mà không gắn cờ, mô hình sẽ bị nhiễu theo hướng này.
2. **Khảo sát tự khai và tin tuyển dụng.** ITviec đo lương **đang nhận**, tự khai, kèm thiên lệch người trả lời: người dùng ITviec, có cả CxO và sinh viên, mỗi ô ít mẫu. TopDev kết hợp khảo sát với dữ liệu JD; phân phối theo thành phố và tỷ trọng cấp bậc đều đo bằng "ratio of JD" (S4, trang 25–26). Vì vậy TopDev là nguồn **gần nhất với lương chào tuyển**. Adecco là khoảng lương **headhunter** đặt ra, thiên về doanh nghiệp lớn và FDI.
3. **Thống kê khác nhau.** ITviec dùng trung vị; TopDev dùng trung bình (cấp bậc, thành phố) và trung vị (vị trí); Adecco dùng min–max. Trung bình lệch phải nên thường cao hơn trung vị. Khoảng min–max không thể so trực tiếp với một điểm dự đoán.
4. **Đặc thù tin tuyển dụng** (suy luận, không có nguồn định lượng). Tin chào tuyển thường ghi khoảng "từ X đến Y" hoặc "up to Y"; tin ghi "thỏa thuận" bị loại khỏi dữ liệu có lương; tin của công ty trả cao thường là USD. Nếu nhãn của mô hình là điểm giữa khoảng chào tuyển, nhãn có thể cao hơn lương thực nhận ở cấp thấp, và thấp hơn ở cấp rất cao, do nhiều vị trí cao cấp không công khai lương. **Không tìm thấy** nguồn sơ cấp định lượng chênh lệch giữa lương chào tuyển và lương thực nhận ở Việt Nam.
5. **Thời điểm.** TopDev 2024-2025 dùng dữ liệu từ 01/2022 đến 07/2024, ITviec 2025-2026 dùng dữ liệu năm 2025, Adecco 2026 dùng dữ liệu cuối năm 2025. TopDev nhận định lương trung bình gần như không đổi giai đoạn 2023–2024: $1.311 lên $1.317 (S4, trang 25).

---

## 5. Khuyến nghị dùng làm bộ đối chiếu

**Dùng được (ưu tiên giảm dần):**

1. **TopDev 2024-2025, mục 3.1 (cấp bậc × thành phố).** Đây là mốc chính để kiểm tra **hiệu ứng thành phố và cấp bậc**: HCM > HN > ĐN, chênh lệch tăng dần từ Middle trở lên, Fresher và Junior gần như bằng nhau. Bảng này là gross và có gốc từ JD. Nên kiểm tra theo **tỷ lệ** (ví dụ HN/HCM ở mức Senior ≈ 0,87; ĐN/HCM ≈ 0,78) thay vì mức tuyệt đối.
2. **TopDev 2024-2025, mục 3.2 và 3.5.** Dùng để kiểm tra đường cong theo cấp bậc và thứ hạng giữa các vai trò: Architect, SRE, Product Manager và Cloud cao; Tester, UI/UX, Helpdesk thấp. Có thể dùng "Range" làm dải chấp nhận, nhưng nên ghi chú rằng báo cáo không định nghĩa khoảng này.
3. **ITviec 2025-2026, mục 3.3.** Dùng để kiểm tra vai trò × năm kinh nghiệm **ở mức tổng và các ô có vẻ ổn định**: Backend, Fullstack, Mobile, Embedded, BA, Tester, QA-QC, ERP, IT Support, PM. Coi như **không rõ gross hay net** và **không theo thành phố**. Bỏ qua các ô bất thường đã nêu ở mục 3.3.
4. **ITviec 2024-2025, mục 3.4.** Mỗi vai trò có một điểm (trung vị tại số năm KN trung vị). Có ích cho các vai trò ITviec 2025-2026 không có: DevOps, Security, System/Network, DBA, BrSE, AI, Designer.

**Chỉ dùng làm cận trên hoặc tham khảo định tính:**

- **Adecco 2026 (mục 3.6).** Khoảng rất rộng, thiên về doanh nghiệp lớn và FDI, không có trung vị. Chỉ dùng để kiểm tra dự đoán không vượt quá cận trên một cách vô lý, nhất là với CTO, IT Director, Data Scientist.

**Không dùng:**

- Số TopCV thứ cấp (mục 3.7), cho tới khi lấy được bản gốc.
- ITviec 2023-2024 (mục 3.3 cuối, 6 vị trí, số năm KN đáng ngờ).
- Số Robert Walters, Michael Page, Navigos, Talentnet: **không tìm thấy** bảng IT công khai.
- Thu nhập bình quân của Tổng cục Thống kê (không theo nghề IT).
- Các trang tổng hợp, blog, EOR hoặc outsourcing vì không truy được về nguồn gốc.

**Gợi ý vận hành:**

- Khi so sánh với mô hình dự đoán **lương chào tuyển**, ưu tiên TopDev vì có gốc JD và là gross.
- Chấp nhận sai lệch cỡ khoảng p25–p75 hoặc "Range" thay vì đòi khớp điểm.
- Kiểm tra **chiều và độ lớn tương đối** (cấp bậc, thành phố, thứ hạng vai trò) chặt hơn so với mức tuyệt đối.
- Ghi rõ trong báo cáo đánh giá rằng tỷ giá quy đổi là tỷ giá của TopDev (25.000 và 23.300), không phải tỷ giá thị trường tại thời điểm dự đoán.
