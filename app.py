import streamlit as st
import asyncio
import json
from utils.ui import inject_css, render_header, render_metric_card

# Configure page (Must be the first Streamlit command)
st.set_page_config(
    page_title="TrustMesh AI | DeFi Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Global Enterprise Styling
inject_css()

# Sidebar Navigation
with st.sidebar:
    st.image("https://cryptologos.cc/logos/avalanche-avax-logo.png?v=025", width=50) # Example logo
    st.markdown("## 🛡️ DeFi AI Sentinel")
    st.markdown("Enterprise-grade Smart Contract Risk & Governance Intelligence.")
    
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["Dashboard", "Smart Contract Scanner", "Whale Monitor", "Governance Simulator"]
    )
    
    st.markdown("---")
    
    # API Key configurations
    st.markdown("### 🔑 API Integrations")
    snowtrace_key = st.text_input("Snowtrace API Key", type="password", help="Required for fetching source code on Avalanche.")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Required for LLM Reports and Governance Risk Analysis.")
    
    st.markdown("---")
    st.caption("Powered by Next.js/FastAPI decoupled backend architecture (simulated in Streamlit).")


# --- Main Application Logic ---

if page == "Dashboard":
    render_header("TrustMesh AI Overview", "Unified intelligence platform for DeFi security.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Contracts Scanned", "142", "⬆ 12% vs last week")
    with col2:
        render_metric_card("High Risk Identified", "8", "Action Required", is_positive=False)
    with col3:
        render_metric_card("Whale Alerts (24h)", "15", "Normal volume")
    with col4:
        render_metric_card("Proposals Analyzed", "3", "Recent Gov. Votes")
        
    st.markdown("### 🌐 Ecosystem Health (Avalanche C-Chain)")
    st.info("System operational. Integrating multi-agent analysis modules...")


elif page == "Smart Contract Scanner":
    render_header("Smart Contract Risk Engine", "Automated heuristic scanning and LLM-powered compliance auditing.")
    
    contract_address = st.text_input("Contract Address (0x...)", placeholder="Enter Avalanche C-Chain contract address")
    
    if st.button("Initialize Deep Scan", type="primary") and contract_address:
        with st.spinner("Connecting to RPC & Fetching Source Code via Snowtrace..."):
            try:
                # Dynamic importing to avoid global load times
                from trustmesh_ai.risk_engine import SmartContractRiskEngine
                # Ensure the engine runs with the provided API key
                import os
                # Pass secrets directly if available
                os.environ["SNOWTRACE_API_KEY"] = snowtrace_key if snowtrace_key else os.getenv("SNOWTRACE_API_KEY", "")
                
                engine = SmartContractRiskEngine()
                results = engine.analyze_contract(contract_address)
                
                # Display Results
                st.success(f"Scan Complete: {results.get('contract_name', 'Unknown Contract')}")
                
                score = results.get('risk_score', 0)
                score_color = "red" if score < 40 else "orange" if score < 70 else "green"
                st.markdown(f"### Overall Security Score: <span style='color:{score_color}'>{score}/100</span>", unsafe_allow_html=True)
                
                st.markdown("#### 🔍 Automated Findings:")
                if results.get("findings"):
                    for finding in results.get("findings"):
                        with st.expander(f"⚠️ {finding['vulnerability']} (Impact: {finding['severity_score_impact']})"):
                            st.write(finding['details'])
                else:
                    st.info("No immediate heuristic vulnerabilities found.")
                
                # Generate LLM Report
                st.markdown("---")
                st.markdown("### 🤖 Generative AI Compliance Audit")
                if openai_key or os.getenv("OPENAI_API_KEY"):
                    with st.spinner("Generating LLM Risk Assessment..."):
                        os.environ["OPENAI_API_KEY"] = openai_key if openai_key else os.getenv("OPENAI_API_KEY", "")
                        from trustmesh_ai.llm_reporter import LLMReportGenerator
                        reporter = LLMReportGenerator()
                        markdown_report, _ = reporter.generate_compliance_report(
                            contract_name=results.get('contract_name'),
                            contract_address=contract_address,
                            risk_analysis_results=results
                        )
                        st.markdown(markdown_report)
                else:
                    st.warning("Please provide an OpenAI API Key in the sidebar to generate the AI compliance report.")
                    
            except Exception as e:
                st.error(f"Error during scan: {e}")

elif page == "Whale Monitor":
    render_header("Whale Transaction Monitoring", "Real-time liquidity flow and systemic risk detection.")
    
    st.info("Live indexing simulated. Historical context loaded for demonstration.")
    target_token = st.text_input("Target Token Address", value="0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7", help="WAVAX default")
    threshold = st.number_input("Alert Threshold (USD)", value=50000)
    
    if st.button("Start Monitor"):
        st.warning("⚠️ Full block scanning requires a dedicated backend daemon. This UI represents the configuration interface for the remote async worker cluster.")
        
        # Displaying simulated logic for portfolio proof-of-concept
        st.markdown("### Simulated Recent Alerts for " + target_token)
        alerts = [
            {"time": "10s ago", "amount": "45,000 WAVAX ~$1.2M", "from": "0xTrader...", "to": "0xBinance..."},
            {"time": "2m ago", "amount": "12,000 WAVAX ~$320K", "from": "0xUnknown...", "to": "0xTraderJoe..."}
        ]
        import pandas as pd
        st.dataframe(pd.DataFrame(alerts), use_container_width=True)


elif page == "Governance Simulator":
    render_header("Governance AI Agent", "Simulate LLM risk assessments on decentralized autonomous organization proposals.")
    
    st.markdown("Evaluate DAO proposals for economic risk, centralization vectors, and technical safety before voting.")
    
    proposal_text = st.text_area("Paste DAO Proposal Description", height=200, placeholder="**Proposal:** Upgrade TreasuryManager.sol to allow 50% fund diversion...")
    
    if st.button("Simulate AI Vote Recommendation") and proposal_text:
        if openai_key or os.getenv("OPENAI_API_KEY"):
            with st.spinner("Agent analyzing governance impact..."):
                os.environ["OPENAI_API_KEY"] = openai_key if openai_key else os.getenv("OPENAI_API_KEY", "")
                from trustmesh_ai.governance_agent import GovernanceProposalAgent
                agent = GovernanceProposalAgent()
                
                # Mock technical details
                mock_technical = {"targets": ["0xDAO"], "values": [0], "signatures": ["upgrade()"]}
                result = agent.analyze_proposal("Manual-Simulation", proposal_text, mock_technical)
                
                st.markdown("### Agent Recommendation")
                rec = result.get('vote_recommendation', 'Error')
                rec_color = "red" if "Against" in rec else "green" if "For" in rec else "orange"
                st.markdown(f"## <span style='color:{rec_color}'>{rec}</span>", unsafe_allow_html=True)
                
                st.markdown("#### 🧠 Justification")
                st.info(result.get('justification', 'No justification provided.'))
                
                st.markdown("#### 📊 Impact Assessment")
                st.write(result.get('impact_assessment', 'N/A'))
        else:
             st.warning("Please provide an OpenAI API Key in the sidebar to run the Governance Agent.")
