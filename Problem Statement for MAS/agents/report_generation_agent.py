import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from typing import TypedDict
from collections import defaultdict


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class State(TypedDict, total=False):
    clean_portfolio_data: list
    calculated_metrics: dict
    routing_decision: str
    validation_log: str


def report_generation_agent(state: State):
    print("\n[RGA] Generating Risk Assessment Report...")

    clean_data = state.get("clean_portfolio_data", [])
    calculated_metrics = state.get("calculated_metrics", {})
    routing_decision = state.get("routing_decision", "UNKNOWN")
    validation_log = state.get("validation_log", "N/A")

    var_99 = calculated_metrics.get("VaR_99", 0.0)
    audit_id = calculated_metrics.get("mcp_audit_id", "N/A")

    total_value = sum(item["Quantity"] * item["Market Price (USD)"] for item in clean_data) if clean_data else 0.0

    sector_values = defaultdict(float)
    for item in clean_data:
        sector_values[item["Sector"]] += item["Quantity"] * item["Market Price (USD)"]
    largest_sector = max(sector_values, key=sector_values.get) if sector_values else "N/A"
    largest_exposure = f"{largest_sector} (${sector_values.get(largest_sector, 0):,.2f})"

    if clean_data:
        largest_asset = max(clean_data, key=lambda x: x["Quantity"] * x["Market Price (USD)"])
        largest_loss_contributor = f"{largest_asset['Asset Type']} ({largest_asset['Asset ID']})"
    else:
        largest_loss_contributor = "N/A"

    if routing_decision == "CLEAR":
        validation_status = "Systemically Approved"
        compliance_status = "Within Limits"
        compliance_color = colors.green
    elif routing_decision == "BREACH":
        validation_status = "Manual Review Required"
        compliance_status = "BREACH  Limit Exceeded"
        compliance_color = colors.red
    else:
        validation_status = "Pending Review"
        compliance_status = "Unknown"
        compliance_color = colors.orange

    report_id = f"RGA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    report_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")

    doc = SimpleDocTemplate(report_path, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Daily Portfolio Risk Summary</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"<i>Risk Report ID:</i> {report_id}", styles["Normal"]))
    story.append(Paragraph(f"<i>Date Generated:</i> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>I. Key Risk Metrics</b>", styles["Heading2"]))
    key_metrics = [
        ["VaR (99%, 1-Day)", f"${var_99:,.2f}"],
        ["VaR Compliance Threshold", "$550,000.00"],
        ["Compliance Status", compliance_status],
    ]
    t1 = Table(key_metrics, hAlign="LEFT", colWidths=[220, 220])
    t1.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 2), (1, 2), colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ]))
    story.append(t1)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>II. Audit & Execution Trace</b>", styles["Heading2"]))
    audit_data = [
        ["Total Portfolio Value (V0)", f"${total_value:,.2f}"],
        ["Calculation Method", "Historical Simulation (10-Day Window)"],
        ["MCP Tool Audit ID", audit_id],
        ["Orchestration Route", f"RARA → RGA → {'Manual Review' if routing_decision=='BREACH' else 'END'}"],
    ]
    t2 = Table(audit_data, hAlign="LEFT", colWidths=[220, 300])
    t2.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.2 * inch))

    if routing_decision == "BREACH":
        story.append(Paragraph("<b>III. Breach Details</b>", styles["Heading2"]))
        breach_details = [
            ["Breach Type", "Value-at-Risk Limit Exceeded"],
            ["Breach Detected On", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Action Required", "Risk Manager review and mitigation plan submission"],
            ["Status", "Pending Manual Approval"],
        ]
        t3 = Table(breach_details, hAlign="LEFT", colWidths=[220, 300])
        t3.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ]))
        story.append(t3)
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>IV. Validation Signature</b>", styles["Heading2"]))
    validation_data = [
        ["Validation Status", validation_status],
        ["Validation Notes", validation_log],
    ]
    t5 = Table(validation_data, hAlign="LEFT", colWidths=[220, 300])
    t5.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t5)

    doc.build(story)
    print(f"[RGA] Report successfully generated at: {report_path}")
    state["report_path"] = report_path
    return state

