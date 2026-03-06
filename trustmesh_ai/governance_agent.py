# trustmesh_ai/part4_governance_agent.py
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
# from web3 import Web3 # For actual proposal submission - include if implementing submission

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("[WARN] OPENAI_API_KEY not found in environment variables. Governance Agent will not function.")

try:
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception as e:
    print(f"[ERROR] Failed to initialize OpenAI client: {e}")
    client = None

# For on-chain voting (conceptual for now, requires more setup)
# AVALANCHE_RPC_URL = os.getenv("AVALANCHE_RPC_URL")
# GOVERNOR_CONTRACT_ADDRESS = os.getenv("GOVERNOR_CONTRACT_ADDRESS") # e.g., a GovernorBravo contract
# GOVERNOR_CONTRACT_ABI_JSON = os.getenv("GOVERNOR_CONTRACT_ABI_JSON", "[]") # Stringified JSON ABI
# YOUR_WALLET_PRIVATE_KEY = os.getenv("YOUR_WALLET_PRIVATE_KEY") # For signing transactions

class GovernanceProposalAgent:
    def __init__(self, model="gpt-4-turbo-preview"): # GPT-4 recommended for nuanced analysis
        self.model = model
        if not client:
            print("[ERROR] OpenAI client not initialized. GovernanceProposalAgent may not work.")
        
        # self.w3 = None
        # self.account = None
        # self.governor_contract = None
        # if AVALANCHE_RPC_URL and YOUR_WALLET_PRIVATE_KEY and GOVERNOR_CONTRACT_ADDRESS:
        #     try:
        #         self.w3 = Web3(Web3.HTTPProvider(AVALANCHE_RPC_URL))
        #         self.account = self.w3.eth.account.from_key(YOUR_WALLET_PRIVATE_KEY)
        #         self.w3.eth.default_account = self.account.address
        #         abi = json.loads(GOVERNOR_CONTRACT_ABI_JSON)
        #         self.governor_contract = self.w3.eth.contract(address=GOVERNOR_CONTRACT_ADDRESS, abi=abi)
        #         print("[INFO] Web3 initialized for potential on-chain voting.")
        #     except Exception as e:
        #         print(f"[WARN] Failed to initialize Web3 for voting: {e}")


    def analyze_proposal(self, proposal_id, proposal_description, technical_details=None):
        """
        Analyzes a DAO governance proposal using an LLM.
        proposal_id: Identifier for the proposal.
        proposal_description: Full text description of the proposal.
        technical_details: Optional dict with 'targets', 'values', 'signatures', 'calldatas'
        """
        if not client:
            return {
                "error": "OpenAI Client Not Initialized",
                "proposal_id": proposal_id,
                "summary": "N/A",
                "impact_assessment": "N/A",
                "vote_recommendation": "Error",
                "justification": "LLM not available."
            }

        technical_details_text = "No specific technical execution details provided."
        if technical_details:
            try:
                technical_details_text = "Technical Execution Details:\n"
                technical_details_text += f"- Target Contracts: {json.dumps(technical_details.get('targets', 'N/A'))}\n"
                technical_details_text += f"- ETH Values (Wei): {json.dumps(technical_details.get('values', 'N/A'))}\n"
                technical_details_text += f"- Function Signatures: {json.dumps(technical_details.get('signatures', 'N/A'))}\n"
                # Calldata can be very long, so maybe summarize or indicate presence
                calldata_preview = [cd[:30] + "..." if len(cd) > 30 else cd for cd in technical_details.get('calldatas', [])]
                technical_details_text += f"- Calldata (preview): {json.dumps(calldata_preview)}\n"
            except Exception as e:
                technical_details_text = f"Error parsing technical details: {e}"
        
        prompt = f"""
        You are TrustMesh AI, an expert AI governance analyst for DAOs, specializing in DeFi protocol safety, security, and economic stability.
        Analyze the following DAO governance proposal:

        Proposal ID: {proposal_id}

        Proposal Description:
        ---
        {proposal_description}
        ---

        {technical_details_text}

        Analysis Task:
        1.  **Summary (1-2 sentences):** Briefly explain the core purpose and main actions of this proposal.
        2.  **Impact Assessment (Critical):**
            * Evaluate the potential impact on protocol safety and security. Are there new attack vectors, vulnerabilities, or oracle manipulation risks introduced?
            * Assess the impact on protocol decentralization. Does it concentrate power or reduce community control?
            * Analyze the economic impact. Could it destabilize tokenomics, liquidity, or create unfair advantages?
            * Consider any risks related to the technical execution details if provided (e.g., risky function calls, incorrect parameters, target contract vulnerabilities).
        3.  **Risk Identification:** Clearly list any specific risks, concerns, or potential unintended negative consequences.
        4.  **Vote Recommendation:** Based on your comprehensive analysis, provide a clear recommendation:
            * **For**
            * **Against**
            * **Abstain** (Use if more information is critically needed or impact is neutral but uncertain)
        5.  **Justification (3-5 concise sentences):** Provide a strong, evidence-based justification for your vote recommendation, directly referencing your impact assessment and risk identification.

        Guidelines:
        - Be objective and analytical.
        - Prioritize the long-term health, security, and decentralization of the protocol.
        - If the proposal involves smart contract interactions or code changes, scrutinize the safety of these changes.
        - If information is insufficient for a strong assessment in a critical area, state this.

        Output the analysis clearly, section by section.
        """

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are TrustMesh AI, an expert AI governance analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Low temperature for precise, analytical responses
                max_tokens=2000
            )
            
            llm_response_text = completion.choices[0].message.content
            
            # Attempt to parse structured information from the LLM's response
            # This is heuristic and might need refinement based on actual LLM output patterns
            summary = re.search(r"Summary:\s*(.*?)(Impact Assessment:|Risk Identification:|$)", llm_response_text, re.DOTALL | re.IGNORECASE)
            impact_assessment = re.search(r"Impact Assessment:\s*(.*?)(Risk Identification:|Vote Recommendation:|$)", ll_m_response_text, re.DOTALL | re.IGNORECASE)
            vote_recommendation_match = re.search(r"Vote Recommendation:\s*(For|Against|Abstain)", llm_response_text, re.IGNORECASE)
            justification = re.search(r"Justification:\s*(.*?)(<END_OF_JUSTIFICATION>|$)", llm_response_text, re.DOTALL | re.IGNORECASE) # Add a marker if needed

            return {
                "proposal_id": proposal_id,
                "full_llm_analysis": llm_response_text,
                "summary": summary.group(1).strip() if summary else "Could not parse summary.",
                "impact_assessment": impact_assessment.group(1).strip() if impact_assessment else "Could not parse impact assessment.",
                "vote_recommendation": vote_recommendation_match.group(1).strip() if vote_recommendation_match else "Error: Could not parse recommendation.",
                "justification": justification.group(1).strip() if justification else "Could not parse justification."
            }

        except Exception as e:
            error_message = f"[ERROR] LLM proposal analysis failed for {proposal_id}: {e}"
            print(error_message)
            return {
                "error": error_message,
                "proposal_id": proposal_id,
                "full_llm_analysis": error_message,
                "summary": "N/A",
                "impact_assessment": "N/A",
                "vote_recommendation": "Error",
                "justification": "LLM analysis failed."
            }

    # def submit_vote_on_chain(self, proposal_id_int, vote_choice_int, gas_limit=300000):
    #     """
    #     Submits a vote to a Governor.sol-based contract.
    #     proposal_id_int: The proposal ID as an integer.
    #     vote_choice_int: 0 for Against, 1 for For, 2 for Abstain.
    #     """
    #     if not self.governor_contract or not self.w3 or not self.account:
    #         print("[ERROR] Cannot submit vote: Web3 or Governor contract not initialized.")
    #         return None
        
    #     print(f"[INFO] Attempting to vote {vote_choice_int} on proposal {proposal_id_int}...")
    #     try:
    #         # Ensure proposalId is int, vote choice is int
    #         proposal_id = int(proposal_id_int)
    #         support = int(vote_choice_int) # 0:Against, 1:For, 2:Abstain (standard for OZ Governor)

    #         # Check if already voted (optional, depends on Governor implementation)
    #         # has_voted = self.governor_contract.functions.hasVoted(proposal_id, self.account.address).call()
    #         # if has_voted:
    #         #     print(f"[INFO] Account {self.account.address} has already voted on proposal {proposal_id}.")
    #         #     return {"status": "already_voted"}

    #         tx_params = {
    #             'from': self.account.address,
    #             'nonce': self.w3.eth.get_transaction_count(self.account.address),
    #             'gasPrice': self.w3.eth.gas_price # Or use a gas price strategy
    #             # 'gas': gas_limit # Let web3.py estimate gas if not provided, or set manually
    #         }
            
    #         # For Governor contracts that take a reason string: castVoteWithReason
    #         # For basic Governor: castVote
    #         # Check your specific Governor's ABI. Assuming castVote for this example.
    #         transaction = self.governor_contract.functions.castVote(proposal_id, support).build_transaction(tx_params)
            
    #         estimated_gas = self.w3.eth.estimate_gas(transaction)
    #         transaction['gas'] = int(estimated_gas * 1.2) # Add 20% buffer

    #         signed_tx = self.w3.eth.account.sign_transaction(transaction, self.account.key)
    #         tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
    #         print(f"[INFO] Vote transaction submitted. Hash: {tx_hash.hex()}")
    #         # Optional: wait for receipt
    #         # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    #         # print(f"[INFO] Vote transaction confirmed. Status: {'Success' if receipt.status == 1 else 'Failed'}")
    #         return {"status": "success", "tx_hash": tx_hash.hex()}

    #     except Exception as e:
    #         print(f"[ERROR] Failed to submit vote for proposal {proposal_id}: {e}")
    #         return {"status": "failed", "error": str(e)}


