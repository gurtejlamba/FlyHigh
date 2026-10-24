"""Generate the SIFT hackathon presentation."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Colour palette ──────────────────────────────────────────────────────────
NAVY   = RGBColor(0x0D, 0x1B, 0x2A)   # dark background
BLUE   = RGBColor(0x1B, 0x6C, 0xA8)   # accent
CYAN   = RGBColor(0x00, 0xC2, 0xD4)   # highlight
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY  = RGBColor(0xE8, 0xEC, 0xF0)
DGRAY  = RGBColor(0x55, 0x65, 0x75)

W = Inches(13.33)   # widescreen 16:9
H = Inches(7.5)


def prs() -> Presentation:
    p = Presentation()
    p.slide_width  = W
    p.slide_height = H
    return p


def blank_slide(p: Presentation):
    layout = p.slide_layouts[6]   # completely blank
    return p.slides.add_slide(layout)


def bg(slide, color: RGBColor = NAVY):
    from pptx.util import Emu
    sp = slide.shapes.add_shape(1, 0, 0, W, H)  # MSO_SHAPE_TYPE.RECTANGLE = 1
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    return sp


def txt(slide, text: str, x, y, w, h,
        size=24, bold=False, color=WHITE, align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return tb


def accent_bar(slide, y=Inches(1.15), color=CYAN):
    sp = slide.shapes.add_shape(1, Inches(0.6), y, Inches(1.0), Inches(0.07))
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()


def bullet_box(slide, items, x, y, w, h, size=20, color=WHITE, spacing=1.2):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(spacing * 4)
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.color.rgb = color


def colored_box(slide, text, x, y, w, h, bg_color=BLUE, fg_color=WHITE,
                size=18, bold=False, align=PP_ALIGN.CENTER):
    sp = slide.shapes.add_shape(1, x, y, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = bg_color
    sp.line.fill.background()
    tf = sp.text_frame
    tf.word_wrap = True
    from pptx.util import Pt as _Pt
    from pptx.enum.text import PP_ALIGN as _A
    from pptx.dml.color import RGBColor as _C
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = _Pt(size)
    run.font.bold = bold
    run.font.color.rgb = fg_color
    return sp


# ── Slides ───────────────────────────────────────────────────────────────────

def slide_title(p):
    s = blank_slide(p)
    bg(s, NAVY)
    # decorative top stripe
    sp = s.shapes.add_shape(1, 0, 0, W, Inches(0.18))
    sp.fill.solid(); sp.fill.fore_color.rgb = CYAN; sp.line.fill.background()

    txt(s, "SIFT", Inches(0.7), Inches(1.4), Inches(12), Inches(1.6),
        size=80, bold=True, color=CYAN, align=PP_ALIGN.LEFT)
    txt(s, "Data-Analyst Agent on Messy Databases",
        Inches(0.7), Inches(2.9), Inches(10), Inches(0.8),
        size=30, bold=False, color=WHITE)
    txt(s, "Hackathon  ·  Track AI-02  ·  Building Intelligent, Trustworthy & Sustainable Systems",
        Inches(0.7), Inches(3.7), Inches(11), Inches(0.6),
        size=16, color=DGRAY, italic=True)
    # bottom bar
    sp2 = s.shapes.add_shape(1, 0, Inches(6.9), W, Inches(0.6))
    sp2.fill.solid(); sp2.fill.fore_color.rgb = BLUE; sp2.line.fill.background()
    txt(s, "Open-weight model  ·  BIRD benchmark  ·  Self-verifying  ·  Abstains when unsure",
        Inches(0.5), Inches(6.95), Inches(12), Inches(0.5),
        size=14, color=WHITE, align=PP_ALIGN.CENTER)


def slide_problem(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "The Problem", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)

    txt(s, "Business users ask questions in plain English.",
        Inches(0.6), Inches(1.3), Inches(11.5), Inches(0.6),
        size=22, color=CYAN, bold=True)

    examples = [
        '❓  "Which schools had falling enrolment last year?"',
        '❓  "What is the average SAT score in low-income districts?"',
        '❓  "Which card games have the highest win rate for blue decks?"',
    ]
    bullet_box(s, examples, Inches(0.6), Inches(2.0), Inches(11.5), Inches(1.8),
               size=20, color=LGRAY)

    txt(s, "Real databases make this hard:", Inches(0.6), Inches(3.5), Inches(6), Inches(0.5),
        size=20, color=WHITE, bold=True)

    pain_points = [
        '🗂  Cryptic column names — no docs',
        '🧹  Dirty values — "N/A", empty strings, mixed date formats',
        '🔗  Business rules that live outside the schema',
        '⚠️   A plausible wrong answer is worse than no answer',
    ]
    bullet_box(s, pain_points, Inches(0.6), Inches(4.0), Inches(11.5), Inches(2.5),
               size=19, color=LGRAY)


def slide_approach(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "Our Approach", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)
    txt(s, "A four-stage agent loop — no heavy framework, fully config-driven",
        Inches(0.6), Inches(1.05), Inches(11), Inches(0.5),
        size=18, color=DGRAY, italic=True)

    stages = [
        ("1  EXPLORE", "Reads schema\nSamples values\nFlags NULLs & dirty data"),
        ("2  GENERATE", "Builds prompt\n(schema + hints + question)\nCalls local LLM → SQL"),
        ("3  VERIFY", "Executes SQL read-only\nChecks errors, empty results\nhigh NULL ratio"),
        ("4  ABSTAIN", "Says 'cannot answer'\nwhen no valid query\ncan be written"),
    ]
    colors = [BLUE, RGBColor(0x1A,0x7A,0x5E), RGBColor(0x7A,0x3A,0x1A), RGBColor(0x5A,0x1A,0x7A)]
    for i, (title, body) in enumerate(stages):
        x = Inches(0.35 + i * 3.17)
        colored_box(s, title, x, Inches(1.75), Inches(2.95), Inches(0.55),
                    bg_color=colors[i], fg_color=WHITE, size=17, bold=True)
        colored_box(s, body,  x, Inches(2.35), Inches(2.95), Inches(1.9),
                    bg_color=RGBColor(0x16,0x24,0x35), fg_color=LGRAY, size=16,
                    align=PP_ALIGN.LEFT)

    # arrow connectors (simple text arrows)
    for i in range(3):
        x = Inches(3.25 + i * 3.17)
        txt(s, "→", x, Inches(2.4), Inches(0.3), Inches(0.5),
            size=28, color=CYAN, align=PP_ALIGN.CENTER)

    txt(s, "Self-repair loop", Inches(0.6), Inches(4.5), Inches(4), Inches(0.45),
        size=18, bold=True, color=CYAN)
    txt(s, "If VERIFY fails → error feedback is passed back to GENERATE for a repair attempt.\n"
           "Capped at max_retries (default 3). Still failing → ABSTAIN.",
        Inches(0.6), Inches(4.95), Inches(11.8), Inches(1.1),
        size=17, color=LGRAY)

    txt(s, "Every stage logs: inputs · outputs · latency · token count",
        Inches(0.6), Inches(6.2), Inches(11), Inches(0.5),
        size=15, color=DGRAY, italic=True)


def slide_dirty_data(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "Handling Messy Data", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)

    rows = [
        ("Problem",              "SIFT's response",                    True),
        ('"N/A" & empty strings',"EXPLORE surfaces them; prompt filters with\nWHERE col NOT IN (\'N/A\',\'\') AND col IS NOT NULL", False),
        ("Mixed date formats",   "Prompt enforces STRFTIME / string slicing,\nnever date arithmetic",                              False),
        ("NULL-heavy columns",   "EXPLORE flags [has NULLs]; VERIFY checks\nnull_ratio > 0.7 → retry",                            False),
        ("Wrong table/column",   "VERIFY catches empty result or error;\nGENERATE gets exact error in repair prompt",              False),
        ("Cryptic column names", "6 sample values per column give\nsemantic context in the prompt",                               False),
        ("Unanswerable question","ABSTAIN → 'cannot answer'\ninstead of a confident wrong answer",                                False),
    ]

    y = Inches(1.2)
    rh = Inches(0.72)
    for i, (prob, resp, header) in enumerate(rows):
        bg_c = BLUE if header else (RGBColor(0x12,0x20,0x30) if i % 2 == 0 else RGBColor(0x16,0x28,0x3C))
        colored_box(s, prob, Inches(0.35), y, Inches(4.3), rh,
                    bg_color=bg_c, fg_color=WHITE if not header else CYAN,
                    size=15 if not header else 14, bold=header, align=PP_ALIGN.LEFT)
        colored_box(s, resp, Inches(4.75), y, Inches(8.2), rh,
                    bg_color=bg_c, fg_color=LGRAY if not header else CYAN,
                    size=14 if not header else 14, bold=header, align=PP_ALIGN.LEFT)
        y += rh + Inches(0.04)


def slide_model(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "Model & Tech Stack", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)

    items = [
        ("🧠  Model", "Qwen2.5-Coder-7B-Instruct\n7.6 B parameters · Apache 2.0\nBest SQL generation under 8 B cap"),
        ("⚙️  Inference", "Ollama (default) or vLLM\nOpenAI-compatible REST API\nSeed=42, temp=0 for determinism"),
        ("🗄  Benchmark", "BIRD dev split\n1,534 questions · 11 SQLite databases\nEX (Execution Accuracy) metric"),
        ("🐍  Runtime", "Python 3.10+\nOnly: requests · pyyaml · tqdm\nNo ML framework required"),
    ]

    for i, (title, body) in enumerate(items):
        col = i % 2
        row = i // 2
        x = Inches(0.5 + col * 6.4)
        y = Inches(1.5 + row * 2.5)
        colored_box(s, title, x, y, Inches(5.9), Inches(0.55),
                    bg_color=BLUE, fg_color=WHITE, size=18, bold=True)
        colored_box(s, body,  x, y + Inches(0.56), Inches(5.9), Inches(1.7),
                    bg_color=RGBColor(0x12,0x22,0x34), fg_color=LGRAY, size=17,
                    align=PP_ALIGN.LEFT)


def slide_eval(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "Evaluation Plan", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)

    txt(s, "Primary: Execution Accuracy (EX) on BIRD dev split",
        Inches(0.6), Inches(1.1), Inches(11), Inches(0.5),
        size=21, color=CYAN, bold=True)

    txt(s, "EX  =  queries where predicted SQL returns the same result set as gold SQL  /  total",
        Inches(0.6), Inches(1.65), Inches(11.5), Inches(0.5),
        size=17, color=LGRAY, italic=True)

    colored_box(s, "Component ablation — record EX before and after each addition",
                Inches(0.5), Inches(2.3), Inches(12.3), Inches(0.5),
                bg_color=BLUE, fg_color=WHITE, size=16, bold=True, align=PP_ALIGN.LEFT)

    headers = ["Component", "EX (dev)"]
    rows_data = [
        ["Baseline (no verify, no repair)", "—"],
        ["+ verify (error detection)",      "—"],
        ["+ repair loop (max 3 retries)",   "—"],
        ["+ dirty-data prompt rules",       "—"],
        ["+ abstention",                    "—"],
    ]
    y = Inches(2.95)
    rh = Inches(0.52)
    for i, row in enumerate([headers] + rows_data):
        is_h = i == 0
        bg_c = BLUE if is_h else (RGBColor(0x12,0x20,0x30) if i%2==1 else RGBColor(0x16,0x28,0x3C))
        colored_box(s, row[0], Inches(0.5),  y, Inches(7.8), rh, bg_color=bg_c,
                    fg_color=WHITE if is_h else LGRAY, size=15, bold=is_h, align=PP_ALIGN.LEFT)
        colored_box(s, row[1], Inches(8.4),  y, Inches(4.4), rh, bg_color=bg_c,
                    fg_color=CYAN  if is_h else LGRAY, size=15, bold=is_h, align=PP_ALIGN.CENTER)
        y += rh + Inches(0.03)

    txt(s, "Also tracking: abstain recall on our 50-question unanswerable set  ·  failure breakdown by cause",
        Inches(0.5), Inches(6.7), Inches(12), Inches(0.5),
        size=14, color=DGRAY, italic=True)


def slide_demo(p):
    s = blank_slide(p)
    bg(s, NAVY)
    accent_bar(s)
    txt(s, "Demo Scenarios", Inches(0.6), Inches(0.3), Inches(10), Inches(0.7),
        size=36, bold=True, color=WHITE)

    s1 = "Question: Which districts spent the most on free meals?\n" \
         "Attempt 1 -> wrong column -> VERIFY flags 0 rows\n" \
         "Attempt 2 -> correct JOIN -> VERIFY passes -> answer returned"
    s2 = "Question: What is the average teacher salary?\n" \
         "Schema has no salary column -> SQL error after all retries\n" \
         "ABSTAIN -> 'cannot answer'  (not a confident wrong number)"
    s3 = "Question: Which schools had falling enrolment last year?\n" \
         "county column contains N/A strings and NULLs\n" \
         "Agent filters dirty values -> correct result"
    scenarios = [
        ("1  Self-repair",    s1),
        ("2  Correct refusal", s2),
        ("3  Dirty data",      s3),
    ]
    colors_s = [BLUE, RGBColor(0x7A,0x3A,0x1A), RGBColor(0x1A,0x7A,0x5E)]
    y = Inches(1.25)
    for i, (title, body) in enumerate(scenarios):
        colored_box(s, title, Inches(0.5), y, Inches(12.3), Inches(0.48),
                    bg_color=colors_s[i], fg_color=WHITE, size=17, bold=True, align=PP_ALIGN.LEFT)
        colored_box(s, body, Inches(0.5), y+Inches(0.49), Inches(12.3), Inches(1.18),
                    bg_color=RGBColor(0x12,0x22,0x34), fg_color=LGRAY, size=16, align=PP_ALIGN.LEFT)
        y += Inches(1.85)


def slide_summary(p):
    s = blank_slide(p)
    bg(s, NAVY)
    sp = s.shapes.add_shape(1, 0, 0, W, Inches(0.18))
    sp.fill.solid(); sp.fill.fore_color.rgb = CYAN; sp.line.fill.background()

    txt(s, "SIFT", Inches(0.7), Inches(0.8), Inches(5), Inches(1.2),
        size=64, bold=True, color=CYAN)
    txt(s, "Text-to-SQL · Self-verifying · Honest",
        Inches(0.7), Inches(2.0), Inches(9), Inches(0.6),
        size=24, color=WHITE)

    points = [
        "✅  Explore → Generate → Verify → Repair → Abstain",
        "✅  Handles NULL, dirty values, cryptic columns",
        "✅  Open-weight model ≤ 8 B (Qwen2.5-Coder-7B)",
        "✅  Scored on BIRD with a re-runnable script",
        "✅  Config-driven — Phase 2 is a config change",
    ]
    bullet_box(s, points, Inches(0.7), Inches(2.8), Inches(11.5), Inches(3.0),
               size=20, color=LGRAY)

    sp2 = s.shapes.add_shape(1, 0, Inches(6.9), W, Inches(0.6))
    sp2.fill.solid(); sp2.fill.fore_color.rgb = BLUE; sp2.line.fill.background()
    txt(s, "A plausible wrong answer is worse than none — so SIFT says so.",
        Inches(0.5), Inches(6.95), Inches(12), Inches(0.5),
        size=15, color=WHITE, align=PP_ALIGN.CENTER, italic=True)


# ── Build & save ─────────────────────────────────────────────────────────────

def build(output: str = "docs/SIFT_presentation.pptx"):
    p = prs()
    slide_title(p)
    slide_problem(p)
    slide_approach(p)
    slide_dirty_data(p)
    slide_model(p)
    slide_eval(p)
    slide_demo(p)
    slide_summary(p)
    p.save(output)
    print(f"Saved: {output}  ({len(p.slides)} slides)")


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    build()
