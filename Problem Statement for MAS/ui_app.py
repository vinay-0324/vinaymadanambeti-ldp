import streamlit as st
import json
import asyncio
import os
import uuid
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from collections import defaultdict

st.set_page_config(page_title="MAS Risk Assessment", layout="centered")

st.title("Daily Risk Assessment System")
st.write("Upload portfolio and market data to perform risk calculations and generate audit reports.")

st.header("Upload Data Files")

col1, col2, col3 = st.columns(3)

with col1:
    portfolio_file = st.file_uploader(
        "Portfolio Data (JSON)",
        type=['json'],
    )

with col2:
    market_file = st.file_uploader(
        "Market Closes Data (JSON)",
        type=['json'],
    )

with col3:
    risk_config_file = st.file_uploader(
        "Risk Config (JSON)",
        type=['json'],
    )

if portfolio_file and market_file and risk_config_file:
    st.success("All required files uploaded!")
else:
    st.warning(" Please upload all three JSON files to proceed")

st.header(" Configuration")
confidence_level = st.slider(
    "VaR Confidence Level",
    min_value=0.90,
    max_value=0.99,
    value=0.99,
    step=0.01,
    format="%.2f"
)

def compute_historical_var(portfolio, hist_returns, conf_level=0.99):
    """Computes Historical Value at Risk (VaR)"""
    pnl_distribution = []
    num_days = len(next(iter(hist_returns.values())))
    
    for day_index in range(num_days):
        daily_pnl = 0.0
        for asset in portfolio:
            asset_id = asset["Asset ID"]
            qty = asset["Quantity"]
            price = asset["Market Price (USD)"]
            
            if asset_id not in hist_returns:
                continue
                
            daily_return = hist_returns[asset_id][day_index]
            daily_pnl += qty * price * daily_return
        
        pnl_distribution.append(daily_pnl)
    
    pnl_distribution.sort()
    var_index = int((1 - conf_level) * len(pnl_distribution))
    var_99 = abs(pnl_distribution[var_index])
    
    return {
        "VaR_99": round(var_99, 2),
        "pnl_distribution": [round(x, 2) for x in pnl_distribution],
        "mcp_audit_id": str(uuid.uuid4()),
    }

def generate_pdf_report(state):
    """Generate PDF report in memory"""
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
    largest_exposure = f"{largest_sector} (${sector_values.get(largest_sector, 0):,.2f})" if clean_data else "N/A"
    
    if routing_decision == "CLEAR":
        validation_status = "Systemically Approved"
        compliance_status = "Within Limits"
        compliance_color = colors.green
    elif routing_decision == "BREACH":
        validation_status = "Manual Review Required"
        compliance_status = "BREACH Limit Exceeded"
        compliance_color = colors.red
    else:
        validation_status = "Pending Review"
        compliance_status = "Unknown"
        compliance_color = colors.orange
    
    report_id = f"RGA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch)
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
        ["VaR Compliance Threshold", f"${state.get('var_threshold', 550000):,.2f}"],
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
        ["Orchestration Route", f"DIA → FCA → RARA → RGA → {'Manual Review' if routing_decision=='BREACH' else 'END'}"],
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
    buffer.seek(0)
    return buffer, report_id

if st.button(" Run Risk Workflow", type="primary", disabled=not (portfolio_file and market_file and risk_config_file)):
    with st.spinner("Running end-to-end risk analysis..."):
        try:
            portfolio_data = json.load(portfolio_file)
            market_data = json.load(market_file)
            risk_config = json.load(risk_config_file)
            
           
            st.info(" [DIA] Data ingestion in progress...")
            clean_portfolio_data = [
                {
                    "Asset ID": item.get("Asset ID", ""),
                    "Asset Type": item.get("Asset Type", "Unknown"),
                    "Quantity": float(item.get("Quantity", 0)),
                    "Market Price (USD)": float(item.get("Market Price (USD)", 0)),
                    "Sector": item.get("Sector", "N/A")
                }
                for item in portfolio_data
            ]
           
            st.info("[FCA] Computing Value-at-Risk (VaR)...")
            calculated_metrics = compute_historical_var(
                clean_portfolio_data,
                market_data,
                confidence_level
            )
         
            st.info("[RARA] Performing risk assessment...")
            var_threshold = risk_config.get("VaR_threshold_usd", 550000.0)
            calculated_var = calculated_metrics.get("VaR_99")
            
            if calculated_var > var_threshold:
                routing_decision = "BREACH"
                validation_log = "Manual Review Required (VaR Breach)"
            else:
                routing_decision = "CLEAR"
                validation_log = "Auto Approved (No Breach)"
            
            state = {
                "clean_portfolio_data": clean_portfolio_data,
                "calculated_metrics": calculated_metrics,
                "routing_decision": routing_decision,
                "validation_log": validation_log,
                "var_threshold": var_threshold
            }
      
            st.info(" [RGA] Generating risk assessment report...")
            pdf_buffer, report_id = generate_pdf_report(state)
            
            st.success(" Workflow completed successfully!")
           
            st.header(" Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Routing Decision",
                    routing_decision,
                    delta="Breach Detected" if routing_decision == "BREACH" else "Within Limits",
                    delta_color="off" if routing_decision == "BREACH" else "normal"
                )
            
            with col2:
                st.metric(
                    "VaR (99%)",
                    f"${calculated_var:,.2f}",
                    delta=f"Threshold: ${var_threshold:,.2f}",
                    delta_color="inverse"
                )
            
            st.subheader(" Key Metrics")
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.write(f"**Audit ID**: {calculated_metrics.get('mcp_audit_id', 'N/A')[:8]}...")
            
            with metrics_col2:
                st.write(f"**Validation**: {validation_log}")
            
            with metrics_col3:
                total_value = sum(item["Quantity"] * item["Market Price (USD)"] for item in clean_portfolio_data)
                st.write(f"**Portfolio Value**: ${total_value:,.2f}")
         
            st.subheader(" Download Report")
            st.download_button(
                label="⬇ Download PDF Report",
                data=pdf_buffer,
                file_name=f"{report_id}.pdf",
                mime="application/pdf",
                type="primary"
            )
            
            if routing_decision == "BREACH":
                st.error(" **VaR Breach Detected!** Manual review required.")
                with st.expander("View Breach Details"):
                    st.write(f"- **Calculated VaR**: ${calculated_var:,.2f}")
                    st.write(f"- **Threshold**: ${var_threshold:,.2f}")
                    st.write(f"- **Excess**: ${calculated_var - var_threshold:,.2f}")
                    st.write(f"- **Action**: Risk Manager review and mitigation plan required")
            else:
                st.success(" **No Breach Detected** - Portfolio within risk limits")
            
        except Exception as e:
            st.error(f" Error during workflow execution: {str(e)}")
            st.exception(e)

st.markdown("---")
st.caption("MAS Daily Risk Assessment System | Powered by Streamlit")