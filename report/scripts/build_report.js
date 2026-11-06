// Báo cáo tiểu luận .docx: Times New Roman 13, giãn 1.5, lề 3.5/2/2.5/3 cm; công thức dạng Word Equation.
// Chạy: NODE_PATH=<thư mục có node_modules/docx> node report/scripts/build_report.js <repo> <file .docx>
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun, LevelFormat, Math: OMath,
  MathFraction, MathRadical, MathRun, MathSubScript, MathSubSuperScript, MathSum, MathSuperScript,
  NumberFormat, Packer, PageNumber, Paragraph, SectionType, StyleLevel, Table, TableCell,
  TableOfContents, TableRow, TabStopType, TextRun, VerticalAlign, WidthType,
} = require("docx");

const ROOT = process.argv[2];
const OUT = process.argv[3];
const FIG = path.join(ROOT, "report/figures");
const DIA = path.join(ROOT, "report/diagrams");
const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, "job_market/artifacts/salary-v2/metrics.json")));
const skillValue = fs.readFileSync(path.join(ROOT, "job_market/artifacts/salary-v2/skill_value.csv"), "utf8")
  .trim().split("\n").slice(1).map((line) => line.split(","));
const FONT = "Times New Roman";
const CM = 567;
const CONTENT = Math.round(15.5 * CM);
const fmt = (v, d = 2) => Number(v).toFixed(d).replace(".", ",");
const V = JSON.parse(fs.readFileSync(path.join(ROOT, "job_market/artifacts/salary-v2/validation.json")));
const M = metrics.models;
const sel = M[metrics.selected];
const ORDER = ["Baseline", "Ridge", "RandomForest", "GradientBoosting"];
const P0 = V.production;

// ---------- văn bản ----------
function runs(text, base = {}) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(/(\*\*[^*]+\*\*|\*[^*]+\*)/g)) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    out.push(t.startsWith("**")
      ? new TextRun({ text: t.slice(2, -2), bold: true, ...base })
      : new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (text, opts = {}) => new Paragraph({ children: runs(text), ...opts });
const H1 = (text, pageBreakBefore = true) =>
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore, children: [new TextRun(text)] });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const H3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
const B = (text) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: runs(text) });
// Một quyết định: vấn đề trước đó → phương án → lựa chọn → lý do → đánh đổi.
const decision = (title, d) => [
  H3(title),
  P(`**Vấn đề gặp phải.** ${d.problem}`),
  P(`**Các phương án đã cân nhắc.** ${d.options}`),
  P(`**Phương án chọn.** ${d.choice}`),
  P(`**Lý do.** ${d.reason}`),
  P(`**Đánh đổi và rủi ro còn lại.** ${d.risk}`),
];
let listNo = 0;
const steps = (items) => {
  listNo += 1;
  return items.map((text) => new Paragraph({ numbering: { reference: "steps", level: 0, instance: listNo }, children: runs(text) }));
};
const center = (text, opts = {}, spacing = {}) =>
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing, children: runs(text, opts) });

// ---------- công thức ----------
const r = (t) => new MathRun(t);
const sb = (base, s) => new MathSubScript({ children: [r(base)], subScript: [r(s)] });
const sp = (base, s) => new MathSuperScript({ children: typeof base === "string" ? [r(base)] : base, superScript: [r(s)] });
const frac = (num, den) => new MathFraction({
  numerator: typeof num === "string" ? [r(num)] : num,
  denominator: typeof den === "string" ? [r(den)] : den,
});
const sum = (children, lower = "i=1", upper = "n") =>
  new MathSum({ children, subScript: typeof lower === "string" ? [r(lower)] : lower, ...(upper ? { superScript: [r(upper)] } : {}) });
const sq = (inner) => [r("("), ...inner, sp(")", "2")];
const eqNo = {};
function eq(children) {
  eqNo[chapter] = (eqNo[chapter] || 0) + 1;
  return new Paragraph({
    indent: { firstLine: 0 },
    spacing: { before: 120, after: 120 },
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(CONTENT / 2) }, { type: TabStopType.RIGHT, position: CONTENT }],
    children: [new TextRun("\t"), new OMath({ children }), new TextRun(`\t(${chapter}.${eqNo[chapter]})`)],
  });
}
const yi = () => sb("y", "i");
const yhat = () => sb("ŷ", "i");

// ---------- hình, bảng ----------
function pngSize(file) {
  const b = fs.readFileSync(file);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}
let chapter = 0;
const figNo = {};
const tabNo = {};
function fig(file, caption, widthCm = 15) {
  figNo[chapter] = (figNo[chapter] || 0) + 1;
  const [w, h] = pngSize(file);
  let width = (widthCm / 2.54) * 96;
  let height = (width * h) / w;
  const maxH = (21 / 2.54) * 96;
  if (height > maxH) { height = maxH; width = (height * w) / h; }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, indent: { firstLine: 0 }, spacing: { before: 120, after: 0, line: 240 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: Math.round(width), height: Math.round(height) }, altText: { title: caption, description: caption, name: caption } })],
    }),
    new Paragraph({ style: "HinhCaption", children: [new TextRun(`Hình ${chapter}.${figNo[chapter]}: ${caption}`)] }),
  ];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(text, width, { bold = false, align = AlignmentType.LEFT } = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    children: String(text).split("\n").map((line) => new Paragraph({
      alignment: align, indent: { firstLine: 0 }, spacing: { before: 0, after: 0, line: 276 }, children: runs(line, { bold, size: 24 }),
    })),
  });
}
function table(caption, headers, rows, ratios, aligns = []) {
  if (caption) tabNo[chapter] = (tabNo[chapter] || 0) + 1;
  const total = ratios.reduce((a, b) => a + b, 0);
  const widths = ratios.map((x) => Math.floor((CONTENT * x) / total));
  widths[widths.length - 1] += CONTENT - widths.reduce((a, b) => a + b, 0);
  return [
    ...(caption ? [new Paragraph({ style: "BangCaption", keepNext: true, children: [new TextRun(`Bảng ${chapter}.${tabNo[chapter]}: ${caption}`)] })] : []),
    new Table({
      width: { size: CONTENT, type: WidthType.DXA }, columnWidths: widths,
      rows: [
        new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { bold: true, align: AlignmentType.CENTER })) }),
        ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((v, i) => cell(v, widths[i], { align: aligns[i] || AlignmentType.LEFT })) })),
      ],
    }),
    new Paragraph({ spacing: { before: 0, after: 120 }, children: [] }),
  ];
}
const R = AlignmentType.RIGHT;
const C = AlignmentType.CENTER;
const tabsAt = (...cms) => cms.map((c) => ({ type: TabStopType.CENTER, position: Math.round(c * CM) }));

// ================================ BÌA ================================
const coverInfo = [
  ["Ngành", "CÔNG NGHỆ THÔNG TIN"],
  ["Chuyên ngành", "KỸ THUẬT PHẦN MỀM"],
  ["Giảng viên hướng dẫn", "ThS. LÝ NGỌC HƯNG"],
  ["Sinh viên thực hiện", "……………………………………"],
  ["MSSV", "……………………………………"],
  ["Lớp học phần", "020100138002"],
];
const cover = [
  center("BỘ GIÁO DỤC VÀ ĐÀO TẠO", { bold: true }, { after: 0 }),
  center("TRƯỜNG ĐẠI HỌC GIA ĐỊNH", { bold: true }, { after: 0 }),
  center("KHOA CÔNG NGHỆ THÔNG TIN", { bold: true }, { after: 0 }),
  center("────────────────"),
  new Paragraph({ spacing: { before: 1600 }, children: [] }),
  center("TIỂU LUẬN", { bold: true, size: 40 }),
  new Paragraph({ spacing: { before: 600 }, children: [] }),
  center("PHÂN TÍCH XU HƯỚNG THỊ TRƯỜNG VIỆC LÀM", { bold: true, size: 32 }, { after: 0 }),
  center("NGÀNH CNTT & DỰ ĐOÁN MỨC LƯƠNG", { bold: true, size: 32 }, { after: 0 }),
  center("LẬP TRÌNH VIÊN", { bold: true, size: 32 }),
  new Paragraph({ spacing: { before: 500 }, children: [] }),
  center("MÔN: LẬP TRÌNH PYTHON", { bold: true, size: 28 }),
  new Paragraph({ spacing: { before: 900 }, children: [] }),
  ...coverInfo.map(([k, v]) => new Paragraph({
    alignment: AlignmentType.LEFT, indent: { left: Math.round(1.5 * CM), firstLine: 0 }, spacing: { after: 60 },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(8 * CM) }],
    children: [new TextRun({ text: `${k}:` }), new TextRun({ text: `\t${v}`, bold: true, size: 28 })],
  })),
  new Paragraph({ spacing: { before: 1300 }, children: [] }),
  center("TP. Hồ Chí Minh, tháng 11 năm 2026", { italics: true }),
];

// ============================ PHIẾU CHẤM ============================
const gradeRows = [
  ["1", "**Bố cục**", "", ""],
  ["", "Trang bìa, mục lục, danh mục hình ảnh, danh mục bảng biểu, danh mục từ viết tắt, tài liệu tham khảo", "", ""],
  ["", "Bố cục các chương logic, phân chia mục rõ ràng", "", ""],
  ["", "Bảng phân công nhiệm vụ và tỷ lệ đóng góp của các thành viên", "", ""],
  ["2", "**Hình thức**", "", ""],
  ["", "Trình bày (font chữ, size chữ, canh lề, giãn dòng…)", "", ""],
  ["", "Kỹ thuật đánh máy, chính tả, sơ đồ, hình ảnh, bảng biểu (có tiêu đề, chú thích)", "", ""],
  ["", "Trích dẫn nguồn tài liệu tham khảo", "", ""],
  ["3", "**Nội dung chính**", "", ""],
  ["", "Tổng quan về đề tài và bối cảnh bài toán", "", ""],
  ["", "Xử lý, làm sạch và chuẩn bị dữ liệu (Pandas, NumPy)", "", ""],
  ["", "Trực quan hóa dữ liệu (Matplotlib & Seaborn) và phân tích insight", "", ""],
  ["", "Xây dựng, huấn luyện và đánh giá mô hình AI", "", ""],
  ["", "Xây dựng ứng dụng hoàn chỉnh, giao diện demo và vấn đáp bảo vệ", "", ""],
  ["", "**Tổng điểm**", "", ""],
];
const grading = [
  new Paragraph({
    alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { after: 0 }, tabStops: tabsAt(3.2, 11),
    children: [new TextRun({ text: "\tTRƯỜNG ĐẠI HỌC GIA ĐỊNH", size: 22 }), new TextRun({ text: "\tCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", bold: true, size: 22 })],
  }),
  new Paragraph({
    alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, tabStops: tabsAt(3.2, 11),
    children: [new TextRun({ text: "\tKHOA CÔNG NGHỆ THÔNG TIN", bold: true, size: 22 }), new TextRun({ text: "\tĐộc lập – Tự do – Hạnh phúc", bold: true, size: 22 })],
  }),
  new Paragraph({ spacing: { before: 360 }, children: [] }),
  center("PHIẾU CHẤM BÀI THI TIỂU LUẬN", { bold: true, size: 28 }),
  new Paragraph({
    alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, tabStops: [{ type: TabStopType.LEFT, position: Math.round(9 * CM) }],
    children: [new TextRun("Tên học phần: Lập trình Python"), new TextRun("\tLớp học phần: 020100138002")],
  }),
  new Paragraph({
    alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, tabStops: [{ type: TabStopType.LEFT, position: Math.round(9 * CM) }],
    children: [new TextRun("Họ và tên sinh viên: ……………………"), new TextRun("\tMã số sinh viên: ……………………")],
  }),
  ...table(null, ["STT", "Tiêu chí", "Điểm", "Ghi chú"], gradeRows, [1, 9, 2, 3], [C]),
  new Paragraph({ indent: { firstLine: 0 }, spacing: { before: 240, after: 0 }, tabStops: tabsAt(11.5), children: [new TextRun({ text: "\tTP. HCM, ngày …… tháng …… năm 2026", italics: true })] }),
  new Paragraph({ indent: { firstLine: 0 }, spacing: { after: 0 }, tabStops: tabsAt(11.5), children: [new TextRun({ text: "\tGiảng viên", bold: true })] }),
  new Paragraph({ indent: { firstLine: 0 }, tabStops: tabsAt(11.5), children: [new TextRun({ text: "\t(Ký và ghi rõ họ tên)", italics: true })] }),
];

// ============================= PHẦN ĐẦU =============================
const front = [
  H1("LỜI CẢM ƠN", false),
  P("Nhóm xin chân thành cảm ơn ThS. Lý Ngọc Hưng, giảng viên học phần Lập trình Python, đã hướng dẫn phương pháp khai phá dữ liệu, trực quan hóa và xây dựng mô hình học máy trong suốt học kỳ. Nhóm cũng cảm ơn các tác giả đã công bố công khai bộ dữ liệu tuyển dụng trên Kaggle, là nguồn dữ liệu chính của đề tài."),
  P("Do thời gian và kinh nghiệm còn hạn chế, báo cáo khó tránh khỏi thiếu sót. Nhóm rất mong nhận được góp ý của thầy để hoàn thiện đề tài."),
  H1("TÓM TẮT"),
  P("Đề tài khai phá dữ liệu tin tuyển dụng ngành Công nghệ thông tin tại Việt Nam để tìm hiểu xu hướng công nghệ và xây dựng mô hình ước tính mức lương lập trình viên. Ba bộ dữ liệu công khai (TopCV 2026; Vietnam IT Job Posts 2026 gồm VietnamWorks, TopCV, ITviec, CareerViet; CareerBuilder 2023) với tổng cộng 8.523 tin được rà soát và làm sạch: phát hiện và loại 2.400 tin do máy sinh tự động, chuẩn hóa chuỗi lương về triệu VND/tháng, phân loại 23 vai trò CNTT theo chức danh, bóc tách 69 kỹ năng công nghệ, chuẩn hóa kinh nghiệm, cấp bậc, khu vực, nền tảng, hình thức làm việc và loại công ty. Độ chính xác của bộ gán nhãn được đo trên mẫu 208 tin. Kết quả là bộ dữ liệu 1.735 tin thật có nhãn lương từ 671 công ty, được chia theo công ty thành ba tập huấn luyện, kiểm định và kiểm tra với 1.169, 278 và 288 tin."),
  P(`Bốn phương pháp được so sánh: mốc trung vị, Ridge Regression, Random Forest và Gradient Boosting. Cả ba mô hình học máy được ràng buộc để lương dự đoán không giảm khi tăng kinh nghiệm hoặc thêm kỹ năng. Gradient Boosting được chọn theo MAE trên tập kiểm định và đạt trên tập kiểm tra MAE = ${fmt(sel.test.MAE)} triệu VND/tháng, R² = ${fmt(sel.test.R2, 3)}, giảm ${Math.round((1 - sel.test.MAE / M.Baseline.test.MAE) * 100)}% sai số so với mốc trung vị; trung vị sai số là ${fmt(P0.overall.metrics.median_error_pct.point, 1)}% và ${fmt(P0.overall.metrics.within_20_pct.point, 1)}% dự đoán sai không quá 20%. Đối chiếu với chuẩn độ chính xác mà các sản phẩm dự đoán lương như Glassdoor và LinkedIn công bố, mô hình **chưa đạt chuẩn production**, nên ứng dụng ghi rõ kết quả chỉ mang tính tham khảo và chỉ hiện con số lương khi hồ sơ thuộc nhóm đủ dữ liệu. Số năm kinh nghiệm là yếu tố quyết định lớn nhất (hệ số Spearman ρ = 0,70 với lương); LLM/GenAI, AWS, Kafka, Next.js, Python và Golang là các kỹ năng mang lại giá trị gia tăng thu nhập cao nhất. Khoảng dự đoán 80% bao phủ ${fmt(V.calibration.levels.find((x) => x.level === 0.8).coverage * 100, 1)}% tin thật trên tập kiểm tra; Gradient Boosting tốt hơn Ridge và Random Forest ở ${fmt(V.bootstrap.differences.Ridge.p_better * 100, 1)}% và ${fmt(V.bootstrap.differences.RandomForest.p_better * 100, 1)}% số lần lấy mẫu lại bootstrap theo công ty, chưa đủ để khẳng định chắc chắn. Nhóm xây dựng ứng dụng web Streamlit gồm dashboard thị trường đủ 23 vai trò và công cụ tư vấn nghề nghiệp: người dùng nhập vai trò, kinh nghiệm, khu vực, kỹ năng để nhận khoảng lương, mức điển hình, danh sách kỹ năng nên học và lộ trình lương theo kinh nghiệm.`),
  P("**Từ khóa:** thị trường việc làm CNTT, dự đoán lương, Gradient Boosting, Random Forest, Ridge Regression, Pandas, Seaborn, Streamlit, tư vấn kỹ năng."),
  H1("MỤC LỤC"),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-3" }),
  H1("DANH MỤC HÌNH ẢNH"),
  new TableOfContents("Danh mục hình ảnh", { hyperlink: true, stylesWithLevels: [new StyleLevel("HinhCaption", 1)] }),
  H1("DANH MỤC BẢNG BIỂU"),
  new TableOfContents("Danh mục bảng biểu", { hyperlink: true, stylesWithLevels: [new StyleLevel("BangCaption", 1)] }),
  H1("DANH MỤC TỪ VIẾT TẮT"),
  ...table(null, ["Từ viết tắt", "Tiếng Anh", "Ý nghĩa"], [
    ["ADR", "Architecture Decision Record", "Hồ sơ quyết định kiến trúc"],
    ["AI", "Artificial Intelligence", "Trí tuệ nhân tạo"],
    ["BA", "Business Analyst", "Chuyên viên phân tích nghiệp vụ"],
    ["BI", "Business Intelligence", "Phân tích kinh doanh thông minh"],
    ["BrSE", "Bridge System Engineer", "Kỹ sư cầu nối"],
    ["CI", "Confidence Interval", "Khoảng tin cậy"],
    ["CNTT", "—", "Công nghệ thông tin"],
    ["CSV", "Comma-Separated Values", "Tệp dữ liệu phân tách bằng dấu phẩy"],
    ["DBA", "Database Administrator", "Quản trị cơ sở dữ liệu"],
    ["EDA", "Exploratory Data Analysis", "Phân tích khám phá dữ liệu"],
    ["LLM", "Large Language Model", "Mô hình ngôn ngữ lớn"],
    ["MAE", "Mean Absolute Error", "Sai số tuyệt đối trung bình"],
    ["MAPE", "Mean Absolute Percentage Error", "Sai số phần trăm tuyệt đối trung bình"],
    ["ML", "Machine Learning", "Học máy"],
    ["OLS", "Ordinary Least Squares", "Bình phương tối thiểu thông thường"],
    ["QA/QC", "Quality Assurance / Quality Control", "Đảm bảo / kiểm soát chất lượng"],
    ["R²", "Coefficient of Determination", "Hệ số xác định"],
    ["RMSE", "Root Mean Squared Error", "Căn bậc hai sai số bình phương trung bình"],
    ["UML", "Unified Modeling Language", "Ngôn ngữ mô hình hóa thống nhất"],
    ["VND", "Vietnam Dong", "Đồng Việt Nam"],
  ], [2, 5, 5]),
];

// ============================== LỜI MỞ ĐẦU ==============================
const body = [
  H1("LỜI MỞ ĐẦU", false),
  H3("Lý do chọn đề tài"),
  P("Thị trường tuyển dụng phần mềm thay đổi liên tục theo công nghệ mới: các vị trí liên quan tới dữ liệu, điện toán đám mây và trí tuệ nhân tạo tạo sinh xuất hiện ngày càng nhiều, trong khi một số công nghệ truyền thống giảm sức hút. Người học và lập trình viên cần thông tin định lượng để trả lời ba câu hỏi: công nghệ nào đang được tuyển nhiều, mức lương của mình có tương xứng với thị trường không và nên học thêm kỹ năng gì. Dữ liệu tin tuyển dụng công khai là nguồn phù hợp để trả lời các câu hỏi đó bằng phương pháp khoa học dữ liệu."),
  H3("Mục tiêu nghiên cứu"),
  B("Khai phá dữ liệu tin tuyển dụng CNTT tại Việt Nam: đọc tệp dữ liệu, xử lý chuỗi, bóc tách kỹ năng công nghệ, chuẩn hóa mức lương và kinh nghiệm."),
  B("Trực quan hóa bằng Matplotlib và Seaborn: top công nghệ có nhu cầu và lương cao nhất, tương quan kinh nghiệm – thu nhập, so sánh lương theo vai trò và khu vực."),
  B("Xây dựng và so sánh ít nhất hai mô hình hồi quy, đánh giá bằng ít nhất hai chỉ số; phân tích kỹ năng mang lại giá trị gia tăng thu nhập cao nhất."),
  B("Xây dựng công cụ tư vấn nghề nghiệp: người dùng nhập vai trò, kinh nghiệm, kỹ năng; hệ thống dự đoán mức lương và đề xuất kỹ năng nên học thêm."),
  H3("Đối tượng và phạm vi nghiên cứu"),
  P("Đối tượng là các tin tuyển dụng thuộc nhóm nghề CNTT có công bố khoảng lương. Phạm vi dữ liệu gồm ba bộ dữ liệu công khai, thu thập giai đoạn 2023 và 2025–2026, chủ yếu ở Hà Nội và TP. Hồ Chí Minh. Mức lương được hiểu là **lương chào tuyển** (trung điểm khoảng lương trong tin), đơn vị triệu VND/tháng, chưa phân biệt gross/net. Lương chào tuyển không đồng nghĩa với lương thực nhận."),
  H3("Phương pháp nghiên cứu"),
  P("Đề tài áp dụng quy trình khoa học dữ liệu gồm sáu giai đoạn: thu thập, tiền xử lý, phân tích khám phá, mô hình hóa, đánh giá và triển khai. Dữ liệu được chia theo công ty để tránh rò rỉ thông tin giữa tập huấn luyện và tập kiểm tra; mô hình được chọn trên tập kiểm định và chỉ báo cáo một lần trên tập kiểm tra."),
  H3("Bố cục báo cáo"),
  P("Ngoài Lời mở đầu, Kết luận và Tài liệu tham khảo, báo cáo gồm sáu chương: Chương 1 giới thiệu đề tài, bối cảnh bài toán và quá trình hình thành dự án; Chương 2 trình bày cơ sở lý thuyết; Chương 3 mô tả dữ liệu, các vấn đề của dữ liệu thô và tiền xử lý; Chương 4 trực quan hóa và phân tích; Chương 5 xây dựng, đánh giá và kiểm định mô hình; Chương 6 trình bày thiết kế và xây dựng ứng dụng. Mỗi chương có một mục giải thích các quyết định quan trọng: vấn đề gặp phải, các phương án đã cân nhắc và lý do lựa chọn."),
];

