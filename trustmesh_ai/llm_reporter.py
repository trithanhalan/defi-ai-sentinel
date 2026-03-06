# trustmesh_ai/part3_llm_reporter.py
import os
import json
from openai import OpenAI # Using the official OpenAI library
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("[WARN] OPENAI_API_KEY not found in environment variables. LLM Reporter will not function.")
    # raise ValueError("OPENAI_API_KEY not found in environment variables.")

# Initialize OpenAI client if API key is available
try:
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception as e:
    print(f"[ERROR] Failed to initialize OpenAI client: {e}")
    client = None


class LLMReportGenerator:
    def __init__(self, model="gpt-3.5-turbo-0125"): # Or "gpt-4-turbo-preview" for better quality
        self.model = model
        if not client:
            print("[ERROR] OpenAI client not initialized. LLMReportGenerator may not work.")


    def generate_compliance_report(self, contract_name, contract_address, risk_analysis_results, on_chain_activity_summary=None):
        if not client:
            return "# LLM Report Generation Failed: OpenAI Client Not Initialized\n\nCould not connect to OpenAI. Please check your API key and network.", {}

        # Extract key info from risk_analysis_results
        risk_score = risk_analysis_results.get("risk_score", "N/A")
        findings = risk_analysis_results.get("findings", [])
        owner_address_identified = risk_analysis_results.get("analysis_summary", {}).get("owner_address_identified", "Not explicitly identified by automated scan")

        findings_summary_for_llm = []
        for f in findings:
            findings_summary_for_llm.append(
                f"- Vulnerability: {f.get('vulnerability', 'N/A')}\n"
                f"  Details: {f.get('details', 'N/A')}\n"
                f"  Severity Impact (Internal): {f.get('severity_score_impact', 'N/A')}"
            )
        
        findings_text = "\n".join(findings_summary_for_llm) if findings_summary_for_llm else "No specific vulnerabilities flagged by automated scan."

        on_chain_text = "No specific on-chain activity data provided for this report."
        if on_chain_activity_summary:
            on_chain_text = "Key On-Chain Activity Insights (if available):\n"
            if on_chain_activity_summary.get("whale_alerts_count"):
                on_chain_text += f"- Recent Whale Alerts Count: {on_chain_activity_summary['whale_alerts_count']}\n"
            if on_chain_activity_summary.get("top_holder_concentration"): # Example data structure
                 on_chain_text += f"- Top Holder Concentration: {on_chain_activity_summary['top_holder_concentration']}\n"
            if on_chain_activity_summary.get("defi_spike_alerts"):
                 on_chain_text += f"- DeFi Protocol Spike Alerts: {on_chain_activity_summary['defi_spike_alerts']}\n"


        prompt = f"""
        You are TrustMesh AI, an advanced AI specializing in smart contract auditing and blockchain compliance.
        Generate a comprehensive compliance and security audit report for the following smart contract.

        Contract Details:
        - Name: {contract_name if contract_name else "Not Available from Scan"}
        - Address: {contract_address}
        - Identified Owner (from scan, if any): {owner_address_identified}
        - Automated Risk Score (0-100, lower is better if 100-deductions, or higher is better if score = deductions - assume 100 is best, 0 is worst for this report): {risk_score}

        Automated Risk Assessment Findings:
        {findings_text}

        {on_chain_text}

        Report Requirements:
        1.  **Executive Summary:** Briefly describe the contract's apparent purpose (if inferable from name or common patterns) and provide an overall risk assessment based on the automated findings. State the final risk score clearly.
        2.  **Detailed Vulnerability Analysis:** For each finding from the automated scan:
            * Explain the vulnerability in simple terms.
            * Discuss its potential impact on the contract and users.
            * Provide concrete, actionable recommendations for remediation or mitigation. If a finding is informational (e.g. "Minting Functions Present"), suggest areas for manual review.
        3.  **Tokenomics and Ownership Review (if applicable):**
            * If 'Centralized Ownership' was flagged, discuss the implications (e.g., rug pull risk, upgrade control) and recommend best practices (e.g., multisig with timelock, DAO governance).
            * If 'Suspicious Minting' was flagged, analyze potential risks (e.g., inflation, unfair distribution) and recommend access controls or transparent minting policies.
        4.  **Compliance Considerations:** Highlight any aspects that might be relevant for regulatory compliance or DAO governance standards (e.g., lack of event emissions for critical actions, upgradeability mechanisms, admin controls).
        5.  **Recommendations for DAO / Users:**
            * Suggest whether a full manual audit by human experts is recommended.
            * Propose any immediate actions for a DAO managing this contract (e.g., pause, community alert, parameter review).
            * Advise end-users on potential risks when interacting with this contract.
        6.  **Conclusion:** Summarize the key takeaways.

        Output Format: Markdown.
        Ensure the language is professional, clear, and actionable for both technical and semi-technical audiences (DAO reviewers, regulators).
        Do not invent findings not present in the automated assessment. Focus on interpreting and elaborating on the provided data.
        If 'No specific vulnerabilities flagged', the report should still cover general smart contract best practices and areas for manual review.
        """

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI smart contract auditor and compliance analyst named TrustMesh AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4, # Lower temperature for more factual and less creative reports
                max_tokens=3000
            )
            
            report_markdown = completion.choices[0].message.content

            # For JSON output, you could ask the LLM to structure parts of its response in JSON,
            # or parse the Markdown. For PoC, we'll focus on Markdown.
            report_json_summary = {
                "contract_name": contract_name,
                "contract_address": contract_address,
                "risk_score": risk_score,
                "key_vulnerabilities_identified": [f["vulnerability"] for f in findings],
                "llm_report_snippet": report_markdown[:500] + "..." # Snippet of the full report
            }
            return report_markdown, report_json_summary

        except Exception as e:
            error_message = f"[ERROR] LLM report generation failed for {contract_address}: {e}"
            print(error_message)
            return f"# Error in Report Generation\n\n{error_message}", {"error": error_message}

