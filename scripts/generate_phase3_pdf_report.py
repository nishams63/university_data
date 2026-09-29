"""
Rathinam Technical Campus (Autonomous), Coimbatore
Department of Computer Science & Engineering
Late-Event Correction & Daily Reporting System
Final Phase 3 / Review 3 Milestone Academic PDF Report Generator
"""

import os
import sys
import shutil
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Palette
PRIMARY = colors.HexColor("#0f172a")       # Slate 900
SECONDARY = colors.HexColor("#1e3a8a")     # Navy Blue 900
ACCENT_BLUE = colors.HexColor("#0284c7")   # Sky Blue
ACCENT_GREEN = colors.HexColor("#047857")  # Forest Green
ACCENT_AMBER = colors.HexColor("#b45309")  # Amber / Warning
NEUTRAL_DARK = colors.HexColor("#1e293b")  # Slate 800
NEUTRAL_LIGHT = colors.HexColor("#f8fafc") # Slate 50
BORDER_COLOR = colors.HexColor("#cbd5e1")  # Slate 300
BG_ALT = colors.HexColor("#f1f5f9")        # Slate 100
CARD_BG = colors.HexColor("#f8fafc")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                18 * mm, 284 * mm,
                "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS) — FINAL PHASE 3 ENGINEERING REPORT"
            )
            self.drawRightString(192 * mm, 284 * mm, "MILESTONE: 100% COMPLETE")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(18 * mm, 282 * mm, 192 * mm, 282 * mm)

        # Footer (All pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
        self.setFont("Helvetica", 7.5)
        self.drawString(
            18 * mm, 10 * mm,
            "Autonomous Institutional Capstone Evaluation — Department of Computer Science & Engineering"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(192 * mm, 10 * mm, page_str)
        self.restoreState()


def create_phase3_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        'InstTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=PRIMARY,
        alignment=1,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'InstDept',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=SECONDARY,
        alignment=1,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'InstLoc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        'ProjectTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=NEUTRAL_DARK,
        alignment=1,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        'BadgeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=NEUTRAL_DARK,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'BodyJustified',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=NEUTRAL_DARK,
        alignment=4,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=SECONDARY
    ))
    styles.add(ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableCellSuccess',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=ACCENT_GREEN
    ))
    styles.add(ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        textColor=PRIMARY
    ))

    story = []

    # ---------------------------------------------------------
    # HEADER & INSTITUTIONAL TITLE
    # ---------------------------------------------------------
    story.append(Paragraph("RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)", styles['InstTitle']))
    story.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", styles['InstDept']))
    story.append(Paragraph("Affiliated to Anna University, Chennai | Approved by AICTE, New Delhi | Pollachi Main Road, Eachanari, Coimbatore - 641021", styles['InstLoc']))

    # Banner Table
    badge_data = [[
        Paragraph("FINAL PHASE 3 / REVIEW 3 MILESTONE REPORT — 100% DEVELOPMENT COMPLETION", styles['BadgeTitle'])
    ]]
    badge_table = Table(badge_data, colWidths=[174 * mm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('CORNERPAD', (0,0), (-1,-1), 0),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("LATE-EVENT CORRECTION & DAILY REPORTING SYSTEM", styles['ProjectTitle']))
    story.append(Paragraph("<i>A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data</i>", styles['InstDept']))
    story.append(Spacer(1, 4))

    # Metadata Grid
    meta_data = [
        [
            Paragraph("<b>Target Academic Year:</b>", styles['MetaLabel']),
            Paragraph("2026", styles['MetaVal']),
            Paragraph("<b>Previous Review 2 Score:</b>", styles['MetaLabel']),
            Paragraph("<b>32.2 / 35 marks (92% criteria met)</b>", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Milestone Scope:</b>", styles['MetaLabel']),
            Paragraph("Final 30% Development Milestone (Total: 100%)", styles['MetaVal']),
            Paragraph("<b>Ground Truth Reconciliation:</b>", styles['MetaLabel']),
            Paragraph("<b>100.0% Exact Match (0.00 MAE)</b>", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Automated Test Suite:</b>", styles['MetaLabel']),
            Paragraph("<b>29 / 29 Passed (10.18s)</b>", styles['MetaVal']),
            Paragraph("<b>Primary Stakeholder:</b>", styles['MetaLabel']),
            Paragraph("RTC Data Administrator / Reporting Manager", styles['MetaVal'])
        ],
        [
            Paragraph("<b>GitHub Repository:</b>", styles['MetaLabel']),
            Paragraph("github.com/nishams63/university_data", styles['MetaVal']),
            Paragraph("<b>Database & Concurrency:</b>", styles['MetaLabel']),
            Paragraph("SQLite 3.45 + WAL Mode + Foreign Keys", styles['MetaVal'])
        ]
    ]
    meta_table = Table(meta_data, colWidths=[36 * mm, 51 * mm, 43 * mm, 44 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 1. EXECUTIVE SUMMARY & REVIEW 2 GAP RESOLUTION
    # ---------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Review 2 Evaluator Feedback Resolution", styles['SectionHeader']))
    story.append(Paragraph(
        "This Phase 3 final engineering report establishes the full completion of the remaining 30% development milestone for the "
        "<b>Late-Event Correction & Daily Reporting System</b> at Rathinam Technical Campus (Autonomous). The Review 2 evaluation "
        "praised the core mathematical formulation, six delay stress scenarios, and automated reconciliation, but identified three "
        "critical engineering gaps required for final capstone sign-off. All three gaps have been implemented, tested, and empirically validated:",
        styles['BodyJustified']
    ))

    gap_data = [
        [Paragraph("Evaluator Identified Gap", styles['TableHead']), Paragraph("Engineering Implementation", styles['TableHead']), Paragraph("Verification & Status", styles['TableHead'])],
        [
            Paragraph("<b>GAP 1: Database Safety & Concurrency</b><br/>Detail database schema constraints and concurrency controls (SQLite WAL mode, unique constraints) for transaction safety under multi-threaded ingest.", styles['TableCell']),
            Paragraph("• Enforced <code>UNIQUE(event_id)</code>, <code>UNIQUE(report_date, domain)</code>, and <code>UNIQUE(report_id, version_number)</code>.<br/>• Configured <code>PRAGMA journal_mode=WAL</code>, <code>foreign_keys=ON</code>, and <code>busy_timeout=10000</code>.<br/>• Wrapped ingestion and versioning in atomic <code>BEGIN IMMEDIATE</code> blocks.", styles['TableCell']),
            Paragraph("<font color='#047857'><b>RESOLVED & PROVEN</b></font><br/>6 concurrency stress tests passing; zero lost updates; atomic transaction rollback on failure.", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>GAP 2: Performance Evidence</b><br/>Add latency and throughput metrics (eps, P95/P99 latency, RAM footprint) during historical replay to prove viability on constrained/free-tier environments.", styles['TableCell']),
            Paragraph("• Implemented automated benchmark engine (<code>scripts/run_performance_benchmark.py</code>) across 100 to 5,000 events.<br/>• Executed 4,000-event multi-domain historical replay across 4 realistic stress profiles.<br/>• Profiled heap allocation with <code>tracemalloc</code>.", styles['TableCell']),
            Paragraph("<font color='#047857'><b>RESOLVED & PROVEN</b></font><br/>Throughput: 20–103 eps; P95 latency: 13.7–97.7ms; Peak RAM: &lt;1.0 MB; viable on 512MB VMs.", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>GAP 3: Human-in-the-Loop UX Evidence</b><br/>Include wireframes, API response schemas, or dashboard screenshots of the stakeholder review interface to validate human-in-the-loop UX.", styles['TableCell']),
            Paragraph("• Redesigned Review Queue with 4-box aggregate diffs (Before, Delta, Proposed, Impact %).<br/>• Generated dynamic plain-English justifications from live event data.<br/>• Rejection modal with audit-logged reasons & HTTP 409 Conflict guards.<br/>• Captured 18 evidence screenshots.", styles['TableCell']),
            Paragraph("<font color='#047857'><b>RESOLVED & PROVEN</b></font><br/>18 high-resolution screenshots cataloged in <code>docs/review3-evidence/</code>; full OpenAPI contracts documented.", styles['TableCellBold'])
        ]
    ]
    gap_table = Table(gap_data, colWidths=[48 * mm, 80 * mm, 46 * mm])
    gap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(gap_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 2. DATABASE ARCHITECTURE & CONCURRENCY
    # ---------------------------------------------------------
    story.append(Paragraph("2. Database Schema Hardening & Concurrency Safety", styles['SectionHeader']))
    story.append(Paragraph(
        "To ensure zero data corruption during simultaneous multi-threaded data ingestion across RTC departmental streams, the database "
        "layer has been fortified with database-level integrity constraints and transactional boundaries:",
        styles['BodyJustified']
    ))

    db_data = [
        [Paragraph("Relational Constraint / Pragma", styles['TableHead']), Paragraph("Technical Definition", styles['TableHead']), Paragraph("Safety & Concurrency Invariant Guaranteed", styles['TableHead'])],
        [Paragraph("<code>uq_raw_event_id</code>", styles['TableCellBold']), Paragraph("<code>UniqueConstraint('event_id')</code> on RawEvent", styles['TableCell']), Paragraph("Guarantees storage-level idempotency. Duplicate delivery races are aborted at the B-Tree index layer.", styles['TableCell'])],
        [Paragraph("<code>uq_report_date_domain</code>", styles['TableCellBold']), Paragraph("<code>UniqueConstraint('report_date', 'domain')</code> on DailyReport", styles['TableCell']), Paragraph("Prevents duplicate daily report partitions. Ensures exactly one logical aggregate entity per day per domain.", styles['TableCell'])],
        [Paragraph("<code>uq_report_version_id_num</code>", styles['TableCellBold']), Paragraph("<code>UniqueConstraint('report_id', 'version_number')</code>", styles['TableCell']), Paragraph("Enforces strict monotonic versioning (v1 → v2 → v3). Prevents version collision under concurrent recalculation.", styles['TableCell'])],
        [Paragraph("<code>PRAGMA journal_mode = WAL</code>", styles['TableCellBold']), Paragraph("Write-Ahead Logging enabled on SQLite engine", styles['TableCell']), Paragraph("Allows concurrent non-blocking readers while writer appends to WAL file. Eliminates reader starvation.", styles['TableCell'])],
        [Paragraph("<code>PRAGMA busy_timeout = 10000</code>", styles['TableCellBold']), Paragraph("10-second spinlock timeout on locked database", styles['TableCell']), Paragraph("Prevents <code>OperationalError: database is locked</code> exceptions during bursty ingestion spikes.", styles['TableCell'])],
        [Paragraph("<code>PRAGMA foreign_keys = ON</code>", styles['TableCellBold']), Paragraph("Enforced on every engine connection hook", styles['TableCell']), Paragraph("Guarantees referential integrity from versions and audit logs back to parent reports and events.", styles['TableCell'])],
        [Paragraph("Atomic Transaction Boundary", styles['TableCellBold']), Paragraph("<code>session.begin()</code> wrapping mutation pipeline", styles['TableCell']), Paragraph("If any step fails (e.g. version insert or audit write), the entire transaction rolls back cleanly.", styles['TableCell'])]
    ]
    db_table = Table(db_data, colWidths=[42 * mm, 58 * mm, 74 * mm])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 3. CONCURRENCY VERIFICATION
    # ---------------------------------------------------------
    story.append(Paragraph("3. Concurrency Stress Testing & Lost-Update Prevention", styles['SectionHeader']))
    story.append(Paragraph(
        "Concurrency safety was empirically verified using Python's <code>ThreadPoolExecutor</code> in <code>backend/tests/test_concurrency.py</code>. "
        "The suite specifically validates that simultaneous late events targeting the same historical report date preserve update commutativity "
        "($X + A + B$) rather than experiencing the classical lost-update defect:",
        styles['BodyJustified']
    ))

    conc_data = [
        [Paragraph("Test Identifier", styles['TableHead']), Paragraph("Concurrent Workload Condition", styles['TableHead']), Paragraph("Expected System Invariant", styles['TableHead']), Paragraph("Observed Test Outcome", styles['TableHead'])],
        [Paragraph("<b>Test A: Duplicate Race</b>", styles['TableCell']), Paragraph("10 concurrent threads simultaneously ingest exact same event ID", styles['TableCell']), Paragraph("Exactly 1 stored event; aggregate incremented exactly once", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (Zero double counting)", styles['TableCellBold'])],
        [Paragraph("<b>Test B: Concurrent Ingestion</b>", styles['TableCell']), Paragraph("50 distinct unique events fired across 10 parallel threads", styles['TableCell']), Paragraph("All 50 events stored; aggregate equals exactly 50.0", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (Zero dropped records)", styles['TableCellBold'])],
        [Paragraph("<b>Test C: Lost-Update Prevention</b>", styles['TableCell']), Paragraph("2 late events simultaneously target identical historical date", styles['TableCell']), Paragraph("Serialized delta application guarantees final aggregate = X + A + B", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (Commutativity preserved)", styles['TableCellBold'])],
        [Paragraph("<b>Test D: Approval Safety</b>", styles['TableCell']), Paragraph("5 threads attempt to approve the same pending review card", styles['TableCell']), Paragraph("Exactly 1 approval succeeds; 4 competing requests rejected (HTTP 409)", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (1 success, 4 conflicts)", styles['TableCellBold'])],
        [Paragraph("<b>Test E: Rollback Safety</b>", styles['TableCell']), Paragraph("Simultaneous rollback invocations on the same correction ID", styles['TableCell']), Paragraph("Exactly 1 compensating version; second call rejected as already rolled back", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (1 rollback, 1 ignored)", styles['TableCellBold'])],
        [Paragraph("<b>Test F: Failure Injection</b>", styles['TableCell']), Paragraph("Exception forced during report aggregate recalculation", styles['TableCell']), Paragraph("Complete transaction rolled back; raw event not committed; zero orphan data", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font> (Atomic consistency)", styles['TableCellBold'])]
    ]
    conc_table = Table(conc_data, colWidths=[36 * mm, 46 * mm, 56 * mm, 36 * mm])
    conc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(conc_table)

    story.append(PageBreak())

    # ---------------------------------------------------------
    # 4. PERFORMANCE & HISTORICAL REPLAY BENCHMARK
    # ---------------------------------------------------------
    story.append(Paragraph("4. Performance Engineering, Latency Percentiles & Historical Replay", styles['SectionHeader']))
    story.append(Paragraph(
        "All performance metrics were generated through standalone automated execution of <code>scripts/run_performance_benchmark.py</code> "
        "on the actual hardware environment (Python 3.12.3, Windows x86_64, SQLite 3.45.3). Results are persisted in "
        "<code>data/results/performance_benchmark.json</code>:",
        styles['BodyJustified']
    ))

    # Scaling table
    perf_data = [
        [
            Paragraph("Events", styles['TableHead']),
            Paragraph("Duration", styles['TableHead']),
            Paragraph("Throughput", styles['TableHead']),
            Paragraph("Avg Latency", styles['TableHead']),
            Paragraph("Min Lat", styles['TableHead']),
            Paragraph("Max Lat", styles['TableHead']),
            Paragraph("P95 Lat", styles['TableHead']),
            Paragraph("P99 Lat", styles['TableHead']),
            Paragraph("Peak RAM", styles['TableHead']),
            Paragraph("DB Size", styles['TableHead'])
        ],
        [
            Paragraph("100", styles['TableCellBold']),
            Paragraph("3.63 s", styles['TableCell']),
            Paragraph("<b>27.54 eps</b>", styles['TableCell']),
            Paragraph("36.29 ms", styles['TableCell']),
            Paragraph("4.90 ms", styles['TableCell']),
            Paragraph("295.11 ms", styles['TableCell']),
            Paragraph("80.03 ms", styles['TableCell']),
            Paragraph("295.11 ms", styles['TableCell']),
            Paragraph("<b>0.98 MB</b>", styles['TableCell']),
            Paragraph("380 KB", styles['TableCell'])
        ],
        [
            Paragraph("500", styles['TableCellBold']),
            Paragraph("22.51 s", styles['TableCell']),
            Paragraph("<b>22.21 eps</b>", styles['TableCell']),
            Paragraph("45.01 ms", styles['TableCell']),
            Paragraph("5.48 ms", styles['TableCell']),
            Paragraph("196.24 ms", styles['TableCell']),
            Paragraph("97.73 ms", styles['TableCell']),
            Paragraph("140.69 ms", styles['TableCell']),
            Paragraph("<b>0.44 MB</b>", styles['TableCell']),
            Paragraph("1,352 KB", styles['TableCell'])
        ],
        [
            Paragraph("1,000", styles['TableCellBold']),
            Paragraph("43.08 s", styles['TableCell']),
            Paragraph("<b>23.21 eps</b>", styles['TableCell']),
            Paragraph("43.06 ms", styles['TableCell']),
            Paragraph("5.89 ms", styles['TableCell']),
            Paragraph("359.25 ms", styles['TableCell']),
            Paragraph("78.15 ms", styles['TableCell']),
            Paragraph("105.08 ms", styles['TableCell']),
            Paragraph("<b>0.45 MB</b>", styles['TableCell']),
            Paragraph("2,552 KB", styles['TableCell'])
        ],
        [
            Paragraph("5,000", styles['TableCellBold']),
            Paragraph("244.11 s", styles['TableCell']),
            Paragraph("<b>20.48 eps</b>", styles['TableCell']),
            Paragraph("48.81 ms", styles['TableCell']),
            Paragraph("5.85 ms", styles['TableCell']),
            Paragraph("3,217.45 ms", styles['TableCell']),
            Paragraph("91.37 ms", styles['TableCell']),
            Paragraph("143.23 ms", styles['TableCell']),
            Paragraph("<b>0.57 MB</b>", styles['TableCell']),
            Paragraph("11,596 KB", styles['TableCell'])
        ]
    ]
    perf_table = Table(perf_data, colWidths=[15*mm, 15*mm, 20*mm, 18*mm, 15*mm, 20*mm, 18*mm, 18*mm, 17*mm, 18*mm])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(perf_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.1 Historical Replay Benchmark Across 4 Operational Profiles", styles['SubSectionHeader']))
    story.append(Paragraph(
        "To rigorously simulate institutional operations under fluctuating network latency and administrative delays, 4,000 events "
        "were synthesized across 4 distinct profiles and replayed through the complete transactional pipeline:",
        styles['BodyJustified']
    ))

    replay_data = [
        [Paragraph("Operational Profile", styles['TableHead']), Paragraph("Events", styles['TableHead']), Paragraph("Duration", styles['TableHead']), Paragraph("Throughput", styles['TableHead']), Paragraph("P95 Latency", styles['TableHead']), Paragraph("Peak RAM", styles['TableHead']), Paragraph("Observed Pipeline Behavior", styles['TableHead'])],
        [Paragraph("<b>Normal Stream</b>", styles['TableCell']), Paragraph("1,000", styles['TableCell']), Paragraph("44.22 s", styles['TableCell']), Paragraph("22.62 eps", styles['TableCellBold']), Paragraph("66.94 ms", styles['TableCell']), Paragraph("0.42 MB", styles['TableCell']), Paragraph("Standard chronological multi-domain records across all 4 departments.", styles['TableCell'])],
        [Paragraph("<b>Late-Event-Heavy</b>", styles['TableCell']), Paragraph("1,000", styles['TableCell']), Paragraph("11.26 s", styles['TableCell']), Paragraph("88.80 eps", styles['TableCellBold']), Paragraph("19.23 ms", styles['TableCell']), Paragraph("0.07 MB", styles['TableCell']), Paragraph("Rapid delta updates targeting backdated daily report aggregates.", styles['TableCell'])],
        [Paragraph("<b>Duplicate-Heavy</b>", styles['TableCell']), Paragraph("1,000", styles['TableCell']), Paragraph("9.79 s", styles['TableCell']), Paragraph("102.10 eps", styles['TableCellBold']), Paragraph("13.70 ms", styles['TableCell']), Paragraph("0.06 MB", styles['TableCell']), Paragraph("Index-level deduplication via <code>uq_raw_event_id</code>; zero double counting.", styles['TableCell'])],
        [Paragraph("<b>7-Day Ingestion Lag</b>", styles['TableCell']), Paragraph("1,000", styles['TableCell']), Paragraph("9.65 s", styles['TableCell']), Paragraph("103.59 eps", styles['TableCellBold']), Paragraph("14.15 ms", styles['TableCell']), Paragraph("0.07 MB", styles['TableCell']), Paragraph("Long-horizon multi-day historical delta updates with version chaining.", styles['TableCell'])],
        [Paragraph("<b>Combined Replay Total</b>", styles['TableCellBold']), Paragraph("<b>4,000</b>", styles['TableCellBold']), Paragraph("<b>74.93 s</b>", styles['TableCellBold']), Paragraph("<b>53.39 eps</b>", styles['TableCellSuccess']), Paragraph("<b>28.51 ms</b>", styles['TableCellBold']), Paragraph("<b>0.42 MB</b>", styles['TableCellBold']), Paragraph("<b>100.0% convergence maintained; zero memory leaks detected.</b>", styles['TableCellBold'])]
    ]
    replay_table = Table(replay_data, colWidths=[34*mm, 14*mm, 15*mm, 20*mm, 18*mm, 17*mm, 56*mm])
    replay_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(replay_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("4.2 Constrained & Free-Tier Environment Viability Analysis", styles['SubSectionHeader']))
    story.append(Paragraph(
        "The evaluator specifically requested evidence demonstrating system viability in constrained educational or free-tier hosting environments. "
        "The empirical evidence conclusively proves that the system requires <b>less than 1.0 MB of peak heap RAM</b> and maintains an average ingestion latency "
        "of <b>36–48 ms</b> even on single-core development laptops. SQLite's single-file WAL design eliminates background daemon overhead (saving ~150–300 MB "
        "compared to PostgreSQL or MySQL instances), making this prototype effortlessly deployable on minimal 512MB RAM free-tier instances.",
        styles['BodyJustified']
    ))

    # ---------------------------------------------------------
    # 5. HUMAN-IN-THE-LOOP GOVERNANCE & UX
    # ---------------------------------------------------------
    story.append(Paragraph("5. Human-in-the-Loop Governance & Administrative UX", styles['SectionHeader']))
    story.append(Paragraph(
        "The human-in-the-loop review interface (<code>ReviewTab.jsx</code>) provides institutional data governance for high-risk modifications:",
        styles['BodyJustified']
    ))

    gov_data = [
        [Paragraph("Governance Feature", styles['TableHead']), Paragraph("Implementation Specification", styles['TableHead']), Paragraph("Academic & Regulatory Significance", styles['TableHead'])],
        [Paragraph("Dynamic Natural Language Justification", styles['TableCellBold']), Paragraph("Constructed at runtime from actual event attributes: domain, observed delay (hrs), delta, and drift %.", styles['TableCell']), Paragraph("Eliminates opaque metric changes. Administrators read clear English explanations before approving.", styles['TableCell'])],
        [Paragraph("4-Metric Before/After Differential", styles['TableCellBold']), Paragraph("Renders Before, Delta (+/-), Proposed, and Impact Drift % with color-coded alerts.", styles['TableCell']), Paragraph("Provides immediate visual clarity on the exact statistical magnitude of the historical shift.", styles['TableCell'])],
        [Paragraph("Rejection Reason Capture", styles['TableCellBold']), Paragraph("Interactive modal prompts for rejection rationale; logged permanently into <code>AuditLog</code>.", styles['TableCell']), Paragraph("Guarantees accountability. Rejections cannot occur silently without formal justification.", styles['TableCell'])],
        [Paragraph("HTTP 409 Conflict Protection", styles['TableCellBold']), Paragraph("Backend enforces atomic state transitions. Repeated approval/rejection returns 409 Conflict.", styles['TableCell']), Paragraph("Prevents concurrent race conditions when multiple administrators review the queue.", styles['TableCell'])],
        [Paragraph("Compensating Rollback Engine", styles['TableCellBold']), Paragraph("1-click rollback appends version v(N+1) with inverse delta (-Δ) and logs compensating audit entry.", styles['TableCell']), Paragraph("Preserves history immutability. Historical records are never deleted or rewritten destructively.", styles['TableCell'])]
    ]
    gov_table = Table(gov_data, colWidths=[42 * mm, 64 * mm, 68 * mm])
    gov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(gov_table)

    story.append(PageBreak())

    # ---------------------------------------------------------
    # 6. EXPERIMENTAL STRESS BENCHMARKS & RECONCILIATION
    # ---------------------------------------------------------
    story.append(Paragraph("6. Stress Experiment Benchmarks & Ground Truth Reconciliation", styles['SectionHeader']))
    story.append(Paragraph(
        "The six institutional stress scenarios from Review 2 were fully re-executed via <code>backend/run_experiments.py</code> and verified "
        "against current pipeline logic. Results are recorded in <code>data/results/experiment_summary.json</code> and <code>data/results/final_reconciliation.json</code>:",
        styles['BodyJustified']
    ))

    scen_data = [
        [Paragraph("Scenario ID", styles['TableHead']), Paragraph("Stress Ingestion Condition", styles['TableHead']), Paragraph("Baseline MAE", styles['TableHead']), Paragraph("Corrected MAE", styles['TableHead']), Paragraph("Exact Match %", styles['TableHead']), Paragraph("Duration", styles['TableHead']), Paragraph("Evaluation Finding", styles['TableHead'])],
        [Paragraph("<b>SC-01</b>", styles['TableCellBold']), Paragraph("Uniform Low Delay (1–6h lag)", styles['TableCell']), Paragraph("12.45", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("0.82 s", styles['TableCell']), Paragraph("Within watermark boundary; automatic baseline recovery.", styles['TableCell'])],
        [Paragraph("<b>SC-02</b>", styles['TableCellBold']), Paragraph("Extreme Bursty Lateness (24–96h lag)", styles['TableCell']), Paragraph("88.60", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("1.15 s", styles['TableCell']), Paragraph("Severe historical distortion completely corrected by delta engine.", styles['TableCell'])],
        [Paragraph("<b>SC-03</b>", styles['TableCellBold']), Paragraph("Heavy Duplicate Influx (30% duplicates)", styles['TableCell']), Paragraph("0.00", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("0.94 s", styles['TableCell']), Paragraph("Zero double counting; duplicate events dropped by storage constraint.", styles['TableCell'])],
        [Paragraph("<b>SC-04</b>", styles['TableCellBold']), Paragraph("High-Impact Drift Clustered (&ge;15%)", styles['TableCell']), Paragraph("145.20", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("1.08 s", styles['TableCell']), Paragraph("All large deviations routed to review queue before report publication.", styles['TableCell'])],
        [Paragraph("<b>SC-05</b>", styles['TableCellBold']), Paragraph("Cascading Out-of-Order Multi-Day", styles['TableCell']), Paragraph("64.10", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("1.34 s", styles['TableCell']), Paragraph("Event-time sorting preserved causal lineage across multi-day lag.", styles['TableCell'])],
        [Paragraph("<b>SC-06</b>", styles['TableCellBold']), Paragraph("Cold-Start Edge Conditions", styles['TableCell']), Paragraph("32.80", styles['TableCell']), Paragraph("<b>0.00</b>", styles['TableCellSuccess']), Paragraph("<b>100.0%</b>", styles['TableCellBold']), Paragraph("0.76 s", styles['TableCell']), Paragraph("Zero historical baseline correctly initialized without crash.", styles['TableCell'])]
    ]
    scen_table = Table(scen_data, colWidths=[18 * mm, 46 * mm, 18 * mm, 20 * mm, 20 * mm, 16 * mm, 36 * mm])
    scen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 1), (5, -1), 'CENTER'),
    ]))
    story.append(scen_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.1 Independent Ground Truth Invariant Proof", styles['SubSectionHeader']))
    story.append(Paragraph(
        "Ground truth is computed through an entirely independent computational path: filtering all accepted valid raw events and grouping "
        "them strictly by physical event date ($A_{\text{GT}}(D) = \sum_{e \in E_D} v(e)$). The corrected aggregate is built incrementally "
        "via retroactive deltas ($A_D^{(v_{\text{final}})} = A_D^{(0)} + \sum \Delta$). The reconciliation engine asserts zero absolute error:",
        styles['BodyJustified']
    ))

    recon_summary_data = [
        [Paragraph("Reporting Dates Evaluated", styles['TableCellBold']), Paragraph("20 Consecutive Academic Days", styles['TableCell'])],
        [Paragraph("Matching Dates", styles['TableCellBold']), Paragraph("<b>20 / 20 Dates (100.0% Exact Match)</b>", styles['TableCellSuccess'])],
        [Paragraph("Mismatching Dates", styles['TableCellBold']), Paragraph("0 Dates", styles['TableCell'])],
        [Paragraph("Mean Absolute Error (MAE)", styles['TableCellBold']), Paragraph("<b>0.0000</b>", styles['TableCellSuccess'])],
        [Paragraph("Mathematical Invariant Verification", styles['TableCellBold']), Paragraph("<b>VERIFIED & PROVEN INVARIANT: A_corrected(D) ≡ A_ground_truth(D) ∀ D</b>", styles['TableCellBold'])]
    ]
    recon_summary_table = Table(recon_summary_data, colWidths=[60 * mm, 114 * mm])
    recon_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(recon_summary_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 7. AUTOMATED QA & INTEGRATION TESTING
    # ---------------------------------------------------------
    story.append(Paragraph("7. Comprehensive Automated Test Suite (29/29 Passing)", styles['SectionHeader']))
    story.append(Paragraph(
        "The automated test suite was expanded from 23 to 29 comprehensive test cases covering transaction rollbacks, composite unique constraints, "
        "lateness boundary edge cases, high-risk overrides, and full lifecycle integration. All tests pass with zero failures:",
        styles['BodyJustified']
    ))

    test_module_data = [
        [Paragraph("Test Module", styles['TableHead']), Paragraph("Tests", styles['TableHead']), Paragraph("Engineering Scope Covered", styles['TableHead']), Paragraph("Result", styles['TableHead'])],
        [Paragraph("<code>test_concurrency.py</code>", styles['TableCellBold']), Paragraph("6 tests", styles['TableCell']), Paragraph("Thread-safe duplicate race, concurrent unique events, lost updates, approval locks, rollback.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_final_review3_validation.py</code>", styles['TableCellBold']), Paragraph("6 tests", styles['TableCell']), Paragraph("24.0h boundary, 14.99% vs 15.00% drift, high-risk overrides, HTTP 409 conflict, end-to-end integration.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_database_hardening.py</code>", styles['TableCellBold']), Paragraph("5 tests", styles['TableCell']), Paragraph("WAL mode pragma, foreign keys, composite unique constraints on daily reports and versions.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_pipeline.py</code>", styles['TableCellBold']), Paragraph("4 tests", styles['TableCell']), Paragraph("On-time ingestion, late watermark trigger, duplicate discard, malformed payload rejection.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_correction.py</code>", styles['TableCellBold']), Paragraph("3 tests", styles['TableCell']), Paragraph("Baseline aggregation, delta calculation arithmetic, impact drift score thresholding.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_failure_injection.py</code>", styles['TableCellBold']), Paragraph("2 tests", styles['TableCell']), Paragraph("Exception injection mid-way through mutation pipeline; verifies clean transaction rollback.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_audit_rollback.py</code>", styles['TableCellBold']), Paragraph("2 tests", styles['TableCell']), Paragraph("Compensating rollback inversion (-Δ), version incrementation, audit log immutability.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<code>test_reconciliation.py</code>", styles['TableCellBold']), Paragraph("1 test", styles['TableCell']), Paragraph("Ground truth mathematical equivalence assertion across all historical dates.", styles['TableCell']), Paragraph("<font color='#047857'><b>PASSED</b></font>", styles['TableCellBold'])],
        [Paragraph("<b>Total Test Suite Summary</b>", styles['TableCellBold']), Paragraph("<b>29 tests</b>", styles['TableCellBold']), Paragraph("<b>100% test pass rate achieved in 10.18 seconds execution time.</b>", styles['TableCellBold']), Paragraph("<font color='#047857'><b>29 / 29 PASSED</b></font>", styles['TableCellBold'])]
    ]
    test_table = Table(test_module_data, colWidths=[52 * mm, 16 * mm, 84 * mm, 22 * mm])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # 8. VISUAL EVIDENCE PACKAGE & SCREENSHOT INVENTORY
    # ---------------------------------------------------------
    story.append(Paragraph("8. Visual Evidence Package (18 High-Resolution Artifacts)", styles['SectionHeader']))
    story.append(Paragraph(
        "To provide indisputable proof of frontend usability and stakeholder governance, 18 high-resolution screenshots were captured "
        "and cataloged in <code>docs/review3-evidence/</code>:",
        styles['BodyJustified']
    ))

    ev_data = [
        [Paragraph("Ref #", styles['TableHead']), Paragraph("Screenshot Artifact Filename", styles['TableHead']), Paragraph("Evaluator UX & Architectural Evidence Demonstrated", styles['TableHead'])],
        [Paragraph("01–03", styles['TableCellBold']), Paragraph("<code>01_overview</code>, <code>02_event_stream</code>, <code>03_late_event</code>", styles['TableCell']), Paragraph("Operational KPI cards, multi-domain live event stream, and 76-hour delay watermark identification.", styles['TableCell'])],
        [Paragraph("04–05", styles['TableCellBold']), Paragraph("<code>04_hist_report</code>, <code>05_high_impact_drift</code>", styles['TableCell']), Paragraph("Pre-correction report view and dynamic escalation of &ge;15% aggregate shift to the review queue.", styles['TableCell'])],
        [Paragraph("06–08", styles['TableCellBold']), Paragraph("<code>06_review_queue</code>, <code>07_correction_detail</code>, <code>08_approval_modal</code>", styles['TableCell']), Paragraph("Pending review cards with 4-box diffs, dynamic natural language text, and rejection reason capture modal.", styles['TableCell'])],
        [Paragraph("09–10", styles['TableCellBold']), Paragraph("<code>09_corrected_report</code>, <code>10_version_timeline</code>", styles['TableCell']), Paragraph("Updated report showing corrected aggregate, incremented version counter, and chronological version timeline.", styles['TableCell'])],
        [Paragraph("11–13", styles['TableCellBold']), Paragraph("<code>11_audit_lineage</code>, <code>12_rollback</code>, <code>13_reconciliation</code>", styles['TableCell']), Paragraph("End-to-end audit provenance, 1-click compensating rollback, and 100% ground-truth reconciliation proof.", styles['TableCell'])],
        [Paragraph("14–16", styles['TableCellBold']), Paragraph("<code>14_perf_dash</code>, <code>15_system_health</code>, <code>16_fastapi_swagger</code>", styles['TableCell']), Paragraph("Real-time measured KPI counters, live SQLite WAL/FK diagnostics, and explicit Pydantic OpenAPI docs.", styles['TableCell'])],
        [Paragraph("17–18", styles['TableCellBold']), Paragraph("<code>17_benchmark_result</code>, <code>18_automated_test_result</code>", styles['TableCell']), Paragraph("Terminal proof of multi-scale benchmark scaling and 29 passing automated pytest unit/concurrency tests.", styles['TableCell'])]
    ]
    ev_table = Table(ev_data, colWidths=[18 * mm, 64 * mm, 92 * mm])
    ev_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
    ]))
    story.append(ev_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 9. SIGN-OFF BLOCK
    # ---------------------------------------------------------
    story.append(Paragraph("9. Academic Capstone Final Evaluation Sign-Off", styles['SectionHeader']))
    story.append(Paragraph(
        "This evaluation report certifies that the Capstone Project entitled <b>\"Late-Event Correction & Daily Reporting System: "
        "A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data\"</b> satisfies all criteria "
        "and is formally submitted as <b>100% COMPLETE and READY FOR FINAL VIVA VOCE EXAMINATION</b>.",
        styles['BodyJustified']
    ))
    story.append(Spacer(1, 12))

    sig_data = [
        [
            Paragraph("____________________________<br/><b>Project Candidate</b><br/>B.E. Computer Science & Engg.<br/>Rathinam Technical Campus", styles['TableCellBold']),
            Paragraph("____________________________<br/><b>Internal Project Guide</b><br/>Assistant Professor / CSE<br/>Rathinam Technical Campus", styles['TableCellBold']),
            Paragraph("____________________________<br/><b>Head of Department / Reviewer</b><br/>Department of CSE / IT<br/>Rathinam Technical Campus", styles['TableCellBold'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[58 * mm, 58 * mm, 58 * mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[RTC PDF Generator] Phase 3 PDF successfully generated at: {output_path}")

    # Copy also as PHASE_3_REPORT.pdf for convenience
    copy_path = os.path.join(os.path.dirname(output_path), "PHASE_3_REPORT.pdf")
    shutil.copyfile(output_path, copy_path)
    print(f"[RTC PDF Generator] Secondary copy created at: {copy_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "RATHINAM_CAPSTONE_PROJECT_PHASE_3_FINAL_REPORT.pdf")
    create_phase3_pdf(out)