// ============================== CHƯƠNG 1 ==============================
chapter = 1;
body.push(
  H1("CHƯƠNG 1: GIỚI THIỆU"),
  H2("1.1. Bối cảnh"),
  P("Ngành CNTT Việt Nam có nhu cầu tuyển dụng lớn và đa dạng vai trò, từ lập trình Backend, Frontend, Mobile tới kỹ sư dữ liệu, DevOps, AI. Các nền tảng như TopCV, VietnamWorks, ITviec, CareerViet đăng hàng nghìn tin mỗi tháng, phần lớn kèm khoảng lương, yêu cầu kinh nghiệm và kỹ năng. Tuy nhiên dữ liệu này ở dạng văn bản tự do, không thống nhất: lương được ghi \"15 - 25 triệu\", \"Tới 30 triệu\", \"$ 1,000-1,500 /tháng\" hay \"Thỏa thuận\"; kinh nghiệm ghi \"2 năm\", \"Trên 5 năm\" hoặc \"Không yêu cầu\"; kỹ năng nằm rải rác trong tiêu đề và mô tả."),
  H2("1.2. Phát biểu bài toán"),
  P("Bài toán gồm hai phần:"),
  B("**Phân tích xu hướng:** từ tập tin tuyển dụng, thống kê công nghệ được yêu cầu nhiều, công nghệ gắn với lương cao, quan hệ giữa kinh nghiệm và thu nhập, khác biệt lương theo vai trò và khu vực."),
  B("**Dự đoán lương (hồi quy có giám sát):** đầu vào là vai trò, khu vực, số năm kinh nghiệm, cấp bậc và tập kỹ năng; đầu ra là mức lương chào tuyển ước tính (triệu VND/tháng). Mô hình còn được dùng để ước lượng mức tăng lương khi bổ sung từng kỹ năng, làm cơ sở đề xuất kỹ năng nên học."),
  H2("1.3. User story"),
  P("Yêu cầu chức năng chính của ứng dụng được phát biểu dưới dạng user story:"),
  P("*Là một người dùng, tôi muốn có một trang để nhập kỹ năng và kinh nghiệm của mình, phần mềm dựa vào mô hình đã huấn luyện sẵn sẽ dự đoán mức lương và tư vấn các kỹ năng nên cải thiện cho tôi.*"),
  P("Tiêu chí chấp nhận:"),
  B("(1) Người dùng chọn được vai trò, khu vực, số năm kinh nghiệm và nhiều kỹ năng."),
  B("(2) Hệ thống trả về mức lương dự đoán kèm khoảng thường gặp."),
  B("(3) Hệ thống đề xuất tối đa 5 kỹ năng chưa có, kèm mức tăng lương dự đoán và tỉ lệ tin yêu cầu."),
  B("(4) Không huấn luyện lại mô hình khi dự đoán."),
  B("(5) Thời gian phản hồi dưới vài giây."),
  H2("1.4. Hiện trạng dự án trước khi mở rộng"),
  P("Phiên bản thăm dò ban đầu chỉ huấn luyện Ridge và Linear Regression trên 14 nhãn lương đã duyệt tay của 11 công ty (10 train, 2 validation, 2 test). Ridge được chọn theo validation với MAE 10,50 triệu; trên test, Ridge có MAE 21,98 triệu và Linear Regression 17,58 triệu VND/tháng. Vì tập test chỉ có 2 tin, các con số này chỉ minh chứng quy trình chứ chưa đủ để kết luận về khả năng khái quát. Dashboard khi đó chỉ thể hiện được 2 vai trò và chưa có chức năng tư vấn kỹ năng."),
  P("Đề tài này bổ sung các phần còn thiếu: mở rộng dữ liệu từ toàn bộ nguồn sẵn có, loại tin sinh tự động để chỉ giữ 1.735 tin thật có nhãn, gắn nhãn train/validation/test, huấn luyện ba mô hình học máy, đối chiếu với chuẩn production, hiển thị đủ 23 vai trò trên dashboard và xây dựng trang tư vấn theo user story ở trên."),
);

body.push(
  H2("1.5. Quá trình hình thành dự án"),
  P("Dự án không đi thẳng tới phiên bản hiện tại mà qua nhiều vòng quyết định, mỗi vòng giải quyết một vấn đề do vòng trước để lại. Các quyết định được ghi lại thành hồ sơ quyết định kiến trúc (ADR) trong kho mã nguồn; Bảng 1.1 tóm tắt các mốc chính."),
  ...table("Các mốc chính của dự án", ["Ngày", "Quyết định", "Vấn đề dẫn tới quyết định", "Hệ quả"], [
    ["28/10", "Làm lại từ đầu bằng Python và Streamlit", "Ứng dụng cũ dùng mô hình có sẵn, khó giải thích khi báo cáo và không đúng yêu cầu tự huấn luyện", "Mọi mô hình phải tự huấn luyện, giải thích được"],
    ["28/10", "Dùng bộ dữ liệu công khai mới, gom tên gọi tương đương", "Dữ liệu cũ không rõ nguồn gốc; cùng một địa điểm được viết nhiều cách (HCM, Hồ Chí Minh, ho chi minh)", "Có danh mục chuẩn cho địa điểm, vai trò"],
    ["28/10", "Phân tích dữ liệu trước, chặn huấn luyện đến khi nhãn lương đủ bằng chứng", "Nhiều chuỗi lương thiếu đơn vị hoặc kỳ trả, nếu đoán sẽ tạo nhãn sai", "Chỉ 14 nhãn được duyệt tay qua cổng kiểm soát"],
    ["29/10", "Chia tập theo công ty, MAE là chỉ số chính", "Tin của cùng công ty giống nhau, chia ngẫu nhiên làm kết quả lạc quan giả", "Đánh giá trên công ty chưa từng gặp"],
    ["29/10", "Tư vấn kỹ năng theo chênh lệch dự đoán", "Xếp kỹ năng theo số tin nhắc tới chỉ phản ánh độ phổ biến, không phản ánh giá trị", "Cơ sở cho thuật toán tư vấn hiện tại"],
    ["30/10", "Huấn luyện thăm dò Ridge và Linear Regression trên 14 nhãn", "Cần một mô hình chạy được để demo gấp", "MAE test 21,98 triệu trên 2 tin; không học được kinh nghiệm, kỹ năng"],
    ["30/10", "Thu hẹp demo về dự đoán theo nghề và thành phố", "14 nhãn không có số năm kinh nghiệm và gần như không có kỹ năng", "Tạm bỏ tư vấn kỹ năng, không đáp ứng đủ đề bài"],
    ["02/11", "Mở rộng lên 3.809 nhãn từ toàn bộ nguồn sẵn có", "Bản thăm dò không đủ dữ liệu để tin cậy, dashboard chỉ có 2 vai trò", "23 vai trò, ba mô hình, tư vấn kỹ năng"],
    ["06/11", "Ràng buộc lương dự đoán đơn điệu theo kỹ năng", "Thêm kỹ năng Java vào hồ sơ làm lương dự đoán giảm từ 47,7 xuống 42,3 triệu", "Lời tư vấn luôn hợp lý; đổi lại sai số tăng"],
    ["06/11", "Đo độ chính xác của bộ gán nhãn trên 208 tin", "Chưa biết nhãn tự động (lương, vai trò, cấp bậc, kỹ năng) sai bao nhiêu", "Lương và kinh nghiệm đúng 100%; sửa luật vai trò, cấp bậc, kỹ năng"],
    ["06/11", "Đặt chuẩn production theo cách Glassdoor, LinkedIn công bố", "Chỉ có tiêu chí \"thắng mốc trung vị\"; mọi hồ sơ đều nhận một con số dù dữ liệu rất ít", "Ba chỉ số, ngưỡng rõ ràng; chỉ hiện con số khi đủ dữ liệu"],
    ["06/11", "Loại 2.400 tin sinh tự động", "Phát hiện 54% tin có nhãn là tin do máy sinh: URL dạng -hist…, đúng 800 tin mỗi nền tảng, kỹ năng ngẫu nhiên", "Phiên bản hiện tại: 1.735 tin thật, sai số trung thực hơn"],
  ], [1.5, 4, 5.5, 4]),
  P("Bài học rút ra là chiến lược \"ít dữ liệu nhưng duyệt tay từng nhãn\" an toàn về độ chính xác của từng nhãn nhưng thất bại về mục tiêu: 14 mẫu không đủ để mô hình học được ảnh hưởng của kinh nghiệm hay kỹ năng, và 2 tin kiểm tra không đủ để biết mô hình tốt hay xấu. Dự án chuyển sang dùng nhiều dữ liệu với quy tắc chuẩn hóa **minh bạch, có ghi rõ giả định**, rồi bù lại bằng cách **đo sai số nghiêm ngặt** (chia theo công ty, bootstrap, hiệu chuẩn, công bằng theo nhóm, chuẩn production). Bài học thứ hai đến ở cuối dự án: \"nhiều dữ liệu\" chỉ có giá trị khi dữ liệu là thật. Hơn một nửa số tin có nhãn ban đầu là tin do máy sinh, dễ đoán hơn tin thật nên làm số liệu đẹp hơn thực tế; loại chúng đi làm sai số tăng nhưng phản ánh đúng chất lượng mô hình. Mỗi quy tắc và giả định được giải thích ở các mục \"Các quyết định … và lý do\" trong Chương 3, 5 và 6."),
);

// ============================== CHƯƠNG 2 ==============================
chapter = 2;
body.push(
  H1("CHƯƠNG 2: CƠ SỞ LÝ THUYẾT"),
  H2("2.1. Bài toán dự đoán lương chào tuyển"),
  P("Đây là bài toán hồi quy có giám sát: mỗi quan sát gồm các thuộc tính đầu vào của một tin tuyển dụng và một nhãn lương. Gọi tập huấn luyện là"),
  eq([r("D = {("), sb("x", "i"), r(", "), yi(), r(")}, i = 1, …, n")]),
  P("trong đó xᵢ là vector đặc trưng của tin thứ i (vai trò, khu vực, cấp bậc, số năm kinh nghiệm, kỹ năng) và yᵢ là mức lương tháng tương ứng. Mô hình tìm hàm dự đoán f(x) sao cho ŷᵢ = f(xᵢ) gần với nhãn thật. Các thông tin như tiêu đề gốc, tên công ty, mã tin, nguồn và các trường lương không được dùng làm đặc trưng, nhằm hạn chế rò rỉ nhãn hoặc mô hình ghi nhớ danh tính nhà tuyển dụng."),
  H2("2.2. Các mô hình hồi quy"),
  H3("2.2.1. Mốc trung vị huấn luyện"),
  P("Để kiểm tra các mô hình có hữu ích hơn một dự đoán đơn giản hay không, đề tài dùng mốc so sánh dự đoán một giá trị cố định là trung vị nhãn lương của tập huấn luyện:"),
  eq([r("ŷ = median{"), yi(), r(" : i ∈ train}")]),
  P("Trung vị ít nhạy với giá trị cực đoan hơn trung bình. Mốc này chỉ dùng để so sánh; một mô hình học máy chỉ có giá trị khi có sai số thấp hơn rõ rệt so với mốc."),
  H3("2.2.2. Hồi quy Ridge"),
  P("Hồi quy tuyến tính giả định lương là tổ hợp tuyến tính của các đặc trưng. Ridge, do Hoerl và Kennard đề xuất năm 1970, bổ sung thành phần điều chuẩn L2 vào hàm mục tiêu bình phương tối thiểu:"),
  eq([
    sb("min", "w"), r(" "),
    sum(sq([yi(), r(" − "), sb("w", "0"), r(" − "), sp("w", "T"), sb("x", "i")])),
    r(" + α"), sum([new MathSubSuperScript({ children: [r("w")], subScript: [r("j")], superScript: [r("2")] })], "j=1", "p"),
  ]),
  P("Thành phần phạt làm co các hệ số về gần 0, giảm độ nhạy của mô hình với dữ liệu huấn luyện. Khi α tăng, mức điều chuẩn mạnh hơn; nếu α quá lớn, mô hình không nắm bắt đủ quan hệ trong dữ liệu. Ridge phù hợp khi có nhiều đặc trưng nhị phân tương quan, ví dụ các kỹ năng thường đi cùng nhau như React và TypeScript. Đây là mô hình tuyến tính, dễ diễn giải và làm mốc so sánh cho các mô hình phi tuyến."),
  H3("2.2.3. Random Forest"),
  P("Random Forest, do Breiman đề xuất năm 2001, là tập hợp B cây quyết định. Mỗi cây được huấn luyện trên một mẫu bootstrap của tập huấn luyện và tại mỗi nút chỉ xét một tập con đặc trưng ngẫu nhiên; dự đoán là trung bình đầu ra các cây:"),
  eq([r("ŷ(x) = "), frac("1", "B"), sum([sb("T", "b"), r("(x)")], "b=1", "B")]),
  P("Việc lấy trung bình nhiều cây ít tương quan với nhau làm giảm phương sai so với một cây đơn lẻ. Mô hình học được quan hệ phi tuyến và tương tác giữa các đặc trưng (ví dụ kỹ năng AWS có giá trị khác nhau với DevOps và Tester) mà không cần chuẩn hóa thang đo."),
  H3("2.2.4. Gradient Boosting"),
  P("Gradient Boosting, do Friedman đề xuất năm 2001, xây dựng mô hình cộng dồn từ các cây nông. Ở bước m, một cây mới hₘ được khớp với gradient âm của hàm mất mát (với bình phương sai số chính là phần dư) của mô hình hiện tại, rồi được cộng vào với hệ số học ν:"),
  eq([sb("F", "m"), r("(x) = "), sb("F", "m−1"), r("(x) + ν · "), sb("h", "m"), r("(x)")]),
  P("Hệ số học nhỏ cùng số vòng lặp lớn giúp mô hình học dần và hạn chế quá khớp. Đề tài dùng biến thể dựa trên histogram: giá trị của mỗi đặc trưng được chia thành các khoảng rời rạc trước khi tìm điểm cắt, theo ý tưởng của LightGBM, giúp huấn luyện nhanh. Biến thể này hỗ trợ **ràng buộc đơn điệu**: lương dự đoán không được giảm khi số năm kinh nghiệm tăng hoặc khi hồ sơ có thêm một kỹ năng, phù hợp với hiểu biết nghiệp vụ và tránh lộ trình lương hay lời khuyên vô lý khi tư vấn (mục 5.6.4 và 5.6.5)."),
  H2("2.3. Biến đổi biến mục tiêu"),
  P("Phân phối lương lệch phải: phần lớn tin nằm trong 15–35 triệu nhưng có vị trí trên 100 triệu. Đề tài huấn luyện mô hình trên logarit của lương rồi đổi ngược bằng hàm mũ khi dự đoán:"),
  eq([r("z = ln y,     ŷ = exp(f(x))")]),
  P("Khi học trên thang logarit, mô hình tối ưu sai số tương đối thay vì tuyệt đối, nên một sai lệch 5 triệu ở mức 15 triệu được coi trọng hơn cùng sai lệch đó ở mức 80 triệu. Cách làm này giảm ảnh hưởng của các giá trị rất lớn và giữ dự đoán luôn dương."),
  H2("2.4. Biểu diễn đặc trưng"),
  B("**Mã hóa one-hot** cho biến phân loại (vai trò, khu vực, cấp bậc, nền tảng đăng tin, hình thức làm việc, loại công ty): mỗi giá trị trở thành một cột nhị phân. Giá trị chưa gặp khi huấn luyện được bỏ qua thay vì gây lỗi."),
  B("**Mã hóa multi-hot** cho tập kỹ năng: mỗi kỹ năng trong từ điển là một cột nhị phân, một tin có thể bật nhiều cột."),
  B("**Cờ từ khóa chức danh**: bốn cột nhị phân bật khi chức danh có các từ như expert/chuyên gia, principal/staff, head/giám đốc, consultant/tư vấn, vì đây là tín hiệu cấp độ mà cột cấp bậc không thể hiện hết."),
  B("**Điền giá trị thiếu** cho số năm kinh nghiệm bằng trung vị tập huấn luyện, kèm một cột cờ đánh dấu giá trị đã được điền, để mô hình phân biệt \"không ghi\" với \"đúng bằng trung vị\"."),
  B("**Chuẩn hóa thang đo** (trừ trung bình, chia độ lệch chuẩn) cho biến số, chỉ áp dụng với Ridge vì mô hình cây không phụ thuộc thang đo."),
  P("Mọi bước biến đổi chỉ học tham số trên tập huấn luyện và được đóng gói cùng mô hình thành một pipeline, đảm bảo dữ liệu được xử lý giống nhau khi huấn luyện và khi dự đoán."),
  H2("2.5. Thiết kế chia dữ liệu và lựa chọn mô hình"),
  P("Dữ liệu được chia thành ba phần: huấn luyện (train) để fit mô hình, kiểm định (validation) để chọn siêu tham số và chọn mô hình, kiểm tra (test) chỉ dùng một lần để báo cáo kết quả cuối. Giữ riêng tập test giúp tránh lựa chọn mô hình quá khớp với chính tập đánh giá."),
  P("Một công ty thường đăng nhiều tin gần giống nhau với cùng khung lương. Nếu chia ngẫu nhiên theo từng tin, mô hình có thể \"nhớ\" lương của công ty và cho kết quả test lạc quan. Vì vậy đề tài chia theo **nhóm công ty**: mọi tin của một công ty nằm trong cùng một tập, nên tập validation và test gồm các nhà tuyển dụng chưa xuất hiện trong train."),
  P("Tiêu chí chọn mô hình là MAE nhỏ nhất trên validation; RMSE, R² và MAPE được báo cáo kèm theo. Sau khi đã chọn, kết quả test được báo cáo nguyên trạng, không đổi mô hình hay tham số dựa trên kết quả test."),
  H2("2.6. Các chỉ số đánh giá"),
  P("Cho yᵢ là giá trị thực, ŷᵢ là giá trị dự đoán và n là số quan sát."),
  H3("2.6.1. Sai số tuyệt đối trung bình (MAE)"),
  eq([r("MAE = "), frac("1", "n"), sum([r("|"), yi(), r(" − "), yhat(), r("|")])]),
  P("MAE cho biết trung bình mỗi dự đoán lệch bao nhiêu so với nhãn thật, cùng đơn vị triệu VND/tháng nên dễ diễn giải. MAE ít bị một sai số rất lớn chi phối và là chỉ số chính để chọn mô hình."),
  H3("2.6.2. Căn bậc hai sai số bình phương trung bình (RMSE)"),
  eq([r("RMSE = "), new MathRadical({ children: [frac("1", "n"), sum(sq([yi(), r(" − "), yhat()]))] })]),
  P("Do bình phương sai số trước khi lấy trung bình, RMSE nhấn mạnh các dự đoán sai lệch lớn. Đọc RMSE cùng MAE giúp nhận biết một vài sai số lớn có đang ảnh hưởng đáng kể tới chất lượng tổng thể hay không."),
  H3("2.6.3. Hệ số xác định (R²)"),
  eq([sp("R", "2"), r(" = 1 − "), frac([sum(sq([yi(), r(" − "), yhat()]))], [sum(sq([yi(), r(" − ȳ")]))])]),
  P("R² so sánh sai số của mô hình với phương án dự đoán bằng trung bình ȳ. R² càng gần 1 thì mô hình giải thích được càng nhiều biến động của lương; R² bằng 0 tương đương dự đoán bằng trung bình và có thể âm nếu mô hình kém hơn mốc đó."),
  H3("2.6.4. Sai số phần trăm tuyệt đối trung bình (MAPE)"),
  eq([r("MAPE = "), frac("100%", "n"), sum([frac([r("|"), yi(), r(" − "), yhat(), r("|")], [yi()])])]),
  P("MAPE biểu diễn sai số tương đối, cho phép so sánh chất lượng dự đoán giữa mức lương thấp và cao."),
  H3("2.6.5. Đọc chỉ số cùng số mẫu và phạm vi dữ liệu"),
  P("Chỉ số tổng hợp không đảm bảo mô hình hoạt động tốt như nhau ở mọi vai trò, khu vực hay mức kinh nghiệm. Khi báo cáo, cần nêu tập dữ liệu, số quan sát và đơn vị; khi xem sai số theo nhóm, nhóm nhỏ không phải bằng chứng vững chắc về chất lượng."),
  H3("2.6.6. Các chỉ số của chuẩn production"),
  P("Các sản phẩm dự đoán lương thực tế công bố độ chính xác theo cách người dùng dễ hiểu hơn MAE. Glassdoor công bố **trung vị sai số phần trăm** và **tỉ lệ dự đoán sai không quá 20%**; LinkedIn Salary hiển thị **khoảng p10–p90**. Đề tài dùng đúng ba chỉ số này để đối chiếu với chuẩn production (mục 5.5.5):"),
  eq([r("median error % = median"), r("{ |"), yhat(), r(" − "), yi(), r("| / "), yi(), r(" × 100% }")]),
  P("Tỉ lệ sai ≤ 20% là phần trăm số tin có |ŷᵢ − yᵢ| / yᵢ ≤ 0,2. Độ phủ p10–p90 là tỉ lệ tin có lương thật nằm trong khoảng dự đoán 80% (công thức 5.1). Khác với MAE, hai chỉ số đầu không bị vài tin lương rất cao chi phối và trả lời trực tiếp câu hỏi \"dự đoán thường lệch bao nhiêu phần trăm\"."),
  H2("2.7. Diễn giải mô hình"),
  P("**Mức độ quan trọng hoán vị** (permutation importance) đo mức giảm R² trên tập validation khi xáo trộn ngẫu nhiên giá trị của đặc trưng j, làm mất liên hệ giữa đặc trưng đó và nhãn:"),
  eq([sb("I", "j"), r(" = "), sp("R", "2"), r("(D) − "), sp("R", "2"), r("("), sb("D", "(j)"), r(")")]),
  P("trong đó D₍ⱼ₎ là tập validation với cột j đã bị xáo trộn. Iⱼ càng lớn thì mô hình càng phụ thuộc vào đặc trưng j."),
  P("**Giá trị gia tăng của kỹ năng** được ước lượng theo nguyên tắc các yếu tố khác không đổi (ceteris paribus). Gọi Sₖ là tập các tin chưa có kỹ năng k; với mỗi tin, bật kỹ năng k lên và đo chênh lệch lương dự đoán:"),
  eq([sb("Δ", "k"), r(" = "), frac([r("1")], [r("|"), sb("S", "k"), r("|")]), sum([r("[ f("), sb("x", "i"), r(" ⊕ k) − f("), sb("x", "i"), r(") ]")], [r("i ∈ "), sb("S", "k")], null)]),
  P("Δₖ là mức tăng lương trung bình mà mô hình gán cho kỹ năng k khi giữ nguyên vai trò, kinh nghiệm và khu vực. Đây là quan hệ tương quan học từ dữ liệu, không phải quan hệ nhân quả."),
  H2("2.8. Phân tích khám phá dữ liệu"),
  P("Phân tích khám phá dữ liệu (EDA) do John Tukey đề xướng năm 1977 là cách tiếp cận tóm tắt các đặc trưng cơ bản của dữ liệu bằng đồ họa và thống kê mô tả trước khi xây dựng mô hình. EDA giúp hiểu phân phối của biến mục tiêu, phát hiện giá trị ngoại lệ và tìm quan hệ giữa các biến đầu vào với lương. Đề tài chọn loại biểu đồ theo câu hỏi phân tích:"),
  ...table("Câu hỏi phân tích và loại biểu đồ tương ứng", ["Câu hỏi phân tích", "Loại biểu đồ", "Lý do chọn"], [
    ["Lương phân bố thế nào?", "Histogram", "Thấy hình dạng phân phối, độ lệch và đuôi"],
    ["Công nghệ nào được tuyển nhiều, trả cao?", "Biểu đồ cột ngang", "So sánh nhiều hạng mục có tên dài"],
    ["Kinh nghiệm liên quan thế nào tới lương?", "Boxplot theo nhóm năm và đường trung vị", "Thấy cả xu hướng trung tâm và độ phân tán"],
    ["Lương khác nhau giữa các vai trò?", "Boxplot ngang theo vai trò", "So sánh phân phối của 23 nhóm"],
    ["Lương khác nhau theo vai trò và khu vực?", "Heatmap", "Thể hiện bảng hai chiều bằng cường độ màu"],
  ], [5, 4, 6]),
  P("Mức độ liên hệ đơn điệu giữa kinh nghiệm và lương được đo bằng hệ số tương quan hạng Spearman, phù hợp khi quan hệ không nhất thiết tuyến tính và dữ liệu có ngoại lệ:"),
  eq([r("ρ = 1 − "), frac([r("6"), sum([sp([sb("d", "i")], "2")])], [r("n("), sp("n", "2"), r(" − 1)")])]),
  P("trong đó dᵢ là chênh lệch giữa hạng của tin thứ i theo kinh nghiệm và theo lương."),
  H2("2.9. Công cụ và thư viện"),
  ...table("Công nghệ sử dụng trong đề tài", ["Thành phần", "Phiên bản", "Vai trò trong đề tài"], [
    ["Python", "3.11", "Ngôn ngữ lập trình chính"],
    ["Pandas", "3.1.0", "Đọc tệp CSV, làm sạch, gộp, khử trùng lặp, thống kê theo nhóm"],
    ["NumPy", "2.4.6", "Tính toán số, biến đổi logarit, phân vị, bootstrap"],
    ["Matplotlib", "3.11.2", "Vẽ biểu đồ nền, lộ trình lương, so sánh mô hình"],
    ["Seaborn", "0.13.2", "Biểu đồ thống kê: boxplot, heatmap, histogram, biểu đồ cột"],
    ["scikit-learn", "1.9.1", "Pipeline tiền xử lý, Ridge, Random Forest, Gradient Boosting, các chỉ số đánh giá"],
    ["joblib", "1.6.0", "Lưu và nạp mô hình đã huấn luyện"],
    ["Streamlit", "1.66.1", "Ứng dụng web: dashboard và trang tư vấn"],
    ["pytest", "9.2.0", "Kiểm thử tự động"],
    ["draw.io", "—", "Vẽ sơ đồ kiến trúc, UML, lưu đồ"],
  ], [3, 2, 8]),
  H2("2.10. Ký hiệu sơ đồ"),
  P("Các sơ đồ được vẽ bằng draw.io theo ký hiệu UML 2.5 (sơ đồ use case, tuần tự, lớp) và ký hiệu lưu đồ chuẩn: hình bầu dục cho bắt đầu/kết thúc, hình bình hành cho nhập/xuất, hình chữ nhật cho xử lý, hình thoi cho rẽ nhánh."),
);

