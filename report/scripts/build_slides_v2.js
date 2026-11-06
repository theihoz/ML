// Slide thuyết trình bản dễ hiểu cho người không làm kỹ thuật: mỗi slide một ý, chữ lớn, ít số.
// Lời nói đầy đủ nằm trong Speaker Notes (giống kịch bản .docx).
// Chạy: NODE_PATH=<node_modules có pptxgenjs> node report/scripts/build_slides_v2.js <repo> <out.pptx>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { SLIDES } = require("./thuyet_trinh_content");

const [ROOT, OUT] = process.argv.slice(2);
const REPORT = path.join(ROOT, "report");

const INK = "0F172A";
const MUTED = "64748B";
const ACCENT = "1D4ED8";
const SOFT = "EFF6FF";
const WARM = "FFF7ED";
const WARM_INK = "C2410C";
const HEAD = "Arial";
const BODY = "Calibri";
const W = 13.333;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Lương ngành IT ở Việt Nam";
pres.author = "Nhóm 3";
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FFFFFF" },
  slideNumber: { x: 12.3, y: 7.0, w: 0.8, h: 0.3, color: MUTED, fontSize: 11, align: "right", fontFace: BODY },
  objects: [{ rect: { x: 0, y: 0, w: W, h: 0.12, fill: { color: ACCENT } } }],
});

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function placeImage(slide, rel, bx, by, bw, bh) {
  const file = path.join(REPORT, rel);
  const { w, h } = pngSize(file);
  const scale = Math.min(bw / w, bh / h);
  const iw = w * scale;
  const ih = h * scale;
  slide.addShape(pres.shapes.RECTANGLE, { x: bx - 0.08, y: by - 0.08, w: bw + 0.16, h: bh + 0.16, fill: { color: SOFT }, line: { color: SOFT } });
  slide.addImage({ path: file, x: bx + (bw - iw) / 2, y: by + (bh - ih) / 2, w: iw, h: ih });
}
const notes = (s) => s.script.join("\n\n");

function title(slide, s) {
  slide.addText(s.section.toUpperCase(), { x: 0.6, y: 0.3, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, color: ACCENT, bold: true, charSpacing: 2 });
  slide.addText(s.title, { x: 0.6, y: 0.6, w: 12.1, h: 1.1, fontFace: HEAD, fontSize: 30, bold: true, color: INK, valign: "middle", fit: "shrink" });
}
function points(slide, list, box, fontSize) {
  slide.addText(
    list.map((t) => ({ text: t, options: { breakLine: true, bullet: t.startsWith("→") ? false : { code: "25CF", indent: 22 }, paraSpaceAfter: 18, color: t.startsWith("→") ? ACCENT : INK, bold: t.startsWith("→") } })),
    { ...box, fontFace: BODY, fontSize, valign: "middle", fit: "shrink", margin: 4 },
  );
}
function note(slide, text) {
  slide.addText(text, { x: 0.6, y: 6.55, w: 11.5, h: 0.45, fontFace: BODY, fontSize: 15, italic: true, color: MUTED, valign: "middle", fit: "shrink" });
}

const ONLY = process.env.ONLY ? Number(process.env.ONLY) : null;
SLIDES.forEach((s, idx) => {
  if (ONLY !== null && idx + 1 !== ONLY) return;
  const layout = s.layout || "points";
  if (layout === "cover") {
    const slide = pres.addSlide();
    slide.background = { color: INK };
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.9, w: 0.12, h: 2.6, fill: { color: "60A5FA" } });
    slide.addText(s.title, { x: 0.95, y: 1.7, w: 11.6, h: 3.0, fontFace: HEAD, fontSize: 40, bold: true, color: "FFFFFF", valign: "middle", fit: "shrink" });
    slide.addText(s.subtitle, { x: 0.95, y: 4.9, w: 11.6, h: 1.4, fontFace: BODY, fontSize: 20, color: "CBD5E1", valign: "top" });
    slide.addNotes(notes(s));
    return;
  }
  if (layout === "section") {
    const slide = pres.addSlide();
    slide.background = { color: ACCENT };
    const [a, b] = s.title.split("\n");
    if (b) slide.addText(a, { x: 0.9, y: 2.2, w: 11.5, h: 0.7, fontFace: BODY, fontSize: 24, color: "BFDBFE", bold: true });
    slide.addText(b || a, { x: 0.9, y: 2.9, w: 11.5, h: 2.0, fontFace: HEAD, fontSize: 42, bold: true, color: "FFFFFF", valign: "top", fit: "shrink" });
    slide.addNotes(notes(s));
    return;
  }

  const slide = pres.addSlide({ masterName: "CONTENT" });
  title(slide, s);
  const top = 1.9;
  const bottom = s.note ? 6.4 : 6.85;
  const hasFig = !!s.fig;
  const leftW = hasFig ? 5.4 : 12.1;

  if (layout === "big") {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: top, w: leftW, h: bottom - top, fill: { color: SOFT }, line: { color: SOFT }, rectRadius: 0.15 });
    slide.addText(s.big.value, { x: 0.8, y: top + 0.3, w: leftW - 0.4, h: (bottom - top) * 0.5, fontFace: HEAD, fontSize: hasFig ? 66 : 96, bold: true, color: ACCENT, align: "center", valign: "middle", fit: "shrink" });
    slide.addText(s.big.caption, { x: 0.9, y: top + (bottom - top) * 0.55, w: leftW - 0.6, h: (bottom - top) * 0.4, fontFace: BODY, fontSize: hasFig ? 20 : 26, color: INK, align: "center", valign: "top", fit: "shrink" });
  } else if (layout === "compare") {
    const gap = 0.5;
    const cw = (12.1 - gap) / 2;
    [[s.compare.left, WARM, WARM_INK], [s.compare.right, SOFT, ACCENT]].forEach(([card, fill, ink], i) => {
      const x = 0.6 + i * (cw + gap);
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: top, w: cw, h: bottom - top, fill: { color: fill }, line: { color: fill }, rectRadius: 0.15 });
      slide.addText(card.head, { x: x + 0.3, y: top + 0.25, w: cw - 0.6, h: 0.7, fontFace: HEAD, fontSize: 26, bold: true, color: ink });
      slide.addText(
        card.lines.map((t) => ({ text: t, options: { breakLine: true, paraSpaceAfter: 16, bold: t.startsWith("→"), color: t.startsWith("→") ? ink : INK } })),
        { x: x + 0.3, y: top + 1.05, w: cw - 0.6, h: bottom - top - 1.3, fontFace: BODY, fontSize: 24, valign: "top", fit: "shrink" },
      );
    });
  } else if (s.points) {
    points(slide, s.points, { x: 0.6, y: top, w: leftW, h: bottom - top }, hasFig ? 22 : 30);
  }
  if (hasFig) placeImage(slide, s.fig, 0.6 + leftW + 0.4, top, W - (0.6 + leftW + 0.4) - 0.6, bottom - top);
  if (s.note) note(slide, s.note);
  slide.addNotes(notes(s));
});

pres.writeFile({ fileName: OUT }).then((f) => console.log("Wrote", f));