# Example Usage:
if __name__ == "__main__":
    if not client:
        print("OpenAI client not available. Skipping Governance Agent example.")
    else:
        agent = GovernanceProposalAgent()

        # Mock Governance Proposal
        mock_proposal_id = "AVIP-042"
        mock_proposal_description = """
        **Proposal Title:** Implement V3 Liquidity Mining Program & Adjust Treasury Allocation

        **Summary:**
        This proposal outlines a plan to launch the V3 Liquidity Mining (LM) program for our DEX, allocating 1,000,000 governance tokens (GOV) per month for 6 months.
        It also proposes to reallocate 20% of the DAO treasury currently held in stablecoins (USDC, USDT) into a diversified portfolio of yield-bearing assets, including direct investment into two new, unaudited protocols ('AlphaYield' and 'BetaFarm') promising high APYs.
        A new smart contract `TreasuryManagerV2.sol` will be deployed to handle these allocations, with its ownership set to a 2-of-3 multisig composed of core team members.

        **Motivation:**
        - Stimulate liquidity for V3 pools.
        - Increase returns on DAO treasury assets.
        - Streamline treasury management via the new contract and smaller multisig.

        **Technical Changes:**
        - Deploy `TreasuryManagerV2.sol` (source code attached separately for review).
        - Call `setRewardsManager(TreasuryManagerV2_address)` on the `RewardsDistributor` contract.
        - Transfer 20% of treasury stablecoins to `TreasuryManagerV2_address`.
        """
        mock_technical_details = {
            "targets": ["0xRewardsDistributorAddress", "0xTreasuryDAOAddress", "0xNewTreasuryManagerV2Address"],
            "values": [0, 0, "200000000000000000000000"], # Example: 200k USDC (assuming 6 decimals, this value is wrong for wei)
            "signatures": [
                "setRewardsManager(address)", 
                "transfer(address,uint256)", # Assuming treasury is an ERC20 holding contract
                "receive()" # If TreasuryManagerV2 has a receive/fallback for ETH if sent
            ],
            "calldatas": [
                "0x<abiEncodedNewTreasuryManagerV2Address>",
                "0x<abiEncodedTransferCallDataToTreasuryManagerV2>",
                "0x" # Empty for receive
            ]
        }

        analysis_result = agent.analyze_proposal(
            proposal_id=mock_proposal_id,
            proposal_description=mock_proposal_description,
            technical_details=mock_technical_details
        )

        print(f"\n--- Governance Proposal Analysis for {analysis_result.get('proposal_id')} ---")
        print(f"\nVote Recommendation: {analysis_result.get('vote_recommendation')}")
        print(f"\nJustification:\n{analysis_result.get('justification')}")
        print(f"\nSummary:\n{analysis_result.get('summary')}")
        print(f"\nImpact Assessment:\n{analysis_result.get('impact_assessment')}")
        
        # print("\nFull LLM Analysis:")
        # print(analysis_result.get('full_llm_analysis'))

        # Conceptual on-chain voting (requires .env setup and a live Governor contract)
        # if analysis_result.get('vote_recommendation') == "Against":
        #     VOTE_CHOICE_AGAINST = 0 
        #     print(f"\n[CONCEPTUAL] Submitting 'AGAINST' vote for proposal {mock_proposal_id}...")
        #     # vote_submission_result = agent.submit_vote_on_chain(mock_proposal_id_numeric, VOTE_CHOICE_AGAINST) # proposal ID needs to be numeric for contract
        #     # print(f"[CONCEPTUAL] Vote submission result: {vote_submission_result}")
        # elif analysis_result.get('vote_recommendation') == "For":
        #     VOTE_CHOICE_FOR = 1
        #     print(f"\n[CONCEPTUAL] Submitting 'FOR' vote for proposal {mock_proposal_id}...")