// ============================== CHƯƠNG 3 ==============================
chapter = 3;
body.push(
  H1("CHƯƠNG 3: DỮ LIỆU VÀ TIỀN XỬ LÝ"),
  H2("3.1. Nguồn dữ liệu"),
  P("Dữ liệu là ba tệp tin tuyển dụng công khai trên Kaggle."),
  ...table("Ba nguồn dữ liệu thô", ["Nguồn, tác giả", "Nền tảng", "Quy mô", "Giấy phép"], [
    ["Vietnam IT Jobs – Raw Data from TopCV (2026), Châu Gia Bảo", "TopCV", "1.550 dòng, 7 cột", "CC BY 4.0"],
    ["ADY201m Dataset / vietnam-it-job-posts, Việt Thành Nguyễn", "VietnamWorks, ITviec, YBox, TopCV, CareerViet", "6.779 dòng, 19 cột", "MIT"],
    ["Vietnamese Job Posting (2023), Nguyen Tran Huu Thinh", "CareerBuilder", "2.056 dòng, 20 cột", "CC0"],
  ], [6, 4.5, 2.5, 2]),
  P("Bộ TopCV 2026 có bảy cột: tiêu đề, công ty, địa điểm, kinh nghiệm, lương, ngày đăng và đường dẫn; bộ này không có mô tả công việc nên kỹ năng chỉ được bóc từ tiêu đề. Bộ vietnam-it-job-posts có thêm cấp bậc, danh sách kỹ năng dạng JSON, yêu cầu công việc và nền tảng nguồn. Bộ CareerBuilder 2023 có mô tả, yêu cầu và thẻ công việc ở dạng HTML; đề tài chỉ giữ các tin có ngành chứa \"CNTT\"."),
  H3("3.1.1. Các vấn đề của dữ liệu thô"),
  P("Trước khi xử lý, nhóm rà soát ba tệp thô và phát hiện nhiều vấn đề khiến không thể đưa dữ liệu trực tiếp vào mô hình. Bảng 3.2 liệt kê từng vấn đề kèm ví dụ nguyên văn, quy mô và cách xử lý; số liệu được đếm lại trên toàn bộ 10.385 dòng thô."),
  ...table("Các vấn đề của dữ liệu thô và cách xử lý", ["Vấn đề", "Ví dụ nguyên văn", "Quy mô", "Cách xử lý"], [
    ["Lương không có con số", "\"Thỏa thuận\", \"Thương lượng\", \"Lương: Cạnh tranh\"", "3.736 dòng (36%)", "Loại khỏi nhãn huấn luyện, vẫn dùng cho thống kê nhu cầu kỹ năng"],
    ["Lương ghi theo nhiều định dạng", "\"15 - 25 triệu\", \"Lương: 10 Tr - 15 Tr VND\", \"15tr-25tr ₫/tháng\", \"Tới 30 triệu\"", "32 mẫu định dạng khác nhau", "Bộ chuẩn hóa nhận diện số, đơn vị, kỳ trả (mục 3.3)"],
    ["Lỗi chính tả trong lương", "\"8 triẹu - 10 triẹu/tháng\"", "264 dòng", "Chữ \"triẹu\" còn lưu theo kiểu Unicode tổ hợp (nhìn giống nhưng khác byte); bộ đọc lương dựa vào con số và từ khóa kỳ trả nên không phụ thuộc cách viết chữ \"triệu\""],
    ["Lương bằng USD hoặc theo năm", "\"$ 1,000-1,500 /tháng\", \"200tr-500tr ₫/năm\"", "352 dòng USD, 30 dòng theo năm", "Quy đổi theo tỷ giá của năm dữ liệu; chia 12 với lương năm"],
    ["Khoảng lương giả, quá rộng", "\"1 triẹu - 40 triẹu/tháng\" (111 dòng), \"2-10 Triệu\"", "322 dòng", "Loại khi cận trên gấp hơn 3 lần cận dưới"],
    ["Tin sinh tự động (giả)", "URL dạng \"…-hist201800001\"; đúng 800 tin mỗi nền tảng TopCV, VietnamWorks, CareerViet; ngày đăng rải đều 2018–2025; danh sách kỹ năng ngẫu nhiên; không có mô tả", "2.400 dòng (35% bộ IT Jobs 2026)", "Loại khỏi bộ dữ liệu (mục 3.10.6)"],
    ["Mô tả chứa mã HTML", "\"<p>- Nam/Nữ từ 25-35 tuổi<br>…\"", "2.038/2.056 tin CareerBuilder", "Bỏ thẻ HTML trước khi tìm kỹ năng"],
    ["Tin trùng lặp", "Cùng chức danh và công ty xuất hiện nhiều lần trong bộ 6.779 tin", "850 cặp trùng chức danh + công ty", "Khử trùng theo chức danh, công ty và lương (mục 3.7)"],
    ["Tên công ty, chức danh dính nhãn quảng cáo", "\"Pro\\nCÔNG TY CỔ PHẦN CHỨNG KHOÁN VPS\", \"GẤP\\nUnity Developer\"", "238 công ty, 14 chức danh", "Bỏ tiền tố, gộp khoảng trắng, chuẩn hóa khóa công ty"],
    ["Địa điểm theo địa giới mới", "\"Hồ Chí Minh (mới)\", \"Bắc Ninh (mới)\"", "774 dòng", "Gom về 5 nhãn khu vực"],
    ["Cột kinh nghiệm chứa nhầm cấp bậc", "CareerBuilder: cột kinh nghiệm ghi \"Nhân viên\", \"Quản lý\"", "245 dòng", "Không đọc được số năm thì để trống, tìm thêm trong chức danh"],
    ["TP. Hồ Chí Minh ít công bố lương", "Phần lớn tin ghi \"Thương lượng\"", "Chỉ 29,3% tin TP. HCM đọc được lương, so với 73,1% ở Hà Nội", "Không xử lý được bằng kỹ thuật; ghi rõ là hạn chế khi so sánh khu vực"],
    ["Tin ngoài ngành CNTT", "Bộ CareerBuilder gồm kế toán, bán hàng; bộ IT Jobs có 583 tin ngành Ngân hàng – Tài chính", "CareerBuilder chỉ 194/2.056 tin thuộc CNTT", "Lọc theo ngành và theo chức danh (mục 3.4)"],
    ["Danh sách kỹ năng bất thường", "Kỹ năng \"Rust\" xuất hiện trong tin Java, PHP, .NET; Android Developer có Swift, React", "Phần lớn nằm ở tin sinh tự động; trong tin thật còn 28 tin có Rust", "Loại tin sinh tự động; ghi rõ khi diễn giải kết quả Rust"],
    ["Điều kiện giới tính trong tin", "\"Giới tính: Nam\", \"Tester Game Chỉ Tuyển Nữ\"", "222 dòng thô; 7 trong 1.735 tin có nhãn", "Gắn nhãn riêng để kiểm tra, không dùng làm đặc trưng (mục 5.5.4)"],
  ], [3.2, 4.8, 3, 4.5]),
  P("Ba vấn đề cuối không thể \"sửa\" hoàn toàn bằng xử lý dữ liệu mà phải ghi nhận và kiểm soát khi diễn giải. Vấn đề TP. Hồ Chí Minh ít công bố lương làm bộ dữ liệu lệch về Hà Nội; vấn đề điều kiện giới tính là dấu hiệu phân biệt trong tuyển dụng, được phân tích riêng ở mục 5.5.4. Vấn đề tin sinh tự động được phát hiện muộn nhất và có ảnh hưởng lớn nhất, trình bày ở mục 3.10.6."),
  H2("3.2. Quy trình tiền xử lý tổng quát"),
  P("Ba tệp có cấu trúc cột khác nhau nên trước hết được đưa về một lược đồ trung gian chung gồm tiêu đề, công ty, địa điểm, chuỗi lương, chuỗi kinh nghiệm, cấp bậc gốc, năm dữ liệu và phần văn bản chứa kỹ năng. Chuẩn hóa chạy trên từng tin trước khi gom tin trùng và chia tập. Quy trình được thể hiện ở Hình 3.1 và gồm các bước:"),
  ...steps([
    "Đọc ba tệp CSV bằng Pandas, ánh xạ cột của từng nguồn về lược đồ chung.",
    "Loại tin sinh tự động của bộ IT Jobs 2026 (đường dẫn dạng …-hist…).",
    "Chuẩn hóa chuỗi lương về khoảng triệu VND/tháng; loại tin không đọc được lương.",
    "Phân loại vai trò CNTT theo chức danh; loại tin ngoài ngành.",
    "Chuẩn hóa số năm kinh nghiệm, suy ra cấp bậc, chuẩn hóa khu vực, nền tảng, hình thức làm việc, loại công ty, bóc tách kỹ năng.",
    "Khử tin trùng lặp.",
    "Gắn nhãn train, validation hoặc test theo nhóm công ty.",
    "Ghi bộ dữ liệu sạch kèm tệp tóm tắt (số dòng, phễu làm sạch, mã băm SHA-256) để đối chiếu.",
  ]),
  ...fig(path.join(DIA, "03-luu-do-tien-xu-ly.png"), "Lưu đồ tiền xử lý dữ liệu", 9.5),
  H2("3.3. Chuẩn hóa mức lương"),
  P("Chuỗi lương được chuyển về chữ thường và bỏ tiền tố \"Lương:\". Lỗi chính tả \"triẹu\" trong dữ liệu thô được lưu theo kiểu Unicode tổ hợp (chữ e cộng dấu nặng rời), nên thay chuỗi trực tiếp không bắt được; vì vậy bộ chuẩn hóa không dựa vào chữ \"triệu\" mà dựa vào con số: số từ 100.000 trở lên được hiểu là đồng, số nhỏ hơn được hiểu là triệu. Sau đó bộ chuẩn hóa nhận diện đơn vị tiền (VND hoặc USD), kỳ trả (tháng hoặc năm) và các con số, rồi suy ra cận dưới, cận trên và trung điểm theo các quy tắc ở Bảng 3.3. Trung điểm là nhãn huấn luyện."),
  ...table("Quy tắc chuẩn hóa lương", ["Dạng ghi trong tin", "Cách xử lý", "Ví dụ (triệu VND/tháng)"], [
    ["Thỏa thuận, thương lượng, cạnh tranh", "Không có số → loại khỏi nhãn", "—"],
    ["Khoảng hai đầu: \"15 - 25 triệu\", \"10 Tr - 15 Tr VND\"", "Lấy trung điểm", "15 – 25 → 20"],
    ["Chỉ cận trên: \"Tới 30 triệu\", \"Dưới 22 Tr\"", "Cận dưới = cận trên ÷ hệ số của nguồn (1,27–1,67), học từ tin ghi đủ hai đầu trên tập train", "TopCV 2026 (hệ số 1,5): 20 – 30 → 25"],
    ["Chỉ cận dưới: \"Từ 20 triệu\", \"Trên 12 Tr\"", "Cận trên = cận dưới × hệ số của nguồn", "TopCV 2026: 20 – 30 → 25"],
    ["USD: \"$ 1,000-1,500 /tháng\"", "Quy đổi theo tỷ giá của năm dữ liệu (26.000 VND/USD năm 2026)", "26 – 39 → 32,5"],
    ["Theo năm: \"240tr-360tr ₫/năm\"", "Chia 12", "20 – 30 → 25"],
    ["Khoảng quá rộng: \"1 triệu - 40 triệu/tháng\"", "Cận trên gấp hơn 3 lần cận dưới → loại vì không mang thông tin", "—"],
    ["Trung điểm dưới 3 hoặc trên 150 triệu", "Coi là lỗi nhập → loại", "—"],
  ], [5.5, 6, 3.5]),
  H2("3.4. Phân loại vai trò"),
  P("Vai trò được gán bằng tập luật biểu thức chính quy áp dụng lên chức danh. Các luật được xét **theo thứ tự ưu tiên từ cụ thể tới chung** và dừng ở luật đầu tiên khớp. Ví dụ luật Data Engineer đứng trước luật Backend Developer, nên chức danh \"Python Data Engineer\" được gán Data Engineer chứ không phải Backend; luật Kiểm thử đứng trước luật Game nên \"Game Tester\" được gán Kiểm thử. Chức danh chứa từ khóa ngoài ngành như sales, kinh doanh, kế toán, tuyển dụng, giáo viên bị loại trước khi xét luật. Kết quả gồm 23 vai trò (Bảng 3.6)."),
  H2("3.5. Bóc tách kỹ năng công nghệ"),
  P("Đề tài xây dựng từ điển 69 kỹ năng chia thành các nhóm: ngôn ngữ lập trình (Python, Java, JavaScript, C#, Go…), framework (React, Spring Boot, .NET, Django…), cơ sở dữ liệu (MySQL, PostgreSQL, MongoDB…), điện toán đám mây và DevOps (AWS, Azure, Docker, Kubernetes, CI/CD…), dữ liệu và AI (Spark, Airflow, Power BI, Machine Learning, LLM/GenAI…), công cụ và phương pháp (Git, Jira, Agile/Scrum) và ngoại ngữ (tiếng Anh, tiếng Nhật). Mỗi kỹ năng có một mẫu nhận dạng gom các cách viết khác nhau (ví dụ \"reactjs\", \"react.js\"). Nguyên tắc nhận dạng:"),
  B("Văn bản được xét gồm tiêu đề, danh sách kỹ năng có sẵn, yêu cầu và mô tả công việc sau khi bỏ thẻ HTML."),
  B("Mẫu nhận dạng dùng **ranh giới từ** để tên ngắn không khớp nhầm bên trong từ dài, và phân biệt các cặp dễ nhầm: Java khác JavaScript, React khác React Native, C++ khác C#."),
  B("Các tên quá ngắn và đa nghĩa như C, R, Go không dùng riêng; Go chỉ nhận ở dạng \"Golang\"."),
  P("Kết quả có 65,8% số tin nhận được ít nhất một kỹ năng. Tỉ lệ này thấp chủ yếu vì bộ TopCV 2026 (596 tin) chỉ có chức danh, không có mô tả công việc. Ngoài ra, một ngôn ngữ chỉ được nhắc ở phần phúc lợi (ví dụ \"phụ cấp tiếng Nhật\") không được tính là yêu cầu, và \"API Testing\", \"OpenAI API\" không bị nhận nhầm thành REST API."),
  H2("3.6. Kinh nghiệm, cấp bậc và khu vực"),
  ...table("Quy tắc chuẩn hóa kinh nghiệm", ["Dạng ghi trong tin", "Giá trị (năm)"], [
    ["Không yêu cầu, chưa có kinh nghiệm", "0"],
    ["Dưới N năm", "N / 2 (ví dụ \"Dưới 1 năm\" → 0,5)"],
    ["Trên N năm", "N + 1"],
    ["Khoảng a – b năm", "(a + b) / 2"],
    ["Một số N", "N (loại bỏ nếu lớn hơn 20)"],
    ["Trống", "Tìm mẫu \"N+ YoE\", \"N years\" trong tiêu đề; nếu không có thì để thiếu"],
  ], [7, 8]),
  P("Chỉ 57 trên 1.735 tin (3,3%) thiếu kinh nghiệm; giá trị thiếu được điền ở bước huấn luyện như mô tả ở mục 2.4."),
  P("**Cấp bậc** gồm bảy mức Intern, Fresher, Junior, Middle, Senior, Lead và Manager. Cấp bậc ghi trong chức danh (ví dụ \"Senior\", \"Trưởng nhóm\", \"Thực tập\") được ưu tiên hơn trường cấp bậc của nguồn, vì nguồn hay ghi sai (\"Senior …\" bị nguồn ghi là Trưởng nhóm). \"Product/Project/Delivery Manager\" là một vai trò chứ không phải cấp Manager. Nguồn ghi Intern/Fresher nhưng tin yêu cầu hơn một năm kinh nghiệm thì bỏ qua cấp bậc của nguồn. Nếu không có thông tin, cấp bậc được suy từ số năm: dưới 1 năm là Fresher, dưới 2,5 năm là Junior, dưới 4,5 năm là Middle, còn lại là Senior."),
  P("**Khu vực** được gom về năm nhãn: Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Remote và Tỉnh/thành khác. Các cách viết tương đương (hcm, tp.hcm, ho chi minh, sài gòn; ha noi, hanoi) được quy về cùng một nhãn. Tin ghi nhiều thành phố lấy thành phố lớn đầu tiên được nhắc tới."),
  P("Ba thuộc tính được bổ sung ở vòng cuối để mô hình có thêm thông tin về nơi tuyển: **nền tảng đăng tin** (ITviec, VietnamWorks, TopCV, TopCV 2026 tách riêng vì chỉ có chức danh, CareerBuilder); **hình thức làm việc** (toàn thời gian, từ xa, không rõ) đọc từ trường hình thức và chức danh; **loại công ty** (ngân hàng/tài chính, outsourcing, công ty nước ngoài, khác) suy từ tên công ty và lĩnh vực. Trung vị lương khác nhau rõ giữa các nền tảng: VietnamWorks 29 triệu, ITviec 27 triệu, TopCV 2026 khoảng 22 triệu."),
  H2("3.7. Khử trùng lặp"),
  P("Một tin có thể được đăng lại hoặc xuất hiện trên nhiều nền tảng. Hai tin được coi là trùng khi cùng tiêu đề đã chuẩn hóa (chữ thường, bỏ ký tự đặc biệt), cùng công ty đã chuẩn hóa và cùng mức lương; chỉ bản đầu tiên được giữ lại. Bước này loại 36 tin."),
  H2("3.8. Quy trình chia train, validation và test"),
  P("Tỷ lệ mục tiêu là 70% train, 15% validation và 15% test, chia theo nhóm công ty. Thay vì xáo trộn ngẫu nhiên phụ thuộc thứ tự dòng, đề tài dùng **hàm băm**: kết quả chia chỉ phụ thuộc tên công ty và hạt giống cố định, nên luôn tái lập được kể cả khi dữ liệu được đọc theo thứ tự khác hoặc bổ sung tin mới. Các bước:"),
  ...steps([
    "Chuẩn hóa tên công ty: chữ thường, gộp khoảng trắng, bỏ tiền tố quảng cáo như \"Pro\", \"Hot\", bỏ ký tự đặc biệt.",
    "Tính mã băm SHA-256 của chuỗi gồm hạt giống 42 và tên công ty đã chuẩn hóa.",
    "Lấy 8 ký tự hex đầu của mã băm, đổi thành số thực trong đoạn [0, 1].",
    "Gán công ty vào train nếu số đó nhỏ hơn 0,70; vào validation nếu nhỏ hơn 0,85; còn lại vào test.",
    "Mọi tin của công ty nhận cùng nhãn tập.",
  ]),
  P("Vì hàm băm phân bố gần đều, tỷ lệ thực tế xấp xỉ tỷ lệ mục tiêu (Bảng 3.7) và không công ty nào xuất hiện ở hai tập."),
  H2("3.9. Kết quả làm sạch"),
  ...table("Phễu làm sạch dữ liệu", ["Bước", "Số tin", "Tỉ lệ so với thô"], [
    ["Đọc ba nguồn thô (CareerBuilder chỉ nhóm CNTT)", "8.523", "100%"],
    ["Sau khi loại 2.400 tin sinh tự động", "6.123", "71,8%"],
    ["Có mức lương đọc được", "2.811", "33,0%"],
    ["Thuộc 23 vai trò CNTT", "1.771", "20,8%"],
    ["Sau khử trùng lặp", "1.735", "20,4%"],
  ], [8, 2, 2.5], [0, R, R]),
  ...table("Số tin và trung vị lương theo vai trò", ["Vai trò", "Số tin", "Trung vị (triệu)", "Trung bình (triệu)"], [
    ["Data Engineer", "26", "41,6", "44,6"], ["Quản lý IT / CTO", "13", "40,0", "51,3"],
    ["Tech Lead / Architect", "75", "39,0", "43,8"], ["BrSE / Cầu nối", "23", "32,5", "33,6"],
    ["Quản trị CSDL (DBA)", "5", "32,5", "30,2"], ["Quản lý dự án / sản phẩm", "65", "32,5", "38,1"],
    ["DevOps / Cloud", "73", "32,5", "35,2"], ["AI / ML Engineer", "80", "29,3", "35,2"],
    ["Fullstack Developer", "119", "28,5", "30,4"], ["Bảo mật", "57", "25,5", "32,5"],
    ["Frontend Developer", "105", "25,0", "27,3"], ["Backend Developer", "278", "25,0", "27,0"],
    ["Mobile Developer", "125", "25,0", "28,3"], ["Business Analyst", "130", "25,0", "26,2"],
    ["Data Analyst / BI", "24", "23,0", "23,6"], ["Embedded / IoT", "45", "22,0", "24,9"],
    ["UI/UX Designer", "11", "21,5", "23,8"], ["Kiểm thử (QA/QC)", "198", "20,0", "21,2"],
    ["ERP / SAP Consultant", "31", "20,0", "25,4"], ["Quản trị hệ thống / Mạng", "57", "20,0", "21,9"],
    ["Software Engineer (chung)", "96", "19,3", "24,4"], ["Game Developer", "25", "15,0", "18,0"],
    ["IT Support / Helpdesk", "74", "13,6", "15,3"],
  ], [6, 2, 3, 3], [0, R, R, R]),
  ...table("Thành phần ba tập dữ liệu", ["Tập", "Số tin", "Số công ty", "Tỷ lệ tin", "Mục đích"], [
    ["Train", "1.169", "442", "67,4%", "Huấn luyện mô hình"],
    ["Validation", "278", "108", "16,0%", "Chọn siêu tham số và chọn mô hình"],
    ["Test", "288", "121", "16,6%", "Báo cáo kết quả cuối, chấm chuẩn production"],
    ["Toàn bộ", "1.735", "671", "100%", ""],
  ], [2.5, 2, 2, 2, 6], [0, R, R, R]),
  P("Tỷ lệ tin lệch nhẹ so với 70/15/15 vì chia theo công ty: một công ty có nhiều tin phải nằm trọn trong một tập. Tỷ lệ theo số công ty là 65,9% / 16,1% / 18,0%."),
  ...fig(path.join(FIG, "split.png"), "Phân bố nhãn train/validation/test theo vai trò", 13),
  ...table("Từ điển dữ liệu của bộ dữ liệu sạch", ["Trường", "Kiểu", "Mô tả"], [
    ["row_id", "chuỗi", "Khóa bản ghi"],
    ["source, platform", "chuỗi, phân loại (5)", "Bộ dữ liệu gốc và nền tảng đăng tin"],
    ["source_url", "chuỗi", "Đường dẫn gốc, dùng để nhận diện tin sinh tự động"],
    ["company_type", "phân loại (4)", "Loại công ty suy từ tên và lĩnh vực"],
    ["work_mode", "phân loại", "Hình thức làm việc"],
    ["title, company", "chuỗi", "Chức danh và tên công ty gốc"],
    ["company_key", "chuỗi", "Khóa công ty chuẩn hóa, dùng để chia tập"],
    ["role", "phân loại (23)", "Vai trò CNTT"],
    ["region", "phân loại (5)", "Khu vực làm việc"],
    ["experience_years", "số thực", "Số năm kinh nghiệm yêu cầu, có thể thiếu"],
    ["level", "phân loại (7)", "Cấp bậc"],
    ["year", "số nguyên", "Năm dữ liệu (2023, 2025, 2026)"],
    ["skills, skill_count", "chuỗi, số nguyên", "Danh sách kỹ năng và số kỹ năng"],
    ["gender_requirement", "phân loại (6)", "Điều kiện giới tính ghi trong tin; chỉ dùng để kiểm tra, không làm đặc trưng"],
    ["salary_text", "chuỗi", "Chuỗi lương gốc để đối chiếu"],
    ["one_sided", "đúng/sai", "Tin chỉ ghi một đầu lương; đầu còn lại được suy bằng hệ số của nguồn"],
    ["salary_min, salary_max, salary", "số thực", "Cận dưới, cận trên, trung điểm (triệu VND/tháng)"],
    ["split", "phân loại (3)", "train / valid / test"],
  ], [4.5, 3, 7]),
  ...fig(path.join(DIA, "08-luoc-do-du-lieu.png"), "Lược đồ dữ liệu", 14),
);

