#!/usr/bin/env python3
"""Generate a Word document of the Quitxt implementation paper.

Produces a properly formatted .docx with:
- IEEE-style title, authors, abstract
- Numbered sections and subsections
- Tables with borders
- Figure placeholders with captions
- References section
- Code blocks where needed

Output: paper/Quitxt_Implementation_Paper.docx
"""

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


def set_cell_shading(cell, color: str) -> None:
    """Set background shading on a table cell."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table) -> None:
    """Apply thin borders to all cells in a table."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def add_heading_numbered(doc: Document, text: str, level: int) -> None:
    """Add a heading paragraph."""
    doc.add_heading(text, level=level)


def add_table_from_data(
    doc: Document, headers: list[str], rows: list[list[str]], caption: str = ""
) -> None:
    """Add a formatted table with optional caption."""
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.bold = True
        run.font.size = Pt(9)

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(9)
        set_cell_shading(cell, "D9E2F3")

    # Data rows
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = val
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(9)


def add_code_block(doc: Document, code: str) -> None:
    """Add a monospaced code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    run = p.add_run(code)
    run.font.name = "Courier New"
    run.font.size = Pt(8)


def add_figure_placeholder(doc: Document, caption: str, fig_path: str = "") -> None:
    """Add a figure placeholder or embed if the image exists."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    fig_dir = Path(__file__).parent / "figures"
    if fig_path and (fig_dir / fig_path).exists():
        run = p.add_run()
        run.add_picture(str(fig_dir / fig_path), width=Inches(5.5))
    else:
        run = p.add_run(f"[Figure: {fig_path or 'placeholder'}]")
        run.font.color.rgb = RGBColor(128, 128, 128)
        run.font.size = Pt(10)
        run.italic = True

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(caption)
    run.font.size = Pt(9)
    run.italic = True


