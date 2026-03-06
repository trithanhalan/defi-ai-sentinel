# DeFi AI Sentinel 🛡️

*Enterprise-grade Smart Contract Risk, Whale Monitoring, and Governance AI Agent Platform.*

## Overview

The **DeFi AI Sentinel** is a comprehensive, modular AI system designed for the Web3 and DeFi ecosystems. Built on top of Avalanche C-Chain infrastructure, it combines on-chain heuristic scanning with advanced Large Language Models (LLMs) to provide automated auditing, systemic risk monitoring, and decentralized governance intelligence.

This platform proves the viability of multi-agent LLM systems in high-risk financial environments.

### 4 Core Modules

1. **Smart Contract Risk Engine (`part1_risk_engine.py`)** 
   - Dynamically fetches verified source code and bytecode from block explorers (Snowtrace).
   - Runs heuristic pattern matching for common Web3 vulnerabilities (Reentrancy, Unchecked External Calls, Permissions, Centralization).
   - Generates an automated Risk Score (0-100).

2. **Whale Transaction Monitor (`part2_whale_monitor.py`)**
   - Asynchronous Web3 listener that scans blockchain blocks for ERC-20 Transfer events.
   - Cross-references on-chain data with CoinGecko pricing APIs to detect high-value capital flights in real-time.
   - Capable of webhook integrations for Discord/Slack alerts.

3. **LLM Compliance & Report Generator (`part3_llm_reporter.py`)**
   - Ingests the heuristic findings of the Risk Engine.
   - Utilizes `gpt-4-turbo` or `gpt-3.5-turbo` to generate professional, human-readable compliance and security audit reports.
   - Designed for DAO boards and technical compliance officers.

4. **Governance Proposal AI Agent (`part4_governance_agent.py`)**
   - Evaluates DAO governance text proposals and technical payloads.
   - Simulates protocol economic and security impact.
   - Automatically generates a "For", "Against", or "Abstain" voting recommendation with LLM-backed justification.
   
---

## Installation & Setup

### 1. Requirements

Ensure you have Python 3.10+ installed.

```bash
git clone https://github.com/trithanhalan/defi-ai-sentinel.git
cd defi-ai-sentinel

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

While you can input API keys directly into the UI, it is recommended to set up a `.env` file in the root directory for local development:

```env
AVALANCHE_RPC_URL=https://api.avax.network/ext/bc/C/rpc
SNOWTRACE_API_KEY=your_snowtrace_key
OPENAI_API_KEY=your_openai_key
WEBHOOK_URL=your_optional_discord_webhook_url
```

### 3. Running the Application

This system includes a unified **Streamlit Dashboard** that ties the internal AI and Web3 modules together using a modern SaaS dark-theme styling architecture.

```bash
streamlit run app.py
```

---

## Architectural Notes

- **Decoupled Logic:** The core AI engines within `trustmesh_ai/` are explicitly decoupled from the Streamlit UI (`app.py`). This allows the logic to be seamlessly transitioned to an enterprise `FastAPI` or `Next.js` backend API architecture as the system scales.
- **Agentic Workflows:** The system is designed to evolve into an autonomous "Agentic Workflow" where the Risk Engine triggers the LLM reporter natively before executing on-chain transactions via the Governance Agent.

---

*Authored by Tri Thanh Alan. Designed to demonstrate Hybrid PM & Technical Architecture capabilities.*