body.push(
  H2("3.10. Các quyết định xử lý dữ liệu và lý do"),
  P("Mỗi quyết định dưới đây được trình bày theo trình tự: vấn đề gặp phải, các phương án đã cân nhắc, phương án chọn, lý do và rủi ro còn lại."),
  ...decision("3.10.1. Bỏ bộ 14 nhãn duyệt tay, gộp ba nguồn dữ liệu", {
    problem: "Bản thăm dò chỉ có 14 tin có nhãn lương. Tập kiểm tra chỉ có 2 tin nên MAE 21,98 triệu có thể thay đổi hoàn toàn nếu đổi một tin; không tin nào có số năm kinh nghiệm nên mô hình không thể học ảnh hưởng của kinh nghiệm, trong khi đề bài yêu cầu tư vấn theo kinh nghiệm và kỹ năng.",
    options: "(1) Tiếp tục duyệt tay thêm nhãn: chính xác từng nhãn nhưng chậm, sau nhiều ngày vẫn chỉ được vài chục tin. (2) Thu thập dữ liệu mới bằng cách cào web: mất thời gian, rủi ro pháp lý. (3) Dùng toàn bộ tin có lương trong ba tệp sẵn có, chuẩn hóa bằng quy tắc minh bạch.",
    choice: "Phương án 3, ban đầu thu được 3.809 tin có nhãn; sau khi loại tin sinh tự động (mục 3.10.6) còn 1.735 tin thật.",
    reason: "Với bài toán thống kê, số lượng mẫu quyết định độ tin cậy của kết luận. Một nhãn lệch vài triệu do quy tắc chuẩn hóa ảnh hưởng ít tới mô hình học trên hàng nghìn tin, nhưng thiếu mẫu thì không thể học được gì. Giống một người mới vào nghề định giá lương: nghe 14 người kể lương thì không thể đoán đúng, nghe 3.800 người thì dù vài người nói hơi sai vẫn nắm được mặt bằng chung.",
    risk: "Nhãn kém chính xác hơn duyệt tay. Rủi ro này được kiểm soát bằng cách ghi rõ từng quy tắc và đo sai số trên tập kiểm tra tách theo công ty, có khoảng tin cậy bootstrap và đối chiếu chuẩn production.",
  }),
  ...decision("3.10.2. Lấy trung điểm khoảng lương làm nhãn", {
    problem: "Tin tuyển dụng ghi khoảng lương (15–25 triệu) chứ không ghi một con số, trong khi mô hình hồi quy cần một giá trị mục tiêu.",
    options: "(1) Dùng cận dưới: thiên thấp. (2) Dùng cận trên: thiên cao, giống \"mức trần\" ít người đạt. (3) Dùng trung điểm. (4) Dự đoán cả hai cận bằng hai mô hình.",
    choice: "Trung điểm, đồng thời vẫn lưu cận dưới và cận trên.",
    reason: "Trung điểm là giá trị đại diện tự nhiên nhất khi không biết người được tuyển sẽ nhận mức nào trong khoảng; đây cũng là cách nhà tuyển dụng thường nói \"lương khoảng 20 triệu\". Hai mô hình riêng cho hai cận làm gấp đôi độ phức tạp mà không giúp người dùng nhiều hơn khoảng thường gặp ở mục 6.4.",
    risk: "Mất thông tin về độ rộng khoảng; người có kỹ năng mạnh thường nhận gần cận trên.",
  }),
  ...decision("3.10.3. Ước lượng cận còn thiếu bằng hệ số theo từng nguồn", {
    problem: "Nhiều tin chỉ ghi một cận như \"Tới 30 triệu\" hay \"Từ 20 triệu\". Nếu loại hết sẽ mất một phần đáng kể tin có lương, đặc biệt ở TopCV.",
    options: "(1) Loại các tin này. (2) Coi cận đã biết là lương. (3) Ước lượng cận còn lại theo tỉ lệ cố định 70% / 130% (cách làm ban đầu). (4) Ước lượng theo tỉ lệ cao/thấp điển hình của từng nguồn, học từ chính các tin ghi đủ hai đầu.",
    choice: "Phương án 4: hệ số là trung vị của tỉ lệ cận trên / cận dưới ở các tin ghi đủ hai đầu thuộc tập train của từng nguồn, từ 1,27 (ITviec) tới 1,67 (TopCV, VietnamWorks). \"Tới X\" được hiểu là X ÷ hệ số – X, \"Từ X\" là X – X × hệ số.",
    reason: "Coi \"Tới 30 triệu\" là 30 triệu sẽ thổi phồng lương vì đó là mức trần. Tỉ lệ cố định 70% được chọn ban đầu vì đơn giản, nhưng các nguồn ghi khoảng lương rất khác nhau: ITviec hay ghi khoảng hẹp, TopCV hay ghi khoảng rộng. Học hệ số từ chính dữ liệu của nguồn đó giống cách một người quen thị trường đoán \"tin TopCV ghi tới 30 thì thường là 18–30\". Hệ số chỉ học trên tập train để không nhìn trước tập kiểm tra.",
    risk: "Vẫn là giả định, có thể sai với từng tin: ví dụ một tin \"Từ 30 triệu\" mà chức danh ghi đúng 30 triệu vẫn được hiểu là một khoảng. 13,8% số tin chỉ ghi một đầu lương.",
  }),
  ...decision("3.10.4. Loại các khoảng lương quá rộng", {
    problem: "111 tin ghi \"1 triệu - 40 triệu/tháng\", 64 tin \"1 triệu - 8 triệu/tháng\". Đây là giá trị mặc định của biểu mẫu đăng tin, không phải lương thật; trung điểm 20,5 triệu sẽ là nhãn vô nghĩa.",
    options: "(1) Giữ nguyên. (2) Loại theo danh sách chuỗi cụ thể. (3) Loại theo quy tắc chung: cận trên gấp hơn 3 lần cận dưới.",
    choice: "Quy tắc chung với ngưỡng gấp 3 lần, loại 322 dòng.",
    reason: "Quy tắc chung bắt được cả những dạng chưa thấy trong danh sách. Trong thực tế, một vị trí hiếm khi trả lương chênh nhau quá 3 lần giữa mức thấp và cao; khoảng rộng hơn cho thấy nhà tuyển dụng không muốn công bố lương.",
    risk: "Có thể loại nhầm vài tin có khoảng thật sự rộng (ví dụ \"10 – 35 triệu\" cho nhiều cấp bậc).",
  }),
  ...decision("3.10.5. Phân loại vai trò bằng luật có thứ tự ưu tiên", {
    problem: "Bản thăm dò chỉ có 7 vai trò, nhiều tin như Business Analyst, Bảo mật, Embedded bị xếp \"ngoài phạm vi\", làm dashboard chỉ vẽ được 2 vai trò. Chức danh lại rất đa dạng và lẫn tiếng Anh, tiếng Việt.",
    options: "(1) Gán tay từng tin: chính xác nhưng không làm nổi với hàng nghìn tin. (2) Huấn luyện mô hình phân loại văn bản: cần dữ liệu đã gán nhãn mà dự án không có. (3) Luật biểu thức chính quy có thứ tự ưu tiên.",
    choice: "Luật có thứ tự, 23 vai trò.",
    reason: "Luật minh bạch, kiểm thử được bằng ví dụ cụ thể và sửa được ngay khi phát hiện sai. Thứ tự ưu tiên giải quyết chức danh có nhiều từ khóa: \"Python Data Engineer\" chứa cả \"Python\" và \"Data Engineer\", nhưng người đọc hiểu đây là kỹ sư dữ liệu, nên luật Data Engineer được xét trước.",
    risk: "Chức danh mơ hồ như \"Kỹ sư phần mềm\" rơi vào nhóm chung; luật cần cập nhật khi có chức danh mới.",
  }),
  ...decision("3.10.6. Phát hiện và loại tin sinh tự động", {
    problem: "Trường ngày đăng của bộ IT Jobs phân bố đều bất thường 2018–2025 ở mọi nền tảng. Ban đầu nhóm chỉ coi đây là một cột hỏng và dùng năm thu thập thay thế. Khi điều tra tiếp (#79, #81), nhóm thấy toàn bộ các tin đó có chung dấu hiệu: đường dẫn dạng \"…-hist201800001\", đúng 800 tin cho mỗi nền tảng TopCV, VietnamWorks, CareerViet, chức danh chung chung, danh sách kỹ năng ngẫu nhiên (Android Developer có Swift và React) và không có mô tả. Đây là 2.400 tin do máy sinh, chiếm 54% số tin có nhãn. Chúng dễ đoán hơn tin thật nên làm số liệu đẹp hơn thực tế: mô hình cũ có trung vị sai số 16,5% trên tập test lẫn tin sinh nhưng 18,0% trên riêng tin thật.",
    options: "(1) Giữ các tin này, chỉ thay ngày đăng bằng năm thu thập (cách làm ban đầu). (2) Giữ nhưng đánh dấu để mô hình tự phân biệt. (3) Loại hẳn khỏi bộ dữ liệu.",
    choice: "Phương án 3: loại 2.400 tin có đường dẫn dạng …-hist…; với các tin thật của bộ IT Jobs vẫn dùng năm thu thập (2026).",
    reason: "Mô hình học từ tin giả giống học sinh ôn thi bằng bộ đề do máy bịa: điểm luyện tập cao nhưng không phản ánh đề thật. Mục tiêu của đề tài là dự đoán lương của tin tuyển dụng thật, nên chỉ tin thật mới được dùng để học và để chấm. Đánh dấu (phương án 2) vẫn để tin giả chiếm hơn nửa tập test, làm con số đánh giá vẫn đẹp giả.",
    risk: "Mất 54% số tin: tập test chỉ còn 288 tin, phần lớn vai trò có dưới 20 tin test nên không chấm riêng được; sai số tăng (MAE test từ 5,82 lên 6,49 triệu) nhưng trung thực hơn. Không phân tích được xu hướng theo thời gian.",
  }),
  ...decision("3.10.7. Chia tập theo công ty bằng hàm băm", {
    problem: "Nhiều công ty đăng hàng chục tin gần giống nhau với cùng khung lương. Nếu chia ngẫu nhiên theo tin, một tin của công ty A nằm trong train và tin gần giống nằm trong test; mô hình chỉ cần \"nhớ\" lương của A là đoán đúng, cho kết quả đẹp giả.",
    options: "(1) Chia ngẫu nhiên theo tin. (2) Chia theo thời gian. (3) Chia theo công ty bằng thuật toán tối ưu tỉ lệ. (4) Chia theo công ty bằng hàm băm.",
    choice: "Chia theo công ty bằng hàm băm SHA-256 với hạt giống 42.",
    reason: "Câu hỏi thực tế của người dùng là \"công ty mới tôi ứng tuyển sẽ trả bao nhiêu\", tức công ty mô hình chưa từng thấy. Chia theo công ty mô phỏng đúng tình huống đó, giống kỳ thi dùng đề mới chứ không dùng lại đề ôn tập. Hàm băm cho kết quả không đổi khi thêm tin mới hay đọc theo thứ tự khác; chia theo thời gian không làm được vì ngày đăng không đáng tin (mục 3.10.6).",
    risk: "Tỷ lệ thực tế 67,4/16,0/16,6 lệch nhẹ so với 70/15/15 vì công ty lớn nằm trọn một tập.",
  }),
  ...decision("3.10.8. Đo độ chính xác của bộ gán nhãn trên mẫu 208 tin", {
    problem: "Mọi nhãn (lương, vai trò, cấp bậc, kinh nghiệm, kỹ năng) đều do luật tự động gán. Nếu luật sai nhiều, mô hình học từ nhãn sai và không cách nào nhận ra từ sai số.",
    options: "(1) Tin luật vì đã có kiểm thử theo ví dụ. (2) Duyệt lại toàn bộ 1.735 tin. (3) Duyệt một mẫu phân tầng và đo tỉ lệ đúng của từng loại nhãn.",
    choice: "Phương án 3: mẫu 208 tin, phân tầng theo nguồn (mỗi nguồn ít nhất 10 tin) và rải đều 23 vai trò; mỗi dòng đặt nhãn tự động cạnh dữ liệu thô để người duyệt so.",
    reason: "Giống kiểm tra chất lượng trong nhà máy: không kiểm từng sản phẩm mà lấy mẫu đại diện. Kết quả lần đầu: lương 100%, kinh nghiệm 100%, vai trò 95,2%, cấp bậc 94,7%, kỹ năng 98,6%. Các lỗi tìm được (MERN stack bị xếp nhầm, cấp bậc của nguồn đè cấp bậc trong chức danh, \"API Testing\" bị nhận là REST API, tin pháp chế lọt vào) được sửa thành luật; sau khi sửa, trên cùng mẫu vai trò đúng 99,5%, cấp bậc 100%, kỹ năng 100%. Kết luận quan trọng: bộ gán nhãn không phải nút thắt của sai số.",
    risk: "Mẫu do AI (Claude) duyệt theo yêu cầu của chủ dự án, không phải người duyệt; cần người duyệt lại trước khi dùng làm số liệu chính thức. Chỉ đo độ chính xác của kỹ năng được gán, chưa đo kỹ năng bị bỏ sót. Tỉ lệ đúng sau khi sửa được đo trên chính mẫu đã dùng để tìm lỗi nên có thể lạc quan.",
  }),
);