def build_document() -> Document:
    doc = Document()

    # -- Page setup --
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # -- Default font --
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.15

    # =========================================================================
    # TITLE
    # =========================================================================
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(
        "Performance Benchmarking of a Cross-Platform\n"
        "Messaging System for mHealth Smoking Cessation"
    )
    run.bold = True
    run.font.size = Pt(16)

    # AUTHORS
    authors_p = doc.add_paragraph()
    authors_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = authors_p.add_run(
        "Venkata Anudeep Adiraju*, David Akopian*, "
        "Ebrahim Melladoust*, Patricia Chalela\u2020, and Vivian Cortez\u2020"
    )
    run.font.size = Pt(10)

    affil1 = doc.add_paragraph()
    affil1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil1.add_run(
        "*Department of Electrical and Computer Engineering,\n"
        "The University of Texas at San Antonio, San Antonio, TX 78249, USA\n"
        "Email: venkataanudeep.adiraju@my.utsa.edu; david.akopian@utsa.edu"
    )
    run.font.size = Pt(9)
    run.italic = True

    affil2 = doc.add_paragraph()
    affil2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil2.add_run(
        "\u2020Institute for Health Promotion Research,\n"
        "The University of Texas Health Science Center at San Antonio, "
        "San Antonio, TX 78229, USA"
    )
    run.font.size = Pt(9)
    run.italic = True

    # =========================================================================
    # ABSTRACT
    # =========================================================================
    doc.add_heading("Abstract", level=1)
    doc.add_paragraph(
        "Mobile health (mHealth) messaging applications require low-latency, "
        "reliable delivery, yet the architecture and client-side performance of "
        "production messaging systems remain poorly characterized. This paper "
        "presents the design, implementation, and performance evaluation of "
        "Quitxt, a cross-platform Flutter application for smoking cessation that "
        "combines real-time messaging with AI-enhanced responses. We describe the "
        "system architecture\u2014including the rationale for selecting Flutter over "
        "React Native, a composition-based messaging service, and binary search "
        "message insertion\u2014and benchmark key operations to confirm they remain "
        "well within a single frame budget. On the server side, we integrate a "
        "retrieval-augmented generation (RAG) layer that retrieves from a "
        "professionally curated smoking cessation knowledge base via ChromaDB and "
        "generates grounded responses through Gemini 2.0 Flash. The measurement "
        "framework and analysis scripts are open-source."
    )

    kw = doc.add_paragraph()
    run = kw.add_run("Index Terms\u2014")
    run.bold = True
    run.font.size = Pt(9)
    run = kw.add_run(
        "Cross-platform mobile development, Flutter, mHealth messaging, "
        "smoking cessation, performance benchmarking, binary search insertion, "
        "retrieval-augmented generation"
    )
    run.font.size = Pt(9)
    run.italic = True

    # =========================================================================
    # I. INTRODUCTION
    # =========================================================================
    doc.add_heading("I. Introduction", level=1)
    doc.add_paragraph(
        "Smoking kills over eight million people annually [1]. Text-based mobile "
        "interventions have shown 50\u201360% higher quit rates compared to controls "
        "[2], making mHealth messaging a practical tool for smoking cessation. "
        "Modern messaging applications go beyond plain SMS by incorporating read "
        "receipts, typing indicators, rich media, and suggested reply buttons. "
        "These features make interactions more engaging than plain text, but they "
        "also make the messaging system more complex."
    )
    doc.add_paragraph(
        "Cross-platform mHealth messaging applications face performance demands "
        "that generic mobile apps do not. The system must deliver messages with "
        "low latency during real-time conversations, keep messages in the right "
        "order, maintain a responsive UI while handling background network "
        "traffic, and avoid memory bloat during sessions that can last 30 "
        "minutes. If the app becomes sluggish during a conversation, the user "
        "may disengage [3]."
    )
    doc.add_paragraph(
        "Flutter, Google\u2019s cross-platform toolkit, compiles to native code from "
        "a single Dart codebase and renders through the Skia engine [4]. Prior "
        "benchmarks have compared Flutter to native development in general [5], "
        "[6], but none have measured Flutter\u2019s behavior in a real-time messaging "
        "context where background network operations, message ordering, and "
        "database synchronization all compete with the rendering pipeline."
    )
    doc.add_paragraph(
        "Most mHealth messaging apps run on Firebase Firestore, which pushes "
        "data changes to connected clients via real-time listeners and handles "
        "caching and offline persistence automatically. The client-side cost of "
        "keeping a sorted, deduplicated message list in sync with Firestore\u2019s "
        "stream\u2014while rendering a responsive UI\u2014has not been characterized for "
        "messaging workloads."
    )

    # Contributions
    doc.add_heading("A. Contributions", level=2)
    doc.add_paragraph("The paper makes four contributions:")
    contributions = [
        "A SQLite-backed metrics service embedded in the application that "
        "captures timing measurements at sub-millisecond precision and exports "
        "to CSV for offline analysis.",
        "Empirical before/after benchmarks of binary-search-guided message "
        "insertion (Section V-A) alongside instrumented design patterns: "
        "composition-based service architecture (Section III-A), multi-layer "
        "caching with LRU eviction (Section III-D), and platform-specific HTTP "
        "client configuration with isolate-based link preview parsing "
        "(Sections III-C, III-E). Sorting benchmarks span 700 runs across 14 "
        "configurations.",
        "Open-source R and Python analysis scripts that run ANOVA, Tukey HSD "
        "post-hoc tests, and Shapiro-Wilk normality checks, and produce "
        "IEEE-formatted figures.",
        "A server-side RAG pipeline that retrieves from the Gemini Protocol "
        "knowledge base (4,847 human-curated Q&A pairs) via ChromaDB and "
        "generates grounded responses through Gemini 2.0 Flash, integrated "
        "into the production messaging flow.",
    ]
    for i, c in enumerate(contributions, 1):
        doc.add_paragraph(f"{i}) {c}", style="List Number")

    doc.add_paragraph(
        "The rest of the paper is organized as follows. Section II surveys "
        "related work. Section III details the system architecture, including "
        "the rationale for selecting Flutter. Section IV describes the "
        "experimental methodology. Section V reports client-side performance "
        "results. Section VI describes the AI-enhanced messaging pipeline. "
        "Section VII discusses findings, and Section VIII concludes."
    )

    # =========================================================================
    # II. RELATED WORK
    # =========================================================================
    doc.add_heading("II. Related Work", level=1)

    doc.add_heading("A. mHealth Messaging for Smoking Cessation", level=2)
    doc.add_paragraph(
        "Whittaker et al. [2] analyzed 26 randomized controlled trials with "
        "over 33,000 participants and found that mobile cessation interventions "
        "increased quit rates by 50\u201360%. SmokefreeTXT, the NCI\u2019s SMS-based "
        "program, sustained engagement over six-week periods [12]. These studies "
        "measure intervention outcomes but say nothing about the performance of "
        "the messaging systems delivering them."
    )
    doc.add_paragraph(
        "More recently, Bricker et al. [15] developed QuitBot, a conversational "
        "chatbot for smoking cessation that uses a library of 11,000 "
        "question-answer pairs with a fine-tuned GPT-3.5 fallback. In a pilot "
        "RCT, QuitBot achieved 63% 30-day point-prevalence abstinence versus "
        "38.5% for the NCI\u2019s SmokefreeTXT (OR 2.58, 95% CI [1.34, 4.99]). "
        "Their work demonstrates that AI-enhanced conversational delivery "
        "improves engagement over linear messaging, but does not address system "
        "performance under load or cross-platform deployment challenges."
    )
    doc.add_paragraph(
        "Moving beyond plain SMS to app-based messaging adds suggested replies, "
        "carousels, and read receipts, which make interactions more engaging but "
        "also more computationally expensive. To our knowledge, no prior work "
        "has benchmarked client-side performance in a cross-platform mHealth "
        "messaging system."
    )

    doc.add_heading("B. Cross-Platform Mobile Performance", level=2)
    doc.add_paragraph(
        "Bi\u00f8rn-Hansen et al. [5] compared React Native, Flutter, and native "
        "Android/iOS, finding that Flutter matched native frame rates but used "
        "more memory on Android. Majchrzak et al. [6] benchmarked progressive "
        "web apps against native approaches on startup time, rendering, and "
        "memory."
    )
    doc.add_paragraph(
        "Flutter-specific studies have measured rendering pipeline efficiency "
        "[4], widget rebuild cost, and platform channel overhead. These focus on "
        "UI workloads. None measure what happens when background network "
        "operations, message ordering, and database synchronization all compete "
        "with the rendering pipeline at the same time, which is the normal "
        "state of a messaging app."
    )

    doc.add_heading("C. Firebase in Mobile Applications", level=2)
    doc.add_paragraph(
        "Firestore\u2019s real-time sync has made it a common backend for mobile "
        "messaging. Moroney [9] covered Firestore query performance and offline "
        "caching. Inupakutika et al. [7] built a four-block testbed for mHealth "
        "application performance evaluation, measuring service response time "
        "under controlled concurrent load with ANOVA and Tukey HSD post-hoc "
        "tests. We adapt their testbed design for our Firebase messaging system."
    )
    doc.add_paragraph(
        "Gunnam et al. [8] extended that work to heterogeneous chatbot systems, "
        "adding throughput and concurrent-user scaling as metrics. They found "
        "that latency under load degrades non-linearly, with sharp inflection "
        "points where performance drops off. This finding is why we calibrate "
        "our Firebase load levels empirically rather than picking arbitrary "
        "thresholds."
    )

    doc.add_heading("D. Message Ordering and Caching", level=2)
    doc.add_paragraph(
        "The naive approach to message ordering re-sorts the entire list on "
        "each insertion: O(n log n) per message. Binary search insertion runs "
        "in O(log n), but its practical effect in a Flutter messaging "
        "context, where the sorted list feeds a reactive widget tree, has not "
        "been measured."
    )
    doc.add_paragraph(
        "Client-side caching in messaging apps trades memory for lookup speed. "
        "LRU eviction is standard [11]. How an application-level cache "
        "interacts with Firebase\u2019s own client-side persistence layer\u2014both "
        "caching independently\u2014has not been characterized for messaging "
        "workloads."
    )

    doc.add_heading("E. Gap in Literature", level=2)
    doc.add_paragraph(
        "mHealth messaging efficacy, cross-platform benchmarks, and Firebase "
        "optimization have each been studied in isolation, but client-side "
        "performance of a deployed mHealth messaging system has not been "
        "characterized. Similarly, existing mHealth chatbot systems rely on "
        "static QnA libraries [15] or cloud-hosted LLM APIs without "
        "domain-specific grounding; none use retrieval-augmented generation "
        "[16] with a curated knowledge base. We address both gaps by "
        "instrumenting a deployed mHealth messaging app and integrating a "
        "curated-knowledge RAG layer into its production pipeline."
    )

    # =========================================================================
    # III. SYSTEM ARCHITECTURE
    # =========================================================================
    doc.add_heading("III. System Architecture", level=1)
    doc.add_paragraph(
        "Quitxt is a cross-platform messaging application for smoking "
        "cessation [13], [14], running on Android and iOS from a single "
        "codebase with Firebase Firestore for real-time message sync and "
        "Firebase Cloud Messaging (FCM) for push notifications. Fig. 1 shows "
        "the end-to-end system architecture."
    )

    add_figure_placeholder(
        doc,
        "Fig. 1. System architecture. The Flutter client communicates with "
        "Firebase Firestore for real-time message sync. The server runs the "
        "RAG pipeline: ChromaDB retrieves from the Gemini Protocol knowledge "
        "base, and Gemini 2.0 Flash generates grounded responses. The embedded "
        "metrics service captures performance measurements at each layer.",
        "fig1_main_results.png",
    )

    doc.add_heading("A. Framework Selection: Flutter", level=2)
    doc.add_paragraph(
        "We evaluated Flutter, React Native, and native development before "
        "selecting Flutter for the following reasons. First, Flutter compiles "
        "to native ARM code via ahead-of-time (AOT) compilation, eliminating "
        "the JavaScript bridge that adds latency in React Native\u2019s architecture "
        "[4]. For a real-time messaging application where every millisecond in "
        "the rendering pipeline matters, this is a meaningful advantage. "
        "Second, Flutter\u2019s Skia-based rendering engine produces consistent UI "
        "across platforms without relying on platform-native widgets, which "
        "simplifies testing and reduces platform-specific bugs. Third, Dart\u2019s "
        "single-threaded event loop with isolate-based concurrency maps well to "
        "the messaging use case: the main isolate handles UI and Firestore "
        "listeners, while CPU-bound tasks (link preview parsing, performance "
        "metrics collection) run on background isolates without shared-memory "
        "concurrency issues. Prior cross-platform benchmarks confirm that "
        "Flutter matches native frame rates while using more memory on Android "
        "[5]; we accept this trade-off given the UI consistency benefit."
    )
    doc.add_paragraph(
        "The subsections below describe each architectural component and the "
        "design decisions whose performance we benchmark in Section V."
    )

    doc.add_heading("B. Composition-Based Messaging Service", level=2)
    doc.add_paragraph(
        "The messaging subsystem uses a composition pattern [10] instead of a "
        "single monolithic service. ComposedMessagingService delegates to three "
        "specialized services:"
    )
    services = [
        "HttpMessageService: HTTP transport to the messaging server, with "
        "platform-specific client configuration.",
        "FirestoreMessageService: Real-time Firestore listeners for incoming "
        "messages and server responses.",
        "MessageCacheService: In-memory message caching with content-based "
        "deduplication.",
    ]
    for s in services:
        doc.add_paragraph(s, style="List Bullet")

    doc.add_paragraph(
        "This separation lets us optimize and test each layer independently. "
        "The send flow works as follows:"
    )
    send_steps = [
        "ComposedMessagingService.sendMessage() receives user input text.",
        "A unique message identifier is generated using UUID v4.",
        "The message is persisted to Firestore via FirestoreMessageService.",
        "The message is cached via MessageCacheService.",
        "An HTTP POST request is dispatched to the server via HttpMessageService.",
        "The server response arrives asynchronously via the Firestore real-time listener.",
    ]
    for i, step in enumerate(send_steps, 1):
        doc.add_paragraph(f"{i}) {step}", style="List Number")

    doc.add_paragraph(
        "Because each layer is a separate service, we can instrument and time "
        "them independently. Fig. 2 illustrates the complete message send and "
        "response lifecycle."
    )

    add_figure_placeholder(
        doc,
        "Fig. 2. Message send and response lifecycle. Steps 1\u20134 execute on "
        "the client; steps 5\u20137 on the server (RAG retrieval and generation); "
        "steps 8\u20139 deliver the response via Firestore\u2019s real-time listener.",
        "fig2_statistical_comparison.png",
    )

    doc.add_heading("C. Binary Search Message Insertion", level=2)
    doc.add_paragraph(
        "A chat UI needs a chronologically sorted message list. The simple "
        "approach, appending and re-sorting, costs O(n log n) per insertion. "
        "Once conversations pass a few hundred messages, the re-sort becomes "
        "visible as UI jank."
    )
    doc.add_paragraph(
        "We use O(log n) binary search insertion in the ChatProvider class. "
        "The _findInsertionIndex() method binary-searches the sorted list to "
        "find where the new message belongs:"
    )
    add_code_block(
        doc,
        "int _findInsertionIndex(ChatMessage msg) {\n"
        "  int low = 0, high = _messages.length;\n"
        "  while (low < high) {\n"
        "    final mid = (low + high) ~/ 2;\n"
        "    if (_comparator(_messages[mid], msg) <= 0)\n"
        "      low = mid + 1;\n"
        "    else\n"
        "      high = mid;\n"
        "  }\n"
        "  return low;\n"
        "}",
    )
    doc.add_paragraph(
        "The comparator sorts by timestamp ascending, breaking ties by message "
        "ID. After finding the index, List.insert() shifts subsequent elements "
        "in O(n) time. The net cost is O(n) per insertion\u2014O(log n) to locate "
        "the position via binary search, O(n) to shift\u2014but the shift is a "
        "contiguous memory move with a much smaller constant factor than the "
        "O(n log n) comparison-heavy full-sort, yielding the empirically "
        "observed speedup. For benchmarking, we retain a baselineFullSort() "
        "method that copies the list, appends the message, and re-sorts, so we "
        "can compare both approaches on identical data."
    )

    doc.add_heading("D. Platform-Specific HTTP Configuration", level=2)
    doc.add_paragraph(
        "Flutter\u2019s http package abstracts platform differences, but Android "
        "and iOS handle HTTP connections differently enough to affect message "
        "delivery latency. We configure each platform separately."
    )
    doc.add_paragraph(
        "Android uses IOClient wrapping Dart\u2019s HttpClient with "
        "Connection: close headers, a 15-second timeout, and a 30-second idle "
        "timeout. We close connections explicitly because Android\u2019s connection "
        "pooling occasionally held stale connections, causing intermittent "
        "timeouts on cellular networks."
    )
    doc.add_paragraph(
        "iOS uses the default http.Client with Connection: keep-alive and an "
        "8-second timeout. iOS\u2019s URLSession manages connection reuse well on "
        "its own, and the shorter timeout accounts for iOS\u2019s more aggressive "
        "background task limits."
    )

    add_table_from_data(
        doc,
        ["Parameter", "Android", "iOS"],
        [
            ["HTTP Client", "IOClient", "Default http.Client"],
            ["Connection", "Close", "Keep-Alive"],
            ["Timeout", "15 s", "8 s"],
            ["Idle Timeout", "30 s", "N/A"],
            ["App Check", "Play Integrity", "DeviceCheck"],
        ],
        "TABLE I: Platform-Specific HTTP Configurations",
    )

    doc.add_heading("E. Multi-Layer Caching Architecture", level=2)
    doc.add_paragraph(
        "The application has two caching layers that interact with each other."
    )
    doc.add_paragraph(
        "MessageCacheService is an in-memory LRU cache holding up to 1,000 "
        "messages. Messages are indexed by ID for direct lookup and by a "
        "content-timestamp composite key for deduplication. When full, the 100 "
        "oldest entries are evicted. We time cache operations using Dart\u2019s "
        "Stopwatch at microsecond resolution."
    )
    doc.add_paragraph(
        "Firestore\u2019s built-in persistence caches documents locally for offline "
        "access and reduced round-trips. We tag each response with "
        "doc.metadata.isFromCache so we can analyze latency separately for "
        "cache-served and server-fetched responses."
    )
    doc.add_paragraph(
        "A message may come from the application cache (fastest), the Firebase "
        "client cache (fast), or the Firebase server (variable, depending on "
        "load and network). These layers interact, and the compound behavior "
        "matters for latency analysis."
    )

    doc.add_heading("F. Isolate-Based Link Preview Processing", level=2)
    doc.add_paragraph(
        "When messages contain URLs, the app fetches HTML and parses it for "
        "link previews. HTML parsing is CPU-bound and will cause UI jank if run "
        "on the main isolate. We offload it using Flutter\u2019s compute() function, "
        "which spawns a background isolate for the HTML extraction of Open "
        "Graph, Twitter Card, and fallback metadata. Results are cached in a "
        "200-entry LRU. Pending requests are deduplicated with a "
        "Completer-based queue so the same URL is never fetched twice "
        "concurrently."
    )

    doc.add_heading("G. Frame Rendering Monitoring", level=2)
    doc.add_paragraph(
        "Flutter exposes per-frame timing via "
        "SchedulerBinding.addTimingsCallback. We record build duration (widget "
        "tree construction) and raster duration (GPU rendering) for each frame. "
        "Frames exceeding 16.67 ms total (the 60 fps budget) are classified as "
        "jank. This gives a direct measure of UI responsiveness during chat "
        "interactions."
    )

    doc.add_heading("H. Security: Firebase App Check", level=2)
    doc.add_paragraph(
        "Firebase App Check verifies that requests come from genuine app "
        "instances. On Android it uses the Play Integrity API; on iOS, "
        "DeviceCheck. We include App Check initialization in our startup timing "
        "because it adds measurable latency to cold start."
    )

    doc.add_heading("I. Application Interface", level=2)
    doc.add_paragraph(
        "Fig. 3 shows four representative screens from the Quitxt application. "
        "The welcome screen (a) greets first-time users with a message input "
        "field connected to the Firestore pipeline. The active chat session (b) "
        "shows an AI message with an isolate-parsed link preview, a binary poll "
        "with tappable response buttons, and an AI-generated motivational "
        "reply. The About screen (c) describes the Quitxt program and its "
        "bilingual support. The Help & Quick Actions screen (d) demonstrates "
        "the bilingual keyword panel (English and Spanish), allowing users to "
        "send protocol keywords\u2014such as Helpnow, Crave, Slip, or "
        "Badmood\u2014with a single tap, triggering targeted RAG-grounded responses "
        "from the server."
    )

    add_figure_placeholder(
        doc,
        "Fig. 3. Quitxt application screens. (a) Welcome screen. (b) Active "
        "chat with AI link preview, poll, and motivational reply. (c) About "
        "screen with program description. (d) Bilingual one-tap protocol "
        "keywords.",
        "fig3_data_leakage_impact.png",
    )

    # =========================================================================
    # IV. EXPERIMENTAL METHODOLOGY
    # =========================================================================
    doc.add_heading("IV. Experimental Methodology", level=1)
    doc.add_paragraph(
        "This section describes the measurement infrastructure, experimental "
        "design, and statistical methods."
    )

    doc.add_heading("A. Performance Metrics Service", level=2)
    doc.add_paragraph(
        "We embedded a PerformanceMetricsService singleton in the app to "
        "capture timing measurements at runtime. The service stores "
        "measurements in a local SQLite database (performance_metrics.db) with "
        "no network overhead, buffers 50 measurements in memory before flushing "
        "to disk every 10 seconds, and is controlled by a compile-time constant "
        "PERF_METRICS_ENABLED tied to Dart\u2019s kDebugMode for zero overhead in "
        "production. Collected data exports to CSV for offline analysis in R "
        "and Python."
    )

    add_table_from_data(
        doc,
        ["Metric Type", "Definition"],
        [
            [
                "appStartup",
                "Time from WidgetsFlutterBinding initialization to first frame "
                "render, decomposed into seven checkpoints (T0\u2013T7).",
            ],
            [
                "messageDelivery",
                "End-to-end latency Tresponse = Treceived \u2212 Tsent, where Tsent "
                "is recorded before HTTP dispatch and Treceived upon Firestore "
                "listener callback.",
            ],
            [
                "messageSort",
                "Duration of message list insertion: binary search O(log n) and "
                "baseline full-sort O(n log n).",
            ],
            [
                "httpRoundtrip",
                "HTTP POST round-trip, differentiated by platform path.",
            ],
            ["cacheOperation", "Cache lookup, insertion, and eviction timing."],
            [
                "memoryUsage",
                "Resident Set Size sampled every 5 s via ProcessInfo.currentRss.",
            ],
            [
                "frameTime",
                "Per-frame build + raster duration, classified as normal "
                "(\u226416.67 ms) or jank (>16.67 ms).",
            ],
            [
                "linkPreview",
                "Duration of isolate-based HTML parsing for link preview "
                "generation.",
            ],
        ],
        "TABLE II: Performance Metric Types and Definitions",
    )

    doc.add_heading("B. Startup Timing Checkpoints", level=2)
    doc.add_paragraph(
        "Cold-start time is split into seven checkpoints, timed with Dart\u2019s "
        "monotonic Stopwatch to avoid NTP clock correction artifacts."
    )

    add_table_from_data(
        doc,
        ["ID", "Event", "Measures"],
        [
            ["T0", "ensureInitialized()", "Absolute start"],
            ["T1", "Platform optimizations", "iOS/Android init"],
            ["T2", "dotenv.load()", "Environment config"],
            ["T3", "Firebase.initializeApp()", "Firebase core init"],
            ["T4", "AppCheck.activate()", "Security attestation"],
            ["T5", "AppCacheManager.init()", "Cache manager setup"],
            ["T6", "getFcmToken()", "Push notification token"],
            ["T7", "First frame callback", "UI ready"],
        ],
        "TABLE III: Application Startup Checkpoints",
    )

    doc.add_paragraph(
        "Total startup time is Tstartup = T7 \u2212 T0. Each sub-interval "
        "(Ti+1 \u2212 Ti) identifies the dominant contributor to startup latency."
    )

    add_figure_placeholder(
        doc,
        "Fig. 4. Application startup checkpoint timeline (T0\u2013T7). "
        "Orange-shaded regions (Firebase initialization, App Check attestation, "
        "FCM token retrieval) are expected to dominate cold-start time on "
        "physical devices. Green checkpoints (Dart-level initialization) "
        "measured at <300 \u03bcs in Section V-B.",
        "fig4_metrics_table.png",
    )

    doc.add_heading("C. Message Delivery Latency (Tresponse)", level=2)
    doc.add_paragraph(
        "Tresponse measures the time from message dispatch to server response "
        "receipt:"
    )
    doc.add_paragraph("Tresponse = Treceived \u2212 Tsent")
    doc.add_paragraph(
        "Tsent is recorded just before HttpMessageService.sendToServer() and "
        "Treceived when the Firestore listener receives the server\u2019s response "
        "document matching the original message UUID. This captures the full "
        "round-trip: HTTP transport, server processing, Firestore write, and "
        "real-time sync back to the client. We also record "
        "doc.metadata.isFromCache to separate cache-served responses from "
        "server-fetched responses."
    )

    doc.add_heading("D. Execution Environment", level=2)
    doc.add_paragraph(
        "The sorting and cache benchmarks reported in Section V run on the "
        "Dart VM (macOS, Apple Silicon M1, Dart 3.10.7) using Flutter\u2019s "
        "integration_test framework. Each benchmark invokes the same "
        "production code paths that the mobile application uses at runtime. "
        "Collected SQLite databases are exported and processed through R and "
        "Python analysis scripts."
    )
    doc.add_paragraph(
        "On-device validation on physical Android and iOS hardware, including "
        "end-to-end message delivery latency under Firebase backend load "
        "following the testbed methodology of Inupakutika et al. [7], is left "
        "for future work."
    )

    doc.add_heading("E. Experiment Configurations", level=2)

    add_table_from_data(
        doc,
        ["Experiment", "Configs", "Runs", "Total"],
        [
            ["Sorting Scalability", "10", "50", "500"],
            ["App Startup", "4", "50", "200"],
            ["Total", "14", "", "700"],
        ],
        "TABLE IV: Experiment Configuration Matrix",
    )

    doc.add_paragraph(
        "Each configuration runs 50 times with 10 additional warm-up "
        "iterations (discarded) to stabilize JIT compilation variance on the "
        "Dart VM. The n=50 sample size exceeds CLT requirements and provides "
        "tighter confidence intervals than the minimum n=30."
    )

    doc.add_heading("F. Statistical Methods", level=2)
    doc.add_paragraph(
        "All statistical analyses follow Inupakutika et al. [7]. Descriptive "
        "statistics include mean, standard deviation, median, min, max, and "
        "skewness for each configuration."
    )
    doc.add_paragraph(
        "We compute 95% confidence intervals as: CI = x\u0304 \u00b1 t(0.025, n\u22121) "
        "\u00b7 s / \u221an, where x\u0304 is the sample mean, s the sample standard "
        "deviation (with Bessel\u2019s correction), and t(0.025, n\u22121) the critical "
        "value from Student\u2019s t-distribution with n\u22121 degrees of freedom. With "
        "n = 50 per configuration, t(0.025, 49) = 2.010."
    )
    doc.add_paragraph(
        "Normality testing uses the Shapiro-Wilk test (\u03b1 = 0.05). If "
        "normality holds, one-way or multiway ANOVA tests for significant "
        "group differences; otherwise Kruskal-Wallis replaces ANOVA. When "
        "ANOVA rejects H0 (p < 0.05), Tukey HSD identifies which pairs "
        "differ. For non-parametric cases, pairwise Wilcoxon rank-sum tests "
        "with Holm correction are used."
    )

    # =========================================================================
    # V. RESULTS
    # =========================================================================
    doc.add_heading("V. Results", level=1)
    doc.add_paragraph(
        "All benchmarks were executed on the host Dart VM (macOS, Apple "
        "Silicon M1, Dart 3.10.7). Each of the 29 configurations was run 50 "
        "times (n = 50) following 10 warm-up iterations discarded to stabilize "
        "JIT compilation. We report means, medians, 95th percentiles, and 95% "
        "confidence intervals computed using Equation 2."
    )

    doc.add_heading("A. Message Sorting Scalability", level=2)

    add_table_from_data(
        doc,
        ["N", "Method", "Mean", "Med.", "P95", "95% CI"],
        [
            ["10", "Bin. Insert", "4.5", "3.0", "12.0", "[3.5, 5.4]"],
            ["10", "Full Sort", "2.8", "1.0", "6.0", "[0.8, 4.7]"],
            ["50", "Bin. Insert", "2.7", "2.0", "6.0", "[2.4, 3.0]"],
            ["50", "Full Sort", "15.2", "8.5", "39.0", "[9.3, 21.0]"],
            ["100", "Bin. Insert", "1.9", "1.0", "7.0", "[0.8, 3.0]"],
            ["100", "Full Sort", "13.6", "10.0", "27.0", "[10.0, 17.3]"],
            ["500", "Bin. Insert", "6.9", "4.0", "22.0", "[2.2, 11.6]"],
            ["500", "Full Sort", "44.1", "26.0", "124.0", "[34.3, 53.9]"],
            ["1000", "Bin. Insert", "4.4", "4.0", "10.0", "[3.5, 5.3]"],
            ["1000", "Full Sort", "84.9", "60.0", "187.0", "[65.7, 104.0]"],
        ],
        "TABLE V: Message Sorting Latency (n = 50, values in \u03bcs)",
    )

    doc.add_paragraph(
        "Binary insertion remains nearly constant across all N values (median "
        "1\u20134 \u03bcs), confirming O(log n) behavior. Full sort grows from a median "
        "of 1 \u03bcs at N=10 to 60 \u03bcs at N=1000, consistent with O(n log n) "
        "scaling."
    )

    add_figure_placeholder(
        doc,
        "Fig. 5. Message sorting scalability. Binary search insertion remains "
        "nearly constant across all N, while full-sort latency grows with "
        "O(n log n) scaling. Shaded regions show 95% confidence intervals "
        "(n = 50).",
        "fig5_targets_assessment.png",
    )

    doc.add_paragraph(
        "At N=10, the overhead of the binary search comparisons makes it "
        "comparable to the sort baseline (median 3 \u03bcs vs. 1 \u03bcs), with "
        "overlapping confidence intervals. Binary insertion\u2019s advantage emerges "
        "at N \u2265 50: the median speedup grows from 4.3\u00d7 at N=50 to 15\u00d7 at "
        "N=1000. By mean, the speedup at N=1000 reaches 19\u00d7 (85 \u03bcs vs. "
        "4.4 \u03bcs). Both methods operate well within a single 16.67 ms frame "
        "budget even in worst-case scenarios: the full sort\u2019s P95 at N=1000 is "
        "187 \u03bcs, while binary insertion stays at 10 \u03bcs."
    )

    doc.add_heading("B. Application Startup Performance", level=2)
    doc.add_paragraph(
        "We measured the Dart-level construction cost of two key components: "
        "ChatProvider instantiation and MessageCacheService initialization with "
        "100 inserts."
    )
    doc.add_paragraph(
        "ChatProvider construction averaged 250 \u03bcs (median 231 \u03bcs, P95 "
        "456 \u03bcs, 95% CI [219, 281]). Cache initialization averaged 74 \u03bcs "
        "(median 64 \u03bcs, P95 167 \u03bcs, 95% CI [64, 83]). Both are negligible "
        "relative to full cold-start time, which on physical devices is "
        "dominated by Firebase initialization (T3), App Check attestation "
        "(T4), and FCM token retrieval (T6) as described in Table III. Full "
        "T0\u2013T7 profiling on mobile hardware remains future work."
    )

    # =========================================================================
    # VI. AI-ENHANCED MESSAGING
    # =========================================================================
    doc.add_heading("VI. AI-Enhanced Messaging", level=1)
    doc.add_paragraph(
        "Quitxt includes a server-side retrieval-augmented generation (RAG) "
        "layer [16] that grounds its AI responses in domain-specific evidence. "
        "Where QuitBot [15] matches against a fixed library of 11,000 QnA "
        "pairs, Quitxt retrieves relevant content from a vector index for each "
        "query and generates a grounded response on the fly using Gemini 2.0 "
        "Flash. The end-to-end pipeline works as follows: (1) the Flutter "
        "client sends a user message through the Firestore pipeline described "
        "in Section III-A; (2) a Firebase Cloud Function receives the message "
        "and queries a ChromaDB vector store indexed with the Gemini Protocol "
        "knowledge base; (3) the top-k retrieved chunks are assembled into a "
        "structured prompt and submitted to Gemini 2.0 Flash "
        "(gemini-2.0-flash-exp); and (4) the generated response is written "
        "back to Firestore, where the client\u2019s real-time listener delivers it "
        "to the UI. RAG processing time is therefore part of the measured "
        "Tresponse."
    )

    doc.add_heading("A. Knowledge Base Construction", level=2)
    doc.add_paragraph(
        "The production knowledge base is the Human-Curated dataset (n = "
        "4,847 Q&A pairs), professionally curated and verified against the "
        "Gemini Protocol\u2014a structured smoking cessation framework developed by "
        "Dr. Louis Willis that encodes motivational interviewing (MI) "
        "strategies, pharmacotherapy guidance (NRT, varenicline, bupropion), "
        "behavioral coping techniques, and relapse prevention protocols. The "
        "dataset was refined iteratively: domain experts reviewed retrieval "
        "quality metrics after each round of edits and adjusted the corpus to "
        "improve downstream RAG performance."
    )
    doc.add_paragraph(
        "The dataset is indexed in a ChromaDB vector store using cosine "
        "similarity over sentence embeddings. At inference, the top-k (k = 3) "
        "most similar chunks are retrieved and injected into a structured "
        "prompt template alongside the user query and up to five prior turns "
        "of conversation history. The prompt instructs the LLM to ground its "
        "response in the retrieved evidence while maintaining a conversational "
        "tone. Gemini 2.0 Flash (gemini-2.0-flash-exp) generates the "
        "response, chosen for its low latency and strong instruction-following "
        "in health domains. The generated response is written back to "
        "Firestore, where the client\u2019s real-time listener delivers it to the "
        "UI."
    )
    doc.add_paragraph(
        "Because embeddings are pre-computed and the ChromaDB index is served "
        "locally alongside the server application, vector retrieval adds "
        "minimal overhead (\u2248150 ms measured). The dominant latency component "
        "is LLM generation, which varies with response length and model load. "
        "Fig. 6 details the retrieval and generation pipeline. Formal "
        "evaluation of response quality\u2014including faithfulness, hallucination "
        "rate, and retrieval precision using the RAGAS framework [17]\u2014is the "
        "subject of a companion study currently in preparation [18]."
    )

    add_figure_placeholder(
        doc,
        "Fig. 6. RAG pipeline detail. The user message is embedded and "
        "matched against the ChromaDB index of Gemini Protocol Q&A pairs. The "
        "top-3 retrieved chunks are assembled with conversation history into a "
        "structured prompt, then submitted to Gemini 2.0 Flash. Retrieval "
        "takes \u2248150 ms; LLM generation dominates at 2\u20135 s.",
    )

    # =========================================================================
    # VII. DISCUSSION
    # =========================================================================
    doc.add_heading("VII. Discussion", level=1)

    doc.add_heading("A. Comparison with Prior Work", level=2)
    doc.add_paragraph(
        "Inupakutika et al. [7] and Gunnam et al. [8] measured server-side "
        "response latency for cloud-based chatbot systems but did not examine "
        "client-side costs. Our sorting benchmarks address that gap: the 15\u00d7 "
        "median speedup from binary insertion at N=1000 shows that client-side "
        "algorithmic choices affect message ordering latency independently of "
        "server-side factors."
    )
    doc.add_paragraph(
        "Bricker et al. [15] demonstrated the efficacy of conversational "
        "chatbot delivery (QuitBot) over linear SMS, using a static library of "
        "11,000 QnA pairs with GPT-3.5 fallback. Quitxt takes a different "
        "approach: the Gemini Protocol knowledge base is indexed in ChromaDB "
        "and used by Gemini 2.0 Flash to generate grounded responses on the "
        "fly, without hand-authored templates. Formal evaluation of response "
        "quality is the subject of a companion study [18]."
    )

    doc.add_heading("B. Architectural Implications", level=2)
    doc.add_paragraph(
        "The composition-based architecture (Section III-B) enables "
        "independent measurement and optimization of each subsystem. Message "
        "sorting has the widest dynamic range: full-sort latency grows roughly "
        "30\u00d7 from N=10 to N=1000, while binary insertion stays flat. The "
        "choice of Flutter over React Native (Section III-A) eliminates the "
        "JavaScript bridge, and isolate-based background processing keeps "
        "CPU-bound tasks (link preview parsing, metrics collection) off the "
        "main rendering thread. The platform-specific HTTP configuration "
        "(Section III-C) reflects how Android and iOS handle connection pooling "
        "differently\u2014a cross-platform trade-off whose latency impact warrants "
        "quantification on physical devices."
    )

    doc.add_heading("C. Deployment Implications", level=2)
    doc.add_paragraph(
        "Client-side sorting operations complete in under 200 \u03bcs even at the "
        "95th percentile for N=1000\u2014well below the 100 ms perception threshold "
        "[3]. The dominant contributor to user-perceived latency is Tresponse, "
        "the server round-trip including RAG retrieval and LLM generation."
    )

    doc.add_heading("D. Threats to Validity", level=2)
    doc.add_paragraph(
        "Internal validity: We use Dart\u2019s monotonic Stopwatch to avoid clock "
        "corrections, and a fixed random seed (42) ensures reproducible test "
        "data generation across runs. JIT warm-up variance is mitigated by "
        "discarding 10 warm-up iterations before each 50-iteration measurement "
        "block."
    )
    doc.add_paragraph(
        "External validity: Benchmarks run on the Dart VM on a host machine "
        "(Apple Silicon), not on mobile hardware. Mobile device performance "
        "will differ due to lower clock speeds and thermal throttling. The "
        "relative comparison (binary insert vs. full sort) should hold "
        "directionally, but absolute latencies will be higher."
    )
    doc.add_paragraph(
        "Construct validity: Startup measurements capture Dart-level "
        "construction cost only and do not include Firebase initialization, "
        "App Check, or platform-specific setup that dominate real cold-start "
        "time."
    )
    doc.add_paragraph(
        "Statistical validity: With n = 50 runs per configuration, sample "
        "sizes exceed CLT requirements. Microsecond-scale measurements are at "
        "the resolution limit of Dart\u2019s Stopwatch; speedup ratios should be "
        "interpreted as order-of-magnitude indicators rather than precise "
        "multipliers."
    )

    # =========================================================================
    # VIII. CONCLUSION
    # =========================================================================
    doc.add_heading("VIII. Conclusion", level=1)
    doc.add_paragraph(
        "We presented the design, implementation, and performance evaluation "
        "of Quitxt, a cross-platform Flutter messaging application for smoking "
        "cessation with an integrated RAG pipeline. The architectural "
        "choices\u2014composition-based service decomposition, binary search message "
        "insertion, platform-specific HTTP configuration, and isolate-based "
        "background processing\u2014keep all client-side operations well within a "
        "single frame budget. Binary search insertion achieves a 15\u00d7 median "
        "speedup over full-sort at N=1000 messages, confirming that "
        "algorithmic optimization at the client layer eliminates message "
        "ordering as a latency contributor. The server-side RAG layer retrieves "
        "from a professionally curated knowledge base via ChromaDB and "
        "generates grounded responses through Gemini 2.0 Flash, providing "
        "domain-specific AI assistance without requiring users to leave the "
        "messaging interface. The measurement framework and analysis scripts "
        "are available at https://github.com/anudeepadi/quit-txt-rag-eval."
    )

    doc.add_heading("A. Future Work", level=2)
    doc.add_paragraph(
        "Three directions follow from this work: (1) on-device validation on "
        "physical Android and iOS hardware with Firebase backend load testing, "
        "following the testbed methodology of Inupakutika et al. [7], to "
        "characterize end-to-end message delivery latency under concurrent "
        "load; (2) formal evaluation of RAG response quality using the RAGAS "
        "framework [17], comparing human-curated and AI-generated knowledge "
        "bases, with results to be reported in a companion study [18]; and "
        "(3) field deployment monitoring to compare laboratory benchmarks "
        "against real-world usage patterns."
    )

    # =========================================================================
    # REFERENCES
    # =========================================================================
    doc.add_heading("References", level=1)
    references = [
        '[1] World Health Organization, "WHO report on the global tobacco '
        'epidemic 2023: Protect people from tobacco smoke," WHO, Tech. Rep., '
        "2023.",
        "[2] R. Whittaker, H. McRobbie, C. Bullen, R. Rodgers, Y. Gu, and "
        'R. Dobson, "Mobile phone text messaging and app-based interventions '
        'for smoking cessation," Cochrane Database of Systematic Reviews, '
        "no. 10, 2019.",
        "[3] W. T. Riley, D. E. Rivera, A. A. Atienza, W. Nilsen, S. M. "
        'Allison, and R. Mermelstein, "Health behavior models in the age of '
        'mobile interventions: Are our theories up to the task?" Translational '
        "Behavioral Medicine, vol. 1, no. 1, pp. 53\u201371, 2011.",
        "[4] S. Nicola, J. Ferreira, and J. P. Fernandes, \u201cFlutter vs. native "
        "vs. React Native: Examining performance of mobile development "
        "approaches,\u201d SN Computer Science, vol. 3, no. 5, p. 385, 2022.",
        "[5] A. Bi\u00f8rn-Hansen, T.-M. Gr\u00f8nli, and G. Ghinea, \u201cA survey and "
        "taxonomy of core concepts and research challenges in cross-platform "
        "mobile development,\u201d ACM Computing Surveys, vol. 51, no. 5, pp. "
        "1\u201334, 2020.",
        "[6] T. A. Majchrzak, A. Bi\u00f8rn-Hansen, and T.-M. Gr\u00f8nli, "
        "\u201cProgressive web apps: The definite approach to cross-platform "
        "development?\u201d in Proc. 51st Hawaii Int. Conf. System Sciences "
        "(HICSS), 2018, pp. 5735\u20135744.",
        "[7] D. Inupakutika, G. Rodriguez, D. Akopian, P. Lama, P. Chalela, "
        'and A. G. Ramirez, "On the performance of cloud-based mHealth '
        "applications: A methodology on measuring service response time and a "
        'case study," IEEE Access, vol. 10, pp. 53208\u201353224, 2022.',
        "[8] G. R. Gunnam, D. Inupakutika, R. Mundlamuri, S. Kaghyan, and D. "
        'Akopian, "Assessing performance of cloud-based heterogeneous chatbot '
        'systems and a case study," IEEE Access, vol. 12, pp. 81631\u201381645, '
        "2024.",
        "[9] L. Moroney, The Definitive Guide to Firebase. Berkeley, CA, USA: "
        "Apress, 2017.",
        "[10] E. Gamma, R. Helm, R. Johnson, and J. Vlissides, Design "
        "Patterns: Elements of Reusable Object-Oriented Software. Reading, "
        "MA, USA: Addison-Wesley, 1994.",
        "[11] N. Megiddo and D. S. Modha, \u201cARC: A self-tuning, low overhead "
        "replacement cache,\u201d in Proc. USENIX FAST, 2003, pp. 115\u2013130.",
        "[12] M. L. Ybarra, M. Holtrop, T. B. Prescott, and D. Strong, "
        "\u201cProcess evaluation of a mHealth program: Lessons learned from Stop "
        "My Smoking USA,\u201d Patient Education and Counseling, vol. 97, no. 2, "
        "pp. 239\u2013243, 2014.",
        "[13] G. R. Gunnam, D. Akopian, A. Adiraju, et al., \u201cDesign and "
        "implementation of a cross-platform RCS messaging application for "
        "mHealth,\u201d Int. J. Computer Applications, vol. 186, 2024.",
        "[14] A. Adiraju, \u201cDesign and implementation of a cross-platform RCS "
        "messaging application for smoking cessation mHealth intervention,\u201d "
        "M.S. thesis, Dept. Elect. Comput. Eng., Univ. Texas San Antonio, "
        "San Antonio, TX, USA, 2025.",
        "[15] J. B. Bricker et al., \u201cConversational chatbot for cigarette "
        "smoking cessation: Results from the 11-step user-centered design "
        "development process and randomized controlled trial,\u201d JMIR mHealth "
        "and uHealth, vol. 12, no. 1, e57318, 2024.",
        "[16] P. Lewis et al., \u201cRetrieval-augmented generation for "
        "knowledge-intensive NLP tasks,\u201d in Advances in Neural Information "
        "Processing Systems (NeurIPS), vol. 33, 2020, pp. 9459\u20139474.",
        "[17] S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, \u201cRAGAS: "
        "Automated evaluation of retrieval augmented generation,\u201d arXiv "
        "preprint arXiv:2309.15217, 2023.",
        "[18] E. Mellatdoust Pordel, D. Akopian, and L. Velez, \u201cWeb "
        "retrieval-augmented generation for a smoking cessation counseling "
        "assistant: Evaluation of faithfulness and latency,\u201d [Manuscript in "
        "preparation], 2024.",
    ]
    for ref in references:
        p = doc.add_paragraph(ref)
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.first_line_indent = Cm(-1)
        for run in p.runs:
            run.font.size = Pt(9)

    return doc


if __name__ == "__main__":
    out_path = Path(__file__).parent / "Quitxt_Implementation_Paper.docx"
    doc = build_document()
    doc.save(str(out_path))
    print(f"Saved: {out_path}")
