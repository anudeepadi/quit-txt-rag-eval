#!/usr/bin/env python3
"""
Generate IEEE-formatted Word document for:
Performance Benchmarking of a Cross-Platform Messaging System for mHealth Smoking Cessation

Based on the actual paper PDF content.
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_shading(cell, color: str) -> None:
    """Set background shading on a table cell."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)


def add_table_from_data(doc: Document, headers: list[str], rows: list[list[str]], caption: str = "") -> None:
    """Add a formatted table with optional caption and IEEE styling."""
    if caption:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(caption)
        run.font.size = Pt(9)
        run.font.name = "Times New Roman"
        run.bold = True

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'

    # Header row
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        set_cell_shading(hdr_cells[i], "D9E2F3")
        for paragraph in hdr_cells[i].paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(9)
                run.font.name = "Times New Roman"

    # Data rows
    for row_idx, row_data in enumerate(rows):
        row_cells = table.rows[row_idx + 1].cells
        for col_idx, cell_text in enumerate(row_data):
            row_cells[col_idx].text = cell_text
            for paragraph in row_cells[col_idx].paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Times New Roman"

    doc.add_paragraph()


def main():
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(10)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Performance Benchmarking of a Cross-Platform\nMessaging System for mHealth Smoking Cessation")
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.name = "Times New Roman"

    # Authors with affiliations
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = authors.add_run("Venkata Anudeep Adiraju")
    run.font.size = Pt(11)
    run.font.name = "Times New Roman"
    run = authors.add_run("*")
    run.font.size = Pt(11)
    run.font.superscript = True
    run = authors.add_run(", David Akopian")
    run.font.size = Pt(11)
    run = authors.add_run("*")
    run.font.size = Pt(11)
    run.font.superscript = True
    run = authors.add_run(", Ebrahim Melladoust")
    run.font.size = Pt(11)
    run = authors.add_run("*")
    run.font.size = Pt(11)
    run.font.superscript = True
    run = authors.add_run(", Patricia Chalela")
    run.font.size = Pt(11)
    run = authors.add_run("†")
    run.font.size = Pt(11)
    run.font.superscript = True
    run = authors.add_run(", and Vivian Cortez")
    run.font.size = Pt(11)
    run = authors.add_run("†")
    run.font.size = Pt(11)
    run.font.superscript = True

    # Affiliations
    affil1 = doc.add_paragraph()
    affil1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil1.add_run("*")
    run.font.size = Pt(9)
    run.font.superscript = True
    run = affil1.add_run("Department of Electrical and Computer Engineering,")
    run.font.size = Pt(9)
    run.font.name = "Times New Roman"

    affil2 = doc.add_paragraph()
    affil2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil2.add_run("The University of Texas at San Antonio, San Antonio, TX 78249, USA")
    run.font.size = Pt(9)
    run.font.name = "Times New Roman"

    affil3 = doc.add_paragraph()
    affil3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil3.add_run("Email: venkataanudeep.adiraju@my.utsa.edu; david.akopian@utsa.edu ")
    run.font.size = Pt(9)
    run.font.name = "Times New Roman"
    run = affil3.add_run("†")
    run.font.size = Pt(9)
    run.font.superscript = True
    run = affil3.add_run("Institute for Health Promotion Research,")
    run.font.size = Pt(9)

    affil4 = doc.add_paragraph()
    affil4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = affil4.add_run("The University of Texas Health Science Center at San Antonio, San Antonio, TX 78229, USA")
    run.font.size = Pt(9)
    run.font.name = "Times New Roman"

    doc.add_paragraph()

    # Abstract (two-column simulation with single column)
    abstract_heading = doc.add_paragraph()
    run = abstract_heading.add_run("Abstract")
    run.font.bold = True
    run.font.italic = True
    run.font.size = Pt(10)

    abstract_text = doc.add_paragraph(
        "Mobile health (mHealth) messaging applications require low-latency, reliable delivery, yet the architecture and "
        "client-side performance of production messaging systems remain poorly characterized. This paper presents the design, implementation, "
        "and performance evaluation of Quitxt, a cross-platform Flutter application for smoking cessation that combines real-time messaging "
        "with AI-enhanced responses. We describe the system architecture—including the rationale for selecting Flutter over React Native, "
        "a composition-based messaging service, and binary search message insertion—and benchmark key operations to confirm they remain well "
        "within a single frame budget. On the server side, we integrate a retrieval-augmented generation (RAG) layer that retrieves from a "
        "professionally curated smoking cessation knowledge base via ChromaDB and generates grounded responses through Gemini 2.0 Flash. "
        "The measurement framework and analysis scripts are open-source."
    )
    abstract_text.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for run in abstract_text.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    # Index Terms
    index_terms = doc.add_paragraph()
    run = index_terms.add_run("Index Terms")
    run.font.bold = True
    run.font.italic = True
    run.font.size = Pt(10)
    run = index_terms.add_run("—Cross-platform mobile development, Flutter, mHealth messaging, smoking cessation, "
                               "performance benchmarking, binary search insertion, retrieval-augmented generation")
    run.font.size = Pt(10)
    run.font.name = "Times New Roman"

    doc.add_paragraph()

    # I. INTRODUCTION
    section1 = doc.add_heading("I. INTRODUCTION", level=1)
    section1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section1.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    intro_p1 = doc.add_paragraph(
        "SMOKING kills over eight million people annually [1]. Text-based mobile interventions have shown 50–60% higher quit rates "
        "compared to controls [2], making mHealth messaging a practical tool for smoking cessation. Modern messaging applications go beyond "
        "plain SMS by incorporating read receipts, typing indicators, rich media, and suggested reply buttons. These features make interactions "
        "more engaging than plain text, but they also make the messaging system more complex."
    )
    intro_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    intro_p2 = doc.add_paragraph(
        "Cross-platform mHealth messaging applications face performance demands that generic mobile apps do not. The system must deliver "
        "messages with low latency during real-time conversations, keep messages in the right order, maintain a responsive UI while handling "
        "background network traffic, and avoid memory bloat during sessions that can last 30 minutes. If the app becomes sluggish during a "
        "conversation, the user may disengage [3]."
    )
    intro_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    intro_p3 = doc.add_paragraph(
        "Flutter, Google's cross-platform toolkit, compiles to native code from a single Dart codebase and renders through the Skia engine [4]. "
        "Prior benchmarks have compared Flutter to native development in general [5], [6], but none have measured Flutter's behavior in a "
        "real-time messaging context where background network operations, message ordering, and database synchronization all compete with the "
        "rendering pipeline."
    )
    intro_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    intro_p4 = doc.add_paragraph(
        "Most mHealth messaging apps run on Firebase Firestore, which pushes data changes to connected clients via real-time listeners and "
        "handles caching and offline persistence automatically. The client-side cost of keeping a sorted, deduplicated message list in sync "
        "with Firestore's stream—while rendering a responsive UI—has not been characterized for messaging workloads."
    )
    intro_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Contributions
    contrib_heading = doc.add_heading("A. Contributions", level=2)
    for run in contrib_heading.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    contrib_text = doc.add_paragraph("The paper makes four contributions:")
    contrib_text.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    contrib_list = [
        "A SQLite-backed metrics service embedded in the application that captures timing measurements at sub-millisecond precision and exports to CSV for offline analysis.",
        "Empirical before/after benchmarks of binary-search-guided message insertion (Section V-A) alongside instrumented design patterns: composition-based service architecture (Section III-A), multi-layer caching with LRU eviction (Section III-D), and platform-specific HTTP client configuration with isolate-based link preview parsing (Sections III-C, III-E). Sorting benchmarks span 700 runs across 14 configurations.",
        "Open-source R and Python analysis scripts that run ANOVA, Tukey HSD post-hoc tests, and Shapiro-Wilk normality checks, and produce IEEE-formatted figures.",
        "A server-side RAG pipeline that retrieves from the Gemini Protocol knowledge base (4,847 human-curated Q&A pairs) via ChromaDB and generates grounded responses through Gemini 2.0 Flash, integrated into the production messaging flow."
    ]

    for i, item in enumerate(contrib_list, 1):
        p = doc.add_paragraph(f"{i}) {item}", style='List Number')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in p.runs:
            run.font.size = Pt(10)

    organization = doc.add_paragraph(
        "The rest of the paper is organized as follows. Section II surveys related work. Section III details the system architecture, "
        "including the rationale for selecting Flutter. Section IV describes the experimental methodology. Section V reports client-side "
        "performance results. Section VI describes the AI-enhanced messaging pipeline. Section VII discusses findings, and Section VIII concludes."
    )
    organization.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # II. RELATED WORK
    section2 = doc.add_heading("II. RELATED WORK", level=1)
    section2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section2.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    # A. mHealth Messaging for Smoking Cessation
    subsec2a = doc.add_heading("A. mHealth Messaging for Smoking Cessation", level=2)
    for run in subsec2a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    related_p1 = doc.add_paragraph(
        "Whittaker et al. [2] analyzed 26 randomized controlled trials with over 33,000 participants and found that mobile cessation "
        "interventions increased quit rates by 50–60%. SmokefreeTXT, the NCI's SMS-based program, sustained engagement over six-week "
        "periods [12]. These studies measure intervention outcomes but say nothing about the performance of the messaging systems delivering them."
    )
    related_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    related_p2 = doc.add_paragraph(
        "More recently, Bricker et al. [15] developed QuitBot, a conversational chatbot for smoking cessation that uses a library of "
        "11,000 question-answer pairs with a fine-tuned GPT-3.5 fallback. In a pilot RCT, QuitBot achieved 63% 30-day point-prevalence "
        "abstinence versus 38.5% for the NCI's SmokefreeTXT (OR 2.58, 95% CI [1.34, 4.99]). Their work demonstrates that AI-enhanced "
        "conversational delivery improves engagement over linear messaging, but does not address system performance under load or cross-platform "
        "deployment challenges."
    )
    related_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    related_p3 = doc.add_paragraph(
        "Moving beyond plain SMS to app-based messaging adds suggested replies, carousels, and read receipts, which make interactions more "
        "engaging but also more computationally expensive. To our knowledge, no prior work has benchmarked client-side performance in a "
        "cross-platform mHealth messaging system."
    )
    related_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # B. Cross-Platform Mobile Performance
    subsec2b = doc.add_heading("B. Cross-Platform Mobile Performance", level=2)
    for run in subsec2b.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    related_p4 = doc.add_paragraph(
        "Biørn-Hansen et al. [5] compared React Native, Flutter, and native Android/iOS, finding that Flutter matched native frame rates but "
        "used more memory on Android. Majchrzak et al. [6] benchmarked progressive web apps against native approaches on startup time, rendering, "
        "and memory."
    )
    related_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    related_p5 = doc.add_paragraph(
        "Flutter-specific studies have measured rendering pipeline efficiency [4], widget rebuild cost, and platform channel overhead. These "
        "focus on UI workloads. None measure what happens when background network operations, message ordering, and database synchronization all "
        "compete with the rendering pipeline at the same time, which is the normal state of a messaging app."
    )
    related_p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # C. Firebase in Mobile Applications
    subsec2c = doc.add_heading("C. Firebase in Mobile Applications", level=2)
    for run in subsec2c.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    related_p6 = doc.add_paragraph(
        "Firestore's real-time sync has made it a common backend for mobile messaging. Moroney [9] covered Firestore query performance and "
        "offline caching. Inupakutika et al. [7] built a four-block testbed for mHealth application performance evaluation, measuring service "
        "response time under controlled concurrent load with ANOVA and Tukey HSD post-hoc tests. We adapt their testbed design for our Firebase "
        "messaging system."
    )
    related_p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    related_p7 = doc.add_paragraph(
        "Gunnam et al. [8] extended that work to heterogeneous chatbot systems, adding throughput and concurrent-user scaling as metrics. They "
        "found that latency under load degrades non-linearly, with sharp inflection points where performance drops off. This finding is why we "
        "calibrate our Firebase load levels empirically rather than picking arbitrary thresholds."
    )
    related_p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # D. Message Ordering and Caching
    subsec2d = doc.add_heading("D. Message Ordering and Caching", level=2)
    for run in subsec2d.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    related_p8 = doc.add_paragraph(
        "The naive approach to message ordering re-sorts the entire list on each insertion: O(n log n) per message. Binary search insertion runs "
        "in O(log n), but its practical effect in a Flutter messaging context, where the sorted list feeds a reactive widget tree, has not been "
        "measured."
    )
    related_p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    related_p9 = doc.add_paragraph(
        "Client-side caching in messaging apps trades memory for lookup speed. LRU eviction is standard [11]. How an application-level cache "
        "interacts with Firebase's own client-side persistence layer—both caching independently—has not been characterized for messaging workloads."
    )
    related_p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # E. Gap in Literature
    subsec2e = doc.add_heading("E. Gap in Literature", level=2)
    for run in subsec2e.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    related_p10 = doc.add_paragraph(
        "mHealth messaging efficacy, cross-platform benchmarks, and Firebase optimization have each been studied in isolation, but client-side "
        "performance of a deployed mHealth messaging system has not been characterized. Similarly, existing mHealth chatbot systems rely on static "
        "QnA libraries [15] or cloud-hosted LLM APIs without domain-specific grounding; none use retrieval-augmented generation [16] with a curated "
        "knowledge base. We address both gaps by instrumenting a deployed mHealth messaging app and integrating a curated-knowledge RAG layer into "
        "its production pipeline."
    )
    related_p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # III. SYSTEM ARCHITECTURE
    section3 = doc.add_heading("III. SYSTEM ARCHITECTURE", level=1)
    section3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section3.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    arch_intro = doc.add_paragraph(
        "Quitxt is a cross-platform messaging application for smoking cessation [13], [14], running on Android and iOS from a single codebase "
        "with Firebase Firestore for real-time message sync and Firebase Cloud Messaging (FCM) for push notifications. Fig. 1 shows the end-to-end "
        "system architecture."
    )
    arch_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Framework Selection: Flutter
    subsec3a = doc.add_heading("A. Framework Selection: Flutter", level=2)
    for run in subsec3a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    flutter_p1 = doc.add_paragraph(
        "We evaluated Flutter, React Native, and native development before selecting Flutter for the following reasons. First, Flutter compiles "
        "to native ARM code via ahead-of-time (AOT) compilation, eliminating the JavaScript bridge that adds latency in React Native's architecture [4]. "
        "For a real-time messaging application where every millisecond in the rendering pipeline matters, this is a meaningful advantage. Second, "
        "Flutter's Skia-based rendering engine produces consistent UI across platforms without relying on platform-native widgets, which simplifies "
        "testing and reduces platform-specific bugs. Third, Dart's single-threaded event loop with isolate-based concurrency maps well to the messaging "
        "use case: the main isolate handles UI and Firestore listeners, while CPU-bound tasks (link preview parsing, performance metrics collection) "
        "run on background isolates without shared-memory concurrency issues. Prior cross-platform benchmarks confirm that Flutter matches native frame "
        "rates while using more memory on Android [5]; we accept this trade-off given the UI consistency benefit."
    )
    flutter_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    flutter_p2 = doc.add_paragraph(
        "The subsections below describe each architectural component and the design decisions whose performance we benchmark in Section V."
    )
    flutter_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # B. Composition-Based Messaging Service
    subsec3b = doc.add_heading("B. Composition-Based Messaging Service", level=2)
    for run in subsec3b.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    composition_p1 = doc.add_paragraph(
        "The messaging subsystem uses a composition pattern [10] instead of a single monolithic service. ComposedMessagingService delegates to "
        "three specialized services:"
    )
    composition_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    services_list = [
        "HttpMessageService: HTTP transport to the messaging server, with platform-specific client configuration.",
        "FirestoreMessageService: Real-time Firestore listeners for incoming messages and server responses.",
        "MessageCacheService: In-memory message caching with content-based deduplication."
    ]

    for item in services_list:
        p = doc.add_paragraph(f"• {item}")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in p.runs:
            run.font.size = Pt(10)

    composition_p2 = doc.add_paragraph(
        "This separation lets us optimize and test each layer independently. The send flow works as follows:"
    )
    composition_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    send_flow = [
        "ComposedMessagingService.sendMessage() receives user input text.",
        "A unique message identifier is generated using UUID v4.",
        "The message is persisted to Firestore via FirestoreMessageService.",
        "The message is cached via MessageCacheService.",
        "An HTTP POST request is dispatched to the server via HttpMessageService.",
        "The server response arrives asynchronously via the Firestore real-time listener."
    ]

    for i, item in enumerate(send_flow, 1):
        p = doc.add_paragraph(f"{i}) {item}", style='List Number')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in p.runs:
            run.font.size = Pt(10)

    composition_p3 = doc.add_paragraph(
        "Because each layer is a separate service, we can instrument and time them independently. Fig. 2 illustrates the complete message send and "
        "response lifecycle."
    )
    composition_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # C. Binary Search Message Insertion
    subsec3c = doc.add_heading("C. Binary Search Message Insertion", level=2)
    for run in subsec3c.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    binary_p1 = doc.add_paragraph(
        "A chat UI needs a chronologically sorted message list. The simple approach, appending and re-sorting, costs O(n log n) per insertion. "
        "Once conversations pass a few hundred messages, the re-sort becomes visible as UI jank."
    )
    binary_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    binary_p2 = doc.add_paragraph(
        "We use O(log n) binary search insertion in the ChatProvider class. The _findInsertionIndex() method binary-searches the sorted list to "
        "find where the new message belongs:"
    )
    binary_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Code snippet
    code = doc.add_paragraph()
    code_text = """int _findInsertionIndex(ChatMessage msg) {
  int low = 0, high = _messages.length;
  while (low < high) {
    final mid = (low + high) ~/ 2;
    if (_comparator(_messages[mid], msg) <= 0)
      low = mid + 1;
    else
      high = mid;
  }
  return low;
}"""
    run = code.add_run(code_text)
    run.font.name = "Courier New"
    run.font.size = Pt(8)

    binary_p3 = doc.add_paragraph(
        "The comparator sorts by timestamp ascending, breaking ties by message ID. After finding the index, List.insert() shifts subsequent "
        "elements in O(n) time. The net cost is O(n) per insertion—O(log n) to locate the position via binary search, O(n) to shift—but the shift "
        "is a contiguous memory move with a much smaller constant factor than the O(n log n) comparison-heavy full-sort, yielding the empirically "
        "observed speedup. For benchmarking, we retain a baselineFullSort() method that copies the list, appends the message, and re-sorts, so we "
        "can compare both approaches on identical data."
    )
    binary_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # TABLE I: Platform-Specific HTTP Configurations
    add_table_from_data(
        doc,
        caption="TABLE I\nPLATFORM-SPECIFIC HTTP CONFIGURATIONS",
        headers=["Parameter", "Android", "iOS"],
        rows=[
            ["HTTP Client", "IOClient", "Default http.Client"],
            ["Connection", "Close", "Keep-Alive"],
            ["Timeout", "15 s", "8 s"],
            ["Idle Timeout", "30 s", "N/A"],
            ["App Check", "Play Integrity", "DeviceCheck"]
        ]
    )

    # D. Platform-Specific HTTP Configuration
    subsec3d = doc.add_heading("D. Platform-Specific HTTP Configuration", level=2)
    for run in subsec3d.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    http_p1 = doc.add_paragraph(
        "Flutter's http package abstracts platform differences, but Android and iOS handle HTTP connections differently enough to affect message "
        "delivery latency. We configure each platform separately."
    )
    http_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    http_p2 = doc.add_paragraph(
        "Android uses IOClient wrapping Dart's HttpClient with Connection: close headers, a 15-second timeout, and a 30-second idle timeout. "
        "We close connections explicitly because Android's connection pooling occasionally held stale connections, causing intermittent timeouts on "
        "cellular networks."
    )
    http_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    http_p3 = doc.add_paragraph(
        "iOS uses the default http.Client with Connection: keep-alive and an 8-second timeout. iOS's URLSession manages connection reuse well on "
        "its own, and the shorter timeout accounts for iOS's more aggressive background task limits."
    )
    http_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    http_p4 = doc.add_paragraph("Table I summarizes the platform-specific configurations.")
    http_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # E. Multi-Layer Caching Architecture
    subsec3e = doc.add_heading("E. Multi-Layer Caching Architecture", level=2)
    for run in subsec3e.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    cache_p1 = doc.add_paragraph("The application has two caching layers that interact with each other.")
    cache_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    cache_p2 = doc.add_paragraph(
        "MessageCacheService is an in-memory LRU cache holding up to 1,000 messages. Messages are indexed by ID for direct lookup and by a "
        "content-timestamp composite key for deduplication. When full, the 100 oldest entries are evicted. We time cache operations using Dart's "
        "Stopwatch at microsecond resolution."
    )
    cache_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    cache_p3 = doc.add_paragraph(
        "Firestore's built-in persistence caches documents locally for offline access and reduced round-trips. We tag each response with "
        "doc.metadata.isFromCache so we can analyze latency separately for cache-served and server-fetched responses."
    )
    cache_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    cache_p4 = doc.add_paragraph(
        "A message may come from the application cache (fastest), the Firebase client cache (fast), or the Firebase server (variable, depending on "
        "load and network). These layers interact, and the compound behavior matters for latency analysis."
    )
    cache_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # F. Isolate-Based Link Preview Processing
    subsec3f = doc.add_heading("F. Isolate-Based Link Preview Processing", level=2)
    for run in subsec3f.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    link_p1 = doc.add_paragraph(
        "When messages contain URLs, the app fetches HTML and parses it for link previews. HTML parsing is CPU-bound and will cause UI jank if run "
        "on the main isolate. We offload it using Flutter's compute() function, which spawns a background isolate for the HTML extraction of Open Graph, "
        "Twitter Card, and fallback metadata. Results are cached in a 200-entry LRU. Pending requests are deduplicated with a Completer-based queue so "
        "the same URL is never fetched twice concurrently."
    )
    link_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # G. Frame Rendering Monitoring
    subsec3g = doc.add_heading("G. Frame Rendering Monitoring", level=2)
    for run in subsec3g.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    frame_p1 = doc.add_paragraph(
        "Flutter exposes per-frame timing via SchedulerBinding.addTimingsCallback. We record build duration (widget tree construction) and raster "
        "duration (GPU rendering) for each frame. Frames exceeding 16.67 ms total (the 60 fps budget) are classified as jank. This gives a direct "
        "measure of UI responsiveness during chat interactions."
    )
    frame_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # H. Security: Firebase App Check
    subsec3h = doc.add_heading("H. Security: Firebase App Check", level=2)
    for run in subsec3h.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    security_p1 = doc.add_paragraph(
        "Firebase App Check verifies that requests come from genuine app instances. On Android it uses the Play Integrity API; on iOS, DeviceCheck. "
        "We include App Check initialization in our startup timing because it adds measurable latency to cold start."
    )
    security_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # I. Application Interface
    subsec3i = doc.add_heading("I. Application Interface", level=2)
    for run in subsec3i.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    ui_p1 = doc.add_paragraph(
        "Fig. 3 shows four representative screens from the Quitxt application. The welcome screen (a) greets first-time users with a message input "
        "field connected to the Firestore pipeline. The active chat session (b) shows an AI message with an isolate-parsed link preview, a binary poll "
        "with tappable response buttons, and an AI-generated motivational reply. The About screen (c) describes the Quitxt program and its bilingual "
        "support. The Help & Quick Actions screen (d) demonstrates the bilingual keyword panel (English and Spanish), allowing users to send protocol "
        "keywords—such as Helpnow, Crave, Slip, or Badmood—with a single tap, triggering targeted RAG-grounded responses from the server."
    )
    ui_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # IV. EXPERIMENTAL METHODOLOGY
    section4 = doc.add_heading("IV. EXPERIMENTAL METHODOLOGY", level=1)
    section4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section4.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    method_intro = doc.add_paragraph(
        "This section describes the measurement infrastructure, experimental design, and statistical methods."
    )
    method_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Performance Metrics Service
    subsec4a = doc.add_heading("A. Performance Metrics Service", level=2)
    for run in subsec4a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    metrics_p1 = doc.add_paragraph(
        "We embedded a PerformanceMetricsService singleton in the app to capture timing measurements at runtime. The service stores measurements in a "
        "local SQLite database (performance_metrics.db) with no network overhead, buffers 50 measurements in memory before flushing to disk every 10 "
        "seconds, and is controlled by a compile-time constant PERF_METRICS_ENABLED tied to Dart's kDebugMode for zero overhead in production. Collected "
        "data exports to CSV for offline analysis in R and Python."
    )
    metrics_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    metrics_p2 = doc.add_paragraph("Table II defines the eight metric types captured.")
    metrics_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # TABLE II: Performance Metric Types
    add_table_from_data(
        doc,
        caption="TABLE II\nPERFORMANCE METRIC TYPES AND DEFINITIONS",
        headers=["Metric Type", "Definition"],
        rows=[
            ["appStartup", "Time from WidgetsFlutterBinding initialization to first frame render, decomposed into seven checkpoints (T0–T7)."],
            ["messageDelivery", "End-to-end latency Tresponse = Treceived − Tsent, where Tsent is recorded before HTTP dispatch and Treceived upon Firestore listener callback."],
            ["messageSort", "Duration of message list insertion: binary search O(log n) and baseline full-sort O(n log n)."],
            ["httpRoundtrip", "HTTP POST round-trip, differentiated by platform path."],
            ["cacheOperation", "Cache lookup, insertion, and eviction timing."],
            ["memoryUsage", "Resident Set Size sampled every 5 s via ProcessInfo.currentRss."],
            ["frameTime", "Per-frame build + raster duration, classified as normal (≤16.67 ms) or jank (>16.67 ms)."],
            ["linkPreview", "Duration of isolate-based HTML parsing for link preview generation."]
        ]
    )

    # TABLE III: Application Startup Checkpoints
    add_table_from_data(
        doc,
        caption="TABLE III\nAPPLICATION STARTUP CHECKPOINTS",
        headers=["ID", "Event", "Measures"],
        rows=[
            ["T0", "ensureInitialized()", "Absolute start"],
            ["T1", "Platform optimizations", "iOS/Android init"],
            ["T2", "dotenv.load()", "Environment config"],
            ["T3", "Firebase.initializeApp()", "Firebase core init"],
            ["T4", "AppCheck.activate()", "Security attestation"],
            ["T5", "AppCacheManager.init()", "Cache manager setup"],
            ["T6", "getFcmToken()", "Push notification token"],
            ["T7", "First frame callback", "UI ready"]
        ]
    )

    # B. Startup Timing Checkpoints
    subsec4b = doc.add_heading("B. Startup Timing Checkpoints", level=2)
    for run in subsec4b.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    startup_p1 = doc.add_paragraph(
        "Cold-start time is split into seven checkpoints, timed with Dart's monotonic Stopwatch to avoid NTP clock correction artifacts. Table III "
        "lists each checkpoint."
    )
    startup_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    startup_p2 = doc.add_paragraph(
        "Total startup time is Tstartup = T7−T0. Each sub-interval (Ti+1 − Ti) identifies the dominant contributor to startup latency. Fig. 4 "
        "visualizes the checkpoint sequence; the shaded regions indicate the phases expected to dominate on physical devices."
    )
    startup_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # C. Message Delivery Latency
    subsec4c = doc.add_heading("C. Message Delivery Latency (Tresponse)", level=2)
    for run in subsec4c.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    delivery_p1 = doc.add_paragraph(
        "Tresponse measures the time from message dispatch to server response receipt:"
    )
    delivery_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    equation1 = doc.add_paragraph()
    equation1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = equation1.add_run("Tresponse = Treceived − Tsent")
    run.font.italic = True
    run.font.size = Pt(10)
    run = equation1.add_run("                    (1)")
    run.font.size = Pt(10)

    delivery_p2 = doc.add_paragraph(
        "Tsent is recorded just before HttpMessageService.sendToServer() and Treceived when the Firestore listener receives the server's response "
        "document matching the original message UUID. This captures the full round-trip: HTTP transport, server processing, Firestore write, and "
        "real-time sync back to the client. We also record doc.metadata.isFromCache to separate cache-served responses from server-fetched responses."
    )
    delivery_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # D. Execution Environment
    subsec4d = doc.add_heading("D. Execution Environment", level=2)
    for run in subsec4d.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    exec_p1 = doc.add_paragraph(
        "The sorting and cache benchmarks reported in Section V run on the Dart VM (macOS, Apple Silicon M1, Dart 3.10.7) using Flutter's "
        "integration_test framework. Each benchmark invokes the same production code paths that the mobile application uses at runtime. Collected "
        "SQLite databases are exported and processed through R and Python analysis scripts. On-device validation on physical Android and iOS hardware, "
        "including end-to-end message delivery latency under Firebase backend load following the testbed methodology of Inupakutika et al. [7], is "
        "left for future work."
    )
    exec_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # E. Experiment Configurations
    subsec4e = doc.add_heading("E. Experiment Configurations", level=2)
    for run in subsec4e.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    config_p1 = doc.add_paragraph(
        "Table IV summarizes the experimental configurations. Each configuration runs 50 times with 10 additional warm-up iterations (discarded) to "
        "stabilize JIT compilation variance on the Dart VM. The n=50 sample size exceeds CLT requirements and provides tighter confidence intervals than "
        "the minimum n=30."
    )
    config_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # TABLE IV: Experiment Configuration Matrix
    add_table_from_data(
        doc,
        caption="TABLE IV\nEXPERIMENT CONFIGURATION MATRIX",
        headers=["Experiment", "Configs", "Runs", "Total"],
        rows=[
            ["Sorting Scalability", "10", "50", "500"],
            ["App Startup", "4", "50", "200"],
            ["Total", "14", "", "700"]
        ]
    )

    # F. Statistical Methods
    subsec4f = doc.add_heading("F. Statistical Methods", level=2)
    for run in subsec4f.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    stats_p1 = doc.add_paragraph(
        "All statistical analyses follow Inupakutika et al. [7]. Descriptive statistics include mean, standard deviation, median, min, max, and "
        "skewness for each configuration."
    )
    stats_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    stats_p2 = doc.add_paragraph("We compute 95% confidence intervals as:")
    stats_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    equation2 = doc.add_paragraph()
    equation2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = equation2.add_run("CI = x̄ ± t")
    run.font.italic = True
    run.font.size = Pt(10)
    run = equation2.add_run("0.025, n−1")
    run.font.size = Pt(7)
    run.font.subscript = True
    run = equation2.add_run(" · s/√n")
    run.font.italic = True
    run.font.size = Pt(10)
    run = equation2.add_run("                    (2)")
    run.font.size = Pt(10)

    stats_p3 = doc.add_paragraph(
        "where x̄ is the sample mean, s the sample standard deviation (with Bessel's correction), and t0.025, n−1 the critical value from Student's "
        "t-distribution with n−1 degrees of freedom. With n = 50 per configuration, t0.025, 49 = 2.010."
    )
    stats_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    stats_p4 = doc.add_paragraph(
        "Normality testing uses the Shapiro-Wilk test (α = 0.05). If normality holds, one-way or multiway ANOVA tests for significant group differences; "
        "otherwise Kruskal-Wallis replaces ANOVA. When ANOVA rejects H0 (p < 0.05), Tukey HSD identifies which pairs differ. For non-parametric cases, "
        "pairwise Wilcoxon rank-sum tests with Holm correction are used."
    )
    stats_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # V. RESULTS
    section5 = doc.add_heading("V. RESULTS", level=1)
    section5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section5.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    results_intro = doc.add_paragraph(
        "All benchmarks were executed on the host Dart VM (macOS, Apple Silicon M1, Dart 3.10.7). Each of the 29 configurations was run 50 times "
        "(n = 50) following 10 warm-up iterations discarded to stabilize JIT compilation. We report means, medians, 95th percentiles, and 95% confidence "
        "intervals computed using Equation 2."
    )
    results_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Message Sorting Scalability
    subsec5a = doc.add_heading("A. Message Sorting Scalability", level=2)
    for run in subsec5a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    # TABLE V: Message Sorting Latency
    add_table_from_data(
        doc,
        caption="TABLE V\nMESSAGE SORTING LATENCY (n = 50, VALUES IN µS)",
        headers=["N", "Method", "Mean", "Med.", "P95", "95% CI"],
        rows=[
            ["10", "Bin. Insert", "4.5", "3.0", "12.0", "[3.5, 5.4]"],
            ["10", "Full Sort", "2.8", "1.0", "6.0", "[0.8, 4.7]"],
            ["50", "Bin. Insert", "2.7", "2.0", "6.0", "[2.4, 3.0]"],
            ["50", "Full Sort", "15.2", "8.5", "39.0", "[9.3, 21.0]"],
            ["100", "Bin. Insert", "1.9", "1.0", "7.0", "[0.8, 3.0]"],
            ["100", "Full Sort", "13.6", "10.0", "27.0", "[10.0, 17.3]"],
            ["500", "Bin. Insert", "6.9", "4.0", "22.0", "[2.2, 11.6]"],
            ["500", "Full Sort", "44.1", "26.0", "124.0", "[34.3, 53.9]"],
            ["1000", "Bin. Insert", "4.4", "4.0", "10.0", "[3.5, 5.3]"],
            ["1000", "Full Sort", "84.9", "60.0", "187.0", "[65.7, 104.0]"]
        ]
    )

    sorting_p1 = doc.add_paragraph(
        "Table V reports binary search insertion and full-sort latency at five message counts in microseconds. Binary insertion remains nearly constant "
        "across all N values (median 1–4 µs), confirming O(log n) behavior. Full sort grows from a median of 1 µs at N=10 to 60 µs at N=1000, consistent "
        "with O(n log n) scaling."
    )
    sorting_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    sorting_p2 = doc.add_paragraph(
        "Fig. 5 plots the scalability trend. At N=10, the overhead of the binary search comparisons makes it comparable to the sort baseline (median 3 µs "
        "vs. 1 µs), with overlapping confidence intervals. Binary insertion's advantage emerges at N ≥ 50: the median speedup grows from 4.3× at N=50 to "
        "15× at N=1000. By mean, the speedup at N=1000 reaches 19× (85 µs vs. 4.4 µs). Both methods operate well within a single 16.67 ms frame budget "
        "even in worst-case scenarios: the full sort's P95 at N=1000 is 187 µs, while binary insertion stays at 10 µs."
    )
    sorting_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # B. Application Startup Performance
    subsec5b = doc.add_heading("B. Application Startup Performance", level=2)
    for run in subsec5b.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    startup_results_p1 = doc.add_paragraph(
        "We measured the Dart-level construction cost of two key components: ChatProvider instantiation and MessageCacheService initialization with 100 "
        "inserts. ChatProvider construction averaged 250 µs (median 231 µs, P95 456 µs, 95% CI [219, 281]). Cache initialization averaged 74 µs (median "
        "64 µs, P95 167 µs, 95% CI [64, 83]). Both are negligible relative to full cold-start time, which on physical devices is dominated by Firebase "
        "initialization (T3), App Check attestation (T4), and FCM token retrieval (T6) as described in Table III. Full T0–T7 profiling on mobile hardware "
        "remains future work."
    )
    startup_results_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # VI. AI-ENHANCED MESSAGING
    section6 = doc.add_heading("VI. AI-ENHANCED MESSAGING", level=1)
    section6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section6.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    ai_intro = doc.add_paragraph(
        "Quitxt includes a server-side retrieval-augmented generation (RAG) layer [16] that grounds its AI responses in domain-specific evidence. Where "
        "QuitBot [15] matches against a fixed library of 11,000 QnA pairs, Quitxt retrieves relevant content from a vector index for each query and "
        "generates a grounded response on the fly using Gemini 2.0 Flash. The end-to-end pipeline works as follows: (1) the Flutter client sends a user "
        "message through the Firestore pipeline described in Section III-A; (2) a Firebase Cloud Function receives the message and queries a ChromaDB "
        "vector store indexed with the Gemini Protocol knowledge base; (3) the top-k retrieved chunks are assembled into a structured prompt and submitted "
        "to Gemini 2.0 Flash (gemini-2.0-flash-exp); and (4) the generated response is written back to Firestore, where the client's real-time listener "
        "delivers it to the UI. RAG processing time is therefore part of the measured Tresponse."
    )
    ai_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Knowledge Base Construction
    subsec6a = doc.add_heading("A. Knowledge Base Construction", level=2)
    for run in subsec6a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    kb_p1 = doc.add_paragraph(
        "The production knowledge base is the Human-Curated dataset (n = 4,847 Q&A pairs), professionally curated and verified against the Gemini "
        "Protocol—a structured smoking cessation framework developed by Dr. Louis Willis that encodes motivational interviewing (MI) strategies, "
        "pharmacotherapy guidance (NRT, varenicline, bupropion), behavioral coping techniques, and relapse prevention protocols. The dataset was refined "
        "iteratively: domain experts reviewed retrieval quality metrics after each round of edits and adjusted the corpus to improve downstream RAG "
        "performance."
    )
    kb_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    kb_p2 = doc.add_paragraph(
        "The dataset is indexed in a ChromaDB vector store using cosine similarity over sentence embeddings. At inference, the top-k (k = 3) most similar "
        "chunks are retrieved and injected into a structured prompt template alongside the user query and up to five prior turns of conversation history. "
        "The prompt instructs the LLM to ground its response in the retrieved evidence while maintaining a conversational tone. Gemini 2.0 Flash "
        "(gemini-2.0-flash-exp) generates the response, chosen for its low latency and strong instruction-following in health domains. The generated response "
        "is written back to Firestore, where the client's real-time listener delivers it to the UI."
    )
    kb_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    kb_p3 = doc.add_paragraph(
        "Because embeddings are pre-computed and the ChromaDB index is served locally alongside the server application, vector retrieval adds minimal "
        "overhead (≈150 ms measured). The dominant latency component is LLM generation, which varies with response length and model load. Fig. 6 details "
        "the retrieval and generation pipeline. Formal evaluation of response quality—including faithfulness, hallucination rate, and retrieval precision "
        "using the RAGAS framework [17]—is the subject of a companion study currently in preparation [18]."
    )
    kb_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # VII. DISCUSSION
    section7 = doc.add_heading("VII. DISCUSSION", level=1)
    section7.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section7.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    # A. Comparison with Prior Work
    subsec7a = doc.add_heading("A. Comparison with Prior Work", level=2)
    for run in subsec7a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    disc_p1 = doc.add_paragraph(
        "Inupakutika et al. [7] and Gunnam et al. [8] measured server-side response latency for cloud-based chatbot systems but did not examine "
        "client-side costs. Our sorting benchmarks address that gap: the 15× median speedup from binary insertion at N=1000 shows that client-side "
        "algorithmic choices affect message ordering latency independently of server-side factors."
    )
    disc_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    disc_p2 = doc.add_paragraph(
        "Bricker et al. [15] demonstrated the efficacy of conversational chatbot delivery (QuitBot) over linear SMS, using a static library of 11,000 "
        "QnA pairs with GPT-3.5 fallback. Quitxt takes a different approach: the Gemini Protocol knowledge base is indexed in ChromaDB and used by "
        "Gemini 2.0 Flash to generate grounded responses on the fly, without hand-authored templates. Formal evaluation of response quality is the "
        "subject of a companion study [18]."
    )
    disc_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # B. Architectural Implications
    subsec7b = doc.add_heading("B. Architectural Implications", level=2)
    for run in subsec7b.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    arch_impl_p1 = doc.add_paragraph(
        "The composition-based architecture (Section III-B) enables independent measurement and optimization of each subsystem. Message sorting has the "
        "widest dynamic range: full-sort latency grows roughly 30× from N=10 to N=1000, while binary insertion stays flat. The choice of Flutter over "
        "React Native (Section III-A) eliminates the JavaScript bridge, and isolate-based background processing keeps CPU-bound tasks (link preview parsing, "
        "metrics collection) off the main rendering thread. The platform-specific HTTP configuration (Section III-C) reflects how Android and iOS handle "
        "connection pooling differently—a cross-platform trade-off whose latency impact warrants quantification on physical devices."
    )
    arch_impl_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # C. Deployment Implications
    subsec7c = doc.add_heading("C. Deployment Implications", level=2)
    for run in subsec7c.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    deploy_p1 = doc.add_paragraph(
        "Client-side sorting operations complete in under 200 µs even at the 95th percentile for N=1000—well below the 100 ms perception threshold [3]. "
        "The dominant contributor to user-perceived latency is Tresponse, the server round-trip including RAG retrieval and LLM generation."
    )
    deploy_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # D. Threats to Validity
    subsec7d = doc.add_heading("D. Threats to Validity", level=2)
    for run in subsec7d.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    threats_p1 = doc.add_paragraph(
        "Internal validity: We use Dart's monotonic Stopwatch to avoid clock corrections, and a fixed random seed (42) ensures reproducible test data "
        "generation across runs. JIT warm-up variance is mitigated by discarding 10 warm-up iterations before each 50-iteration measurement block."
    )
    threats_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    threats_p2 = doc.add_paragraph(
        "External validity: Benchmarks run on the Dart VM on a host machine (Apple Silicon), not on mobile hardware. Mobile device performance will differ "
        "due to lower clock speeds and thermal throttling. The relative comparison (binary insert vs. full sort) should hold directionally, but absolute "
        "latencies will be higher."
    )
    threats_p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    threats_p3 = doc.add_paragraph(
        "Construct validity: Startup measurements capture Dart-level construction cost only and do not include Firebase initialization, App Check, or "
        "platform-specific setup that dominate real cold-start time."
    )
    threats_p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    threats_p4 = doc.add_paragraph(
        "Statistical validity: With n = 50 runs per configuration, sample sizes exceed CLT requirements. Microsecond-scale measurements are at the resolution "
        "limit of Dart's Stopwatch; speedup ratios should be interpreted as order-of-magnitude indicators rather than precise multipliers."
    )
    threats_p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # VIII. CONCLUSION
    section8 = doc.add_heading("VIII. CONCLUSION", level=1)
    section8.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in section8.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    conclusion_p1 = doc.add_paragraph(
        "We presented the design, implementation, and performance evaluation of Quitxt, a cross-platform Flutter messaging application for smoking cessation "
        "with an integrated RAG pipeline. The architectural choices—composition-based service decomposition, binary search message insertion, platform-specific "
        "HTTP configuration, and isolate-based background processing—keep all client-side operations well within a single frame budget. Binary search insertion "
        "achieves a 15× median speedup over full-sort at N=1000 messages, confirming that algorithmic optimization at the client layer eliminates message "
        "ordering as a latency contributor. The server-side RAG layer retrieves from a professionally curated knowledge base via ChromaDB and generates grounded "
        "responses through Gemini 2.0 Flash, providing domain-specific AI assistance without requiring users to leave the messaging interface. The measurement "
        "framework and analysis scripts are available at https://github.com/anudeepadi/quit-txt-rag-eval."
    )
    conclusion_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # A. Future Work
    subsec8a = doc.add_heading("A. Future Work", level=2)
    for run in subsec8a.runs:
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    future_p1 = doc.add_paragraph(
        "Three directions follow from this work: (1) on-device validation on physical Android and iOS hardware with Firebase backend load testing, following "
        "the testbed methodology of Inupakutika et al. [7], to characterize end-to-end message delivery latency under concurrent load; (2) formal evaluation "
        "of RAG response quality using the RAGAS framework [17], comparing human-curated and AI-generated knowledge bases, with results to be reported in a "
        "companion study [18]; and (3) field deployment monitoring to compare laboratory benchmarks against real-world usage patterns."
    )
    future_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # REFERENCES
    ref_heading = doc.add_heading("REFERENCES", level=1)
    ref_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in ref_heading.runs:
        run.font.size = Pt(11)
        run.font.name = "Times New Roman"
        run.font.bold = True

    references = [
        'World Health Organization, "WHO report on the global tobacco epidemic 2023: Protect people from tobacco smoke," WHO, Tech. Rep., 2023.',
        'R. Whittaker, H. McRobbie, C. Bullen, R. Rodgers, Y. Gu, and R. Dobson, "Mobile phone text messaging and app-based interventions for smoking cessation," Cochrane Database of Systematic Reviews, no. 10, 2019.',
        'W. T. Riley, D. E. Rivera, A. A. Atienza, W. Nilsen, S. M. Allison, and R. Mermelstein, "Health behavior models in the age of mobile interventions: Are our theories up to the task?" Translational Behavioral Medicine, vol. 1, no. 1, pp. 53–71, 2011.',
        'S. Nicola, J. Ferreira, and J. P. Fernandes, "Flutter vs. native vs. React Native: Examining performance of mobile development approaches," SN Computer Science, vol. 3, no. 5, p. 385, 2022.',
        'A. Biørn-Hansen, T.-M. Grønli, and G. Ghinea, "A survey and taxonomy of core concepts and research challenges in cross-platform mobile development," ACM Computing Surveys, vol. 51, no. 5, pp. 1–34, 2020.',
        'T. A. Majchrzak, A. Biørn-Hansen, and T.-M. Grønli, "Progressive web apps: The definite approach to cross-platform development?" in Proc. 51st Hawaii Int. Conf. System Sciences (HICSS), 2018, pp. 5735–5744.',
        'D. Inupakutika, G. Rodriguez, D. Akopian, P. Lama, P. Chalela, and A. G. Ramirez, "On the performance of cloud-based mHealth applications: A methodology on measuring service response time and a case study," IEEE Access, vol. 10, pp. 53208–53224, 2022.',
        'G. R. Gunnam, D. Inupakutika, R. Mundlamuri, S. Kaghyan, and D. Akopian, "Assessing performance of cloud-based heterogeneous chatbot systems and a case study," IEEE Access, vol. 12, pp. 81631–81645, 2024.',
        'L. Moroney, The Definitive Guide to Firebase. Berkeley, CA, USA: Apress, 2017.',
        'E. Gamma, R. Helm, R. Johnson, and J. Vlissides, Design Patterns: Elements of Reusable Object-Oriented Software. Reading, MA, USA: Addison-Wesley, 1994.',
        'N. Megiddo and D. S. Modha, "ARC: A self-tuning, low overhead replacement cache," in Proc. USENIX FAST, 2003, pp. 115–130.',
        'M. L. Ybarra, M. Holtrop, T. B. Prescott, and D. Strong, "Process evaluation of a mHealth program: Lessons learned from Stop My Smoking USA," Patient Education and Counseling, vol. 97, no. 2, pp. 239–243, 2014.',
        'G. R. Gunnam, D. Akopian, A. Adiraju, et al., "Design and implementation of a cross-platform RCS messaging application for mHealth," Int. J. Computer Applications, vol. 186, 2024.',
        'A. Adiraju, "Design and implementation of a cross-platform RCS messaging application for smoking cessation mHealth intervention," M.S. thesis, Dept. Elect. Comput. Eng., Univ. Texas San Antonio, San Antonio, TX, USA, 2025.',
        'J. B. Bricker et al., "Conversational chatbot for cigarette smoking cessation: Results from the 11-step user-centered design development process and randomized controlled trial," JMIR mHealth and uHealth, vol. 12, no. 1, e57318, 2024.',
        'P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 9459–9474.',
        'S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAS: Automated evaluation of retrieval augmented generation," arXiv preprint arXiv:2309.15217, 2023.',
        'E. Mellatdoust Pordel, D. Akopian, and L. Velez, "Web retrieval-augmented generation for a smoking cessation counseling assistant: Evaluation of faithfulness and latency," [Manuscript in preparation], 2024.'
    ]

    for i, ref in enumerate(references, 1):
        p = doc.add_paragraph(f"[{i}] {ref}")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        # Hanging indent
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        for run in p.runs:
            run.font.size = Pt(9)
            run.font.name = "Times New Roman"

    # Save document
    output_path = "paper/Performance_Benchmarking_Paper.docx"
    doc.save(output_path)
    print(f"✓ Generated: {output_path}")
    print(f"  Document structure:")
    print(f"    - Title and authors with superscript affiliations")
    print(f"    - Abstract and Index Terms")
    print(f"    - 8 numbered sections (I-VIII)")
    print(f"    - 5 tables (I-V)")
    print(f"    - 18 references")
    print(f"    - IEEE formatting throughout")


if __name__ == "__main__":
    main()