// ============================== CHƯƠNG 4 ==============================
chapter = 4;
body.push(
  H1("CHƯƠNG 4: TRỰC QUAN HÓA VÀ PHÂN TÍCH"),
  H2("4.1. Phương pháp trực quan hóa"),
  P("Các biểu đồ được vẽ bằng Matplotlib và Seaborn trên toàn bộ 1.735 tin thật của bộ dữ liệu sạch, theo cách chọn loại biểu đồ đã nêu ở mục 2.8. Mỗi biểu đồ ghi rõ đơn vị (triệu VND/tháng) và số tin; trung vị được dùng làm thước đo trung tâm vì lương lệch phải. Dashboard của ứng dụng dùng cùng các biểu đồ này nên số liệu trên web và trong báo cáo thống nhất."),
  H2("4.2. Phân bố mức lương"),
  ...fig(path.join(FIG, "distribution.png"), "Phân bố lương chào tuyển (triệu VND/tháng)", 13),
  P("Lương có trung vị 25 triệu, trung bình 28,1 triệu và phân vị 90% là 47,5 triệu. Phân phối lệch phải rõ rệt: phần lớn tin nằm trong khoảng 15–35 triệu nhưng có đuôi dài tới khoảng 139 triệu ở các vị trí quản lý và kiến trúc sư. Đây là lý do mô hình được huấn luyện trên logarit của lương."),
  H2("4.3. Nhu cầu tuyển dụng và công nghệ chủ đạo"),
  ...fig(path.join(FIG, "role_demand.png"), "Số tin có công bố lương theo vai trò", 13),
  P("Backend Developer chiếm nhiều tin nhất (278 tin, 16,0%), tiếp theo là Kiểm thử (198), Business Analyst (130), Mobile (125), Fullstack (119) và Frontend (105). Nhóm dữ liệu – AI (AI/ML, Data Engineer, Data Analyst) có 130 tin, DevOps/Cloud 73 tin và Bảo mật 57 tin, cho thấy nhu cầu đáng kể ngoài nhóm lập trình truyền thống."),
  ...fig(path.join(FIG, "skill_demand.png"), "Số tin nhắc đến của toàn bộ ngôn ngữ và công nghệ", 13),
  P("JavaScript là kỹ năng được nhắc nhiều nhất (251 tin), sau đó là Java (179), React (154), SQL (129), Node.js (126), Git (119) và Python (111). Hệ sinh thái web (JavaScript, React, Node.js) và nền tảng backend (Java, SQL, Redis, PostgreSQL) là hai cụm có nhu cầu lớn nhất."),
  ...fig(path.join(FIG, "skill_salary.png"), "Trung vị lương theo toàn bộ công nghệ (thanh xám: dưới 30 tin)", 13),
  P("Trong các công nghệ có ít nhất 30 tin, lương cao nhất gắn với AWS (trung vị 36 triệu), LLM/GenAI (35), Next.js (34), Kubernetes (32,5), Flutter (32,25), Kafka (31,75) và Golang (31), đều thuộc nhóm điện toán đám mây, AI và hệ thống phân tán. Ngược lại, PHP (19,5), MySQL, Selenium (20), C# (20,5), Jira (21) và Angular (21,5) thấp hơn trung vị chung 25 triệu. Kỹ năng phổ biến nhất chưa chắc là kỹ năng được trả cao nhất."),
  H2("4.4. Tương quan giữa số năm kinh nghiệm và thu nhập"),
  ...fig(path.join(FIG, "experience.png"), "Phân bố lương theo số năm kinh nghiệm", 13),
  P("Kinh nghiệm có tương quan mạnh với lương (ρ = 0,70). Trung vị tăng từ 13,5 triệu (dưới 1 năm), 15,5 triệu (1 năm) lên 22,75 triệu (2 năm), 28 triệu (3 năm), 31,2 triệu (4 năm), 48 triệu (5–7 năm) và 53,5 triệu (từ 8 năm, chỉ 23 tin). Bước nhảy lớn nhất nằm giữa mốc 4 năm và 5 năm, tương ứng chuyển từ Middle lên Senior. Độ phân tán cũng tăng theo kinh nghiệm: ở mức cao, vai trò và kỹ năng quyết định nhiều hơn số năm."),
  H2("4.5. Phân bố theo vai trò và khu vực"),
  ...fig(path.join(FIG, "roles.png"), "Phân bố lương theo 23 vai trò CNTT", 14.5),
  P("Biểu đồ hộp thể hiện đủ 23 vai trò. Nhóm có trung vị cao nhất là Data Engineer (41,6 triệu), Quản lý IT/CTO (40) và Tech Lead/Architect (39), nhưng Data Engineer chỉ có 26 tin và CTO 13 tin nên cần thận trọng. DevOps/Cloud, Quản lý dự án và BrSE đạt 32,5 triệu, AI/ML 29,3 triệu, cao hơn các vai trò lập trình phổ thông (Backend, Frontend, Mobile 25 triệu, Fullstack 28,5). Kiểm thử, Quản trị hệ thống, ERP (20), Game (15) và IT Support (13,6) có trung vị thấp nhất."),
  ...fig(path.join(FIG, "regions.png"), "Trung vị lương theo khu vực", 12),
  P("Hà Nội chiếm 80,3% số tin có lương (1.393 tin) với trung vị 25 triệu. Tin Remote có trung vị cao nhất (30,25 triệu, 56 tin), phần lớn từ doanh nghiệp nước ngoài hoặc dự án outsourcing. TP. Hồ Chí Minh có trung vị 23,5 triệu trên 187 tin; tuy nhiên nhiều tin tại TP. Hồ Chí Minh ghi \"Thương lượng\" nên số tin có lương ít, cần thận trọng khi so sánh hai thành phố. Tỉnh/thành khác thấp nhất (17 triệu)."),
  ...fig(path.join(FIG, "heatmap.png"), "Trung vị lương theo vai trò và khu vực", 14.5),
  P("Với các vai trò đông tin như Backend, Kiểm thử, Mobile, Business Analyst, trung vị tại Hà Nội và TP. Hồ Chí Minh chỉ chênh 0–2 triệu (Backend 25 so với 25, Kiểm thử 20,6 so với 21). Chênh lệch lớn chỉ xuất hiện ở các vai trò có ít tin tại TP. Hồ Chí Minh và không theo một chiều cố định: Fullstack (36,8 so với 26,5, 12 tin) và AI/ML (42,5 so với 26,8, 9 tin) cao hơn ở TP. Hồ Chí Minh, còn Tech Lead (27,7 so với 40, 13 tin) cao hơn ở Hà Nội. Các ô trống là tổ hợp có dưới 3 tin, không đủ để kết luận."),
  H2("4.6. Tổng hợp insight"),
  B("Kinh nghiệm là yếu tố quyết định lớn nhất; mốc 4–5 năm (lên Senior) mang lại bước tăng lương lớn nhất."),
  B("Vai trò dữ liệu, DevOps/Cloud và quản lý kỹ thuật được trả cao hơn rõ rệt lập trình phổ thông (Data Engineer 41,6, DevOps 32,5 so với Backend 25 triệu)."),
  B("Kỹ năng phổ biến nhất (JavaScript, Java, React) không phải kỹ năng trả cao nhất; kỹ năng ít phổ biến hơn như AWS, LLM/GenAI, Next.js, Kubernetes gắn với trung vị cao hơn."),
  B("Remote và Hà Nội có mặt bằng lương công bố cao hơn TP. Hồ Chí Minh trong dữ liệu này, nhưng chênh lệch bị ảnh hưởng bởi tỉ lệ tin công bố lương khác nhau giữa các thành phố."),
);

// ============================== CHƯƠNG 5 ==============================
chapter = 5;
const mrow = (name, part) => [M[name].label, fmt(M[name][part].MAE), fmt(M[name][part].RMSE), fmt(M[name][part].R2, 3), fmt(M[name][part].MAPE, 1)];
const paramName = { alpha: "α", min_samples_leaf: "số mẫu tối thiểu ở lá", learning_rate: "hệ số học", max_leaf_nodes: "số lá tối đa" };
body.push(
  H1("CHƯƠNG 5: XÂY DỰNG VÀ ĐÁNH GIÁ MÔ HÌNH"),
  H2("5.1. Xây dựng các mô hình học máy"),
  P("Nhóm xây dựng ba mô hình hồi quy và một mốc so sánh. Cả bốn dùng chung đặc trưng đầu vào (Bảng 5.1), chung cách chia tập và chung biến đổi logarit cho biến mục tiêu để phép so sánh công bằng. Đặc trưng \"số kỹ năng của tin\" có trong phiên bản đầu đã bị bỏ, lý do trình bày ở mục 5.6.5."),
  ...table("Các nhóm đặc trưng đầu vào", ["Nhóm", "Biến đổi", "Số cột"], [
    ["Vai trò, khu vực, cấp bậc", "Mã hóa one-hot, bỏ qua giá trị chưa gặp", "35"],
    ["Nền tảng, hình thức làm việc, loại công ty", "Mã hóa one-hot", "12"],
    ["Từ khóa chức danh", "Cờ 0/1 (expert, principal, head, consultant)", "4"],
    ["Số năm kinh nghiệm, năm dữ liệu", "Điền trung vị, thêm cột cờ thiếu cho kinh nghiệm; chuẩn hóa (chỉ Ridge)", "3"],
    ["Kỹ năng", "Mã hóa multi-hot (mỗi kỹ năng một cột 0/1)", "69"],
    ["Tổng", "", "123"],
  ], [4, 7, 1.5], [0, 0, R]),
  H3("5.1.1. Mốc trung vị"),
  P("Dự đoán mọi tin bằng trung vị lương tập train. Mốc này cho biết mức sai số khi không dùng bất kỳ thông tin nào về tin tuyển dụng."),
  H3("5.1.2. Ridge Regression"),
  P("Mô hình tuyến tính có điều chuẩn L2, đầu vào được chuẩn hóa thang đo. Tham số α được chọn trong tập {0,3; 1; 3; 10}. Ridge được chọn làm đại diện tuyến tính vì ổn định khi có nhiều cột kỹ năng tương quan. Hệ số của các cột kỹ năng bị chặn không âm (giải bằng bình phương tối thiểu có chặn), để thêm một kỹ năng không bao giờ làm lương dự đoán giảm."),
  H3("5.1.3. Random Forest"),
  P("Gồm 300 cây quyết định, mỗi cây học trên một mẫu bootstrap; số mẫu tối thiểu ở mỗi lá được chọn trong {1; 3; 5}. Mô hình đại diện cho nhóm phương pháp tổng hợp song song (bagging). Vì cây quyết định không hỗ trợ ràng buộc dấu theo từng cột, Random Forest được bọc bằng **bao đơn điệu**: dự đoán cho một bộ kỹ năng là giá trị lớn nhất của mô hình gốc trên mọi tập con của bộ đó, nên thêm kỹ năng không thể làm kết quả giảm. Với 12 kỹ năng (mức tối đa của một tin trong dữ liệu) một lần dự đoán mất khoảng 0,1 giây."),
  H3("5.1.4. Gradient Boosting"),
  P("Gồm tối đa 500 vòng tăng cường, hệ số điều chuẩn L2 bằng 1, ràng buộc đơn điệu tăng theo số năm kinh nghiệm và theo từng cột trong 69 cột kỹ năng; hệ số học được chọn trong {0,05; 0,1} và số lá tối đa của mỗi cây trong {15; 31}. Mô hình đại diện cho nhóm phương pháp tổng hợp tuần tự (boosting)."),
  H3("5.1.5. Hiểu các mô hình qua ví dụ thực tế"),
  P("Để hiểu vì sao các mô hình cho kết quả khác nhau, có thể so sánh chúng với cách con người định giá lương cho một hồ sơ ứng viên."),
  ...table("So sánh các mô hình với cách con người định giá lương", ["Mô hình", "Giống như", "Điểm mạnh trong thực tế", "Điểm yếu trong thực tế"], [
    ["Mốc trung vị", "Trả lời mọi câu hỏi \"lương bao nhiêu\" bằng \"khoảng 25 triệu\"", "Không bao giờ sai quá xa với phần đông", "Không phân biệt intern với trưởng phòng"],
    ["Ridge", "Một chuyên viên nhân sự có bảng giá cố định: Backend +2 triệu, mỗi năm kinh nghiệm +3 triệu, biết AWS +1 triệu, rồi cộng lại", "Dễ giải thích, ổn định, không bị dao động bởi vài trường hợp lạ", "Không hiểu \"tùy hoàn cảnh\": AWS đáng giá với kỹ sư DevOps hơn hẳn với tester, nhưng bảng giá chỉ có một con số cho AWS"],
    ["Random Forest", "Hỏi ý kiến 300 chuyên viên, mỗi người chỉ được xem một phần hồ sơ và chỉ từng gặp một phần thị trường, rồi lấy trung bình 300 ý kiến", "Ý kiến sai của từng người bù trừ nhau. Con người không thể tự có 300 góc nhìn độc lập như vậy cùng lúc, nhưng máy làm được", "Mỗi chuyên viên dễ \"thuộc lòng\" các hồ sơ đã gặp: ở phiên bản chưa ràng buộc, sai số trên dữ liệu học 2,75 triệu nhưng trên dữ liệu mới 5,59 triệu"],
    ["Gradient Boosting", "Một hội đồng chấm lương làm việc nối tiếp: người đầu đưa ra mức sơ bộ, người thứ hai chỉ tập trung sửa những hồ sơ người đầu đánh giá sai, người thứ ba sửa tiếp phần còn sai…", "Học được các quy luật tinh tế như tương tác giữa vai trò và kỹ năng; mỗi lần sửa chỉ một bước nhỏ nên ít học vẹt", "Khó giải thích hơn Ridge; cần dò tham số cẩn thận"],
  ], [2.5, 5, 4, 4]),
  P("Ràng buộc đơn điệu tương đương hai quy tắc mà hội đồng phải tuân thủ: không được trả cho người nhiều kinh nghiệm hơn thấp hơn người ít kinh nghiệm hơn, và không được trả cho người biết thêm một kỹ năng thấp hơn người không biết, khi các điều kiện khác như nhau. Không có các quy tắc này, mô hình có thể học từ vài tin bất thường rằng 7 năm kinh nghiệm được trả thấp hơn 5 năm, hoặc rằng biết thêm Java làm giảm lương, và người dùng sẽ thấy lời tư vấn vô lý."),
  H2("5.2. Huấn luyện mô hình"),
  H3("5.2.1. Mục đích"),
  P("Huấn luyện là quá trình đưa dữ liệu train vào mô hình để mô hình học quy luật giữa các đặc trưng đầu vào và mức lương. Tập train gồm 1.169 tin của 442 công ty."),
  H3("5.2.2. Quy trình huấn luyện"),
  ...fig(path.join(DIA, "04-luu-do-huan-luyen.png"), "Lưu đồ huấn luyện và chọn mô hình", 11),
  ...steps([
    "Đọc bộ dữ liệu sạch và tách ba tập theo nhãn split.",
    "Tạo ma trận đặc trưng theo Bảng 5.1; biến mục tiêu là logarit của lương.",
    "Với mỗi mô hình và mỗi bộ siêu tham số: huấn luyện trên train, tính MAE trên validation.",
    "Với mỗi mô hình, giữ bộ siêu tham số có MAE validation nhỏ nhất.",
    "Chọn mô hình có MAE validation nhỏ nhất trong ba mô hình.",
    "Lưu toàn bộ mô hình đã huấn luyện cùng bảng chỉ số để ứng dụng nạp lại mà không huấn luyện lại.",
  ]),
  P("Các bước tiền xử lý và mô hình được đóng gói chung trong một pipeline, nên dữ liệu khi dự đoán được xử lý giống hệt khi huấn luyện."),
  H3("5.2.3. Tối ưu và lựa chọn mô hình"),
  ...table("Kết quả dò siêu tham số (MAE trên validation, triệu VND/tháng)", ["Mô hình", "Siêu tham số", "MAE validation"],
    Object.entries(metrics.tuning).filter(([name]) => name !== "Baseline").flatMap(([name, trials]) =>
      trials.map((t) => [
        M[name].label,
        Object.entries(t.params).map(([k, v]) => `${paramName[k] || k} = ${String(v).replace(".", ",")}`).join("; "),
        fmt(t.valid_MAE, 3) + (JSON.stringify(t.params) === JSON.stringify(M[name].params) ? " (chọn)" : ""),
      ])),
    [4, 6, 3], [0, 0, R]),
  ...table("Kết quả trên tập validation", ["Mô hình", "MAE", "RMSE", "R²", "MAPE (%)"], ORDER.map((n) => mrow(n, "valid")), [4, 2, 2, 2, 2], [0, R, R, R, R]),
  P(`Gradient Boosting có MAE validation thấp nhất (${fmt(M.GradientBoosting.valid.MAE)} triệu) nên được chọn làm mô hình chính cho ứng dụng. Quyết định này được đưa ra trước khi xem kết quả test.`),
  H2("5.3. Kiểm thử mô hình"),
  H3("5.3.1. Mục đích kiểm thử"),
  P("Kiểm thử dùng tập dữ liệu chưa được đưa vào huấn luyện để kiểm tra khả năng dự đoán trên dữ liệu mới. Tập test gồm 288 tin của 121 công ty không xuất hiện trong train và validation."),
  H3("5.3.2. Quy trình kiểm thử"),
  P("Sau khi đã chọn mô hình bằng validation, các mô hình đã huấn luyện dự đoán lương cho tập test; kết quả được so sánh với lương thực tế để tính sai số. Tập test không được dùng để điều chỉnh tham số hoặc chọn lại mô hình."),
  H3("5.3.3. Kết quả kiểm thử"),
  ...table("Kết quả trên tập test", ["Mô hình", "MAE", "RMSE", "R²", "MAPE (%)"], ORDER.map((n) => mrow(n, "test")), [4, 2, 2, 2, 2], [0, R, R, R, R]),
  ...fig(path.join(FIG, "models_test.png"), "So sánh MAE và RMSE của các mô hình trên tập test", 13),
  P(`Cả ba mô hình đều vượt xa mốc trung vị (MAE ${fmt(M.Baseline.test.MAE)} triệu). Gradient Boosting đạt MAE ${fmt(sel.test.MAE)} triệu, R² ${fmt(sel.test.R2, 3)} và MAPE ${fmt(sel.test.MAPE, 1)}%, nghĩa là sai số trung bình khoảng một phần năm mức lương. Thứ tự các mô hình trên test giống trên validation. Các con số này cao hơn phiên bản trước (MAE 5,82 triệu) không phải vì mô hình kém đi, mà vì tập test giờ chỉ gồm tin thật, khó đoán hơn tin sinh tự động (mục 3.10.6); hai con số không so trực tiếp được. So với bản thăm dò 14 mẫu (MAE 21,98 triệu trên 2 tin test), sai số giảm hơn 3 lần và được đo trên ${sel.test.n} tin.`),
  H2("5.4. Đánh giá mô hình"),
  H3("5.4.1. Mức độ khớp và quá khớp"),
  ...table("So sánh MAE trên ba tập (triệu VND/tháng)", ["Mô hình", "Train", "Validation", "Test"], ORDER.map((n) => [M[n].label, fmt(M[n].train.MAE), fmt(M[n].valid.MAE), fmt(M[n].test.MAE)]), [4, 2, 2, 2], [0, R, R, R]),
  P(`Gradient Boosting có sai số thấp nhất trên cả ba tập nhưng khoảng cách train – validation cũng lớn nhất (${fmt(M.GradientBoosting.train.MAE)} so với ${fmt(M.GradientBoosting.valid.MAE)}): khi tập train chỉ còn 1.169 tin, mô hình bắt đầu học thuộc một phần. Nó vẫn được chọn vì sai số validation thấp nhất theo quy tắc đã khóa trước. Random Forest được bọc bao đơn điệu (lấy giá trị lớn nhất trên mọi tập con kỹ năng), nên khuếch đại sai số của những cây quá khớp; quy trình chọn trên validation vì vậy chọn lá ít nhất ${M.RandomForest.params.min_samples_leaf} mẫu (train ${fmt(M.RandomForest.train.MAE)}, validation ${fmt(M.RandomForest.valid.MAE)}). Ridge có sai số ba tập gần nhau, ổn định nhưng không học được tương tác phi tuyến giữa vai trò và kỹ năng.`),
  H3("5.4.2. Phân tích sai số"),
  ...fig(path.join(FIG, "actual_pred.png"), "Lương thực tế và dự đoán của Gradient Boosting trên tập test", 10.5),
  P("Các điểm tập trung quanh đường chéo ở vùng 10–50 triệu. Với lương trên 70 triệu (chủ yếu Tech Lead, CTO), mô hình có xu hướng dự đoán thấp hơn thực tế do ít mẫu ở vùng này."),
  ...fig(path.join(FIG, "error_role.png"), "MAE theo vai trò trên tập test", 13),
  P("Sai số thấp nhất ở các vai trò có khung lương hẹp (IT Support 2,9, Frontend 3,7, Kiểm thử và Business Analyst 4,6 triệu) và cao nhất ở Tech Lead/Architect (khoảng 22 triệu), Quản lý dự án (10,6) và DevOps (9,5), nơi lương phụ thuộc nhiều vào quy mô công ty và phạm vi trách nhiệm, vốn không có đủ trong dữ liệu. Nhiều vai trò chỉ có vài tin test nên sai số theo vai trò chỉ mang tính tham khảo."),
  H3("5.4.3. Mức độ quan trọng của đặc trưng"),
  ...fig(path.join(FIG, "importance.png"), "Mức độ quan trọng hoán vị của các đặc trưng (tập validation)", 13),
  P(`Số năm kinh nghiệm là đặc trưng quan trọng nhất (xáo trộn làm R² giảm ${fmt(metrics.permutation_importance.experience_years)}), tiếp theo là vai trò, cấp bậc và **nền tảng đăng tin**: cùng một hồ sơ, tin trên VietnamWorks thường ghi lương cao hơn tin trên TopCV 2026. Trong nhóm kỹ năng, Next.js, LLM/GenAI, Kafka và Golang có ảnh hưởng lớn nhất; loại công ty và hình thức làm việc cũng đóng góp một phần.`),
  H3("5.4.4. Kỹ năng mang lại giá trị gia tăng thu nhập"),
  P("Bảng 5.7 so sánh hai cách nhìn cho các kỹ năng có ít nhất 20 tin: chênh lệch trung vị giữa tin có và không có kỹ năng (mô tả, chưa loại trừ ảnh hưởng của vai trò và kinh nghiệm) và mức tăng lương Δₖ theo công thức (2.12)."),
  ...table("Top 12 kỹ năng theo mức tăng lương ước lượng", ["Kỹ năng", "Số tin", "Trung vị có / không (triệu)", "Chênh trung vị", "Mức tăng Δₖ"],
    skillValue.slice(0, 12).map((x) => [x[0], x[1], `${fmt(+x[2], 1)} / ${fmt(+x[3], 1)}`, (+x[4] >= 0 ? "+" : "") + fmt(+x[4], 1), "+" + fmt(+x[5])]),
    [3.5, 1.5, 4, 2.5, 3], [0, R, R, R, R]),
  ...fig(path.join(FIG, "uplift.png"), "Mức tăng lương dự đoán khi bổ sung kỹ năng", 13),
  P("Các kỹ năng mang lại giá trị gia tăng thu nhập cao nhất là **LLM/GenAI** (+7,0 triệu), **AWS** (+3,8), **Kafka** (+2,5), **Next.js** (+2,4), **Python** và **Golang** (+1,8), **Kotlin** (+1,7). Hướng đầu tư rõ nhất là AI tạo sinh và điện toán đám mây, sau đó là các kỹ năng hệ thống phân tán (Kafka, Golang, Kubernetes, Microservices). Nhờ ràng buộc đơn điệu, không kỹ năng nào có mức tăng âm. Các kỹ năng phổ biến như JavaScript (+0,13), Java (+0,04), Docker, Git có mức tăng gần 0: đây là kỹ năng nền tảng mà gần như tin nào cũng yêu cầu, nên biết chúng là điều kiện để có việc chứ không phải lý do để được trả thêm."),
  H3("5.4.5. Nhận xét kết quả"),
  B("Cả ba mô hình học máy đều tốt hơn mốc trung vị khoảng 2 lần trên cả validation và test."),
  B("Gradient Boosting đạt kết quả tốt nhất trên validation và cũng tốt nhất trên test; Random Forest phải dùng lá lớn để bao đơn điệu không khuếch đại sai số; Ridge ổn định nhưng kém linh hoạt."),
  B("Ràng buộc đơn điệu theo kỹ năng được giữ trên bộ dữ liệu tin thật: không hồ sơ nào bị dự đoán giảm lương khi thêm kỹ năng (mục 5.6.5)."),
  B("Sai số còn lớn ở các vị trí lương rất cao và các vai trò ít mẫu."),
  B("Mức tăng lương theo kỹ năng là quan hệ tương quan; ứng dụng vì vậy tính mức tăng riêng cho từng hồ sơ cụ thể thay vì dùng con số trung bình."),
);

