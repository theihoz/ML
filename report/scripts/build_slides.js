// Slide thuyết trình học thuật: nền tối, mỗi slide một ý, dựng dần; lời thuyết minh trong Speaker Notes.
// Chạy: NODE_PATH=<node_modules> node report/scripts/build_slides.js <repo> <slides.json> <out.pptx> <apply_theme.js>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const [ROOT, DATA, OUT, THEME_SCRIPT] = process.argv.slice(2);
const D = JSON.parse(fs.readFileSync(DATA, "utf8"));
const FIG = path.join(ROOT, "report/figures");
const DIA = path.join(ROOT, "report/diagrams");
const { applyTheme } = require(THEME_SCRIPT);

const BG = "111318";
const CARD = "1C1F26";
const TEXT = "F5F5F5";
const MUTED = "9CA3AF";
const ACCENT = "4ADE80";
const WARN = "FBBF24";
const GRID = "2A2E36";
const THEME = {
  name: "Luong CNTT Dark",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: BG, lt1: TEXT, dk2: CARD, lt2: MUTED,
    accent1: ACCENT, accent2: WARN, accent3: "60A5FA", accent4: "F87171", accent5: "A78BFA", accent6: "2DD4BF",
    hlink: "60A5FA", folHlink: "A78BFA",
  },
};
const fmt = (v, d = 1) => Number(v).toFixed(d).replace(".", ",");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333" × 7,5"
pres.title = "Phân tích thị trường việc làm CNTT và dự đoán lương lập trình viên";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const W = 13.333;
const number = { x: 12.2, y: 6.95, w: 0.8, h: 0.35, color: MUTED, fontSize: 11, align: "right" };

pres.defineSlideMaster({
  title: "Statement",
  background: { color: BG },
  slideNumber: number,
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 1.7, w: 11.5, h: 2.6, fontSize: 44, bold: true, color: TEXT, valign: "bottom", fontFace: "Arial" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 4.5, w: 11.5, h: 1.8, fontSize: 22, color: MUTED, valign: "top", fontFace: "Calibri" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Content",
  background: { color: BG },
  slideNumber: number,
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.4, w: 11.9, h: 1.0, fontSize: 32, bold: true, color: TEXT, valign: "middle", fontFace: "Arial" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Section",
  background: { color: BG },
  slideNumber: number,
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.9, y: 2.3, w: 11.5, h: 0.6, fontSize: 18, color: MUTED, fontFace: "Calibri" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.9, w: 11.5, h: 1.6, fontSize: 54, bold: true, color: ACCENT, valign: "top", fontFace: "Arial" }, text: "" } },
  ],
});

// ---------- helpers ----------
const runs = (parts) => parts.map((p) => (typeof p === "string" ? { text: p } : { text: p.a, options: { color: p.c || ACCENT } }));
let section = "";
function slide(master, sectionTitle) {
  if (sectionTitle && sectionTitle !== section) {
    pres.addSection({ title: sectionTitle });
    section = sectionTitle;
  }
  return pres.addSlide({ masterName: master, sectionTitle: section });
}
function statement(sectionTitle, title, body, notes) {
  const s = slide("Statement", sectionTitle);
  s.addText(runs(title), { placeholder: "title" });
  if (body) s.addText(runs(body), { placeholder: "body" });
  s.addNotes(notes);
  return s;
}
function content(sectionTitle, title, notes) {
  const s = slide("Content", sectionTitle);
  s.addText(runs(title), { placeholder: "title" });
  s.addNotes(notes);
  return s;
}
function divider(sectionTitle, kicker, title, notes) {
  const s = slide("Section", sectionTitle);
  s.addText(kicker, { placeholder: "kicker" });
  s.addText(title, { placeholder: "title" });
  s.addNotes(notes);
  return s;
}
function stat(s, x, y, w, value, label, color = ACCENT, size = 60) {
  s.addText(value, { x, y, w, h: 1.2, fontSize: size, bold: true, color, fontFace: "Arial", margin: 0, isTextBox: true, objectName: `stat ${label}` });
  s.addText(label, { x, y: y + 1.25, w, h: 0.9, fontSize: 16, color: MUTED, margin: 0, valign: "top", isTextBox: true });
}
function card(s, x, y, w, h, title, body, color = TEXT) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: CARD }, line: { color: CARD }, rectRadius: 0.12, objectName: `card ${title}` });
  s.addText(title, { x: x + 0.3, y: y + 0.25, w: w - 0.6, h: 0.6, fontSize: 20, bold: true, color, margin: 0, valign: "top", isTextBox: true });
  s.addText(body, { x: x + 0.3, y: y + 0.9, w: w - 0.6, h: h - 1.1, fontSize: 16, color: MUTED, margin: 0, valign: "top", isTextBox: true });
}
function quote(s, x, y, w, text, note) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.8, fill: { color: CARD }, line: { color: CARD }, rectRadius: 0.08 });
  s.addText(text, { x: x + 0.25, y, w: w * 0.62, h: 0.8, fontSize: 18, color: WARN, fontFace: "Courier New", valign: "middle", margin: 0, isTextBox: true });
  s.addText(note, { x: x + w * 0.62 + 0.3, y, w: w * 0.38 - 0.5, h: 0.8, fontSize: 15, color: MUTED, valign: "middle", margin: 0, isTextBox: true });
}
function chartOptions(extra = {}) {
  return {
    showLegend: false,
    showValue: true,
    dataLabelColor: TEXT,
    dataLabelFontSize: 13,
    dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: "D1D5DB",
    catAxisLabelFontSize: 14,
    catAxisLabelFontFace: "+mn-lt",
    valAxisLabelColor: MUTED,
    valAxisLabelFontSize: 12,
    valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: GRID, size: 0.75 },
    catGridLine: { style: "none" },
    catAxisLineShow: false,
    valAxisLineShow: false,
    plotArea: { fill: { color: BG } },
    chartArea: { fill: { color: BG } },
    ...extra,
  };
}
function framedImage(s, file, x, y, maxW, maxH, alt) {
  const b = fs.readFileSync(file);
  const ratio = b.readUInt32BE(16) / b.readUInt32BE(20);
  let w = maxW;
  let h = w / ratio;
  if (h > maxH) { h = maxH; w = h * ratio; }
  const left = x + (maxW - w) / 2;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: left - 0.15, y: y - 0.15, w: w + 0.3, h: h + 0.3, fill: { color: "FFFFFF" }, line: { color: "FFFFFF" }, rectRadius: 0.08 });
  s.addImage({ path: file, x: left, y, w, h, altText: alt });
}

const M = D.models;
const B = D.bootstrap;
const lv = (level) => D.calibration.levels.find((row) => row.level === level);

