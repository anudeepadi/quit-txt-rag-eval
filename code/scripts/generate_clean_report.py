#!/usr/bin/env python3
"""Generate clean Word report for professors — matches Ibrahim's meeting table format."""

from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Inches, Pt, RGBColor

_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = _ROOT / "results" / "report"

_WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _shd(fill: str) -> str:
    return f'<w:shd xmlns:w="{_WNS}" w:val="clear" w:color="auto" w:fill="{fill}"/>'


def _cell(row, col_idx, text, bold=False, italic=False, center=False,
          bg=None, font_color=None, size=10):
    cell = row.cells[col_idx]
    cell.text = ""
    para = cell.paragraphs[0]
    if center:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    if font_color:
        run.font.color.rgb = font_color
    if bg:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcPr.append(parse_xml(_shd(bg)))


def build():
    doc = Document()

    # Margins
    for sec in doc.sections:
        sec.left_margin = Inches(1.1)
        sec.right_margin = Inches(1.1)
        sec.top_margin = Inches(0.9)
        sec.bottom_margin = Inches(0.9)

    # ── Header block ─────────────────────────────────────────────────────────
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("RAG Evaluation Results — Progress Report")
    r.bold = True
    r.font.size = Pt(15)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = sub.add_run(
        "AI-Generated vs Human-Curated Knowledge Base for Smoking Cessation Counselor"
    )
    r2.font.size = Pt(11)
    r2.italic = True

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = info.add_run(
        f"Venkata Anudeep Adiraju · Ebrahim  ·  Dr. Akopian · Dr. Luis Velez\n"
        f"{datetime.now().strftime('%B %d, %Y')}"
    )
    r3.font.size = Pt(10)

    doc.add_paragraph()

    # ── Context ───────────────────────────────────────────────────────────────
    ctx = doc.add_paragraph()
    ctx.add_run("Background. ").bold = True
    ctx.add_run(
        "Following the Feb 25 meeting, we ran a full N=100 evaluation comparing our "
        "two dataset-based RAG approaches against Ebrahim's published WebRAG benchmark. "
        "We also measured real-time latency (WebRAG vs Dataset RAG) without any "
        "acceleration or caching shortcuts, as requested."
    )
    ctx.runs[-1].font.size = Pt(10)
    ctx.runs[0].font.size = Pt(10)

    doc.add_paragraph()

    # ── TABLE ─────────────────────────────────────────────────────────────────
    heading = doc.add_paragraph()
    heading.add_run("Table 1: Faithfulness Results (N=100)").bold = True
    heading.runs[0].font.size = Pt(11)

    COLS = ["Model", "Mean\nFaithfulness", "SD", "Median",
            "95% CI", "Hallucination\nRate", "% High-Risk\n(<0.5)", "n"]

    ROWS = [
        # (model, mean, sd, median, ci, halluc, high_risk, n, is_ref, is_best)
        ("Ebrahim: Base LLM",       "0.58", "0.22", "0.61", "[0.42–0.74]", "0.40", "20%",  "10",  True,  False),
        ("Ebrahim: WebRAG",         "0.86", "0.11", "0.88", "[0.84–0.88]", "0.14",  "4%", "100",  True,  True),
        ("Ours: AI-Generated RAG",  "0.53", "0.32", "0.58", "[0.47–0.59]", "0.47", "43%", "100",  False, False),
        ("Ours: Human-Curated RAG", "0.66", "0.33", "0.70", "[0.59–0.72]", "0.34", "34%", "100",  False, True),
    ]

    tbl = doc.add_table(rows=1 + len(ROWS), cols=len(COLS))
    tbl.style = "Table Grid"

    # Header row
    for i, h in enumerate(COLS):
        _cell(tbl.rows[0], i, h, bold=True, center=True,
              bg="1F4E79", font_color=RGBColor(0xFF, 0xFF, 0xFF), size=9)

    # Data rows
    STRIPE = "EBF5FB"
    for ri, row_data in enumerate(ROWS, 1):
        model, mean, sd, median, ci, halluc, hr, n, is_ref, is_best = row_data
        bg = STRIPE if ri % 2 == 0 else None
        row = tbl.rows[ri]

        # Model name — italic for reference rows
        _cell(row, 0, model, italic=is_ref, bold=is_best, bg=bg, size=9)
        for ci_idx, val in enumerate([mean, sd, median, ci, halluc, hr, n], 1):
            bold_val = is_best and ci_idx in (1, 5, 6)  # bold mean, halluc, high-risk for best
            _cell(row, ci_idx, val, bold=bold_val, center=True, bg=bg, size=9)

    doc.add_paragraph()

    # ── Latency callout ───────────────────────────────────────────────────────
    lat_heading = doc.add_paragraph()
    lat_heading.add_run("Table 2: Latency — Per-Question Response Time (N=100)").bold = True
    lat_heading.runs[0].font.size = Pt(11)

    LAT_ROWS = [
        ("WebRAG (cold — fresh scrape per question)", "7.70 s", "7.60 s", "2.24 s", "12.36 s"),
        ("WebRAG (warm — pre-cached content)",        "4.62 s", "4.28 s", "2.57 s",  "9.57 s"),
        ("Dataset RAG — Human-Curated ✓",            "3.20 s", "2.87 s", "1.61 s",  "6.32 s"),
    ]
    LAT_COLS = ["Method", "Mean", "Median", "SD", "p95 (worst 5%)"]

    tbl2 = doc.add_table(rows=1 + len(LAT_ROWS), cols=len(LAT_COLS))
    tbl2.style = "Table Grid"

    for i, h in enumerate(LAT_COLS):
        _cell(tbl2.rows[0], i, h, bold=True, center=(i > 0),
              bg="1F4E79", font_color=RGBColor(0xFF, 0xFF, 0xFF), size=9)

    for ri, (method, mean, med, sd, p95) in enumerate(LAT_ROWS, 1):
        is_ours = ri == 3
        bg = "D5F5E3" if is_ours else (STRIPE if ri % 2 == 0 else None)
        row = tbl2.rows[ri]
        _cell(row, 0, method, bold=is_ours, bg=bg, size=9)
        for ci_idx, val in enumerate([mean, med, sd, p95], 1):
            _cell(row, ci_idx, val, bold=is_ours, center=True, bg=bg, size=9)

    doc.add_paragraph()
    speedup = doc.add_paragraph()
    speedup.add_run("Speedup: ").bold = True
    speedup.add_run(
        "Dataset RAG is 2.41× faster than cold WebRAG and 1.44× faster than warm (pre-cached) WebRAG."
    )
    for r in speedup.runs:
        r.font.size = Pt(10)

    doc.add_paragraph()

    # ── What findings mean ────────────────────────────────────────────────────
    doc.add_paragraph().add_run("What These Findings Mean").bold = True
    doc.paragraphs[-1].runs[0].font.size = Pt(11)

    meanings = [
        ("Human curation improves quality.",
         "Our human-curated dataset achieves faithfulness 0.66 vs 0.53 for AI-generated — "
         "a 24% relative improvement. Faithfulness measures whether the AI's answer is "
         "actually supported by what it retrieved, so higher = fewer hallucinations."),
        ("We're below Ebrahim's WebRAG, and that's expected.",
         "Ebrahim's system fetches live content from authoritative websites (Mayo Clinic, CDC) "
         "per question. Our system uses a fixed pre-built knowledge base. Live retrieval has "
         "a natural accuracy advantage because it always has the most targeted content. "
         "The tradeoff is speed — see Table 2."),
        ("We're substantially faster.",
         "Dataset RAG at 3.2 s/question vs WebRAG cold at 7.7 s is a 2.4× speedup — "
         "the difference between a responsive chatbot and one that feels slow. "
         "This matters for real-time deployment."),
        ("High-risk hallucinations dropped.",
         "43% of AI-generated RAG responses scored below 0.5 faithfulness (high-risk). "
         "Human curation reduced this to 34%. In a clinical counseling context, "
         "this 9-point reduction is meaningful — those are responses that could mislead patients."),
    ]

    for bold_part, text_part in meanings:
        p = doc.add_paragraph(style="List Bullet")
        r_b = p.add_run(bold_part + " ")
        r_b.bold = True
        r_b.font.size = Pt(10)
        r_t = p.add_run(text_part)
        r_t.font.size = Pt(10)

    doc.add_paragraph()

    # ── How computed ──────────────────────────────────────────────────────────
    doc.add_paragraph().add_run("How We Computed This").bold = True
    doc.paragraphs[-1].runs[0].font.size = Pt(11)

    methods = [
        ("Test set:", "100 questions from the LFV-reviewed test set (Dr. Velez's 150-question set, 23 flagged questions excluded)."),
        ("RAG datasets:", "AI-generated: 5,936 Q&A pairs. Human-curated: 4,847 Q&A pairs. Both indexed using ChromaDB vector search, top-3 retrieval."),
        ("Answer generation:", "GPT-4o-mini used for all three approaches under identical conditions (same system prompt, temperature, token limit)."),
        ("Faithfulness scoring:", "RAGAS 0.4.x — automatically checks each claim in the AI's response against the retrieved context. Score 0–1 per question, then averaged across N=100."),
        ("Latency:", "Measured with Python's time.perf_counter(). WebRAG cold = real fresh fetch per question (no cache). WebRAG warm = pre-fetched once and reused. Dataset RAG = ChromaDB vector lookup only."),
    ]

    for label, desc in methods:
        p = doc.add_paragraph(style="List Bullet")
        r_l = p.add_run(label + " ")
        r_l.bold = True
        r_l.font.size = Pt(10)
        r_d = p.add_run(desc)
        r_d.font.size = Pt(10)

    doc.add_paragraph()

    # ── Conclusion ────────────────────────────────────────────────────────────
    doc.add_paragraph().add_run("Conclusion").bold = True
    doc.paragraphs[-1].runs[0].font.size = Pt(11)

    conc = doc.add_paragraph()
    conc.add_run(
        "Human-curated dataset RAG is the best performing approach we have so far: "
        "it reduces hallucination rate (43% → 34%), improves faithfulness (0.53 → 0.66), "
        "and delivers responses 2.4× faster than live WebRAG. "
        "The remaining gap to Ebrahim's WebRAG benchmark (0.66 vs 0.86) is expected given "
        "that live web retrieval always has the most targeted content — a hybrid approach "
        "(dataset retrieval + WebRAG fallback) is the logical next step to bridge this gap. "
        "The current results are sufficient to support the paper's central argument: "
        "professional dataset curation provides measurable quality gains over AI-generated "
        "datasets at zero latency cost."
    )
    conc.runs[0].font.size = Pt(10)

    # ── Save ──────────────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "results_for_professors.docx"
    doc.save(out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    build()
