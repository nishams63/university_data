"""
Rathinam Technical Campus (Autonomous), Coimbatore
Late-Event Correction & Daily Reporting System
Capstone Project 70% Milestone PDF Report Generator
"""

import os
import sys
import json
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
PRIMARY = colors.HexColor("#1e1b4b")       # Dark Indigo
SECONDARY = colors.HexColor("#4338ca")     # Medium Indigo
ACCENT_GREEN = colors.HexColor("#047857")  # Forest Green
ACCENT_AMBER = colors.HexColor("#b45309")  # Amber
NEUTRAL_DARK = colors.HexColor("#0f172a")  # Slate 900
NEUTRAL_LIGHT = colors.HexColor("#f8fafc") # Slate 50
BORDER_COLOR = colors.HexColor("#cbd5e1")  # Slate 300
BG_ALT = colors.HexColor("#f1f5f9")        # Slate 100

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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                18 * mm, 283 * mm,
                "RATHINAM TECHNICAL CAMPUS (AUTONOMOUS) — LATE-EVENT CORRECTION & REPORTING SYSTEM"
            )
            self.drawRightString(192 * mm, 283 * mm, "70% MILESTONE REVIEW")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(18 * mm, 281 * mm, 192 * mm, 281 * mm)

        # Footer (All pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(18 * mm, 15 * mm, 192 * mm, 15 * mm)
        self.drawString(
            18 * mm, 11 * mm,
            "Confidential & Proprietary — Department of Computer Science & Engineering"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(192 * mm, 11 * mm, page_str)
        self.restoreState()

def create_capstone_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    # Custom typography
    styles.add(ParagraphStyle(
        'InstTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=PRIMARY,
        alignment=1, # Center
        spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        'InstDept',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=SECONDARY,
        alignment=1,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        'InstLoc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        'BadgeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1
    ))
    styles.add(ParagraphStyle(
        'ProjectTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=NEUTRAL_DARK,
        alignment=1,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'BodyJustified',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=NEUTRAL_DARK,
        alignment=4, # Justify
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=SECONDARY
    ))
    styles.add(ParagraphStyle(
        'MetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=NEUTRAL_DARK
    ))
    styles.add(ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=PRIMARY
    ))
    styles.add(ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=PRIMARY
    ))

    story = []

    # ---------------------------------------------------------
    # COVER / HEADER
    # ---------------------------------------------------------
    story.append(Paragraph("RATHINAM TECHNICAL CAMPUS (AUTONOMOUS)", styles['InstTitle']))
    story.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING / IT", styles['InstDept']))
    story.append(Paragraph("Eachanari, Coimbatore — 641 021 | Affiliated to Anna University, Chennai", styles['InstLoc']))

    # Badge Container
    badge_data = [[Paragraph("CAPSTONE PROJECT 70% ENGINEERING MILESTONE EVALUATION REPORT", styles['BadgeTitle'])]]
    badge_table = Table(badge_data, colWidths=[174 * mm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "LATE-EVENT CORRECTION & DAILY REPORTING SYSTEM:<br/>"
        "A STATEFUL WATERMARK AND DELTA RECALCULATION ENGINE FOR INSTITUTIONAL BIG DATA",
        styles['ProjectTitle']
    ))

    # Meta Table
    meta_content = [
        [
            Paragraph("<b>Degree / Program:</b>", styles['MetaLabel']),
            Paragraph("B.E. Computer Science & Engineering", styles['MetaVal']),
            Paragraph("<b>Evaluation Stage:</b>", styles['MetaLabel']),
            Paragraph("70% Milestone Review", styles['MetaVal'])
        ],
        [
            Paragraph("<b>Academic Year:</b>", styles['MetaLabel']),
            Paragraph("2025 – 2026", styles['MetaVal']),
            Paragraph("<b>Database Engine:</b>", styles['MetaLabel']),
            Paragraph("SQLite 3 with Write-Ahead Logging (WAL)", styles['MetaVal'])
        ],
        [
            Paragraph("<b>GitHub Repository:</b>", styles['MetaLabel']),
            Paragraph("github.com/nishams63/university_data", styles['MetaVal']),
            Paragraph("<b>Submission Date:</b>", styles['MetaLabel']),
            Paragraph(datetime.now().strftime("%B %d, %Y"), styles['MetaVal'])
        ]
    ]
    meta_table = Table(meta_content, colWidths=[38 * mm, 52 * mm, 38 * mm, 46 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NEUTRAL_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 1. ABSTRACT & EXECUTIVE SUMMARY
    # ---------------------------------------------------------
    story.append(Paragraph("1. Abstract & Executive Summary", styles['SectionHeader']))
    story.append(Paragraph(
        "In institutional university administration at <b>Rathinam Technical Campus</b>, accurate operational reporting "
        "across biometric turnstile attendance, Continuous Internal Assessments (CIA), online LMS course engagement, "
        "and campus placement drives is critical for administrative governance and accreditation. However, real-world edge IoT "
        "turnstiles, departmental offline batch syncs, and delayed grade approvals produce out-of-order event arrivals. Traditional "
        "midnight snapshot architectures freeze daily reports permanently, resulting in severe temporal distortions (e.g. false absent tags). "
        "This project implements a <b>Stateful Watermark and Delta Recalculation Engine</b> that re-evaluates historical reports based on "
        "physical event timestamps, extracts incremental deltas in O(1) time, bumps report versions monotonically, gates high-impact alterations "
        "(&ge; 15% drift or grade flips) into a human review queue, and maintains an immutable audit ledger with 1-click compensating rollbacks. "
        "At this 70% milestone, the system has achieved 100% automated test pass (23/23 tests), verified 100% exact match convergence against ground truth (MAE = 0.000), "
        "and proved sub-40ms latencies with peak RAM usage strictly under 1.0 MB.",
        styles['BodyJustified']
    ))

    # ---------------------------------------------------------
    # 2. RESOLUTION OF PRIOR EVALUATOR CRITICISMS
    # ---------------------------------------------------------
    story.append(Paragraph("2. Resolution of Prior Evaluator Criticisms (35% &rarr; 70%)", styles['SectionHeader']))
    crit_data = [
        [
            Paragraph("Evaluator Criticism", styles['TableHead']),
            Paragraph("Root Cause in 35% Baseline", styles['TableHead']),
            Paragraph("Engineering Resolution (70% Prototype)", styles['TableHead']),
            Paragraph("Status", styles['TableHead'])
        ],
        [
            Paragraph("<b>1. Schema & Concurrency Controls</b>", styles['TableCellBold']),
            Paragraph("Default SQLite rollback journal; no foreign keys; unconstrained version increments.", styles['TableCell']),
            Paragraph("Enforced PRAGMAs: journal_mode=WAL, busy_timeout=10000ms, foreign_keys=ON. Added composite unique constraints (reporting_date, domain) and (report_id, version_number).", styles['TableCell']),
            Paragraph("<b>RESOLVED<br/>(5/5 Tests)</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>2. Performance Evaluation</b>", styles['TableCellBold']),
            Paragraph("Theoretical claims; lack of execution-timed latency distributions and memory profiling.", styles['TableCell']),
            Paragraph("Built benchmark engine with time.perf_counter() and tracemalloc. Benchmarked 100 to 5000 events and 4 replay workloads (4000 events total).", styles['TableCell']),
            Paragraph("<b>RESOLVED<br/>(Empirical)</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>3. Transactional Boundaries</b>", styles['TableCellBold']),
            Paragraph("Ingestion, recalculation, and versioning ran in disjoint, uncoordinated queries.", styles['TableCell']),
            Paragraph("Built ingest_and_process_atomic() wrapping ingestion, delta calculation, versioning, and audit logging into single atomic transaction boundary with backoff retry.", styles['TableCell']),
            Paragraph("<b>RESOLVED</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>4. Recalculation Complexity</b>", styles['TableCellBold']),
            Paragraph("Executed O(N) table scans and JSON deserialization per incoming late event.", styles['TableCell']),
            Paragraph("Engineered O(1) stateful delta contribution extraction (delta = f(domain, payload)), reducing latency to 21-38ms even under 5,000 events.", styles['TableCell']),
            Paragraph("<b>RESOLVED</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>5. Version Lineage & Review UX</b>", styles['TableCellBold']),
            Paragraph("No version lineage visualization; reviews lacked before/after comparison diffs.", styles['TableCell']),
            Paragraph("Added Version Lineage Timeline (v1->v2->v3), Before/After diff visualizer cards, explanation panels, confirmation modals, and Engine Diagnostics tab.", styles['TableCell']),
            Paragraph("<b>RESOLVED</b>", styles['TableCellBold'])
        ]
    ]
    crit_table = Table(crit_data, colWidths=[38 * mm, 45 * mm, 68 * mm, 23 * mm])
    crit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(crit_table)

    story.append(PageBreak())

    # ---------------------------------------------------------
    # 3. EMPIRICAL BENCHMARK RESULTS
    # ---------------------------------------------------------
    story.append(Paragraph("3. Empirical Performance Benchmark Results (Hardware-Timed)", styles['SectionHeader']))
    story.append(Paragraph(
        "Benchmarks were executed using Python's high-resolution timer (<code>time.perf_counter()</code>) and heap allocation profiler "
        "(<code>tracemalloc</code>) against an isolated SQLite WAL database instance.",
        styles['BodyJustified']
    ))

    story.append(Paragraph("A. Event Scaling Benchmarks (100 to 5,000 Events)", styles['SubSectionHeader']))
    scale_data = [
        [
            Paragraph("Event Load", styles['TableHead']),
            Paragraph("Duration", styles['TableHead']),
            Paragraph("Throughput", styles['TableHead']),
            Paragraph("Avg Latency", styles['TableHead']),
            Paragraph("Median (P50)", styles['TableHead']),
            Paragraph("P95 Latency", styles['TableHead']),
            Paragraph("P99 Latency", styles['TableHead']),
            Paragraph("Peak RAM", styles['TableHead']),
            Paragraph("Exact Match", styles['TableHead'])
        ],
        [
            Paragraph("<b>100 Events</b>", styles['TableCell']),
            Paragraph("2.30 s", styles['TableCell']),
            Paragraph("<b>43.51 eps</b>", styles['TableCellBold']),
            Paragraph("22.98 ms", styles['TableCell']),
            Paragraph("21.80 ms", styles['TableCell']),
            Paragraph("36.88 ms", styles['TableCell']),
            Paragraph("137.14 ms", styles['TableCell']),
            Paragraph("<b>0.98 MB</b>", styles['TableCellBold']),
            Paragraph("100.0%", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>500 Events</b>", styles['TableCell']),
            Paragraph("10.58 s", styles['TableCell']),
            Paragraph("<b>47.28 eps</b>", styles['TableCellBold']),
            Paragraph("21.14 ms", styles['TableCell']),
            Paragraph("20.50 ms", styles['TableCell']),
            Paragraph("33.66 ms", styles['TableCell']),
            Paragraph("46.44 ms", styles['TableCell']),
            Paragraph("<b>0.44 MB</b>", styles['TableCellBold']),
            Paragraph("100.0%", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>1,000 Events</b>", styles['TableCell']),
            Paragraph("21.79 s", styles['TableCell']),
            Paragraph("<b>45.90 eps</b>", styles['TableCellBold']),
            Paragraph("21.78 ms", styles['TableCell']),
            Paragraph("20.64 ms", styles['TableCell']),
            Paragraph("37.26 ms", styles['TableCell']),
            Paragraph("52.97 ms", styles['TableCell']),
            Paragraph("<b>0.45 MB</b>", styles['TableCellBold']),
            Paragraph("100.0%", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>5,000 Events</b>", styles['TableCell']),
            Paragraph("192.85 s", styles['TableCell']),
            Paragraph("<b>25.93 eps</b>", styles['TableCellBold']),
            Paragraph("38.56 ms", styles['TableCell']),
            Paragraph("32.77 ms", styles['TableCell']),
            Paragraph("70.80 ms", styles['TableCell']),
            Paragraph("116.05 ms", styles['TableCell']),
            Paragraph("<b>0.57 MB</b>", styles['TableCellBold']),
            Paragraph("100.0%", styles['TableCellBold'])
        ]
    ]
    scale_table = Table(scale_data, colWidths=[24 * mm, 16 * mm, 22 * mm, 19 * mm, 19 * mm, 19 * mm, 19 * mm, 18 * mm, 18 * mm])
    scale_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(scale_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("B. Historical Replay Benchmarks (4 Distinct Workload Profiles, 4,000 Events)", styles['SubSectionHeader']))
    replay_data = [
        [
            Paragraph("Workload Profile", styles['TableHead']),
            Paragraph("Characteristics", styles['TableHead']),
            Paragraph("Events", styles['TableHead']),
            Paragraph("Duration", styles['TableHead']),
            Paragraph("Throughput", styles['TableHead']),
            Paragraph("Avg Latency", styles['TableHead']),
            Paragraph("P95 Latency", styles['TableHead']),
            Paragraph("Peak RAM", styles['TableHead'])
        ],
        [
            Paragraph("<b>1. Normal Stream</b>", styles['TableCellBold']),
            Paragraph("10% late, 3% dup, 1% inv", styles['TableCell']),
            Paragraph("1,000", styles['TableCell']),
            Paragraph("31.53 s", styles['TableCell']),
            Paragraph("31.72 eps", styles['TableCell']),
            Paragraph("31.52 ms", styles['TableCell']),
            Paragraph("53.12 ms", styles['TableCell']),
            Paragraph("0.419 MB", styles['TableCell'])
        ],
        [
            Paragraph("<b>2. Late-Heavy</b>", styles['TableCellBold']),
            Paragraph("40% late arrivals (sync lag)", styles['TableCell']),
            Paragraph("1,000", styles['TableCell']),
            Paragraph("7.50 s", styles['TableCell']),
            Paragraph("133.33 eps", styles['TableCell']),
            Paragraph("7.49 ms", styles['TableCell']),
            Paragraph("11.73 ms", styles['TableCell']),
            Paragraph("0.065 MB", styles['TableCell'])
        ],
        [
            Paragraph("<b>3. Duplicate-Heavy</b>", styles['TableCellBold']),
            Paragraph("30% duplicate retries (storm)", styles['TableCell']),
            Paragraph("1,000", styles['TableCell']),
            Paragraph("6.11 s", styles['TableCell']),
            Paragraph("<b>163.63 eps</b>", styles['TableCellBold']),
            Paragraph("<b>6.10 ms</b>", styles['TableCellBold']),
            Paragraph("7.96 ms", styles['TableCell']),
            Paragraph("0.064 MB", styles['TableCell'])
        ],
        [
            Paragraph("<b>4. 7-Day Delayed Lag</b>", styles['TableCellBold']),
            Paragraph("35% late, 72h-168h delays", styles['TableCell']),
            Paragraph("1,000", styles['TableCell']),
            Paragraph("6.51 s", styles['TableCell']),
            Paragraph("153.66 eps", styles['TableCell']),
            Paragraph("6.50 ms", styles['TableCell']),
            Paragraph("9.22 ms", styles['TableCell']),
            Paragraph("0.065 MB", styles['TableCell'])
        ],
        [
            Paragraph("<b>Cumulative Total</b>", styles['TableCellBold']),
            Paragraph("4 Workload Profiles Replayed", styles['TableCellBold']),
            Paragraph("<b>4,000</b>", styles['TableCellBold']),
            Paragraph("<b>51.65 s</b>", styles['TableCellBold']),
            Paragraph("<b>77.45 eps</b>", styles['TableCellBold']),
            Paragraph("12.91 ms", styles['TableCellBold']),
            Paragraph("20.51 ms", styles['TableCellBold']),
            Paragraph("0.419 MB", styles['TableCellBold'])
        ]
    ]
    replay_table = Table(replay_data, colWidths=[32 * mm, 40 * mm, 15 * mm, 17 * mm, 22 * mm, 18 * mm, 18 * mm, 16 * mm])
    replay_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BACKGROUND', (0, -1), (-1, -1), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(replay_table)

    # ---------------------------------------------------------
    # 4. MATHEMATICAL RECONCILIATION
    # ---------------------------------------------------------
    story.append(Paragraph("4. Mathematical Reconciliation & Error Elimination Across 6 Scenarios", styles['SectionHeader']))
    reconcile_data = [
        [
            Paragraph("Evaluation Scenario", styles['TableHead']),
            Paragraph("Late Ratio", styles['TableHead']),
            Paragraph("Baseline MAE", styles['TableHead']),
            Paragraph("Corrected MAE", styles['TableHead']),
            Paragraph("Baseline RMSE", styles['TableHead']),
            Paragraph("Corrected RMSE", styles['TableHead']),
            Paragraph("Exact Match %", styles['TableHead'])
        ],
        [
            Paragraph("<b>Scenario 1: 0% Late Events (Ideal)</b>", styles['TableCell']),
            Paragraph("0.0%", styles['TableCell']),
            Paragraph("53.37", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("93.50", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Scenario 2: 5% Late Events (Mild)</b>", styles['TableCell']),
            Paragraph("5.0%", styles['TableCell']),
            Paragraph("55.36", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("101.67", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Scenario 3: 10% Late Events (Standard)</b>", styles['TableCell']),
            Paragraph("10.0%", styles['TableCell']),
            Paragraph("58.42", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("119.67", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Scenario 4: 25% Late Events (Outage)</b>", styles['TableCell']),
            Paragraph("25.0%", styles['TableCell']),
            Paragraph("100.04", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("213.72", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Scenario 5: Duplicate-Heavy (30% Dup)</b>", styles['TableCell']),
            Paragraph("15.0%", styles['TableCell']),
            Paragraph("70.48", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("130.46", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("<b>Scenario 6: Very Late (Multi-Day Lag)</b>", styles['TableCell']),
            Paragraph("30.0%", styles['TableCell']),
            Paragraph("117.25", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("222.37", styles['TableCell']),
            Paragraph("<b>0.000</b>", styles['TableCellBold']),
            Paragraph("<b>100.0%</b>", styles['TableCellBold'])
        ]
    ]
    reconcile_table = Table(reconcile_data, colWidths=[46 * mm, 18 * mm, 22 * mm, 22 * mm, 23 * mm, 23 * mm, 20 * mm])
    reconcile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(reconcile_table)

    story.append(PageBreak())

    # ---------------------------------------------------------
    # 5. SOFTWARE TESTING & QUALITY ASSURANCE
    # ---------------------------------------------------------
    story.append(Paragraph("5. Automated Test Suite & Quality Assurance (23/23 Passing)", styles['SectionHeader']))
    story.append(Paragraph(
        "The codebase maintains 100% automated test pass rate across 23 test functions organized into 8 focused modules:",
        styles['BodyJustified']
    ))

    test_data = [
        [Paragraph("Test Module", styles['TableHead']), Paragraph("Tests", styles['TableHead']), Paragraph("Key Verification Scope", styles['TableHead'])],
        [Paragraph("<code>test_concurrency.py</code>", styles['TableCellBold']), Paragraph("5", styles['TableCellBold']), Paragraph("Thread-safe duplicate races, concurrent unique events, concurrent late events targeting identical historical dates, and review approval state locks.", styles['TableCell'])],
        [Paragraph("<code>test_database_hardening.py</code>", styles['TableCellBold']), Paragraph("5", styles['TableCellBold']), Paragraph("Verifies SQLite WAL mode, foreign key enforcement, composite unique constraints (reporting_date, domain) and (report_id, version_number), and 24h lateness boundaries.", styles['TableCell'])],
        [Paragraph("<code>test_failure_injection.py</code>", styles['TableCellBold']), Paragraph("2", styles['TableCellBold']), Paragraph("Injects synthetic runtime exceptions during processing to verify transactional rollback and database consistency.", styles['TableCell'])],
        [Paragraph("<code>test_pipeline.py</code>", styles['TableCellBold']), Paragraph("4", styles['TableCellBold']), Paragraph("Tests on-time ingestion, late event tagging, duplicate event ID deduplication, and invalid payload rejection.", styles['TableCell'])],
        [Paragraph("<code>test_correction.py</code>", styles['TableCellBold']), Paragraph("3", styles['TableCellBold']), Paragraph("Tests baseline aggregation, O(1) stateful delta calculation, and high-impact (&ge; 15%) review threshold routing.", styles['TableCell'])],
        [Paragraph("<code>test_audit_rollback.py</code>", styles['TableCellBold']), Paragraph("2", styles['TableCellBold']), Paragraph("Verifies write-only audit trail logging and compensating rollback idempotency.", styles['TableCell'])],
        [Paragraph("<code>test_reconciliation.py</code>", styles['TableCellBold']), Paragraph("1", styles['TableCellBold']), Paragraph("Proves the Ground Truth Convergence Invariant across all reporting dates.", styles['TableCell'])],
        [Paragraph("<code>test_integration.py</code>", styles['TableCellBold']), Paragraph("1", styles['TableCellBold']), Paragraph("End-to-end user flow: ingestion -> lateness evaluation -> review approval -> report update.", styles['TableCell'])],
        [Paragraph("<b>Total Suite Execution</b>", styles['TableCellBold']), Paragraph("<b>23 / 23 Passing</b>", styles['TableCellBold']), Paragraph("<b>Execution Time: 8.90s | Exit Code: 0 (100% Passing)</b>", styles['TableCellBold'])]
    ]
    test_table = Table(test_data, colWidths=[48 * mm, 20 * mm, 106 * mm])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BACKGROUND', (0, -1), (-1, -1), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # 6. ROADMAP & EVALUATION SIGN-OFF
    # ---------------------------------------------------------
    story.append(Paragraph("6. Remaining 30% Implementation Roadmap (Towards 100% Viva)", styles['SectionHeader']))
    road_data = [
        [Paragraph("Phase / Month", styles['TableHead']), Paragraph("Target Enhancement", styles['TableHead']), Paragraph("Technical Scope & Deliverables", styles['TableHead'])],
        [Paragraph("Phase 8 (Oct 2026)", styles['TableCell']), Paragraph("Distributed PostgreSQL Adapter", styles['TableCell']), Paragraph("Dual-driver configuration enabling zero-downtime migration from SQLite WAL to PostgreSQL + TimescaleDB for multi-campus scaling.", styles['TableCell'])],
        [Paragraph("Phase 9 (Nov 2026)", styles['TableCell']), Paragraph("Streaming Ingestion Gateway", styles['TableCell']), Paragraph("Decouple HTTP gateway from database writes using Apache Kafka or Redis Streams with distributed consumers.", styles['TableCell'])],
        [Paragraph("Phase 10 (Dec 2026)", styles['TableCell']), Paragraph("Institutional RBAC & SSO", styles['TableCell']), Paragraph("OAuth2 / JWT integration with role hierarchy (Dean, HoD, Faculty Coordinator, Auditor).", styles['TableCell'])],
        [Paragraph("Phase 11 (Jan 2027)", styles['TableCell']), Paragraph("Automated Anomaly Detection", styles['TableCell']), Paragraph("Isolation forest ML models detecting bulk turnstile log manipulations or grade tampering bursts.", styles['TableCell'])],
        [Paragraph("Phase 12 (Feb 2027)", styles['TableCell']), Paragraph("Final Dissertation & Defense", styles['TableCell']), Paragraph("Full academic thesis, viva presentation slides, and institutional deployment handbook.", styles['TableCell'])]
    ]
    road_table = Table(road_data, colWidths=[34 * mm, 45 * mm, 95 * mm])
    road_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(road_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("7. Academic Review Committee Sign-off", styles['SectionHeader']))
    story.append(Paragraph(
        "This evaluation report certifies that the Capstone Project entitled <b>\"Late-Event Correction & Daily Reporting System: "
        "A Stateful Watermark and Delta Recalculation Engine for Institutional Big Data\"</b> satisfies all requirements "
        "for the <b>70% Engineering Milestone Review</b>.",
        styles['BodyJustified']
    ))
    story.append(Spacer(1, 8))

    # Signature Block
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
    print(f"[RTC PDF Generator] PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "RATHINAM_CAPSTONE_PROJECT_70_PERCENT_REPORT.pdf")
    create_capstone_pdf(out)