// ================================ MỞ ĐẦU ================================
{
  const s = slide("Statement", "Mở đầu");
  s.addText("TIỂU LUẬN · LẬP TRÌNH PYTHON · TRƯỜNG ĐẠI HỌC GIA ĐỊNH", { x: 0.9, y: 0.8, w: 11.5, h: 0.5, fontSize: 14, color: MUTED, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText(runs(["Lương lập trình viên Việt Nam: ", { a: "dự đoán được không?" }]), { placeholder: "title" });
  s.addText("Phân tích xu hướng thị trường việc làm ngành CNTT và dự đoán mức lương lập trình viên", { placeholder: "body" });
  s.addText("GVHD: ThS. Lý Ngọc Hưng   ·   Nhóm: ……………………   ·   Lớp học phần 020100138002", { x: 0.9, y: 6.4, w: 11.5, h: 0.45, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
  s.addNotes("Kính chào thầy và các bạn. Nhóm em trình bày đề tài phân tích xu hướng thị trường việc làm ngành CNTT và dự đoán mức lương lập trình viên. Câu hỏi xuyên suốt bài: từ các tin tuyển dụng công khai, liệu có dự đoán được một lập trình viên nên được trả bao nhiêu, và nên học gì để tăng thu nhập hay không.");
}
statement("Mở đầu",
  ["Bạn có ", { a: "3 năm" }, " kinh nghiệm, biết ", { a: "Python" }, " và ", { a: "SQL" }],
  ["Bạn nên được trả bao nhiêu? Nên học gì tiếp theo?"],
  "Hãy bắt đầu bằng một người dùng cụ thể: một kỹ sư dữ liệu có 3 năm kinh nghiệm, biết Python và SQL. Họ có hai câu hỏi rất thực tế: mức lương thị trường của mình là bao nhiêu, và nên đầu tư học kỹ năng gì để tăng lương. Đây chính là user story của đề tài: người dùng nhập vai trò, kinh nghiệm, kỹ năng; hệ thống dựa vào mô hình đã huấn luyện sẵn để dự đoán lương và tư vấn kỹ năng.");

// ============================ BẢN THĂM DÒ ============================
{
  const s = statement("Vấn đề ban đầu", ["Phiên bản đầu tiên học từ ", { a: "14", c: WARN }, " tin tuyển dụng"],
    ["Mỗi nhãn lương đều được duyệt tay — chính xác, nhưng quá ít."],
    "Phiên bản đầu tiên của dự án rất thận trọng: mỗi nhãn lương phải được duyệt tay, chuỗi lương nào thiếu đơn vị hay kỳ trả đều bị loại. Kết quả là chỉ còn 14 tin của 11 công ty. Từng nhãn rất chính xác, nhưng 14 mẫu thì quá ít cho bất kỳ mô hình nào.");
}
{
  const s = content("Vấn đề ban đầu", ["Kiểm tra trên ", { a: "2 tin", c: WARN }, " thì không biết mô hình tốt hay xấu"],
    "Với 14 tin, nhóm chia 10 tin huấn luyện, 2 tin kiểm định, 2 tin kiểm tra. Sai số trên 2 tin kiểm tra là 21,98 triệu mỗi tháng. Con số này gần như vô nghĩa: chỉ cần đổi một tin là kết quả thay đổi hoàn toàn. Không tin nào có số năm kinh nghiệm nên mô hình không học được ảnh hưởng của kinh nghiệm, và dashboard chỉ vẽ được 2 vai trò. Phiên bản này không đáp ứng được đề bài.");
  stat(s, 0.9, 2.0, 3.6, "10/2/2", "tin train / validation / test", WARN);
  stat(s, 4.85, 2.0, 3.6, "21,98", "triệu sai số trung bình trên tập test", WARN);
  stat(s, 8.8, 2.0, 3.6, "0", "tin có số năm kinh nghiệm", WARN);
  s.addText("Không học được kinh nghiệm, không tư vấn được kỹ năng, dashboard chỉ có 2 vai trò.", { x: 0.9, y: 5.2, w: 11.5, h: 0.8, fontSize: 20, color: TEXT, margin: 0, isTextBox: true });
}
statement("Vấn đề ban đầu", ["Quyết định: dùng ", { a: "toàn bộ" }, " dữ liệu sẵn có, với quy tắc minh bạch"],
  ["Rồi bù lại bằng cách đo sai số thật nghiêm ngặt."],
  "Nhóm đổi chiến lược. Thay vì ít dữ liệu nhưng duyệt tay, nhóm dùng toàn bộ tin có lương trong ba bộ dữ liệu sẵn có, chuẩn hóa bằng các quy tắc được ghi rõ giả định. Một nhãn lệch vài triệu do quy tắc ảnh hưởng rất ít khi mô hình học trên hàng nghìn tin. Đổi lại, nhóm phải đo sai số nghiêm ngặt: chia theo công ty, bootstrap, hiệu chuẩn và công bằng — phần cuối bài sẽ trình bày.");

// ============================== DỮ LIỆU ==============================
divider("Dữ liệu", "Phần 1", "Dữ liệu thô rất bẩn",
  "Phần đầu tiên là dữ liệu. Ba bộ dữ liệu công khai trên Kaggle có tổng cộng hơn mười nghìn dòng, nhưng không thể đưa thẳng vào mô hình.");
{
  const s = content("Dữ liệu", ["Ba nguồn công khai, ", { a: "10.385" }, " dòng thô"],
    "Ba nguồn gồm: bộ TopCV 2026 với 1.550 tin, chỉ có tiêu đề không có mô tả; bộ Vietnam IT Job Posts với 6.779 tin từ năm nền tảng VietnamWorks, TopCV, ITviec, CareerViet, YBox, có danh sách kỹ năng; và bộ CareerBuilder 2023 với 2.056 tin, có mô tả dạng HTML nhưng phần lớn ngoài ngành CNTT.");
  card(s, 0.7, 1.8, 3.8, 3.6, "TopCV 2026", "1.550 tin\nChỉ có tiêu đề, không có mô tả công việc\nGiấy phép CC BY 4.0");
  card(s, 4.77, 1.8, 3.8, 3.6, "Vietnam IT Job Posts", "6.779 tin, 5 nền tảng\nCó cấp bậc, danh sách kỹ năng\nGiấy phép MIT");
  card(s, 8.83, 1.8, 3.8, 3.6, "CareerBuilder 2023", "2.056 tin\nMô tả dạng HTML; chỉ 194 tin thuộc CNTT\nGiấy phép CC0");
}
{
  const s = content("Dữ liệu", ["Lương được ghi theo ", { a: "32" }, " định dạng khác nhau"],
    "Ngay cột lương đã có 32 kiểu định dạng: khoảng hai đầu, chỉ có cận trên như 'Tới 30 triệu', đơn vị đô la, lương theo năm, và cả lỗi chính tả 'triẹu' xuất hiện ở 264 dòng. Bộ chuẩn hóa phải nhận diện số, đơn vị, kỳ trả rồi quy hết về triệu đồng mỗi tháng.");
  const rows = [
    ["\"15 - 25 triệu\"", "→ 20 triệu (trung điểm)"],
    ["\"Tới 30 triệu\"", "→ 21–30, trung điểm 25,5"],
    ["\"$ 1,000-1,500 /tháng\"", "→ 26–39 triệu (tỷ giá 2026)"],
    ["\"240tr-360tr ₫/năm\"", "→ 20–30 triệu/tháng"],
    ["\"8 triẹu - 10 triẹu/tháng\"", "→ sửa lỗi chính tả, 264 dòng"],
  ];
  rows.forEach(([q, n], i) => quote(s, 0.7, 1.75 + i * 0.98, 11.9, q, n));
}
{
  const s = content("Dữ liệu", [{ a: "36%", c: WARN }, " số dòng không ghi lương"],
    "36% số dòng, tức 3.736 dòng, ghi 'Thỏa thuận', 'Thương lượng' hay 'Cạnh tranh'. Những tin này không thể làm nhãn lương. Vấn đề nặng nhất ở TP. Hồ Chí Minh: chỉ 29% tin đọc được lương, so với 73% ở Hà Nội. Đây là hạn chế không sửa được bằng kỹ thuật, nên bộ dữ liệu lệch về Hà Nội và nhóm phải nói rõ điều đó khi so sánh khu vực.");
  stat(s, 0.9, 1.9, 3.6, "3.736", "dòng \"Thỏa thuận / Thương lượng\"", WARN);
  stat(s, 4.85, 1.9, 3.6, "73%", "tin Hà Nội đọc được lương");
  stat(s, 8.8, 1.9, 3.6, "29%", "tin TP. Hồ Chí Minh đọc được lương", WARN);
  s.addText("→ Dữ liệu lệch về Hà Nội. Không sửa được bằng kỹ thuật, phải ghi rõ khi so sánh khu vực.", { x: 0.9, y: 5.2, w: 11.5, h: 0.8, fontSize: 20, color: TEXT, margin: 0, isTextBox: true });
}
statement("Dữ liệu", [{ a: "\"1 triệu – 40 triệu\"", c: WARN }, " không phải là mức lương"],
  ["111 tin ghi đúng khoảng này — giá trị mặc định của biểu mẫu đăng tin. Quy tắc: loại khi cận trên gấp hơn 3 lần cận dưới → loại 322 dòng."],
  "Một ví dụ dữ liệu giả: 111 tin ghi lương '1 triệu đến 40 triệu'. Trung điểm 20,5 triệu là con số vô nghĩa — đây là giá trị mặc định của biểu mẫu đăng tin khi nhà tuyển dụng không muốn công bố lương. Thay vì liệt kê từng chuỗi, nhóm dùng một quy tắc chung: cận trên gấp hơn 3 lần cận dưới thì loại. Quy tắc này loại 322 dòng, bắt được cả những dạng chưa gặp.");
{
  const s = content("Dữ liệu", ["Ngày đăng ", { a: "đều một cách bất thường", c: WARN }],
    "Bộ Vietnam IT Job Posts có trường ngày đăng. Nhưng ở ITviec, TopCV và CareerViet, mỗi năm từ 2018 đến 2025 đều có khoảng 160–175 tin — đều tới mức không thể là thị trường thật, và tin năm 2018 không thể còn được thu thập năm 2026. Trường này nhiều khả năng sinh tự động. Nếu tin vào nó, mô hình sẽ học một xu hướng theo năm không có thật. Nhóm dùng năm thu thập thay thế, và chấp nhận không phân tích xu hướng theo thời gian.");
  const years = Object.keys(D.posted_years);
  s.addChart(pres.charts.BAR, [{ name: "Số tin", labels: years, values: years.map((y) => D.posted_years[y]) }], chartOptions({
    x: 0.7, y: 1.6, w: 7.6, h: 4.9, barDir: "col", chartColors: [WARN], valAxisMinVal: 0, valAxisMaxVal: 250,
    showTitle: true, title: "Số tin theo năm đăng (ITviec, TopCV, CareerViet)", titleColor: MUTED, titleFontSize: 14, titleFontFace: "+mn-lt",
  }));
  s.addText("Thị trường thật không phẳng như vậy.\n\n→ Dùng năm thu thập dữ liệu, không phân tích xu hướng theo năm.", { x: 8.8, y: 2.2, w: 3.8, h: 3.5, fontSize: 20, color: TEXT, margin: 0, valign: "top", isTextBox: true });
}
{
  const s = content("Dữ liệu", ["Sau làm sạch: ", { a: "3.809" }, " tin có nhãn lương"],
    "Sau khi chuẩn hóa lương, phân loại vai trò theo chức danh, bóc tách 70 kỹ năng và khử trùng lặp, từ 8.523 tin thô còn 3.809 tin có nhãn lương thuộc 23 vai trò CNTT, từ 685 công ty. Gấp hơn 270 lần bản thăm dò.");
  const steps = [["8.523", "tin thô (CareerBuilder chỉ CNTT)"], ["5.041", "đọc được lương"], ["3.857", "thuộc 23 vai trò CNTT"], ["3.809", "sau khử trùng lặp"]];
  steps.forEach(([v, l], i) => {
    const w = 11.6 - i * 2.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.7, y: 1.75 + i * 1.2, w, h: 0.95, fill: { color: i === 3 ? "1F3A2B" : CARD }, line: { color: i === 3 ? ACCENT : CARD }, rectRadius: 0.08 });
    s.addText([{ text: v, options: { bold: true, color: i === 3 ? ACCENT : TEXT, fontSize: 28 } }, { text: `   ${l}`, options: { color: MUTED, fontSize: 18 } }], { x: 1.0, y: 1.75 + i * 1.2, w: w - 0.5, h: 0.95, valign: "middle", margin: 0, isTextBox: true });
  });
}
{
  const s = content("Dữ liệu", ["Chia tập ", { a: "theo công ty" }, ", không theo từng tin"],
    "Một công ty thường đăng hàng chục tin gần giống nhau cùng khung lương. Nếu chia ngẫu nhiên theo tin, mô hình chỉ cần nhớ lương của công ty là đoán đúng — giống đi thi mà đề trùng đề ôn. Câu hỏi thật của người dùng là: công ty mới tôi ứng tuyển trả bao nhiêu. Vì vậy nhóm chia theo công ty bằng hàm băm cố định: 449 công ty để học, 112 để chọn mô hình, 124 công ty hoàn toàn mới để kiểm tra.");
  stat(s, 0.9, 1.9, 3.6, "449", "công ty · 2.461 tin để huấn luyện");
  stat(s, 4.85, 1.9, 3.6, "112", "công ty · 652 tin để chọn mô hình");
  stat(s, 8.8, 1.9, 3.6, "124", "công ty mới · 696 tin để kiểm tra");
  s.addText("Giống kỳ thi dùng đề mới, không dùng lại đề ôn tập.", { x: 0.9, y: 5.2, w: 11.5, h: 0.8, fontSize: 20, color: TEXT, margin: 0, isTextBox: true });
}

// ============================== INSIGHT ==============================
divider("Thị trường", "Phần 2", "Thị trường nói gì?",
  "Phần thứ hai: dữ liệu sạch cho thấy điều gì về thị trường.");
{
  const s = content("Thị trường", [{ a: "Kinh nghiệm" }, " quyết định nhiều nhất"],
    "Kinh nghiệm có tương quan hạng Spearman 0,76 với lương. Trung vị tăng từ 13,5 triệu khi dưới 1 năm lên 28 triệu ở 3 năm, nhưng bước nhảy lớn nhất là từ 4 năm (29 triệu) lên 5–7 năm (49 triệu) — tương ứng lên cấp Senior. Đây cũng là đặc trưng quan trọng nhất của mô hình.");
  const labels = Object.keys(D.experience);
  s.addChart(pres.charts.BAR, [{ name: "Trung vị", labels: labels.map((l) => `${l} năm`), values: labels.map((l) => D.experience[l]) }], chartOptions({
    x: 0.7, y: 1.6, w: 8.2, h: 5.0, barDir: "col", chartColors: [ACCENT], dataLabelFormatCode: "0.0", valAxisHidden: true,
  }));
  stat(s, 9.4, 2.2, 3.3, "ρ = 0,76", "tương quan hạng giữa kinh nghiệm và lương", ACCENT, 44);
  s.addText("4 → 5 năm: +20 triệu", { x: 9.4, y: 4.6, w: 3.3, h: 0.6, fontSize: 20, bold: true, color: TEXT, margin: 0, isTextBox: true });
}
{
  const s = content("Thị trường", ["Phổ biến ", { a: "≠", c: WARN }, " trả cao"],
    "Bên trái là 8 kỹ năng được nhắc nhiều nhất — JavaScript, React, Java dẫn đầu. Bên phải là 8 kỹ năng có trung vị lương cao nhất — LLM, AWS, Airflow, GCP. Hai danh sách gần như không trùng nhau. Kỹ năng phổ biến giúp có việc; kỹ năng hiếm hơn trong mảng dữ liệu, AI và đám mây gắn với lương cao hơn.");
  const demand = D.top_demand.slice().reverse();
  const salary = D.top_salary.slice().reverse();
  s.addChart(pres.charts.BAR, [{ name: "Số tin", labels: demand.map((r) => r.skill), values: demand.map((r) => r.postings) }], chartOptions({
    x: 0.5, y: 1.55, w: 6.1, h: 5.2, barDir: "bar", chartColors: ["60A5FA"], valAxisHidden: true,
    showTitle: true, title: "Nhắc nhiều nhất (số tin)", titleColor: MUTED, titleFontSize: 15, titleFontFace: "+mn-lt",
  }));
  s.addChart(pres.charts.BAR, [{ name: "Trung vị", labels: salary.map((r) => r.skill), values: salary.map((r) => r.median) }], chartOptions({
    x: 6.8, y: 1.55, w: 6.1, h: 5.2, barDir: "bar", chartColors: [ACCENT], valAxisHidden: true, dataLabelFormatCode: "0.0",
    showTitle: true, title: "Lương cao nhất (trung vị, triệu)", titleColor: MUTED, titleFontSize: 15, titleFontFace: "+mn-lt",
  }));
}
{
  const s = content("Thị trường", [{ a: "23" }, " vai trò, trung vị chênh nhau ", { a: "3,5 lần" }],
    "Dashboard mới thể hiện đủ 23 vai trò — bản cũ chỉ có 2. Nhóm quản lý và kiến trúc đứng đầu với khoảng 47–48 triệu; Data Engineer, DevOps, AI/ML từ 33 đến 39 triệu, cao hơn rõ rệt lập trình phổ thông 24–27 triệu; IT Support thấp nhất 13,6 triệu.");
  const roles = Object.entries(D.roles).reverse();
  s.addChart(pres.charts.BAR, [{ name: "Trung vị", labels: roles.map(([k]) => k), values: roles.map(([, v]) => v) }], chartOptions({
    x: 0.7, y: 1.4, w: 11.9, h: 5.6, barDir: "bar", chartColors: [ACCENT], valAxisHidden: true, dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 11, dataLabelFontSize: 10,
  }));
}

// ============================== MÔ HÌNH ==============================
divider("Mô hình", "Phần 3", "Ba cách định giá lương",
  "Phần thứ ba là mô hình. Thay vì nói về công thức, nhóm so sánh mỗi mô hình với cách một con người định giá lương.");
{
  const s = content("Mô hình", ["Ridge: một ", { a: "bảng giá cố định" }],
    "Ridge giống một chuyên viên nhân sự có bảng giá cố định: Backend cộng 2 triệu, mỗi năm kinh nghiệm cộng 3 triệu, biết AWS cộng 1 triệu, rồi cộng tất cả lại. Ưu điểm: dễ giải thích, ổn định. Nhược điểm: không hiểu 'tùy hoàn cảnh' — AWS đáng giá với kỹ sư DevOps hơn hẳn với tester, nhưng bảng giá chỉ có một con số cho AWS.");
  card(s, 0.7, 1.8, 5.8, 4.4, "Giống như", "Chuyên viên nhân sự cộng điểm theo bảng giá:\nBackend +2 triệu\nMỗi năm kinh nghiệm +3 triệu\nBiết AWS +1 triệu");
  card(s, 6.83, 1.8, 2.85, 4.4, "Mạnh", "Dễ giải thích, ổn định", ACCENT);
  card(s, 9.88, 1.8, 2.75, 4.4, "Yếu", "AWS với DevOps và với Tester được cộng như nhau", WARN);
}
{
  const s = content("Mô hình", ["Random Forest: ", { a: "300 chuyên viên" }, ", mỗi người thấy một phần"],
    "Random Forest giống hỏi ý kiến 300 chuyên viên tuyển dụng, mỗi người chỉ được xem một phần hồ sơ và chỉ từng gặp một phần thị trường, rồi lấy trung bình. Ý kiến sai của từng người bù trừ nhau. Một con người thật không thể tự có 300 góc nhìn độc lập cùng lúc — máy thì làm được. Nhược điểm: mỗi chuyên viên học thuộc các hồ sơ đã gặp; sai số trên dữ liệu đã học chỉ 2,75 triệu nhưng trên công ty mới là 5,6 triệu.");
  card(s, 0.7, 1.8, 5.8, 4.4, "Giống như", "Hỏi 300 chuyên viên, mỗi người xem một phần hồ sơ, rồi lấy trung bình.\n\nCon người không thể tự có 300 góc nhìn độc lập — máy thì làm được.");
  card(s, 6.83, 1.8, 2.85, 4.4, "Mạnh", "Sai lệch của từng người bù trừ nhau; học được tương tác", ACCENT);
  card(s, 9.88, 1.8, 2.75, 4.4, "Yếu", `Học thuộc: sai số ${fmt(M.RandomForest.train.MAE, 2)} khi đã gặp, ${fmt(M.RandomForest.valid.MAE, 2)} khi gặp mới`, WARN);
}
{
  const s = content("Mô hình", ["Gradient Boosting: hội đồng ", { a: "sửa sai nối tiếp" }],
    "Gradient Boosting giống một hội đồng làm việc nối tiếp: người đầu đưa ra mức sơ bộ, người thứ hai chỉ tập trung sửa những hồ sơ người đầu đánh giá sai, người thứ ba sửa tiếp phần còn sai. Mỗi lần chỉ sửa một bước nhỏ nên ít học vẹt. Nhóm thêm một quy tắc cho hội đồng: không được trả người nhiều kinh nghiệm hơn thấp hơn người ít kinh nghiệm hơn khi các điều kiện khác như nhau — gọi là ràng buộc đơn điệu.");
  card(s, 0.7, 1.8, 5.8, 4.4, "Giống như", "Người sau chỉ sửa phần người trước đánh giá sai, mỗi lần một bước nhỏ.\n\nQuy tắc: thêm kinh nghiệm không bao giờ làm giảm lương.");
  card(s, 6.83, 1.8, 2.85, 4.4, "Mạnh", "Học quy luật tinh tế, ít học vẹt", ACCENT);
  card(s, 9.88, 1.8, 2.75, 4.4, "Yếu", "Khó giải thích hơn Ridge; cần dò tham số", WARN);
}
{
  const s = content("Mô hình", ["Gradient Boosting sai ", { a: `${fmt(M.GradientBoosting.test.MAE, 2)} triệu` }, ", bằng một nửa mốc trung vị"],
    `Trên 696 tin của 124 công ty mới, mốc trung vị sai trung bình 12,15 triệu. Cả ba mô hình đều tốt hơn khoảng hai lần. Gradient Boosting tốt nhất với MAE ${fmt(M.GradientBoosting.test.MAE, 2)} triệu, R² ${fmt(M.GradientBoosting.test.R2, 3)}, tức sai trung bình khoảng một phần năm mức lương. Mô hình được chọn bằng tập kiểm định trước khi nhìn tập kiểm tra.`);
  const order = ["Baseline", "Ridge", "RandomForest", "GradientBoosting"];
  s.addChart(pres.charts.BAR, [{ name: "MAE", labels: order.map((n) => M[n].label), values: order.map((n) => +M[n].test.MAE.toFixed(2)) }], chartOptions({
    x: 0.7, y: 1.6, w: 7.8, h: 5.0, barDir: "col", chartColors: [MUTED, MUTED, MUTED, ACCENT], valAxisHidden: true, dataLabelFormatCode: "0.00",
  }));
  stat(s, 9.0, 1.9, 3.7, `R² ${fmt(M.GradientBoosting.test.R2, 3)}`, "trên 696 tin của 124 công ty mới", ACCENT, 44);
  stat(s, 9.0, 4.0, 3.7, `${fmt(M.GradientBoosting.test.MAPE, 1)}%`, "sai số tương đối trung bình", TEXT, 44);
}
{
  const s = content("Mô hình", ["Random Forest ", { a: "học thuộc bài", c: WARN }],
    "So sánh sai số trên dữ liệu đã học và dữ liệu mới cho thấy mức học vẹt. Random Forest chênh 2,8 triệu giữa hai tập; Gradient Boosting chỉ chênh khoảng 0,6 triệu nhờ hệ số học nhỏ, cây nông và điều chuẩn. Ridge gần như không chênh nhưng sai số chung cao hơn vì không học được quan hệ phi tuyến.");
  const order = ["Ridge", "RandomForest", "GradientBoosting"];
  s.addChart(pres.charts.BAR, [
    { name: "Dữ liệu đã học (train)", labels: order.map((n) => M[n].label), values: order.map((n) => +M[n].train.MAE.toFixed(2)) },
    { name: "Công ty mới (validation)", labels: order.map((n) => M[n].label), values: order.map((n) => +M[n].valid.MAE.toFixed(2)) },
  ], chartOptions({
    x: 0.7, y: 1.6, w: 11.9, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: [MUTED, ACCENT], valAxisHidden: true, dataLabelFormatCode: "0.00",
    showLegend: true, legendPos: "t", legendColor: "D1D5DB", legendFontSize: 14, legendFontFace: "+mn-lt",
  }));
}

// ============================ KIỂM ĐỊNH ============================
divider("Kiểm định", "Phần 4", "Có tin được không?",
  "Một con số MAE chưa đủ. Phần thứ tư trả lời ba câu hỏi: ưu thế của Gradient Boosting có thật không, khoảng lương ứng dụng đưa ra có đáng tin không, và mô hình có thiên lệch với nhóm nào không.");
{
  const d = B.differences;
  const s = content("Kiểm định", ["Gradient Boosting thắng ở ", { a: `${fmt(d.RandomForest.p_better * 100, 0)}%` }, " số lần lấy mẫu lại"],
    `Nếu tập kiểm tra là một nhóm công ty khác, kết quả có đổi không? Bootstrap giả lập ${B.rounds} tập kiểm tra bằng cách rút ngẫu nhiên có hoàn lại ${B.companies} công ty — rút theo công ty chứ không theo tin, vì tin cùng công ty giống nhau. Khoảng tin cậy MAE của các mô hình chồng lên nhau, nhưng khi so cặp trên cùng một lần rút, Gradient Boosting tốt hơn Random Forest ở 100% và tốt hơn Ridge ở 99,8% số lần. Ưu thế là thật, dù nhỏ: khoảng 0,35 đến 0,56 triệu mỗi tin.`);
  stat(s, 0.9, 1.9, 5.5, `${fmt(d.RandomForest.p_better * 100, 0)}%`, `thắng Random Forest · chênh ${fmt(d.RandomForest.mean, 2)} triệu (95%: ${fmt(d.RandomForest.ci95[0], 2)} đến ${fmt(d.RandomForest.ci95[1], 2)})`);
  stat(s, 6.9, 1.9, 5.5, `${fmt(d.Ridge.p_better * 100, 1)}%`, `thắng Ridge · chênh ${fmt(d.Ridge.mean, 2)} triệu (95%: ${fmt(d.Ridge.ci95[0], 2)} đến ${fmt(d.Ridge.ci95[1], 2)})`);
  s.addText(`${B.rounds} lần rút ngẫu nhiên ${B.companies} công ty — theo công ty, không theo từng tin.`, { x: 0.9, y: 5.2, w: 11.5, h: 0.8, fontSize: 20, color: TEXT, margin: 0, isTextBox: true });
}
{
  const s = content("Kiểm định", ["Nói ", { a: "80%" }, ", thực tế bao ", { a: `${fmt(lv(0.8).coverage * 100, 1)}%` }],
    `Ứng dụng đưa ra một khoảng thường gặp 80%. Khoảng đó được hiệu chuẩn tốt nếu nó thật sự chứa 80% lương thật. Trên tập kiểm tra, khoảng 80% bao ${fmt(lv(0.8).coverage * 100, 1)}%, khoảng 90% bao ${fmt(lv(0.9).coverage * 100, 1)}%, khoảng 50% bao ${fmt(lv(0.5).coverage * 100, 1)}% — đường hiệu chuẩn gần như trùng đường chéo. Điểm yếu: vai trò quản lý như Tech Lead chỉ được bao 33%, nên ứng dụng cần thận trọng với các vai trò này.`);
  const rel = D.calibration.reliability;
  s.addChart(pres.charts.LINE, [
    { name: "Hoàn hảo", labels: rel.map((r) => `${Math.round(r.level * 100)}%`), values: rel.map((r) => r.level * 100) },
    { name: "Thực tế trên tập test", labels: rel.map((r) => `${Math.round(r.level * 100)}%`), values: rel.map((r) => +(r.coverage * 100).toFixed(1)) },
  ], chartOptions({
    x: 0.7, y: 1.6, w: 7.8, h: 5.0, chartColors: [MUTED, ACCENT], showValue: false, lineSize: 3, lineDataSymbolSize: 7,
    valAxisMinVal: 0, valAxisMaxVal: 100, showLegend: true, legendPos: "t", legendColor: "D1D5DB", legendFontSize: 14, legendFontFace: "+mn-lt",
    catAxisLabelFontSize: 11, showValAxisTitle: true, valAxisTitle: "% tin nằm trong khoảng", valAxisTitleColor: MUTED, valAxisTitleFontSize: 12,
  }));
  stat(s, 9.0, 1.9, 3.7, `${fmt(lv(0.9).coverage * 100, 1)}%`, "khoảng 90% bao phủ thực tế", TEXT, 44);
  stat(s, 9.0, 4.0, 3.7, "33%", "Tech Lead: khoảng 80% chỉ bao 33%", WARN, 44);
}
{
  const s = content("Kiểm định", ["Junior bị dự đoán ", { a: "cao hơn 7%", c: WARN }],
    "Đo độ lệch tương đối: dự đoán trừ thực tế, chia thực tế. Các khu vực lớn Hà Nội, TP. Hồ Chí Minh, Remote lệch tương đương nhau, từ 0 đến 3%, không có bằng chứng thiên vị thành phố. Sai lệch có ý nghĩa thống kê duy nhất là cấp Junior: dự đoán cao hơn khoảng 7%, khoảng tin cậy 2,5 đến 12% không chứa 0. Nghĩa là với người mới ra trường, ứng dụng có thể đưa mức kỳ vọng hơi cao. Các nhóm dưới 20 tin không dùng để kết luận.");
  const level = D.fairness.level.slice().sort((a, b) => a.bias_pct - b.bias_pct);
  s.addChart(pres.charts.BAR, [{ name: "Độ lệch", labels: level.map((g) => `${g.group} (n=${g.n})`), values: level.map((g) => +g.bias_pct.toFixed(1)) }], chartOptions({
    x: 0.7, y: 1.6, w: 7.8, h: 5.0, barDir: "bar", chartColors: [ACCENT], invertedColors: [WARN], dataLabelFormatCode: "0.0", valAxisHidden: true,
  }));
  s.addText("Độ lệch = (dự đoán − thật) / thật\n\nHà Nội +2,7% · TP. HCM +2,8% · Remote −0,2%\n→ không thiên vị thành phố lớn\n\nJunior +6,9% (95%: 2,5 đến 12)\n→ sai lệch có hệ thống duy nhất", { x: 9.0, y: 1.9, w: 3.7, h: 4.6, fontSize: 16, color: TEXT, margin: 0, valign: "top", isTextBox: true });
}
{
  const s = content("Kiểm định", ["Giới tính: ", { a: "không đo được", c: WARN }, " — và đó là một phát hiện"],
    `Dữ liệu không có thông tin giới tính, và mô hình không dùng giới tính làm đầu vào, nên mô hình không thể trả khác nhau cho nam và nữ cùng hồ sơ. Nhưng nhóm cũng không thể đo công bằng giới theo nghĩa đầy đủ. Điều kiểm tra được là chính tin tuyển dụng: 222 dòng thô ghi điều kiện giới tính, như 'Tester Game Chỉ Tuyển Nữ'. Trong ${fmt(3809, 0)} tin CNTT có lương chỉ còn ${D.gender.mentioned} tin — quá ít để kết luận. Đề xuất: ứng dụng thật nên cảnh báo các tin này vì Bộ luật Lao động cấm phân biệt giới tính.`);
  quote(s, 0.7, 1.75, 11.9, "\"Tester Game Chỉ Tuyển Nữ\"", "TopCV 2026");
  quote(s, 0.7, 2.73, 11.9, "\"Business Analyst … Tuyển Nam\"", "TopCV 2026");
  quote(s, 0.7, 3.71, 11.9, "\"Giới tính: Nam\"", "CareerBuilder 2023");
  stat(s, 0.9, 4.75, 3.6, "222", "dòng thô ghi điều kiện giới tính", WARN, 40);
  stat(s, 4.85, 4.75, 3.6, String(D.gender.mentioned), "trong 3.809 tin CNTT có lương", WARN, 40);
  stat(s, 8.8, 4.75, 3.6, "0", "lần mô hình dùng giới tính", ACCENT, 40);
}

// ============================== ỨNG DỤNG ==============================
divider("Ứng dụng", "Phần 5", "Từ mô hình đến tư vấn",
  "Phần cuối là ứng dụng: biến mô hình thành câu trả lời cho người dùng ở đầu bài.");
{
  const s = content("Ứng dụng", ["Nên học gì? Hỏi mô hình ", { a: "\"nếu tôi biết thêm…\"" }],
    "Nếu xếp kỹ năng theo số tin nhắc tới, JavaScript đứng đầu — nhưng tin có JavaScript không trả cao hơn. Nhóm hỏi mô hình một câu khác: nếu tôi giống hệt hiện tại nhưng biết thêm đúng một kỹ năng, lương thay đổi bao nhiêu. Trung bình trên toàn dữ liệu, LLM/GenAI và tiếng Anh tăng gần 7 triệu, Agile/Scrum 5,2, AWS 4,7. Đây là quan hệ tương quan, không phải lời hứa tăng lương.");
  const up = D.uplift.slice().reverse();
  s.addChart(pres.charts.BAR, [{ name: "Tăng lương", labels: up.map((r) => r.skill), values: up.map((r) => +r.model_uplift.toFixed(2)) }], chartOptions({
    x: 0.7, y: 1.6, w: 7.8, h: 5.0, barDir: "bar", chartColors: [ACCENT], valAxisHidden: true, dataLabelFormatCode: "+0.0",
  }));
  s.addText("Giữ nguyên vai trò, kinh nghiệm, khu vực.\nChỉ thêm đúng một kỹ năng.\n\nTriệu đồng/tháng, trung bình trên toàn dữ liệu.", { x: 9.0, y: 2.0, w: 3.7, h: 4.0, fontSize: 18, color: TEXT, margin: 0, valign: "top", isTextBox: true });
}
{
  const s = content("Ứng dụng", ["Kiến trúc: ", { a: "huấn luyện một lần" }, ", dự đoán tức thì"],
    "Hệ thống có bốn tầng: dữ liệu nguồn, xử lý dữ liệu, mô hình và giao diện Streamlit. Mô hình được huấn luyện ngoại tuyến và lưu lại; ứng dụng chỉ nạp mô hình đã kiểm định, không huấn luyện lại khi người dùng bấm. Nhờ vậy cùng một hồ sơ luôn cho cùng kết quả và phản hồi dưới một giây.");
  framedImage(s, path.join(DIA, "01-kien-truc-he-thong.png"), 1.9, 1.75, 9.5, 5.0, "Sơ đồ kiến trúc bốn tầng của hệ thống");
}
{
  const s = content("Ứng dụng", ["Quay lại người dùng: ", { a: "35,4 triệu" }, ", nên học LLM và AWS"],
    "Quay lại người dùng ở đầu bài: Data Engineer, Hà Nội, 3 năm, biết Python, SQL, Spark. Ứng dụng dự đoán 35,4 triệu mỗi tháng, khoảng thường gặp 25,8 đến 46,3 triệu, ở phân vị 44 của vai trò. Kỹ năng đề xuất: LLM/GenAI cộng 4,8 triệu, AWS cộng 2,8, Kafka cộng 1,1. Lộ trình cho thấy lên khoảng 55 triệu khi đạt 5 năm và cấp Senior.");
  framedImage(s, path.join(FIG, "ui-advisor.png"), 0.7, 1.75, 6.2, 5.2, "Ảnh chụp trang Tư vấn và dự đoán lương");
  stat(s, 7.6, 1.9, 5.0, "35,4 triệu", "khoảng thường gặp 25,8 – 46,3 · phân vị 44", ACCENT, 44);
  s.addText("Nên học:\nLLM/GenAI +4,8 · AWS +2,8 · Kafka +1,1\n\n5 năm, Senior: ≈ 55 triệu", { x: 7.6, y: 4.2, w: 5.0, h: 2.4, fontSize: 20, color: TEXT, margin: 0, valign: "top", isTextBox: true });
}

// ============================== KẾT ==============================
{
  const s = content("Kết luận", ["Điều mô hình ", { a: "chưa làm được", c: WARN }],
    "Nhóm nói rõ các hạn chế. Thứ nhất, đây là lương chào tuyển trong tin, không phải lương thực nhận, và 41% tin không công bố lương bị loại. Thứ hai, 87% tin có lương ở Hà Nội. Thứ ba, các vai trò quản lý ít mẫu, khoảng dự đoán kém tin cậy. Thứ tư, mức tăng theo kỹ năng là tương quan, không phải nhân quả. Cuối cùng, không có dữ liệu giới tính nên không đo được công bằng giới.");
  card(s, 0.7, 1.8, 3.8, 2.3, "Lương chào tuyển", "Không phải lương thực nhận; 41% tin không công bố bị loại", WARN);
  card(s, 4.77, 1.8, 3.8, 2.3, "Lệch về Hà Nội", "87% tin có lương ở Hà Nội; TP. HCM ít công bố", WARN);
  card(s, 8.83, 1.8, 3.8, 2.3, "Vai trò quản lý", "Ít mẫu; khoảng 80% chỉ bao 33% với Tech Lead", WARN);
  card(s, 0.7, 4.4, 5.85, 2.3, "Tương quan, không nhân quả", "Học thêm kỹ năng không bảo đảm được tăng lương", WARN);
  card(s, 6.78, 4.4, 5.85, 2.3, "Không có giới tính", "Không đo được công bằng giới; chỉ kiểm tra được nội dung tin", WARN);
}
statement("Kết luận",
  [{ a: "3.809" }, " tin · ", { a: "23" }, " vai trò · sai ", { a: "5,38" }, " triệu · đã kiểm định"],
  ["Dữ liệu lớn với quy tắc minh bạch, chia theo công ty, kiểm tra bằng bootstrap, hiệu chuẩn và công bằng — rồi mới đưa vào tư vấn."],
  "Tóm lại: từ 14 tin duyệt tay, nhóm mở rộng lên 3.809 tin có nhãn, 23 vai trò, với quy tắc chuẩn hóa minh bạch. Gradient Boosting sai trung bình 5,38 triệu trên công ty mới, ưu thế được xác nhận bằng bootstrap, khoảng dự đoán được hiệu chuẩn, không thiên vị khu vực lớn. Trên nền đó, ứng dụng trả lời được câu hỏi của người dùng: nên được trả bao nhiêu và nên học gì tiếp theo.");
statement("Kết luận", ["Cảm ơn thầy và các bạn", { a: " — xin mời đặt câu hỏi" }],
  ["Mã nguồn: github.com/theihoz/ML"],
  "Nhóm em xin cảm ơn thầy và các bạn đã lắng nghe. Nhóm sẵn sàng trả lời câu hỏi. Các slide phụ lục phía sau có bảng chi tiết về xử lý dữ liệu, các quyết định và kết quả kiểm định nếu cần.");

// ============================== PHỤ LỤC ==============================
const tableStyle = { fontSize: 13, color: TEXT, fill: { color: CARD }, border: { type: "solid", pt: 0.5, color: GRID }, margin: 0.06, valign: "middle" };
const head = (cells) => cells.map((text) => ({ text, options: { bold: true, color: ACCENT, fill: { color: BG } } }));
function appendixTable(title, header, rows, colW, notes) {
  const s = content("Phụ lục", [title], notes);
  s.addTable([head(header), ...rows], { x: 0.7, y: 1.55, w: colW.reduce((a, b) => a + b, 0), colW, ...tableStyle });
}
appendixTable("Phụ lục A · Vấn đề dữ liệu thô và cách xử lý", ["Vấn đề", "Quy mô", "Cách xử lý"], [
  ["Lương không có con số (thỏa thuận)", "3.736 dòng", "Loại khỏi nhãn, vẫn dùng thống kê kỹ năng"],
  ["32 định dạng lương, lỗi \"triẹu\"", "264 dòng lỗi", "Bộ chuẩn hóa số, đơn vị, kỳ trả"],
  ["USD và lương theo năm", "352 + 30 dòng", "Quy đổi tỷ giá theo năm; chia 12"],
  ["Khoảng giả \"1 – 40 triệu\"", "322 dòng", "Loại khi cận trên > 3 × cận dưới"],
  ["Ngày đăng phân bố đều 2018–2025", "1.768 dòng", "Dùng năm thu thập"],
  ["Mô tả chứa HTML", "2.038 tin", "Bỏ thẻ trước khi tìm kỹ năng"],
  ["Tin trùng chức danh + công ty", "850 cặp", "Khử trùng theo chức danh, công ty, lương"],
  ["Tiền tố \"Pro\\n\", \"GẤP\\n\"", "238 + 14", "Chuẩn hóa khóa công ty, chức danh"],
  ["Địa điểm \"(mới)\"", "774 dòng", "Gom về 5 khu vực"],
  ["Kinh nghiệm ghi \"Nhân viên\"", "245 dòng", "Để trống, tìm trong chức danh"],
  ["TP. HCM ít công bố lương", "29% đọc được", "Ghi nhận là hạn chế"],
  ["Điều kiện giới tính", "222 dòng thô", "Gắn nhãn kiểm tra, không làm đặc trưng"],
], [5.0, 2.2, 4.7], "Bảng đầy đủ các vấn đề dữ liệu thô với số dòng bị ảnh hưởng và cách xử lý, dùng khi thầy hỏi chi tiết về tiền xử lý.");
appendixTable("Phụ lục B · Các quyết định và lý do", ["Quyết định", "Vấn đề trước đó", "Lý do chọn"], [
  ["Gộp 3 nguồn thay 14 nhãn", "14 mẫu, test 2 tin", "Số mẫu quyết định độ tin cậy"],
  ["Trung điểm khoảng lương", "Tin ghi khoảng, cần một số", "Giá trị đại diện tự nhiên"],
  ["\"Tới X\" → 0,7X–X", "Mất nhiều tin chỉ có một cận", "Gần độ rộng khoảng điển hình"],
  ["Chia theo công ty", "Tin cùng công ty giống nhau", "Mô phỏng công ty mới"],
  ["Học trên log(lương)", "Lương lệch phải", "Sai lệch lương cảm nhận theo tỉ lệ"],
  ["Ba mô hình khác họ", "Bản cũ chỉ 2 mô hình tuyến tính", "Kiểm tra cần phi tuyến hay không"],
  ["MAE là tiêu chí", "Chỉ số khác nhau cho thứ tự khác", "Đơn vị triệu đồng, dễ hiểu"],
  ["Ràng buộc đơn điệu", "Lộ trình lương giảm vô lý", "Đúng quy luật thị trường"],
  ["Khoảng theo tỉ lệ sai số", "Một con số gây chắc chắn giả", "Co giãn theo mức lương, kiểm chứng được"],
  ["Tư vấn theo \"nếu biết thêm\"", "Phổ biến ≠ giá trị", "Giữ nguyên các yếu tố khác"],
], [3.8, 4.0, 4.1], "Mười quyết định chính, mỗi quyết định nêu vấn đề dẫn tới nó và lý do chọn. Chi tiết đầy đủ trong báo cáo, các mục 3.10, 5.6 và 6.8.");
appendixTable("Phụ lục C · Kiểm định trên tập test", ["Chỉ số", "Giá trị", "Ghi chú"], [
  ...["Ridge", "RandomForest", "GradientBoosting"].map((n) => [`MAE ${M[n].label}`, `${fmt(B.models[n].MAE.point, 2)} (95%: ${fmt(B.models[n].MAE.ci95[0], 2)}–${fmt(B.models[n].MAE.ci95[1], 2)})`, `Bootstrap ${B.rounds} lần theo công ty`]),
  ["Bao phủ khoảng 50% / 80% / 90%", `${fmt(lv(0.5).coverage * 100, 1)}% / ${fmt(lv(0.8).coverage * 100, 1)}% / ${fmt(lv(0.9).coverage * 100, 1)}%`, "Khoảng dựng trên validation"],
  ...D.calibration.by_salary_band.map((b) => [`Bao phủ 80% · lương ${b.group.toLowerCase()} (${b.range.replace(/\./g, ",")})`, `${fmt(b.coverage * 100, 1)}%`, `${b.n} tin`]),
  ...D.fairness.platform.map((g) => [`Độ lệch · ${g.group}`, `${g.bias_pct >= 0 ? "+" : ""}${fmt(g.bias_pct, 1)}%`, `95%: ${fmt(g.bias_pct_ci95[0], 1)} đến ${fmt(g.bias_pct_ci95[1], 1)} · n=${g.n}`]),
], [4.8, 3.6, 3.5], "Bảng số liệu kiểm định chi tiết: khoảng tin cậy bootstrap của MAE, tỉ lệ bao phủ theo mức lương và độ lệch theo nền tảng nguồn. TopCV bị dự đoán cao hơn khoảng 6,5% vì nền tảng này đăng nhiều tin lương thấp hơn mặt bằng cùng hồ sơ.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
