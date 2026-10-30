# Khảo sát bốn nguồn tuyển dụng Việt Nam mới — 28/10/2026

Phục vụ [Chọn nguồn dataset Việt Nam mới có thể kiểm chứng](https://github.com/theihoz/ML/issues/3), thuộc [Bản đồ quyết định xây mới ứng dụng CNTT và dự đoán lương](https://github.com/theihoz/ML/issues/2). Đây là kết quả nghiên cứu nguồn, chưa phải quyết định chấp nhận dữ liệu hay kết quả huấn luyện.

## Kết luận để chốt spec

**Chưa chọn được nguồn đáp ứng đầy đủ yêu cầu.** Không nên cam kết số mẫu huấn luyện, độ phủ bảy vai trò hoặc phân tích nhiều năm từ bốn ứng viên này. Có thể tiếp tục thẩm định CareerViet và `salary_csv`, nhưng chưa coi chúng là nguồn chính đã được duyệt.

| Ứng viên | Bằng chứng trực tiếp | Trở ngại quyết định |
| --- | --- | --- |
| [Vincentran/careerviet-job-market](https://huggingface.co/datasets/Vincentran/careerviet-job-market) | 2.682 dòng và URL khác nhau; có lương raw, kinh nghiệm, địa điểm, JD/yêu cầu | Chỉ 87 tin gắn ngành CNTT, không đồng nghĩa 87 tin thuộc vai trò mục tiêu; ngày đăng chưa xác minh; thiếu kỳ lương rõ ràng |
| [jasong03/salary_csv](https://huggingface.co/datasets/jasong03/salary_csv) | 11.617 dòng nhưng 1.174 mã tin TopCV khác nhau; có JD và lương raw | Trùng nhiều, lỗi trường, nhiều ngành; chỉ có hạn nộp; chưa thấy giấy phép/provenance đầy đủ |
| [SonPhatTranDeveloper/IT-Job-Posting](https://github.com/SonPhatTranDeveloper/IT-Job-Posting) | Chỉ đọc README và metadata/cây tệp | Schema công bố không có lương, kinh nghiệm riêng hoặc ngày đăng; một số cột do LLM trích; không tải CSV |
| [NamAnh-dev/Vn-IT-Job](https://github.com/NamAnh-dev/Vn-IT-Job) | Đọc ba CSV trong `data/raw`, tổng 1.310 dòng | Raw không có URL, ngày đăng hoặc JD; nhãn `level` không nhất quán; chưa thấy giấy phép |

Các con số trong bảng là kiểm kê tệp ghim revision ở phần cuối, trừ ứng viên SonPhat chỉ khảo sát metadata. **Số nhãn lương đạt đầy đủ hợp đồng đã được xác minh và chấp nhận trong nghiên cứu này: chưa xác lập**; không được thay bằng số chuỗi có chữ số hoặc khoảng lương tìm thấy.

## Phương pháp, tiêu chuẩn và giới hạn

- Chỉ khảo sát bốn ứng viên được giao. Đọc issue bằng `gh`; dùng API chính chủ Hugging Face/GitHub, README của bên công bố và trang tuyển dụng gốc để đối chiếu. Không mở rộng thêm nguồn sau yêu cầu kết thúc của parent.
- Tải mới hai tệp Hugging Face và ba CSV raw của NamAnh vào thư mục tạm ngoài repository. Đếm bằng CSV reader/PyArrow; không huấn luyện, không chạy notebook/code bên thứ ba, không đọc model hoặc tệp clean. Chỉ báo cáo này được giữ làm đầu ra nghiên cứu trong worktree.
- Không đọc, dùng hoặc tải lại dữ liệu cũ bị cấm: TiniX, VietJobs, Stack Overflow, DataForge, Level, aijobs, public_jobs, joboko, file Vietnam IT Job Posts cũ hay dẫn xuất đã nhận diện. Không đọc dữ liệu trong workspace. Vì không đối chiếu dữ liệu cũ, **chưa chứng minh được tính độc lập với mọi tập cũ**; “ứng viên mới” chỉ có nghĩa mới trong đợt khảo sát này.
- Ô thiếu: `null`, chuỗi rỗng hoặc chuỗi chỉ gồm `nan`/`none`/`null`, không phân biệt hoa thường. Giá trị `0` được giữ nguyên khi kiểm kê, nhưng không xem là lương chào tuyển có nhãn hợp lệ.
- Phân biệt năm loại số lượng: dòng raw; dòng khác nhau hoàn toàn; URL/mã tin khác nhau; tập CNTT/vai trò đã xác minh; mẫu có nhãn lương đạt hợp đồng. Không cộng số tin giữa các nguồn thành tổng tin độc lập khi chưa đối chiếu trùng chéo.
- Lương có nhãn cần hai đầu hoặc mức cố định, tiền tệ và kỳ trả rõ ràng. Chuỗi “triệu” không tự chứng minh VND/tháng; USD không tự đổi thành VND. Khoảng chỉ có một đầu, thỏa thuận, cạnh tranh và yêu cầu đăng nhập không phải nhãn chính xác. Giữ raw để thẩm định sau.
- Chưa đánh giá đầy đủ toàn bộ JD để phân nhóm Backend, Frontend, Fullstack, Mobile, Data/ML, DevOps, QA Automation. Nhãn ngành CNTT chỉ là bộ lọc ứng viên; kỹ năng văn phòng trong JD không đủ để nhận diện nghề CNTT.
- Ngày phát hành repo, ngày commit, ngày tải, ngày cập nhật tin và hạn nộp không được dùng thay ngày đăng. Không suy ra dữ liệu nhiều năm từ deadline hay năm của repository.

## 1. CareerViet trên Hugging Face

**Nguồn công bố:** tài khoản Vincentran, không phải bằng chứng CareerViet tự phát hành dataset. [API metadata](https://huggingface.co/api/datasets/Vincentran/careerviet-job-market) trả `gated=false`, tạo ngày 07/06/2026, cập nhật ngày 07/06/2026 và revision `7ba7998ed5bad98b3a51beacd94f5a26ae026bf0`. [README ghim revision](https://huggingface.co/datasets/Vincentran/careerviet-job-market/blob/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/README.md) chỉ có metadata `license: mit`; chưa có mô tả phương pháp thu thập, quyền từ nguồn upstream hay giấy phép riêng cho nội dung tin. Đây là ghi nhận metadata, chưa xác nhận quyền phân phối lại JD.

**Schema thực đọc:** `job_title`, `company`, `salary`, `location`, `posted_date`, `job_url`, `benefits`, `job_description`, `requirements`, `market_skill`, `industry`, `employment_type`, `experience`, `job_level`, `deadline`, `updated_date`, `degree`, `working_time`, `salary_detail`. Không dùng `market_skill` vì nguồn gốc/cách tạo chưa được mô tả. Nguồn kiểm kê: [jobs.parquet ghim revision](https://huggingface.co/datasets/Vincentran/careerviet-job-market/resolve/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/jobs.parquet).

| Chỉ tiêu trên toàn tệp | Kết quả |
| --- | ---: |
| Dòng raw / dòng khác nhau hoàn toàn | 2.682 / 2.682 |
| URL / mã tin CareerViet khác nhau | 2.682 / 2.682 |
| Thiếu công ty / JD / kinh nghiệm | 36 / 15 / 230 |
| Có địa điểm / yêu cầu công việc / `posted_date` | 2.682 / 2.682 / 2.682 |
| Lương “Cạnh tranh” | 1.389 |
| Lương có chữ số | 1.293 |
| Khoảng hai đầu nhận diện được kèm VND hoặc USD | 1.238 |
| Trong 1.238 dòng trên, đủ thêm kinh nghiệm, JD, yêu cầu, địa điểm, trường ngày | 1.148 |

Các khoảng hai đầu ở đây chỉ là **ứng viên cú pháp**, chưa là nhãn đã duyệt: 0 chuỗi `salary` ghi rõ kỳ tháng/năm theo phép dò nêu dưới. Trong 1.293 dòng có chữ số, 1.257 ghi VND và 36 ghi USD. Không dùng 1.148 làm số mẫu huấn luyện. Các phép tính trên dựa vào [tệp gốc](https://huggingface.co/datasets/Vincentran/careerviet-job-market/resolve/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/jobs.parquet).

**CNTT khác toàn bộ thị trường:** lọc `industry` chứa chuỗi `CNTT` được 87 URL, trong đó 80 có `CNTT - Phần mềm`. Trong 87 tin: 79 có kinh nghiệm; cả 87 có JD/yêu cầu/địa điểm; 17 có lương chứa chữ số, 14 có khoảng hai đầu kèm tiền tệ, 13 trong 14 có thêm kinh nghiệm. Tuy nhiên tập này chứa cả kế toán, sales và chăm sóc khách hàng. Ví dụ `Revenue & AR Accountant` được gắn cả ngành phần mềm; không thể gọi 87 hoặc 13 là số tin/mẫu của bảy vai trò mục tiêu. [Dữ liệu kiểm kê](https://huggingface.co/datasets/Vincentran/careerviet-job-market/resolve/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/jobs.parquet).

**Ngày có tên `posted_date` chưa chứng minh ngày đăng:** parse toàn bộ trường này được 08/05–07/06/2026, không lỗi định dạng. Toàn bộ 2.579 dòng có `updated_date` đều trùng ngày với `posted_date` sau đổi dấu phân cách; cả 87 tin gắn CNTT cũng vậy. Deadline trải 24/07/2025–31/12/2026, có 55 dòng deadline trước `posted_date`; không coi đó là độ phủ nhiều năm. [Tệp snapshot](https://huggingface.co/datasets/Vincentran/careerviet-job-market/resolve/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/jobs.parquet).

Đối chiếu [tin Technical Leader trên CareerViet](https://careerviet.vn/vi/tim-viec-lam/technical-leader-nodejs-golang-php.35C761C0.html): bản trang do web tool trả về ghi **Ngày cập nhật 14/07/2026**, lương 4.000–7.000 USD, kinh nghiệm 5–15 năm và hạn nộp riêng. Snapshot dataset ghi `posted_date=04-06-2026`, `updated_date=04/06/2026`. Trang do web tool cung cấp đã được crawl khoảng hai tháng trước đợt khảo sát; nó không phải ảnh chụp tại ngày snapshot và không đủ khôi phục ngày đăng đầu tiên. Lần thử HTTP trực tiếp không trả về các nội dung lương/ngày tương ứng hoặc JSON-LD cần kiểm tra, nên cũng không xác nhận được `datePosted` hay kỳ lương. Tin Senior Data Engineer bị timeout khi đối chiếu; không suy diễn thêm.

**Đánh giá:** ứng viên để thử hợp đồng nhập liệu và tiếp tục kiểm tra provenance/ngày/kỳ lương. Chưa phù hợp làm nguồn chính cho huấn luyện hay xu hướng thời gian.

## 2. `jasong03/salary_csv`

[Metadata chính chủ](https://huggingface.co/api/datasets/jasong03/salary_csv) trả `gated=false`, revision `100926d43e363f4c109024a6f58b975157caa933`, tạo/cập nhật ngày 02/12/2024. Danh sách tệp chỉ có `.gitattributes` và `output.csv`, `cardData=null`: chưa thấy giấy phép, dataset card giải thích nguồn hay phương pháp lấy dữ liệu. Cả 11.617 URL trong tệp trỏ `www.topcv.vn`, nhưng URL không chứng minh quyền phân phối nội dung.

Schema: `job_title`, `company`, `salary`, `year_of_experience`, `job_city`, `due_date`, `jd`, `url`. [Tải output.csv ghim revision](https://huggingface.co/datasets/jasong03/salary_csv/resolve/100926d43e363f4c109024a6f58b975157caa933/output.csv).

| Chỉ tiêu thực đếm | Kết quả |
| --- | ---: |
| Dòng raw / dòng khác nhau hoàn toàn | 11.617 / 11.053 |
| URL đầy đủ khác nhau | 11.041 |
| URL bỏ query/fragment khác nhau | 1.179 |
| Mã tin TopCV khác nhau, gồm URL `/brand/...-j<ID>.html` | 1.174 |
| Thiếu title / company / salary | 978 / 978 / 624 |
| Thiếu experience / location / JD / deadline | 3.053 / 917 / 978 / 1.047 |
| Lương thỏa thuận / có chữ số | 3.033 / 7.612 |
| Khoảng hai đầu đúng mẫu cú pháp khảo sát | 6.437 dòng / 557 mã tin |
| Khoảng hai đầu, đủ title/company/experience/location/JD | 5.625 dòng / 435 mã tin |

Nguồn tất cả phép đếm: [CSV đã tải](https://huggingface.co/datasets/jasong03/salary_csv/resolve/100926d43e363f4c109024a6f58b975157caa933/output.csv). Dùng mã tin thay URL tracking tránh phóng đại số mẫu; chưa coi các mã này là các vị trí tuyển dụng độc lập sau đối chiếu công ty/JD.

**Lỗi và đơn vị:** 304 dòng có giá trị `salary` đúng bằng Hà Nội/Hồ Chí Minh/Đà Nẵng; có trường bị lệch hoặc lỗi thu thập. Trong 6.437 khoảng hai đầu, chỉ 210 dòng ghi tiền tệ `USD`; các dòng còn lại theo mẫu này chỉ ghi “triệu”. Toàn cột salary không có kỳ trả rõ ràng theo phép dò. Có một mã tin mang nhiều salary khác nhau không rỗng, cần xem lại raw trước khi chọn bản ghi. Không điền lương, tiền tệ hoặc kỳ lương bằng phỏng đoán. [Tệp kiểm kê](https://huggingface.co/datasets/jasong03/salary_csv/resolve/100926d43e363f4c109024a6f58b975157caa933/output.csv).

**Thời gian và CNTT:** `due_date` ghi rõ “Hạn nộp hồ sơ”, parse được 02/11/2024–01/10/2025; không có cột ngày đăng. Không chuyển timestamp trong query tracking thành ngày đăng. Dữ liệu có cả sales, quản lý chuỗi cửa hàng và tuyển sinh; **chưa xác minh số tin CNTT/vai trò mục tiêu hoặc số nhãn đạt hợp đồng**. Lần mở tin gốc TopCV mẫu không truy cập được qua web tool. Không thể suy ra nhiều năm tuyển dụng từ deadline. [Schema và raw](https://huggingface.co/datasets/jasong03/salary_csv/resolve/100926d43e363f4c109024a6f58b975157caa933/output.csv).

**Đánh giá:** có tiềm năng làm nguồn phụ cho kiểm tra JD/lương raw sau khi giải quyết quyền sử dụng, lỗi và tính độc lập với nguồn cũ. Hiện không đáp ứng ngày đăng hoặc nhãn lương chuẩn đầy đủ.

## 3. `SonPhatTranDeveloper/IT-Job-Posting`

[Commit khảo sát](https://github.com/SonPhatTranDeveloper/IT-Job-Posting/commit/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac) là `6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac`, ngày 08/07/2025. [Cây tệp API](https://api.github.com/repos/SonPhatTranDeveloper/IT-Job-Posting/git/trees/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac?recursive=1) có README, HTML phân tích và `job_descriptions.csv` 11.087.006 byte; metadata license trả null, không có LICENSE trong cây tệp đã đọc.

[README ghim commit](https://github.com/SonPhatTranDeveloper/IT-Job-Posting/blob/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac/README.md) nói có 3.101 tin từ LinkedIn, ITViec, TopCV, chỉ dùng cho giáo dục. Schema công bố: `title`, `company`, `company_image_url`, `location`, `description`, `site`, `job_url`, `it_role_type`, `main_programming_languages`, `key_technologies`, `city`. README xác nhận ba cột cuối được trích bằng LLM; cách tạo `it_role_type` chưa được giải thích. Không dùng bất kỳ cột nhãn đó.

**Không tải/đọc CSV**, do schema công bố đã thiếu các trường cốt lõi và cần tránh đồng nhất nhầm với file Vietnam IT Job Posts cũ bị cấm. Không kết luận đây chính là tập cũ khi chưa có bằng chứng. Link tệp để parent truy xuất metadata nếu cần: [job_descriptions.csv tại commit](https://github.com/SonPhatTranDeveloper/IT-Job-Posting/blob/6af3d7cb7fbd05dcff7962fd40f85a20129fc9ac/job_descriptions.csv); đây không phải khuyến nghị tải.

**Chưa xác minh:** số dòng thực, tin duy nhất, ngày đăng, lương hoặc kinh nghiệm có nằm trong description không, phạm vi thời gian và tính độc lập với dữ liệu cũ. Con số 3.101 chỉ là tuyên bố của tác giả. Không có SHA-256 tải mới vì không tải tệp. **Loại khỏi vòng chọn hiện tại.**

## 4. `NamAnh-dev/Vn-IT-Job`

[README ghim commit](https://github.com/NamAnh-dev/Vn-IT-Job/blob/98a95291bd19e32ca9360ad61e6e3a7df2256e39/README.md) tuyên bố tự cào TopCV/ITViec/TopDev, 1.140 tin sau làm sạch và 301 tin dùng phân tích lương. Đây là mô tả của tác giả, **không phải số đã kiểm chứng lại từ raw**. Revision khảo sát `98a95291bd19e32ca9360ad61e6e3a7df2256e39`, commit ngày 14/09/2026. [Metadata](https://api.github.com/repos/NamAnh-dev/Vn-IT-Job) trả license null; [cây tệp ghim revision](https://api.github.com/repos/NamAnh-dev/Vn-IT-Job/git/trees/98a95291bd19e32ca9360ad61e6e3a7df2256e39?recursive=1) không có LICENSE.

Chỉ đọc ba tệp trong `data/raw`; tất cả có schema `title, company, salary, location, skills, level, source`.

| Tệp raw | Dòng | Dòng khác nhau hoàn toàn | Khóa proxy `(title, company, location)` khác nhau | Khoảng lương hai đầu theo mẫu |
| --- | ---: | ---: | ---: | ---: |
| [ITViec_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/ITViec_jobs.csv) | 529 | 458 | 421 | 0 |
| [TopCV_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopCV_jobs.csv) | 616 | 574 | 564 | 264 dòng / 247 dòng khác nhau hoàn toàn |
| [TopDEV_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopDEV_jobs.csv) | 165 | 164 | 164 | 0 |

Proxy không phải mã tin: có thể gộp nhầm tin khác ngày hoặc tách cùng tin khác địa điểm. Không gọi tổng proxy là tin duy nhất đã xác minh; chưa kiểm tra trùng chéo nguồn.

ITViec có toàn bộ salary bằng `0`; TopDev có 139 giá trị yêu cầu đăng nhập và 26 ô thiếu, thiếu location ở 38 dòng. TopCV có 289 dòng thỏa thuận. `level` của TopCV có thể là số năm kinh nghiệm, của TopDev có thể là seniority; không thay thế lẫn nhau. Kỹ năng raw có dạng danh sách hoặc chuỗi đã trích, nhưng chưa xác minh cách tạo, nên chưa duyệt làm nhãn kỹ năng. Các số này được tính từ [ITViec raw](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/ITViec_jobs.csv), [TopCV raw](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopCV_jobs.csv), [TopDev raw](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopDEV_jobs.csv).

Không tệp raw nào có URL tin, JD, cột ngày đăng hoặc kỳ lương riêng. Vì vậy không thể kiểm tra ngược từng tin hoặc dùng raw này đáp ứng hợp đồng đủ trường. Không đọc clean, notebook, code, model, taxonomy hay nhãn suy diễn. Số tin thuộc vai trò mục tiêu và số nhãn đủ điều kiện **chưa xác minh**. **Không chọn** làm nguồn chính/phụ ở trạng thái hiện tại.

## Khả năng tái lập phép đếm

1. Chỉ dùng các URL ghim revision ở bảng hash bên dưới; đối chiếu SHA-256 trước khi đọc. `csv.DictReader` với UTF-8 BOM; Parquet đọc bằng PyArrow 26.0.0. Các parser không tự điền ô thiếu.
2. Dòng khác nhau hoàn toàn là tập tuple toàn bộ cột. URL chuẩn bỏ query và fragment, không tự gộp các path khác nhau. Với TopCV, lấy ID bằng regex `(?:/|-j)(\d+)\.html`; đọc được ID ở cả 11.617 dòng. Có 1.179 path nhưng 1.174 ID, nên báo cả hai.
3. Khoảng hai đầu CareerViet khớp toàn chuỗi: `Lương:\s*\d+(?:[.,]\d+)?\s*(?:Tr)?\s*-\s*\d+(?:[.,]\d+)?\s*(?:Tr)?\s*(?:VND|USD)`.
4. Khoảng hai đầu TopCV khớp toàn chuỗi, không phân biệt hoa thường: `\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?\s*(triệu|USD)`. Đây là bộ dò cú pháp hẹp, chưa phải parser lương hoàn chỉnh; không tự giải nghĩa dấu chấm/phẩy hay gross/net.
5. “Không có kỳ rõ trong salary” là kết quả dò `tháng|month|/mo|/năm|year` ở cột salary, không phải khẳng định toàn bộ JD đều không nhắc kỳ. Chưa duyệt tay JD toàn bộ hoặc quy ước upstream, nên chưa tính số nhãn lương cuối cùng.
6. Parse CareerViet `posted_date` theo `%d-%m-%Y`, `updated_date`/`deadline` theo `%d/%m/%Y`; TopCV parse phần sau `Hạn nộp hồ sơ:`. Không suy diễn ngày đăng từ các trường khác.

## Manifest tải mới

Mỗi tệp được tải trực tiếp, không qua bản clean/convert của dự án khác; ngày tải 28/10/2026. Không đưa các tệp dữ liệu vào commit báo cáo. SHA-256 dưới đây là hash của byte thực tải, không phải ETag hoặc Git blob SHA.

| Tệp và link tải ghim revision | Byte | SHA-256 |
| --- | ---: | --- |
| [CareerViet jobs.parquet](https://huggingface.co/datasets/Vincentran/careerviet-job-market/resolve/7ba7998ed5bad98b3a51beacd94f5a26ae026bf0/jobs.parquet) | 3.218.931 | `1a6de542b13209542e16ea69ccbf0e59cbda580dd2ec212e9ace98f97ed79852` |
| [jasong03 output.csv](https://huggingface.co/datasets/jasong03/salary_csv/resolve/100926d43e363f4c109024a6f58b975157caa933/output.csv) | 32.004.040 | `099ae5a58fa3386514359f95f1d7fa85b0fad40fd446f3b62655dab17f21b36d` |
| [NamAnh ITViec_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/ITViec_jobs.csv) | 101.182 | `fff109467e1de78bbecacb1d1adedb5fa93c32f926a223031f2441b2020993dc` |
| [NamAnh TopCV_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopCV_jobs.csv) | 106.317 | `797fbf063eb2353dca746f78393e967e4f2bd385eefda87d2e702d642b652d79` |
| [NamAnh TopDEV_jobs.csv](https://raw.githubusercontent.com/NamAnh-dev/Vn-IT-Job/98a95291bd19e32ca9360ad61e6e3a7df2256e39/data/raw/TopDEV_jobs.csv) | 26.190 | `68a1055cc0d57249630254ce2182146ac17c02a593549f0c740fec1b44c27616` |

## Việc tiếp theo và điều kiện mở khóa

1. **Giữ quyết định nguồn ở trạng thái chưa chốt.** Spec có thể chốt schema, parser, kiểm toán và hành vi khi thiếu dữ liệu; số lượng mẫu/độ phủ và tính năng nhiều năm phải phụ thuộc nguồn được duyệt.
2. Với CareerViet: hỏi bên phát hành về cách lấy `posted_date`, giấy phép nội dung upstream, kỳ lương và provenance của `market_skill`; kiểm tra ngày gốc bằng bằng chứng có thể lưu. Nếu thực chất là ngày cập nhật thì giữ đúng tên và không dựng biểu đồ ngày đăng.
3. Với `salary_csv`: xác nhận quyền dùng/phân phối, tính độc lập với nguồn cũ; duyệt 1.174 mã thay 11.617 dòng; cách ly dòng lệch trường và xung đột; phân loại nghề từ raw title/JD. Chỉ bổ sung ngày đăng và kỳ lương từ nguồn có thể chứng minh, không nội suy từ deadline.
4. Nếu không lấy được bằng chứng còn thiếu: cần đợt thu thập mới được nguồn cho phép, lưu URL/ID, thời điểm thu thập, ngày đăng thật nếu có, raw salary, tiền tệ/kỳ và JD/yêu cầu. Chưa thực hiện thu thập này trong báo cáo và không cam kết số mẫu trước khi đo.
5. Sau khi qua các bước trên mới thống kê số tin duy nhất, số mẫu lương hợp lệ theo từng vai trò/địa điểm và kỳ quan sát; kiểm tra trùng chéo nguồn trước chia train/test. Không dùng kết quả/model/nhãn LLM của các repo ứng viên.

**Facts còn mở:** quyền phân phối lại; độc lập với tập cũ; ngày đăng thật; kỳ và gross/net của lương; độ phủ bảy vai trò; số mẫu cuối sau khử trùng/kiểm tra lỗi; thời gian đủ so sánh; nguồn gốc kỹ năng đã trích. Không có bằng chứng trong đợt này để lấp các khoảng trống đó.
