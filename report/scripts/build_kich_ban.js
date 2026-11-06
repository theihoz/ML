// Kịch bản đọc khi thuyết trình (.docx), dùng chung nội dung với slide.
// Chạy: NODE_PATH=<node_modules có docx> node report/scripts/build_kich_ban.js <out.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, LevelFormat, PageBreak, Footer, PageNumber, TableOfContents,
} = require("docx");
const { SLIDES, QA, CHEAT } = require("./thuyet_trinh_content");

const OUT = process.argv[2];
const FONT = "Times New Roman";
const GREY = "6B7280";
const ACCENT = "1D4ED8";
const CONTENT_W = 9638; // A4 trừ lề 2 cm mỗi bên (DXA)

const run = (text, opts = {}) => new TextRun({ text, font: FONT, ...opts });
const para = (text, opts = {}) =>
  new Paragraph({ spacing: { after: 160, line: 360 }, ...opts, children: [run(text, opts.run || {})] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "D1D5DB" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(head, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, isHead) =>
    new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: isHead ? { fill: "E5E7EB", type: ShadingType.CLEAR, color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [run(text, { size: 22, bold: isHead })] })],
    });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, i, false)) })),
    ],
  });
}
const evenWidths = (n) => {
  const w = Math.floor(CONTENT_W / n);
  return Array.from({ length: n }, (_, i) => (i === n - 1 ? CONTENT_W - w * (n - 1) : w));
};

const children = [];

// ── Trang bìa
children.push(
  new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER, children: [run("KỊCH BẢN THUYẾT TRÌNH", { size: 40, bold: true, color: ACCENT })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [run("Phân tích xu hướng thị trường việc làm CNTT", { size: 32, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 }, children: [run("& dự đoán mức lương lập trình viên", { size: 32, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run("Tiểu luận môn Lập trình Python – Đề tài 4 – Nhóm 3", { size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run("GVHD: ThS. Lý Ngọc Hưng – Trường Đại học Gia Định", { size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 }, children: [run("Người trình bày: ……………………………… MSSV: ………………", { size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200 }, children: [run(`Đi kèm bộ slide SlideThuyetTrinh_De4_v2.pptx (${SLIDES.length} slide)`, { size: 22, italics: true, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ── Cách dùng
children.push(
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run("Cách dùng kịch bản")] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Mỗi mục ứng với một slide, đánh số giống trên slide. Ô xám nhỏ \"Trên slide\" nhắc lại những gì khán giả đang thấy.", { size: 26 })] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Phần chữ lớn là lời nói, viết sẵn để đọc. Đọc chậm, dừng một nhịp ở mỗi con số.", { size: 26 })] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Dấu ▶ CHUYỂN SLIDE ở cuối mỗi mục là lúc bấm sang slide tiếp theo.", { size: 26 })] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Mọi quyết định được kể theo cùng một mạch: vấn đề trước đó → hậu quả nếu để nguyên → các phương án → lựa chọn và lý do → cái giá phải trả.", { size: 26 })] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Slide viết cho người không làm kỹ thuật: mỗi slide một ý, ít số. Thuật ngữ chuyên môn (MAE, hiệu chuẩn, bootstrap…) chỉ xuất hiện trong lời nói, luôn kèm giải thích bằng lời thường. Số liệu lấy từ mô hình đang phục vụ: 1.735 tin thật, sau khi loại 2.400 tin sinh tự động.", { size: 26 })] }),
  new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 }, children: [run("Cuối kịch bản có phần Hỏi – đáp: 12 câu hội đồng có thể hỏi kèm câu trả lời.", { size: 26 })] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [run("Số liệu cần nhớ")] }),
  table(["Nội dung", "Số liệu"], CHEAT, [2900, CONTENT_W - 2900]),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run("Mục lục")] }),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ── Từng slide
let currentSection = "";
SLIDES.forEach((s, idx) => {
  const n = idx + 1;
  if (s.section !== currentSection) {
    currentSection = s.section;
    if (idx > 0) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(s.section.toUpperCase())] }));
  }
  const title = s.title.replace(/\n/g, " – ");
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(`Slide ${n}. ${title}`)] }));

  const onSlide = [];
  if (s.subtitle) onSlide.push(...s.subtitle.split("\n"));
  if (s.big) onSlide.push(`Số lớn: ${s.big.value} – ${s.big.caption}`);
  if (s.points) onSlide.push(...s.points);
  if (s.compare) onSlide.push(`${s.compare.left.head}: ${s.compare.left.lines.join("; ")}`, `${s.compare.right.head}: ${s.compare.right.lines.join("; ")}`);
  if (s.note) onSlide.push(`Ghi chú: ${s.note}`);
  if (s.fig) onSlide.push(`Hình: ${path.basename(s.fig)}${s.fig2 ? " + " + path.basename(s.fig2) : ""}`);
  if (onSlide.length) {
    children.push(
      new Paragraph({
        shading: { fill: "F3F4F6", type: ShadingType.CLEAR, color: "auto" },
        spacing: { after: 40 },
        children: [run("Trên slide:", { size: 20, bold: true, color: GREY })],
      }),
      ...onSlide.map(
        (t) =>
          new Paragraph({
            shading: { fill: "F3F4F6", type: ShadingType.CLEAR, color: "auto" },
            spacing: { after: 20 },
            indent: { left: 240 },
            children: [run("– " + t, { size: 20, color: GREY })],
          }),
      ),
      new Paragraph({ spacing: { after: 120 }, children: [] }),
    );
  }
  s.script.forEach((t) =>
    children.push(new Paragraph({ spacing: { after: 200, line: 400 }, alignment: AlignmentType.JUSTIFIED, children: [run(t, { size: 28 })] })),
  );
  if (n < SLIDES.length)
    children.push(new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 320 }, children: [run("▶ CHUYỂN SLIDE", { size: 20, bold: true, color: ACCENT })] }));
});

// ── Hỏi đáp
children.push(
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run("HỎI – ĐÁP: CÂU HỎI HỘI ĐỒNG CÓ THỂ HỎI")] }),
  para("Mỗi câu trả lời đi theo cùng mạch của bài: nêu vấn đề, lý do chọn, và thừa nhận cái giá. Không cần đọc nguyên văn, chỉ cần nắm ý chính.", { run: { size: 26, italics: true } }),
);
QA.forEach((item, i) => {
  children.push(
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(`Câu ${i + 1}. ${item.q}`)] }),
    new Paragraph({ spacing: { after: 240, line: 380 }, alignment: AlignmentType.JUSTIFIED, children: [run("Trả lời: ", { size: 26, bold: true }), run(item.a, { size: 26 })] }),
  );
});

const doc = new Document({
  creator: "Nhóm 3",
  title: "Kịch bản thuyết trình – Đề tài 4",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 26 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: ACCENT }, paragraph: { spacing: { before: 240, after: 200 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }],
  },
  sections: [
    {
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      footers: {
        default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Trang ", { size: 20, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20, color: GREY })] })] }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Wrote", OUT, buf.length, "bytes");
});