const lv = (level) => V.calibration.levels.find((row) => row.level === level);
const bm = (name, key) => V.bootstrap.models[name][key];
const ci = (pair, d = 2) => `${fmt(pair[0], d)} – ${fmt(pair[1], d)}`;
const fg = (key) => V.fairness[key].groups;
body.push(
  H2("5.5. Kiểm định độ tin cậy của mô hình"),
  P(`Một con số MAE duy nhất chưa trả lời được bốn câu hỏi quan trọng: (1) khoảng lương mà ứng dụng đưa ra có đáng tin như nó tuyên bố không, (2) Gradient Boosting có thật sự tốt hơn hay chỉ may mắn trên tập kiểm tra này, (3) mô hình có sai lệch có hệ thống với một nhóm nào không, (4) mô hình đã đủ tốt để đưa cho người dùng thật chưa. Mục này trả lời từng câu hỏi trên ${V.test_rows} tin kiểm tra.`),
  H3("5.5.1. Hiệu chuẩn khoảng dự đoán"),
  P("Ứng dụng không chỉ đưa ra một con số mà còn đưa ra \"khoảng thường gặp\" với độ tin cậy 80% (mục 6.4). Một khoảng **được hiệu chuẩn tốt** nếu khoảng 80% thật sự chứa khoảng 80% lương thật. Tỉ lệ bao phủ được tính bằng"),
  eq([r("coverage = "), frac("1", "n"), sum([r("1[ "), sb("L", "i"), r(" ≤ "), yi(), r(" ≤ "), sb("U", "i"), r(" ]")])]),
  P("trong đó [Lᵢ, Uᵢ] là khoảng dự đoán của tin thứ i và 1[·] bằng 1 khi điều kiện đúng. Khoảng được dựng hoàn toàn từ tập validation, rồi kiểm tra trên tập test chưa dùng; cách làm này tương tự phương pháp dự đoán phù hợp (conformal prediction) dạng tách tập."),
  ...table("Tỉ lệ bao phủ của khoảng dự đoán trên tập test", ["Mức tin cậy danh nghĩa", "Tỉ lệ bao phủ thực tế", "Độ rộng trung bình (triệu)", "Nhận xét"],
    [0.5, 0.8, 0.9].map((level) => {
      const row = lv(level);
      const gap = (row.coverage - level) * 100;
      return [`${Math.round(level * 100)}%`, `${fmt(row.coverage * 100, 1)}%`, fmt(row.mean_width, 1), Math.abs(gap) < 3 ? "Sát mức danh nghĩa" : `Thấp hơn ${fmt(-gap, 1)} điểm %`];
    }), [3, 3, 3, 4], [C, R, R]),
  ...fig(path.join(FIG, "reliability.png"), "Biểu đồ hiệu chuẩn khoảng dự đoán trên tập test", 10),
  P(`Đường hiệu chuẩn nằm sát đường chéo và hơi cao hơn ở mọi mức tin cậy: khoảng 80% bao phủ ${fmt(lv(0.8).coverage * 100, 1)}% tin, khoảng 90% bao phủ ${fmt(lv(0.9).coverage * 100, 1)}%, cao hơn mức danh nghĩa khoảng 2–3,5 điểm phần trăm. Nghĩa là khoảng hơi rộng hơn cần thiết, tức thận trọng: người dùng ít khi bị bất ngờ vì lương thật nằm ngoài khoảng. Mức chênh này là bình thường vì tập test gồm các công ty khác với tập validation dùng để dựng khoảng.`),
  ...table("Tỉ lệ bao phủ của khoảng 80% theo mức lương thật", ["Nhóm lương", "Khoảng lương (triệu)", "Số tin", "Tỉ lệ bao phủ"],
    V.calibration.by_salary_band.map((row) => [row.group, row.range.replace(/\./g, ","), String(row.n), `${fmt(row.coverage * 100, 1)}%`]), [3, 4, 2, 3], [0, C, R, R]),
  P("Hiệu chuẩn không đều theo mức lương: khoảng bao phủ tốt ở nhóm lương thấp (85%) và trung bình (92%) nhưng kém ở nhóm lương cao (72%). Theo vai trò có ít nhất 15 tin test, Quản lý dự án bao phủ kém nhất (73%), các vai trò lập trình phổ thông đều từ 80% trở lên. Tech Lead/Architect chỉ có 10 tin test nên không kết luận được. Lương cao phụ thuộc nhiều vào yếu tố không có trong dữ liệu (quy mô công ty, phạm vi trách nhiệm), nên ứng dụng chỉ hiện khoảng mở rộng cho các nhóm này (mục 5.5.5)."),
  H3("5.5.2. Khoảng tin cậy bootstrap"),
  P(`Kết quả MAE trên tập test phụ thuộc vào việc tập test gồm những công ty nào. Nếu đổi sang một nhóm công ty khác, MAE sẽ thay đổi bao nhiêu? Bootstrap trả lời câu hỏi này bằng cách giả lập ${V.bootstrap.rounds} tập test khác nhau: mỗi lần rút ngẫu nhiên có hoàn lại ${V.bootstrap.companies} công ty từ tập test (một công ty có thể được rút nhiều lần), tính lại các chỉ số, rồi lấy khoảng chứa 95% kết quả ở giữa.`),
  P("Việc lấy mẫu lại theo **công ty** chứ không theo từng tin là có chủ đích: các tin cùng công ty giống nhau, nếu rút từng tin riêng lẻ thì khoảng tin cậy sẽ hẹp hơn thực tế, tạo cảm giác chắc chắn giả."),
  ...table("Khoảng tin cậy 95% của các chỉ số trên tập test (bootstrap theo công ty)", ["Mô hình", "MAE", "MAE 95%", "R²", "R² 95%"],
    ORDER.map((n) => [M[n].label, fmt(bm(n, "MAE").point), ci(bm(n, "MAE").ci95), fmt(bm(n, "R2").point, 3), ci(bm(n, "R2").ci95, 3)]),
    [3.5, 2, 3, 2, 3], [0, R, C, R, C]),
  ...table("Chênh lệch MAE giữa Gradient Boosting và các mô hình khác", ["So với", "Chênh MAE trung bình (triệu)", "Khoảng 95%", "Tỉ lệ lần Gradient Boosting tốt hơn"],
    ["Ridge", "RandomForest", "Baseline"].map((n) => {
      const d = V.bootstrap.differences[n];
      return [M[n].label, fmt(d.mean), ci(d.ci95), `${fmt(d.p_better * 100, 1)}%`];
    }), [3.5, 3.5, 3, 4], [0, R, C, R]),
  ...fig(path.join(FIG, "bootstrap.png"), "Phân phối bootstrap của chênh lệch MAE (âm nghĩa là Gradient Boosting tốt hơn)", 13),
  P(`Khoảng tin cậy MAE của các mô hình chồng lên nhau (Gradient Boosting ${ci(bm("GradientBoosting", "MAE").ci95)}, Random Forest ${ci(bm("RandomForest", "MAE").ci95)}, Ridge ${ci(bm("Ridge", "MAE").ci95)}). Khi so sánh **theo cặp trên cùng một lần lấy mẫu**, Gradient Boosting tốt hơn Random Forest ở ${fmt(V.bootstrap.differences.RandomForest.p_better * 100, 1)}% và tốt hơn Ridge ở ${fmt(V.bootstrap.differences.Ridge.p_better * 100, 1)}% số lần, nhưng khoảng 95% của chênh lệch vẫn chứa 0 (${ci(V.bootstrap.differences.RandomForest.ci95)} và ${ci(V.bootstrap.differences.Ridge.ci95)}). Nói cách khác, trên ${V.test_rows} tin thật **chưa đủ bằng chứng** để khẳng định Gradient Boosting tốt hơn hẳn hai mô hình kia; trên bộ dữ liệu cũ có lẫn tin sinh, ưu thế này từng rõ ràng (99,9–100%). Nhóm vẫn giữ Gradient Boosting vì nó thắng theo quy tắc chọn đã khóa trước (MAE validation) và hỗ trợ ràng buộc đơn điệu một cách tự nhiên; khẳng định chắc chắn cần thêm tin thật. Ưu thế so với mốc trung vị thì chắc chắn: tốt hơn ở ${fmt(V.bootstrap.differences.Baseline.p_better * 100, 1)}% số lần.`),
  H3("5.5.3. Công bằng theo nhóm"),
  P("Một mô hình có MAE tổng thể tốt vẫn có thể thường xuyên dự đoán cao hơn cho một nhóm và thấp hơn cho nhóm khác. Ngoài MAE theo nhóm, đề tài đo **độ lệch tương đối** của từng nhóm g:"),
  eq([sb("bias", "g"), r(" = "), frac([r("100%")], [sb("n", "g")]), sum([frac([sb("ŷ", "i"), r(" − "), yi()], [yi()])], [r("i ∈ g")], null)]),
  P("Độ lệch dương nghĩa là mô hình dự đoán cao hơn thực tế cho nhóm đó, âm là thấp hơn. Khoảng tin cậy 95% của độ lệch được tính bằng bootstrap theo công ty như mục 5.5.2. Nhóm có dưới 20 tin chỉ được báo cáo, không dùng để kết luận."),
  ...table("Sai số và độ lệch theo khu vực, cấp bậc và nền tảng nguồn (tập test)", ["Nhóm", "Số tin", "MAPE (%)", "Độ lệch (%)", "Độ lệch 95%"],
    [["region", "Khu vực"], ["level", "Cấp bậc"], ["platform", "Nền tảng"]].flatMap(([key, label]) =>
      fg(key).map((g) => [`${label}: ${g.group}${g.enough ? "" : " (ít mẫu)"}`, String(g.n), fmt(g.MAPE, 1), (g.bias_pct >= 0 ? "+" : "") + fmt(g.bias_pct, 1), ci(g.bias_pct_ci95, 1)])),
    [5, 1.5, 2, 2, 3], [0, R, R, R, C]),
  ...fig(path.join(FIG, "fair_level.png"), "Độ lệch dự đoán theo cấp bậc, kèm khoảng tin cậy 95%", 12),
  ...fig(path.join(FIG, "fair_platform.png"), "Độ lệch dự đoán theo nền tảng nguồn, kèm khoảng tin cậy 95%", 12),
  P("Nhận xét:"),
  B("**Toàn mô hình có xu hướng dự đoán cao hơn thực tế khoảng 3,8%.** Đây chủ yếu là hệ quả của việc huấn luyện trên logarit rồi đổi ngược bằng hàm mũ. Mức lệch nhỏ so với sai số chung nên chấp nhận được, và được ghi ở phần hạn chế."),
  B("**Theo khu vực**, Hà Nội lệch +3,9% (khoảng tin cậy −0,1 đến 8,6%) và TP. Hồ Chí Minh −5,1% (−16,8 đến 8,0%), cả hai khoảng đều chứa 0 nên không có bằng chứng mô hình thiên vị một thành phố lớn. Remote, Đà Nẵng và Tỉnh/thành khác chỉ có 3–8 tin test; Tỉnh/thành khác bị dự đoán cao hơn 43% vì lương ở tỉnh thấp hơn nhiều mà dữ liệu huấn luyện quá ít tin tỉnh."),
  B("**Theo cấp bậc**, Junior bị dự đoán cao hơn khoảng 7% (khoảng tin cậy 1,3–12,8%, không chứa 0) — đây là sai lệch có hệ thống duy nhất có ý nghĩa thống kê ở các nhóm đủ mẫu. Với người mới đi làm 1–2 năm, ứng dụng có thể đưa ra mức kỳ vọng hơi cao. Lead bị dự đoán cao hơn 13% nhưng khoảng tin cậy còn chứa 0 (21 tin)."),
  B("**Theo nền tảng**, không nền tảng nào lệch có ý nghĩa thống kê sau khi thêm nền tảng làm đặc trưng. TopCV (của bộ IT Jobs) lệch +15% nhưng chỉ 22 tin và khoảng tin cậy chứa 0. MAPE cao nhất ở TopCV (31%) và TopCV 2026 (25%), vì bộ TopCV 2026 chỉ có tiêu đề, thiếu thông tin kỹ năng."),
  H3("5.5.4. Vấn đề giới tính"),
  P(`Bộ dữ liệu **không có thông tin giới tính** của ứng viên hay người được tuyển, và mô hình **không dùng giới tính làm đặc trưng**. Vì vậy mô hình không thể đưa ra mức lương khác nhau cho nam và nữ có cùng hồ sơ, nhưng đồng thời cũng không thể đo được công bằng giới theo nghĩa đầy đủ (so sánh sai số giữa nam và nữ).`),
  P(`Điều có thể kiểm tra là bản thân tin tuyển dụng: nhóm gắn nhãn những tin ghi điều kiện giới tính trong nội dung. Trên dữ liệu thô có 222 dòng ghi điều kiện (29 tin chỉ tuyển nam, 14 chỉ tuyển nữ, 24 ưu tiên một giới, 155 ghi \"Nam/Nữ\"), phần lớn ở các ngành ngoài CNTT. Trong 1.735 tin CNTT có nhãn lương chỉ còn ${V.gender.mentioned} tin (${fmt(V.gender.share_pct, 2)}%), ví dụ \"Tester Game Chỉ Tuyển Nữ\" và \"Business Analyst… Tuyển Nam\". Số lượng quá ít để kết luận về chênh lệch lương theo giới.`),
  P("Đề xuất cho ứng dụng thực tế: tin tuyển dụng ghi điều kiện giới tính không liên quan tới công việc là dấu hiệu phân biệt đối xử theo Bộ luật Lao động; hệ thống nên cảnh báo khi phát hiện, và nếu sau này thu thập được dữ liệu lương thực nhận có giới tính thì cần đo sai số theo giới như cách đã làm với khu vực và cấp bậc."),
  H3("5.5.5. Đối chiếu với chuẩn production"),
  P("Ba phép kiểm định trên cho biết mô hình đáng tin đến đâu, nhưng chưa trả lời câu hỏi thực tế nhất: đã đủ tốt để đưa cho người dùng thật chưa? Thay vì tự đặt một ngưỡng MAPE, nhóm dùng cách các sản phẩm dự đoán lương thực tế công bố độ chính xác. Glassdoor công bố trung vị sai số (10,2%) và tỉ lệ dự đoán sai không quá 20% (75,3%), và không hiện ước tính khi thiếu dữ liệu; LinkedIn Salary hiển thị p10 – trung vị – p90 và chỉ dùng phân vị thực nghiệm cho nhóm từ 20 mẫu. Cả hai dựa trên lương thực nhận và có thông tin công ty, nên mức của Glassdoor là mục tiêu dài hạn; ngưỡng production của đề tài nới hơn (Bảng 5.13)."),
  ...table("Ngưỡng của chuẩn production", ["Phạm vi", "Trung vị sai số", "Tỉ lệ sai ≤ 20%", "Độ phủ p10–p90", "So bằng"], [
    ["Toàn bộ tập test", "≤ 15%", "≥ 65%", "75–85%", "Cận bất lợi của khoảng tin cậy bootstrap 95%"],
    ["Mỗi vai trò, cấp bậc có ≥ 20 tin test", "≤ 20%", "≥ 50%", "≥ 70%", "Giá trị điểm"],
    ["Mục tiêu dài hạn (không bắt buộc)", "≤ 10%", "≥ 75%", "—", "Cận bất lợi bootstrap"],
  ], [4, 2.5, 2.5, 2.5, 4], [0, C, C, C]),
  P("Ngưỡng chung được so bằng **cận bất lợi** của khoảng tin cậy: ví dụ trung vị sai số chỉ đạt khi cả cận trên của khoảng 95% cũng ≤ 15%, để không \"đậu nhờ may\". Ngưỡng theo nhóm so bằng giá trị điểm, vì mỗi nhóm chỉ có 20–106 tin test nên khoảng tin cậy quá rộng: nếu so bằng cận bất lợi thì cả Backend và Junior cũng trượt dù giá trị điểm đạt."),
  ...table("Kết quả của mô hình đang phục vụ theo chuẩn production (tập test)", ["Chỉ số chung", "Giá trị điểm", "Khoảng 95%", "Ngưỡng", "Kết quả"],
    [["median_error_pct", "Trung vị sai số", "%", "≤ 15%"], ["within_20_pct", "Tỉ lệ sai ≤ 20%", "%", "≥ 65%"], ["coverage_pct", "Độ phủ p10–p90", "%", "75–85%"]].map(([key, label, unit, limit]) => {
      const m = P0.overall.metrics[key];
      return [label, `${fmt(m.point, 1)}${unit}`, ci(m.ci95, 1), limit, m.pass ? "Đạt" : "Chưa đạt"];
    }), [4, 2.5, 3, 2.5, 2.5], [0, R, C, C, C]),
  ...table("Kết quả theo vai trò và cấp bậc có ít nhất 20 tin test", ["Nhóm", "Số tin test", "Trung vị sai số (%)", "Sai ≤ 20% (%)", "Độ phủ (%)", "Kết quả"],
    [["role", "Vai trò"], ["level", "Cấp bậc"]].flatMap(([key, label]) => P0[key].filter((g) => g.status !== "not_scored").map((g) => [`${label}: ${g.group}`, String(g.n), fmt(g.metrics.median_error_pct.point, 1), fmt(g.metrics.within_20_pct.point, 1), fmt(g.metrics.coverage_pct.point, 1), g.status === "pass" ? "Đạt" : "Trượt"])),
    [5, 2, 2.5, 2.5, 2, 2], [0, R, R, R, R, C]),
  P(`**Kết luận: mô hình chưa đạt chuẩn production.** Trung vị sai số ${fmt(P0.overall.metrics.median_error_pct.point, 1)}% (cận trên ${fmt(P0.overall.metrics.median_error_pct.ci95[1], 1)}%) và tỉ lệ sai ≤ 20% là ${fmt(P0.overall.metrics.within_20_pct.point, 1)}% đều chưa qua ngưỡng chung; độ phủ ${fmt(P0.overall.metrics.coverage_pct.point, 1)}% nằm trong khoảng 75–85% nhưng cận trên của khoảng tin cậy vượt 85%. Theo nhóm, bốn vai trò đông tin (Backend, Kiểm thử, Mobile, Fullstack) và ba cấp bậc Junior, Middle, Senior đạt; cấp Lead trượt rõ (trung vị sai số 34,6%). Mười tám vai trò còn lại có dưới 20 tin test nên không được chấm.`),
  P("Từ kết quả này, ứng dụng làm ba việc. Thứ nhất, trang tư vấn và trang đánh giá ghi rõ kết quả chỉ mang tính tham khảo. Thứ hai, một hồ sơ chỉ được hiện **con số lương** khi thuộc **nhóm đủ dữ liệu** (vai trò × cấp bậc có ít nhất 20 tin train) và cả vai trò lẫn cấp bậc không trượt chuẩn; ngược lại chỉ hiện **khoảng lương mở rộng** kèm lý do, không có con số và không xếp hạng phân vị. Thứ ba, khi huấn luyện lại, mô hình mới chỉ thay mô hình đang phục vụ nếu đạt chuẩn, hoặc khi cả hai chưa đạt mà mô hình mới không tệ hơn ở chỉ số chung nào và qua được nhiều phạm vi hơn hoặc tốt hơn hẳn ở ít nhất một chỉ số. Muốn đạt chuẩn, nhiều khả năng cần **thêm tin thật có lương**: tập test 288 tin còn quá nhỏ để chấm phần lớn vai trò, và đo ở #79 cho thấy bộ gán nhãn không phải nút thắt."),
  H2("5.6. Các quyết định về mô hình và lý do"),
  ...decision("5.6.1. Huấn luyện trên logarit của lương", {
    problem: "Lương lệch phải mạnh: trung vị 25 triệu nhưng có tin trên 100 triệu. Khi học trực tiếp trên lương, vài tin rất cao chi phối hàm mất mát, làm mô hình dự đoán lệch cho phần đông.",
    options: "(1) Học trực tiếp trên lương. (2) Loại các tin lương cao. (3) Học trên logarit của lương.",
    choice: "Học trên logarit, đổi ngược bằng hàm mũ khi dự đoán.",
    reason: "Trong thực tế, chênh lệch lương được cảm nhận theo tỉ lệ: lệch 5 triệu với người lương 10 triệu là rất lớn, với người lương 100 triệu là nhỏ. Thang logarit phản ánh đúng cảm nhận đó. Loại tin lương cao thì mất thông tin về các vị trí quản lý.",
    risk: "Gây xu hướng dự đoán cao hơn thực tế khoảng 2–3% (mục 5.5.3).",
  }),
  ...decision("5.6.2. Chọn ba mô hình Ridge, Random Forest, Gradient Boosting", {
    problem: "Đề bài yêu cầu ít nhất hai mô hình. Bản thăm dò dùng Ridge và Linear Regression, hai mô hình cùng họ tuyến tính, nên so sánh không cho thấy gì về việc có cần mô hình phi tuyến hay không.",
    options: "Hồi quy tuyến tính, Ridge, Lasso, cây quyết định đơn, Random Forest, Gradient Boosting, mạng nơ-ron.",
    choice: "Một mô hình tuyến tính (Ridge) và hai mô hình tổng hợp cây đại diện cho hai cách tổng hợp khác nhau (song song và tuần tự).",
    reason: "Ba mô hình trả lời ba câu hỏi: quan hệ tuyến tính có đủ không (Ridge), tổng hợp nhiều cây có giúp không (Random Forest), sửa sai tuần tự có tốt hơn trung bình song song không (Gradient Boosting). Mạng nơ-ron không được chọn vì với khoảng 2.500 tin huấn luyện dạng bảng, các mô hình cây thường tốt hơn, nhanh hơn và dễ giải thích hơn.",
    risk: "Chưa thử các thư viện boosting chuyên dụng như XGBoost; chênh lệch thường nhỏ trên dữ liệu cỡ này.",
  }),
  ...decision("5.6.3. Chọn MAE làm tiêu chí chọn mô hình", {
    problem: "Bốn chỉ số có thể cho thứ tự khác nhau; cần một tiêu chí khóa trước để không \"chọn chỉ số đẹp\" sau khi xem kết quả.",
    options: "MAE, RMSE, R², MAPE.",
    choice: "MAE trên tập validation, các chỉ số khác báo cáo kèm.",
    reason: "MAE có đơn vị triệu đồng, trả lời đúng câu hỏi người dùng quan tâm: \"dự đoán sai trung bình bao nhiêu tiền\". RMSE bị chi phối bởi vài tin lương rất cao; R² khó hiểu với người không chuyên; MAPE phóng đại sai số ở tin lương thấp.",
    risk: "MAE không phạt mạnh các sai số lớn; RMSE được báo cáo kèm để theo dõi.",
  }),
  ...decision("5.6.4. Ràng buộc đơn điệu theo kinh nghiệm", {
    problem: "Khi chưa có ràng buộc, lộ trình lương do Gradient Boosting dự đoán có lúc giảm khi tăng kinh nghiệm (ví dụ 7 năm thấp hơn 5 năm), do mô hình học theo vài tin bất thường.",
    options: "(1) Để nguyên. (2) Làm mượt lộ trình sau khi dự đoán. (3) Ràng buộc ngay trong mô hình.",
    choice: "Ràng buộc đơn điệu tăng theo số năm kinh nghiệm trong Gradient Boosting.",
    reason: "Quy luật \"thêm kinh nghiệm không làm giảm lương khi các yếu tố khác như nhau\" đúng với thị trường lao động và người dùng sẽ không tin một công cụ tư vấn vi phạm nó. Đưa ràng buộc vào mô hình nhất quán hơn sửa kết quả sau. Tại thời điểm đưa ra quyết định, MAE validation gần như không đổi (5,35 so với 5,24 triệu khi không ràng buộc), đổi lại lộ trình luôn hợp lý.",
    risk: "Nếu thị trường thật có đoạn lương không tăng theo kinh nghiệm, mô hình không thể hiện được.",
  }),
  ...decision("5.6.5. Ràng buộc đơn điệu theo kỹ năng", {
    problem: "Khi chạy thử trang tư vấn (06/11), hồ sơ Backend Developer ở Hà Nội, 5 năm kinh nghiệm, không kỹ năng được dự đoán 47,7 triệu; thêm đúng kỹ năng Java thì còn 42,3 triệu, thêm nhiều kỹ năng đôi khi còn giảm tiếp. Mô hình không lỗi lập trình mà học đúng dữ liệu: cột kỹ năng ghi những gì **tin tuyển dụng yêu cầu**, không phải những gì ứng viên có. Tin liệt kê nhiều kỹ năng thường là tin junior hoặc tuyển hàng loạt: với Backend (trên bộ dữ liệu lúc đó), tin có 7–8 kỹ năng có trung vị khoảng 21,5 triệu, tin có 1–2 kỹ năng khoảng 25,5 triệu. Đặc trưng \"số kỹ năng\" và các cột kỹ năng không ràng buộc đã học tương quan đó. Đây là tín hiệu thật để đoán lương của một tin, nhưng trả lời sai câu hỏi của trang tư vấn: biết thêm một kỹ năng thì lương thay đổi thế nào.",
    options: "(1) Giữ nguyên, chỉ ẩn các gợi ý có mức tăng âm. (2) Sửa kết quả sau khi dự đoán (lấy giá trị lớn hơn giữa có và không có kỹ năng). (3) Đưa quy tắc vào ngay trong mô hình. (4) Ép mỗi kỹ năng cộng một mức tối thiểu.",
    choice: "Phương án 3: bỏ đặc trưng số kỹ năng; Gradient Boosting có ràng buộc đơn điệu tăng cho mọi cột kỹ năng; Ridge chặn hệ số kỹ năng không âm; Random Forest được bọc bao đơn điệu. Mức tăng của từng kỹ năng vẫn do dữ liệu quyết định, không ép mức cộng tối thiểu.",
    reason: "Ngoài đời không nhà tuyển dụng nào trả ít hơn chỉ vì ứng viên biết thêm Java; một công cụ tư vấn khuyên \"học Java thì mất 5 triệu\" sẽ mất lòng tin của người dùng. Ẩn gợi ý âm (phương án 1) vẫn để con số lương trên trang tự mâu thuẫn khi người dùng tự thêm kỹ năng. Ràng buộc cả ba mô hình để người dùng chọn mô hình nào trên giao diện cũng không gặp lại lỗi. Không ép mức cộng tối thiểu vì như vậy là bịa ra giá trị mà dữ liệu không có. Sau khi ràng buộc, cùng hồ sơ trên: không kỹ năng 39,8 triệu, thêm Java vẫn 39,8 triệu, thêm Java, Spring Boot, Docker và AWS lên 48,8 triệu.",
    risk: "Ngân sách ban đầu chỉ cho phép MAE test tăng tối đa 5%; thực tế tăng từ 5,38 lên 5,82 triệu (+8,2%). Nhóm đã thử chọn theo validation với nhiều tốc độ học, số lá, điều chuẩn, số vòng, hàm mất mát MAE và bao đơn điệu trên mô hình không ràng buộc; MAE validation luôn từ 5,68 trở lên so với 5,35 khi không ràng buộc, nghĩa là phần mất mát đến từ chính ràng buộc chứ không phải do tham số. Ngân sách được nới lên 5,85 triệu và không chỉnh tham số theo test. Hồ sơ không kỹ năng trở thành mức sàn nên thấp hơn trước. Kiểm thử tự động chặn lỗi tái phát: thêm kỹ năng không làm giảm lương, mọi gợi ý có mức tăng không âm. Ngân sách MAE này được đo trên bộ dữ liệu còn lẫn tin sinh tự động nên về sau được thay bằng chuẩn production (mục 5.5.5).",
  }),
  ...decision("5.6.6. Đối chiếu với chuẩn production thay vì tự đặt ngưỡng", {
    problem: "Tiêu chí cũ chỉ là \"thắng mốc trung vị trên validation và test\". Một mô hình sai trung bình 6 triệu vẫn qua tiêu chí này, và không ai biết nó đã đủ tốt để đưa cho người dùng thật hay chưa. Tự đặt một ngưỡng MAPE thì dễ chọn con số vừa với kết quả mình đang có.",
    options: "(1) Giữ tiêu chí thắng mốc. (2) Tự đặt ngưỡng MAPE. (3) Dùng chỉ số và mức mà các sản phẩm dự đoán lương thực tế công bố (Glassdoor, LinkedIn Salary).",
    choice: "Phương án 3: trung vị sai số %, tỉ lệ sai ≤ 20%, độ phủ p10–p90; ngưỡng chung so bằng cận bất lợi bootstrap, ngưỡng nhóm so bằng giá trị điểm; khóa ngưỡng ở một chỗ trong code.",
    reason: "Giống việc chấm một học sinh theo barem của kỳ thi thật thay vì barem tự đặt sau khi xem bài. Ba chỉ số này cũng dễ hiểu với người dùng: \"một nửa số dự đoán lệch dưới 16%\" dễ hiểu hơn \"MAE 6,49\". So ngưỡng chung bằng cận bất lợi để mô hình không đậu nhờ may mắn của một tập test.",
    risk: "Mô hình hiện tại chưa đạt, nên ứng dụng phải ghi rõ kết quả chỉ mang tính tham khảo. So ngưỡng nhóm bằng giá trị điểm thì kém chặt hơn, đổi lại không đánh trượt cả những nhóm thực sự tốt chỉ vì ít mẫu.",
  }),
  ...decision("5.6.7. Chỉ hiện con số lương khi đủ dữ liệu", {
    problem: "Mọi hồ sơ đều nhận một con số lương như nhau, kể cả Data Engineer cấp Middle chỉ có 7 tin train hay Tech Lead cấp Senior không có tin nào. Con số khi đó trông chắc chắn như mọi con số khác nhưng thực chất gần như đoán.",
    options: "(1) Hiện con số cho mọi hồ sơ. (2) Không trả gì khi thiếu dữ liệu (như ADR 0008 đề ra ban đầu). (3) Chỉ hiện khoảng lương mở rộng, kèm lý do, cho hồ sơ thiếu dữ liệu.",
    choice: "Phương án 3: con số chỉ hiện khi nhóm vai trò × cấp bậc có ít nhất 20 tin train và không trượt chuẩn; còn lại hiện khoảng rộng hơn trong hai khoảng của vai trò và của cấp bậc.",
    reason: "Một người tư vấn trung thực sẽ nói \"với vị trí này tôi chỉ biết lương thường nằm trong khoảng 24–61 triệu\" thay vì bịa một con số. Không trả gì thì người dùng mất cả thông tin hữu ích: khoảng mở rộng vẫn phủ đúng khoảng 88% trên test. Ngưỡng 20 tin theo cách LinkedIn Salary làm.",
    risk: "Nhiều hồ sơ hiếm chỉ nhận khoảng rộng, có thể kém hấp dẫn với người dùng. Khoảng mở rộng của nhóm có dưới 20 tin valid dùng p10–p90 lương thị trường trên tập train.",
  }),
);