# Example Usage (assuming Part 1's output is available):
if __name__ == "__main__":
    # This example requires output from part1_risk_engine.py
    # For a standalone test, mock the risk_analysis_results:
    mock_risk_analysis_results = {
        "contract_address": "0x1234567890123456789012345678901234567890",
        "contract_name": "Mock DeFi Protocol",
        "risk_score": 65,
        "findings": [
            {
                "vulnerability": "Centralized Ownership / Control",
                "details": "owner() function (0x8da5cb5b) present. Non-zero address found at common owner storage slot (0x0...0): 0xOwnerAddressHere. Contract appears to have Ownable patterns or a single owner address. Assess owner privileges and security (e.g., multisig, timelock).",
                "severity_score_impact": 15
            },
            {
                "vulnerability": "Potential Permissionless/Suspicious Minting",
                "details": "Mint-related function selectors found in bytecode: 40c10f19. Potentially permissionless public/external mint function 'function mint(address to, uint256 amount) public' found around line 75 without apparent strong access control modifiers (e.g., onlyOwner, onlyRole). Ensure minting functions are adequately access-controlled.",
                "severity_score_impact": 25
            }
        ],
        "analysis_summary": {
            "reentrancy_detected": False,
            "unchecked_calls_detected": False,
            "centralized_ownership_detected": True,
            "suspicious_minting_detected": True,
            "owner_address_identified": "0xOwnerAddressHere"
        },
        "source_code_analyzed": True
    }
    
    mock_on_chain_summary = {
        "whale_alerts_count": 5,
        "top_holder_concentration": "Top 3 holders own 60% (example data)",
        "defi_spike_alerts": 1
    }

    if not client:
        print("OpenAI client not available. Skipping LLM report generation example.")
    else:
        reporter = LLMReportGenerator()
        markdown_report, json_summary = reporter.generate_compliance_report(
            contract_name=mock_risk_analysis_results["contract_name"],
            contract_address=mock_risk_analysis_results["contract_address"],
            risk_analysis_results=mock_risk_analysis_results,
            on_chain_activity_summary=mock_on_chain_summary
        )

        print("\n--- LLM Generated Compliance Report (Markdown) ---")
        print(markdown_report)

        # print("\n--- LLM Generated Report (JSON Summary) ---")
        # print(json.dumps(json_summary, indent=2))

        # Save the report
        filename = f"compliance_report_{mock_risk_analysis_results['contract_address'][-10:]}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        print(f"\n[INFO] Markdown report saved to {filename}")