// ============================== CHƯƠNG 6 ==============================
chapter = 6;
body.push(
  H1("CHƯƠNG 6: XÂY DỰNG ỨNG DỤNG"),
  H2("6.1. Kiến trúc hệ thống"),
  ...fig(path.join(DIA, "01-kien-truc-he-thong.png"), "Kiến trúc tổng thể của hệ thống", 15),
  P("Hệ thống gồm bốn tầng. **Tầng dữ liệu nguồn** chứa ba tệp CSV thô. **Tầng xử lý dữ liệu** thực hiện quy trình ở Chương 3 và tạo bộ dữ liệu sạch có nhãn. **Tầng mô hình** huấn luyện ngoại tuyến theo Chương 5 và lưu mô hình, bảng chỉ số, bảng giá trị kỹ năng, kết quả kiểm định. **Tầng trình bày** là ứng dụng web Streamlit chỉ nạp mô hình đã lưu, không huấn luyện lại khi người dùng thao tác; dữ liệu, mô hình và biểu đồ được lưu đệm để phản hồi nhanh. Tách huấn luyện khỏi dự đoán giúp kết quả ổn định giữa các lần sử dụng và đáp ứng tiêu chí chấp nhận (4), (5) của user story."),
  H2("6.2. Phân tích chức năng"),
  ...fig(path.join(DIA, "02-use-case.png"), "Sơ đồ use case", 14),
  ...table("Đặc tả use case Dự đoán lương và đề xuất kỹ năng", ["Mục", "Nội dung"], [
    ["Tác nhân", "Người dùng (ứng viên CNTT)"],
    ["Tiền điều kiện", "Mô hình đã được huấn luyện và lưu sẵn"],
    ["Luồng chính", "1. Người dùng mở trang Tư vấn & dự đoán lương.\n2. Chọn vai trò, khu vực, số năm kinh nghiệm, các kỹ năng đang có; có thể thêm chức danh, loại công ty, hình thức làm việc và chọn mô hình.\n3. Bấm Dự đoán & tư vấn.\n4. Hệ thống hiển thị khoảng lương 80%, mức điển hình kèm số tin cùng vai trò và cấp bậc, và vị trí so với thị trường của vai trò.\n5. Hệ thống hiển thị tối đa 5 kỹ năng nên học và lộ trình lương theo kinh nghiệm."],
    ["Luồng phụ", "(a) Hồ sơ thuộc nhóm ít dữ liệu: chỉ hiện khoảng lương mở rộng, cảnh báo \"Ít dữ liệu\" kèm lý do; gợi ý kỹ năng không hiện mức tăng lương. (b) Mở đường dẫn có chứa hồ sơ (vai trò, số năm, kỹ năng) để xem ngay kết quả của một hồ sơ được chia sẻ."],
    ["Hậu điều kiện", "Kết quả được giữ trong phiên làm việc; mô hình không bị thay đổi"],
  ], [3, 12]),
  H2("6.3. Thiết kế chi tiết"),
  P("Mã nguồn được tổ chức thành các module độc lập theo trách nhiệm (Hình 6.3): **salary_dataset** đọc ba nguồn, gán nhãn và chia tập; **salary_model** dựng đặc trưng, huấn luyện, dự đoán và tư vấn; **salary_validation** kiểm định (hiệu chuẩn, bootstrap, công bằng); **production_standard** chấm chuẩn production; **prediction_support** quyết định hồ sơ nào được hiện con số; **model_promotion** là cổng thay mô hình khi huấn luyện lại; **label_review** lấy mẫu và chấm độ chính xác nhãn; **salary_charts** vẽ biểu đồ; **salary_app** là bộ nhớ đệm cho giao diện. Các trang giao diện chỉ gọi tới bộ nhớ đệm, không đọc trực tiếp dữ liệu thô. Mỗi tính năng của ứng dụng có một notebook trình bày lại logic phía sau trong thư mục **notebooks/**. Hình 6.4 mô tả trình tự trao đổi giữa các thành phần khi người dùng yêu cầu tư vấn."),
  ...fig(path.join(DIA, "07-so-do-module.png"), "Sơ đồ module của hệ thống", 14),
  ...fig(path.join(DIA, "05-tuan-tu-tu-van.png"), "Sơ đồ tuần tự chức năng tư vấn", 15),
  H2("6.4. Thuật toán tư vấn kỹ năng"),
  P("Thuật toán nhận hồ sơ người dùng và trả về mức lương dự đoán, khoảng thường gặp, danh sách kỹ năng đề xuất và lộ trình theo kinh nghiệm (Hình 6.5):"),
  ...steps([
    "Biểu diễn hồ sơ thành vector đặc trưng như một tin tuyển dụng; cấp bậc được suy ra từ số năm kinh nghiệm theo quy tắc ở mục 3.6.",
    "Tính lương dự đoán ŷ = f(x) bằng mô hình đã chọn.",
    "Tính khoảng thường gặp theo công thức (6.1).",
    "Kiểm tra nhóm đủ dữ liệu: nếu vai trò × cấp bậc có dưới 20 tin train, hoặc vai trò hay cấp bậc trượt chuẩn production, thì bỏ con số và thay khoảng bằng khoảng mở rộng của vai trò/cấp bậc (mục 5.5.5).",
    "Lập danh sách kỹ năng ứng viên: kỹ năng người dùng chưa có và xuất hiện ở ít nhất 3% số tin của cùng vai trò, để không gợi ý kỹ năng không liên quan tới nghề.",
    "Với mỗi kỹ năng ứng viên k, bật đúng kỹ năng đó trong hồ sơ, dự đoán lại và tính mức tăng Δₖ = f(x ⊕ k) − f(x).",
    "Xếp hạng: kỹ năng có Δₖ lớn hơn 0,1 triệu được xếp trước theo Δₖ giảm dần; nếu chưa đủ 5 kỹ năng, bổ sung kỹ năng được yêu cầu nhiều nhất của vai trò để người dùng vẫn có định hướng.",
    "Dự đoán lương với số năm kinh nghiệm tăng thêm 0, 1, 2, 3 và 5 năm (cấp bậc được suy lại theo số năm mới) để vẽ lộ trình.",
  ]),
  P("Khoảng thường gặp được xây dựng từ sai số thực nghiệm trên tập validation. Gọi q₀,₁ và q₀,₉ là phân vị 10% và 90% của tỉ lệ yᵢ / ŷᵢ trên validation, khoảng thường gặp của một dự đoán là"),
  eq([r("[ŷ · "), sb("q", "0,1"), r(" ;  ŷ · "), sb("q", "0,9"), r("]")]),
  P(`với q₀,₁ = ${fmt(metrics.interval_ratio.p10)} và q₀,₉ = ${fmt(metrics.interval_ratio.p90)}. Khoảng này bao khoảng 80% tin tương tự trong dữ liệu kiểm định, dễ hiểu với người dùng hơn một con số đơn lẻ.`),
  ...fig(path.join(DIA, "06-thuat-toan-de-xuat.png"), "Lưu đồ thuật toán đề xuất kỹ năng", 10),
  H2("6.5. Giao diện demo"),
  P("Ứng dụng có năm trang trong thanh điều hướng: Tư vấn & dự đoán lương (trang chủ), Tổng quan, Thị trường việc làm, Đánh giá mô hình và Dữ liệu huấn luyện."),
  P("Trang Thị trường việc làm vẫn dùng quy trình kiểm duyệt nghiêm ngặt ban đầu (MarketService): 320 tin vượt cổng kiểm tra bằng chứng và 14 nhãn lương được chấp nhận. Trang này có bộ lọc nguồn, nhóm nghề, địa điểm và hình thức làm việc; số liệu phụ thuộc bộ lọc đang chọn. Đây là tập riêng, không phải bộ 1.735 tin có lương của salary-v2 dùng ở Tổng quan, Đánh giá mô hình, Dữ liệu huấn luyện và công cụ Tư vấn. Sáu notebook tính năng trình bày riêng hai quy trình để người đọc không so nhầm các mẫu số."),
  ...fig(path.join(FIG, "ui-advisor.png"), "Trang Tư vấn & dự đoán lương với hồ sơ Backend Developer, 3 năm, Java/Spring Boot/SQL", 15),
  P("Với hồ sơ Backend Developer tại Hà Nội, 3 năm kinh nghiệm, biết Java, Spring Boot, SQL (nhóm Backend × Middle có 58 tin train, đủ dữ liệu), hệ thống hiện khoảng lương 13,4–29,9 triệu và mức điển hình 20,2 triệu/tháng, ở phân vị 34 của vai trò (trung vị 25 triệu trên 278 tin). Kỹ năng đề xuất là Kafka (+4,4 triệu), Python (+3,5), Golang (+3,2), Kubernetes (+1,8) và Microservices (+1,5). Lộ trình tăng chậm ở cấp Middle (21,7 triệu khi 4 năm) rồi nhảy lên 32,8 triệu khi có 5 năm (cấp Senior), khớp với bước nhảy Middle → Senior ở Hình 4.5. Ngược lại, hồ sơ Data Engineer 3 năm (nhóm Data Engineer × Middle chỉ có 7 tin train) chỉ nhận khoảng 23,7–61,1 triệu kèm cảnh báo \"Ít dữ liệu\", không có con số và không hiện mức tăng lương của từng kỹ năng."),
  ...fig(path.join(FIG, "ui-advisor-lowdata.png"), "Hồ sơ ít dữ liệu (Data Engineer, 3 năm): chỉ hiện khoảng lương kèm cảnh báo", 15),
  ...fig(path.join(FIG, "ui-overview.png"), "Dashboard tổng quan thị trường với đủ 23 vai trò", 12),
  ...fig(path.join(FIG, "ui-evaluation.png"), "Trang đánh giá mô hình", 11),
  ...fig(path.join(FIG, "ui-dataset.png"), "Trang dữ liệu huấn luyện với nhãn train/validation/test", 15),
  H2("6.6. Kiểm thử ứng dụng"),
  P("Ứng dụng có 467 ca kiểm thử tự động, tất cả đạt, gồm kiểm thử đơn vị cho các quy tắc xử lý dữ liệu, kiểm thử hành vi chạy trên chính mô hình đã lưu, kiểm thử chuẩn production và cổng thay mô hình, kiểm thử các notebook chạy hết từ đầu đến cuối, và kiểm thử giao diện mô phỏng thao tác người dùng trên từng trang. Bảng 6.2 liệt kê các nhóm ca kiểm thử chính."),
  ...table("Các nhóm ca kiểm thử", ["Nhóm kiểm thử", "Nội dung kiểm tra", "Kết quả"], [
    ["Chuẩn hóa lương", "8 dạng chuỗi lương: khoảng, cận trên, USD, theo năm, thỏa thuận, khoảng quá rộng", "Đạt"],
    ["Chuẩn hóa kinh nghiệm", "\"2 năm\", \"Dưới 1 năm\", \"Trên 5 năm\", \"1 - 3 Năm\", \"Không yêu cầu\"", "Đạt"],
    ["Phân loại vai trò", "Java Developer, Data Engineer, ML Engineer, Tester; loại IT Sales, Kế toán", "Đạt"],
    ["Bộ dữ liệu", "Hơn 3.000 tin, đủ 23 vai trò, công ty không trùng giữa các tập", "Đạt"],
    ["Mô hình", "Mọi mô hình có MAE test thấp hơn mốc trung vị; đủ 4 chỉ số", "Đạt"],
    ["Kiểm định", "Khoảng 80% bao phủ 70–90% tin test; MAE nằm trong khoảng tin cậy bootstrap; nhận đúng điều kiện giới tính có dấu, bỏ qua \"Nam Kinh Nghiem\" không dấu", "Đạt"],
    ["Tư vấn", "Lương trong khoảng hợp lý, đề xuất không chứa kỹ năng đã có, lộ trình không giảm", "Đạt"],
    ["Hành vi mô hình", "Với cả ba mô hình: thêm kỹ năng không làm giảm lương, bỏ bất kỳ kỹ năng nào khỏi hồ sơ 12 kỹ năng không làm tăng lương; gợi ý và bảng giá trị kỹ năng không có mức tăng âm; báo cáo đã lưu khớp mô hình hiện tại", "Đạt"],
    ["Dữ liệu thật", "Không còn tin sinh tự động; hệ số tin một đầu học trên train theo nguồn; đặc trưng nền tảng, hình thức, loại công ty", "Đạt"],
    ["Chuẩn production và cổng", "Ngưỡng, cách chấm nhóm, hồ sơ ít dữ liệu chỉ nhận khoảng, mô hình mới chỉ thay khi qua cổng", "Đạt"],
    ["Notebook", "Mọi notebook được commit không kèm output và chạy hết không lỗi", "Đạt"],
    ["Giao diện", "Trang tư vấn là trang chủ; dashboard có 23 vai trò; trang đánh giá và dữ liệu hiển thị không lỗi", "Đạt"],
  ], [3, 9, 1.5], [0, 0, C]),
  H2("6.7. Triển khai"),
  P("Ứng dụng chạy trên Python 3.11. Sau khi cài các thư viện khai báo trong tệp cấu hình của dự án, người dùng khởi động máy chủ Streamlit và mở ứng dụng trên trình duyệt tại cổng 8502. Dự án cũng có cấu hình Docker đóng gói sẵn dữ liệu và mô hình, chạy được không cần Internet vào ngày demo. Việc tạo lại bộ dữ liệu, huấn luyện lại và kiểm định mô hình là một thao tác riêng, chỉ cần khi có dữ liệu mới. Mã nguồn được lưu trữ tại https://github.com/theihoz/ML."),
);

body.push(
  H2("6.8. Các quyết định thiết kế ứng dụng và lý do"),
  ...decision("6.8.1. Khoảng thường gặp dựa trên sai số thực nghiệm", {
    problem: "Một con số lương duy nhất tạo cảm giác chắc chắn giả: sai số trung bình là khoảng 6,5 triệu, nên nói \"lương của bạn là 24,3 triệu\" dễ gây hiểu lầm.",
    options: "(1) Cộng trừ MAE. (2) Khoảng từ độ phân tán của các cây trong Random Forest. (3) Hồi quy phân vị. (4) Phân vị của tỉ lệ lương thật / dự đoán trên tập validation.",
    choice: "Phương án 4: khoảng = dự đoán × [phân vị 10%, phân vị 90%] của tỉ lệ.",
    reason: "Cộng trừ một số cố định không hợp lý vì sai số với người lương 80 triệu lớn hơn nhiều người lương 15 triệu; dùng tỉ lệ tự động co giãn theo mức lương. Phương án 4 dùng được cho mọi mô hình và kiểm chứng được: mục 5.5.1 cho thấy khoảng 80% bao phủ 83,0% tin test.",
    risk: "Cùng một độ rộng tương đối cho mọi vai trò, trong khi vai trò quản lý cần khoảng rộng hơn.",
  }),
  ...decision("6.8.2. Đề xuất kỹ năng theo mức tăng lương dự đoán", {
    problem: "Xếp kỹ năng theo số tin nhắc tới chỉ cho biết kỹ năng phổ biến: JavaScript đứng đầu về nhu cầu nhưng tin có JavaScript không trả cao hơn. Người dùng hỏi \"nên học gì để tăng lương\" chứ không hỏi \"kỹ năng nào phổ biến\".",
    options: "(1) Xếp theo số tin. (2) Xếp theo chênh lệch trung vị lương có/không kỹ năng. (3) Xếp theo mức tăng lương mô hình dự đoán cho chính hồ sơ người dùng.",
    choice: "Phương án 3, kết hợp lọc kỹ năng phải xuất hiện ở ít nhất 3% tin cùng vai trò.",
    reason: "Chênh lệch trung vị bị nhiễu bởi vai trò và kinh nghiệm: kỹ năng xuất hiện nhiều ở tin Senior sẽ có trung vị cao dù không tự làm tăng lương. Phương án 3 giữ nguyên mọi yếu tố khác của người dùng và chỉ thay đổi đúng một kỹ năng, giống việc hỏi \"nếu tôi giống hệt hiện tại nhưng biết thêm AWS thì lương thay đổi bao nhiêu\". Bộ lọc 3% tránh gợi ý kỹ năng không liên quan nghề, ví dụ gợi ý Figma cho kỹ sư Backend.",
    risk: "Vẫn là quan hệ tương quan học từ tin tuyển dụng, không chứng minh học kỹ năng sẽ được tăng lương.",
  }),
  ...decision("6.8.3. Không huấn luyện lại khi người dùng dự đoán", {
    problem: "Nếu huấn luyện lại mỗi lần dự đoán, kết quả có thể khác nhau giữa các lần bấm và người dùng phải chờ hàng chục giây.",
    options: "(1) Huấn luyện khi khởi động ứng dụng. (2) Huấn luyện ngoại tuyến, lưu mô hình, ứng dụng chỉ nạp.",
    choice: "Phương án 2.",
    reason: "Một công cụ tư vấn phải nhất quán: cùng hồ sơ phải ra cùng kết quả hôm nay và ngày mai. Mô hình đã lưu cũng chính là mô hình đã được đánh giá ở Chương 5, nên các con số kiểm định áp dụng đúng cho thứ người dùng đang dùng. Thời gian phản hồi dưới 1 giây, đáp ứng tiêu chí chấp nhận (5).",
    risk: "Cần chủ động huấn luyện lại khi có dữ liệu mới; việc thay mô hình đi qua cổng ở mục 5.5.5.",
    }),
    ...decision("6.8.4. Hiện khoảng lương trước, con số sau, giải thích bằng lời thường", {
      problem: "Trang tư vấn ban đầu hiện một con số lớn, khoảng lương nằm ở dòng nhỏ bên dưới. Người dùng dễ hiểu \"20,2 triệu\" là lời hứa, trong khi một nửa số dự đoán lệch hơn 16%. Thông báo về dữ liệu ít lại dùng thuật ngữ như \"tin train\", \"production\".",
      options: "(1) Giữ nguyên. (2) Bỏ con số, chỉ hiện khoảng. (3) Hiện khoảng trước làm thông tin chính, con số là \"mức điển hình\" kèm số tin hỗ trợ; giải thích bằng lời thường, chi tiết kỹ thuật để trong mục \"Vì sao?\".",
      choice: "Phương án 3.",
      reason: "Giống dự báo thời tiết nói \"nhiệt độ 26–32 độ\" thay vì \"29,3 độ\": người nghe hiểu ngay mức độ chắc chắn. Con số điển hình vẫn hữu ích cho hồ sơ đủ dữ liệu. Người dùng không làm kỹ thuật đọc được lý do mà không phải hiểu thuật ngữ.",
      risk: "Khoảng 80% khá rộng (trung bình khoảng 22 triệu) nên có thể kém hấp dẫn; đây là phản ánh trung thực của độ chính xác hiện tại.",
  }),
);

// ============================== KẾT LUẬN ==============================
chapter = 7;
body.push(
  H1("KẾT LUẬN VÀ KIẾN NGHỊ"),
  H3("Kết quả đạt được"),
  B("Xây dựng quy trình xử lý dữ liệu tái lập được, gộp ba nguồn với 8.523 tin, phát hiện và loại 2.400 tin sinh tự động, thu được bộ dữ liệu 1.735 tin thật có nhãn lương, 23 vai trò, 69 kỹ năng, gắn nhãn train/validation/test theo công ty; đo độ chính xác bộ gán nhãn trên 208 tin."),
  B("Trực quan hóa đầy đủ các yêu cầu: top công nghệ theo nhu cầu và theo lương, tương quan kinh nghiệm – thu nhập (ρ = 0,70), so sánh lương theo vai trò, khu vực và vai trò × khu vực."),
  B(`Huấn luyện và so sánh ba mô hình cùng mốc trung vị trên bốn chỉ số; Gradient Boosting đạt MAE test ${fmt(sel.test.MAE)} triệu, R² ${fmt(sel.test.R2, 3)}, trung vị sai số ${fmt(P0.overall.metrics.median_error_pct.point, 1)}%; cả ba mô hình được ràng buộc để lương dự đoán không giảm khi tăng kinh nghiệm hoặc thêm kỹ năng.`),
  B("Xác định các kỹ năng gia tăng thu nhập cao nhất: LLM/GenAI, AWS, Kafka, Next.js, Python, Golang."),
  B("Kiểm định độ tin cậy: khoảng dự đoán 80% bao phủ 83,0% tin test; không có thiên lệch đáng kể giữa các thành phố lớn; đối chiếu chuẩn production theo cách Glassdoor và LinkedIn công bố, và trình bày trung thực rằng mô hình chưa đạt."),
  B("Hoàn thành ứng dụng Streamlit với công cụ tư vấn nghề nghiệp đúng user story, chỉ hiện con số lương khi đủ dữ liệu, dashboard đủ 23 vai trò, trang đánh giá mô hình và trang dữ liệu; 467 ca kiểm thử tự động đều đạt; mỗi tính năng có một notebook trình bày."),
  H3("Hạn chế"),
  B("Lương là lương chào tuyển trong tin, không phải lương thực nhận, và chưa phân biệt gross/net; các tin không công bố hoặc không đọc được lương (3.312 trong 6.123 tin sau khi loại tin sinh tự động, khoảng 54,1%) bị loại nên mẫu có thể lệch về doanh nghiệp công bố lương."),
  B("Dữ liệu lệch mạnh về Hà Nội (80,3%); TP. Hồ Chí Minh và Đà Nẵng có ít tin có lương nên kết quả cho các khu vực này kém tin cậy hơn."),
  B("Phân loại vai trò và bóc tách kỹ năng dựa trên luật; độ chính xác được đo trên mẫu 208 tin do AI duyệt, chưa có người duyệt lại; hệ số suy đầu lương còn thiếu theo nguồn là giả định."),
  B("Chỉ còn 1.735 tin thật; tập test 288 tin quá nhỏ: 18/22 vai trò có dưới 20 tin test nên không chấm được, và chưa đủ bằng chứng để khẳng định Gradient Boosting tốt hơn hẳn Ridge hay Random Forest."),
  B("Mô hình chưa đạt chuẩn production (trung vị sai số 16,4%, 56% dự đoán sai không quá 20%); cấp Lead trượt rõ. Một số vai trò có rất ít mẫu (DBA 5 tin, UI/UX 11 tin, CTO 13 tin)."),
  B("Mức tăng lương theo kỹ năng là quan hệ tương quan, không phải nhân quả."),
  B("Ràng buộc đơn điệu theo kỹ năng đổi một phần độ chính xác lấy lời tư vấn luôn hợp lý."),
  B("Mô hình dự đoán cao hơn thực tế khoảng 7% với cấp Junior và khoảng tin cậy hẹp ở vai trò quản lý; dữ liệu không có giới tính nên không đo được công bằng giới."),
  H3("Hướng phát triển"),
  B("Thu thập thêm tin tuyển dụng thật có lương, định kỳ, bổ sung TP. Hồ Chí Minh và các thành phố khác: đây là cách nhiều khả năng nhất để đạt chuẩn production và phân tích xu hướng theo thời gian."),
  B("Dùng mô hình ngôn ngữ để bóc tách kỹ năng và chuẩn hóa chức danh thay cho luật thủ công."),
  B("Bổ sung đặc trưng quy mô và làm giàu thông tin loại hình công ty; dự đoán khoảng bằng hồi quy phân vị; kết hợp dữ liệu khảo sát lương thực nhận."),
  B("Cá nhân hóa lộ trình học: gợi ý chuỗi kỹ năng theo thứ tự và ước lượng thời gian học."),
  B("Mời người duyệt lại mẫu nhãn 208 tin và đo thêm tỉ lệ kỹ năng bị bỏ sót."),
);

// ============================ PHÂN CÔNG ============================
body.push(
  H1("BẢNG PHÂN CÔNG NHIỆM VỤ"),
  new Paragraph({ style: "BangCaption", children: [new TextRun("Phân công nhiệm vụ và tỷ lệ đóng góp của các thành viên")] }),
  ...table(null, ["STT", "Họ và tên", "MSSV", "Nhiệm vụ", "Tỷ lệ đóng góp"], [
    ["1", "", "", "Trưởng nhóm; tổng quan đề tài, kiến trúc hệ thống, tổng hợp báo cáo", ""],
    ["2", "", "", "Thu thập, làm sạch và chuẩn bị dữ liệu (Pandas, NumPy)", ""],
    ["3", "", "", "Trực quan hóa dữ liệu (Matplotlib, Seaborn) và phân tích insight", ""],
    ["4", "", "", "Xây dựng, huấn luyện, đánh giá và kiểm định mô hình AI", ""],
    ["5", "", "", "Xây dựng ứng dụng Streamlit, kiểm thử và sơ đồ draw.io", ""],
    ["", "**Tổng**", "", "", "100%"],
  ], [1, 4, 2.5, 7, 2], [C, 0, 0, 0, C]),
);

// ============================ TÀI LIỆU THAM KHẢO (APA) ============================
const refs = [
  "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.",
  "Châu, G. B. (2026). *Vietnam IT jobs – Raw data from TopCV (2026)* [Data set]. Kaggle. https://www.kaggle.com/datasets/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026",
  "Efron, B., & Tibshirani, R. J. (1993). *An introduction to the bootstrap*. Chapman & Hall.",
  "Fisher, A., Rudin, C., & Dominici, F. (2019). All models are wrong, but many are useful: Learning a variable's importance by studying an entire class of prediction models simultaneously. *Journal of Machine Learning Research, 20*(177), 1–81.",
  "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *The Annals of Statistics, 29*(5), 1189–1232.",
  "Harris, C. R., Millman, K. J., van der Walt, S. J., et al. (2020). Array programming with NumPy. *Nature, 585*(7825), 357–362.",
  "Hoerl, A. E., & Kennard, R. W. (1970). Ridge regression: Biased estimation for nonorthogonal problems. *Technometrics, 12*(1), 55–67.",
  "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering, 9*(3), 90–95.",
  "Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting, 22*(4), 679–688.",
  "JGraph Ltd. (2026). *draw.io documentation*. https://www.drawio.com/doc/",
  "Ke, G., Meng, Q., Finley, T., et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. In *Advances in Neural Information Processing Systems 30* (pp. 3146–3154).",
  "Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association, 113*(523), 1094–1111.",
  "McKinney, W. (2010). Data structures for statistical computing in Python. In *Proceedings of the 9th Python in Science Conference* (pp. 56–61).",
  "Nguyen, T. H. T. (2023). *Vietnamese job posting – Vietnamese version* [Data set]. Kaggle. https://www.kaggle.com/datasets/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version",
  "Nguyễn, V. T. (2026). *ADY201m dataset: Vietnam IT job posts* [Data set]. Kaggle. https://www.kaggle.com/datasets/vitthnhnguyn138/vietnam-it-job-posts",
  "Object Management Group. (2017). *OMG Unified Modeling Language (OMG UML), version 2.5.1*.",
  "Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.",
  "Python Software Foundation. (2026). *Python 3.11 documentation*. https://docs.python.org/3.11/",
  "Quốc hội. (2019). *Bộ luật Lao động* (Luật số 45/2019/QH14).",
  "Snowflake Inc. (2026). *Streamlit documentation*. https://docs.streamlit.io",
  "Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology, 15*(1), 72–101.",
  "Tukey, J. W. (1977). *Exploratory data analysis*. Addison-Wesley.",
  "Waskom, M. L. (2021). seaborn: Statistical data visualization. *Journal of Open Source Software, 6*(60), 3021.",
];
body.push(
  H1("TÀI LIỆU THAM KHẢO"),
  ...refs.map((text) => new Paragraph({ indent: { left: 720, hanging: 720, firstLine: 0 }, alignment: AlignmentType.LEFT, children: runs(text) })),
);

// ============================== TÀI LIỆU ==============================
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] });
const page = {
  size: { width: 11906, height: 16838 },
  margin: { top: Math.round(2.5 * CM), bottom: 3 * CM, left: Math.round(3.5 * CM), right: 2 * CM, header: 709, footer: 709 },
};
const doc = new Document({
  creator: "Nhóm thực hiện",
  title: "Phân tích xu hướng thị trường việc làm ngành CNTT và dự đoán mức lương lập trình viên",
  description: "Tiểu luận học phần Lập trình Python",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 26 }, paragraph: { spacing: { line: 360, after: 120 } } } },
    paragraphStyles: [
      { id: "Normal", name: "Normal", run: { font: FONT, size: 26 }, paragraph: { alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, before: 0, after: 120 }, indent: { firstLine: CM } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true, allCaps: true }, paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 0, after: 360 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true }, paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { before: 240, after: 120 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true, italics: true }, paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { before: 120, after: 120 }, outlineLevel: 2, keepNext: true } },
      { id: "HinhCaption", name: "HinhCaption", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 24, italics: true }, paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 60, after: 240, line: 276 } } },
      { id: "BangCaption", name: "BangCaption", basedOn: "Normal", next: "Normal", run: { font: FONT, size: 24, italics: true }, paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 60, line: 276 }, keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360, firstLine: 0 } } } }] },
      { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "Bước %1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1134, hanging: 1134, firstLine: 0 } } } }] },
    ],
  },
  sections: [
    { properties: { page }, children: cover },
    { properties: { page, type: SectionType.NEXT_PAGE }, children: grading },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } }, type: SectionType.NEXT_PAGE }, footers: { default: footer }, children: front },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } }, type: SectionType.NEXT_PAGE }, footers: { default: footer }, children: body },
  ],
});
Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(OUT, buffer);
  console.log("wrote", OUT, buffer.length);
});
