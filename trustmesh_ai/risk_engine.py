# trustmesh_ai/part1_risk_engine.py
import os
import re
import requests # For Snowtrace API
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

AVALANCHE_RPC_URL = os.getenv("AVALANCHE_RPC_URL", "https_//api.avax.network/ext/bc/C/rpc")
SNOWTRACE_API_KEY = os.getenv("SNOWTRACE_API_KEY") # Get from Snowtrace (Etherscan for Avalanche)
SNOWTRACE_API_URL = "https_//api.snowtrace.io/api"

# Common function selectors (first 4 bytes of keccak256 hash)
# Ownable (OpenZeppelin)
OWNER_SELECTOR = "0x8da5cb5b" # owner()
TRANSFER_OWNERSHIP_SELECTOR = "0xf2fde38b" # transferOwnership(address)
RENOUNCE_OWNERSHIP_SELECTOR = "0x715018a6" # renounceOwnership()

# ERC20 Minting (common patterns - can be expanded)
MINT_SELECTOR_ADDR_UINT = "0x40c10f19" # mint(address,uint256)
MINT_SELECTOR_UINT_ADDR = "0x0f63c14a" # mint(uint256,address) - less common
MINT_SELECTOR_UINT = "0xa0712d68"      # mint(uint256) - if to msg.sender or fixed address
MINT_SELECTOR_NO_ARGS = "0x1249c58b" # mint() - very generic, needs context

# Known Ownable contract storage slots for owner (heuristic, depends on implementation)
OWNER_STORAGE_SLOT = "0x0000000000000000000000000000000000000000000000000000000000000000" # OZ Ownable
OWNER_STORAGE_SLOT_GNOSIS_SAFE = "0x0000000000000000000000000000000000000000000000000000000000000001" # Gnosis Safe owners list start

# Reentrancy guard check (common modifier names)
REENTRANCY_GUARD_MODIFIERS = ["nonReentrant", "ReentrancyGuard"]

class SmartContractRiskEngine:
    def __init__(self, rpc_url=AVALANCHE_RPC_URL, snowtrace_api_key=SNOWTRACE_API_KEY):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.snowtrace_api_key = snowtrace_api_key
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Avalanche RPC at {rpc_url}")
        print(f"[INFO] Connected to RPC: {rpc_url}")
        if not self.snowtrace_api_key:
            print("[WARN] SNOWTRACE_API_KEY not set. Source code fetching will be disabled.")

    def get_contract_data(self, contract_address_str):
        contract_address = self.w3.to_checksum_address(contract_address_str)
        bytecode = self.w3.eth.get_code(contract_address).hex()
        source_code = None
        contract_name = "Unknown"
        abi = None

        if self.snowtrace_api_key:
            try:
                params = {
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": contract_address,
                    "apikey": self.snowtrace_api_key
                }
                response = requests.get(SNOWTRACE_API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data["status"] == "1" and data["result"][0]["SourceCode"]:
                    source_code = data["result"][0]["SourceCode"]
                    contract_name = data["result"][0]["ContractName"]
                    abi = data["result"][0]["ABI"]
                    # Handle contracts that are split into multiple files (JSON input format)
                    if source_code.startswith('{'):
                        try:
                            source_data = json.loads(source_code.lstrip('{').rstrip('}'))
                            if 'sources' in source_data: # Truffle/Hardhat JSON format
                                combined_source = ""
                                for path, content_obj in source_data['sources'].items():
                                    combined_source += f"// File: {path}\n{content_obj.get('content', '')}\n\n"
                                source_code = combined_source
                            elif 'SourceCode' in source_data : # Etherscan single file JSON
                                source_code = source_data['SourceCode']
                        except json.JSONDecodeError:
                            print(f"[WARN] Contract source for {contract_address} is JSON but could not be parsed fully.")
                            # Keep original JSON string if parsing fails for some reason
                    print(f"[INFO] Fetched source code for {contract_name} ({contract_address})")
                else:
                    print(f"[INFO] No verified source code found on Snowtrace for {contract_address}. Message: {data.get('message', 'Unknown error')}, Result: {data.get('result', 'N/A')}")
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Could not fetch source code from Snowtrace for {contract_address}: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error parsing Snowtrace response for {contract_address}: {e}")

        return bytecode, source_code, contract_name, abi

    def analyze_contract(self, contract_address_str):
        bytecode, source_code, contract_name, _ = self.get_contract_data(contract_address_str)

        findings = []
        risk_score_deductions = 0 # Start at 0, add points for bad things

        # 1. Reentrancy Risk (Heuristic)
        # True reentrancy detection is complex. This is a basic check.
        # Looks for low-level calls (.call, .delegatecall, .send) not followed by a state change check or reentrancy guard.
        reentrancy_details = []
        if source_code:
            # Regex to find .call, .send, .delegatecall followed by state modification without reentrancy guard
            # This is a simplified regex and might need refinement.
            # It looks for a call, then optionally some lines, then an assignment (state change).
            # It also tries to check if a known reentrancy guard modifier is present on the function.

            # Find functions
            func_pattern = re.compile(r"function\s+\w+\s*\(.*?\)\s*(?:public|external|payable)?\s*(.*?)\s*\{([\s\S]*?)\}", re.IGNORECASE)
            call_pattern = re.compile(r"\.\s*(call|send|delegatecall)\s*\((.*?)\)", re.IGNORECASE)
            assignment_pattern = re.compile(r"\b([a-zA-Z_]\w*)\s*(=|\+=|-=|\*=|/=)\s*.*;", re.IGNORECASE) # State var assignment

            for match in func_pattern.finditer(source_code):
                func_modifiers = match.group(1)
                func_body = match.group(2)

                has_reentrancy_guard = any(guard in func_modifiers for guard in REENTRANCY_GUARD_MODIFIERS)

                call_matches = list(call_pattern.finditer(func_body))
                if not call_matches:
                    continue

                for call_match_obj in call_matches:
                    # Check if the call's return value is checked
                    # This is tricky with regex. A simple check: look for `require(` or `if (` after the call.
                    # Or if it's assigned: `(bool success, ) = ...call...` then `require(success`.

                    # For PoC, a simpler heuristic: if a call exists and no reentrancy guard on function, flag.
                    # More advanced: check if state is written *after* the call within the same block *before* a check.
                    if not has_reentrancy_guard:
                        # Check for state change after this call
                        remaining_body_after_call = func_body[call_match_obj.end():]
                        if assignment_pattern.search(remaining_body_after_call):
                             # This is still very heuristic. A real tool would build a control-flow graph.
                            line_number = source_code.count('\n', 0, match.start() + func_body.find(call_match_obj.group(0))) + 1
                            reentrancy_details.append(f"Potential reentrancy in function around line {line_number} due to external call '{call_match_obj.group(0)}' without a clear reentrancy guard and subsequent state change.")
                            break # Flag function once

            if reentrancy_details:
                findings.append({
                    "vulnerability": "Potential Reentrancy Risk",
                    "details": " ".join(reentrancy_details) + " Detected patterns that might indicate reentrancy (e.g., external call before state update without strong guards). Manual review required.",
                    "severity_score_impact": 30
                })
                risk_score_deductions += 30

        # 2. Unchecked External Calls
        unchecked_calls_details = []
        if source_code:
            # Look for raw .call(), .send() that are not wrapped in require() or if() or assigned for checking
            # Example: `someAddress.call{value: x}("");` without `(bool success, ) = ...` and `require(success)`
            # This regex is a basic heuristic.
            unchecked_call_pattern = re.compile(r"(?<!\(bool\s*success\s*,\s*bytes\s*memory\s*returnData\s*\)\s*=\s*)(?<!\(bool\s*success\s*,\s*\)\s*=\s*)(?<!\(bool\s*success\s*\)\s*=\s*)([^=\s]*\.\s*(call|send)\s*\(.*?\)\s*;)", re.IGNORECASE)
            for match in unchecked_call_pattern.finditer(source_code):
                # Further check: ensure it's not part of `require(target.call(...))`
                line_start_index = source_code.rfind('\n', 0, match.start()) + 1
                line_end_index = source_code.find('\n', match.end())
                current_line = source_code[line_start_index:line_end_index if line_end_index != -1 else len(source_code)]
                if not current_line.strip().startswith("require(") and not current_line.strip().startswith("if("):
                    line_number = source_code.count('\n', 0, match.start()) + 1
                    unchecked_calls_details.append(f"Potential unchecked external call '{match.group(1).strip()}' around line {line_number}.")

        if unchecked_calls_details:
            findings.append({
                "vulnerability": "Potential Unchecked External Call",
                "details": " ".join(unchecked_calls_details) + " Found external calls where the return value might not be checked. This could lead to unexpected behavior if the call fails.",
                "severity_score_impact": 20
            })
            risk_score_deductions += 20


        # 3. Centralized Ownership
        is_centralized = False
        owner_address_from_slot = "Unknown"
        centralization_details = []

        # Check common owner selectors in bytecode
        if OWNER_SELECTOR[2:] in bytecode: centralization_details.append(f"owner() function ({OWNER_SELECTOR}) present.")
        if TRANSFER_OWNERSHIP_SELECTOR[2:] in bytecode: centralization_details.append(f"transferOwnership() function ({TRANSFER_OWNERSHIP_SELECTOR}) present.")
        if RENOUNCE_OWNERSHIP_SELECTOR[2:] in bytecode: centralization_details.append(f"renounceOwnership() function ({RENOUNCE_OWNERSHIP_SELECTOR}) present.")

        # Check common storage slot for owner (heuristic)
        try:
            owner_val_hex = self.w3.eth.get_storage_at(self.w3.to_checksum_address(contract_address_str), OWNER_STORAGE_SLOT).hex()
            if owner_val_hex != "0x" + "00" * 32 and owner_val_hex != "0x00":
                owner_address_from_slot = self.w3.to_checksum_address("0x" + owner_val_hex[26:]) # Last 20 bytes for address
                centralization_details.append(f"Non-zero address found at common owner storage slot ({OWNER_STORAGE_SLOT}): {owner_address_from_slot}.")
            else: # Check Gnosis Safe style owner slot if main one is zero
                gnosis_owner_val_hex = self.w3.eth.get_storage_at(self.w3.to_checksum_address(contract_address_str), OWNER_STORAGE_SLOT_GNOSIS_SAFE).hex()
                if gnosis_owner_val_hex != "0x" + "00" * 32 and gnosis_owner_val_hex != "0x00":
                     centralization_details.append(f"Potential Gnosis Safe style ownership pattern detected at slot ({OWNER_STORAGE_SLOT_GNOSIS_SAFE}).")


        except Exception as e:
            print(f"[WARN] Could not read storage for ownership check: {e}")

        if centralization_details:
            is_centralized = True
            findings.append({
                "vulnerability": "Centralized Ownership / Control",
                "details": " ".join(centralization_details) + " Contract appears to have Ownable patterns or a single owner address. Assess owner privileges and security (e.g., multisig, timelock).",
                "severity_score_impact": 15 # Can be adjusted based on owner's privileges if known
            })
            risk_score_deductions += 15

        # 4. Permissionless or Suspicious Minting
        # Look for public mint functions not protected by typical access control.
        minting_details = []
        suspicious_minting_found = False
        mint_selectors_in_bytecode = [
            sel[2:] for sel in [MINT_SELECTOR_ADDR_UINT, MINT_SELECTOR_UINT_ADDR, MINT_SELECTOR_UINT, MINT_SELECTOR_NO_ARGS] if sel[2:] in bytecode
        ]

        if mint_selectors_in_bytecode:
            minting_details.append(f"Mint-related function selectors found in bytecode: {', '.join(mint_selectors_in_bytecode)}.")
            if source_code:
                # Search for mint functions and check their modifiers
                mint_func_pattern = re.compile(r"function\s+mint\w*\s*\(.*?\)\s*(public|external)?\s*(.*?)(\s*\{|\s*returns\s*\(.*\)\s*\{)", re.IGNORECASE)
                for match in mint_func_pattern.finditer(source_code):
                    func_visibility = (match.group(1) or "").lower()
                    func_modifiers = (match.group(2) or "").lower()

                    is_public_or_external = "public" in func_visibility or "external" in func_visibility or not func_visibility # Default is public

                    # Basic check for common access control modifiers
                    has_access_control = "onlyowner" in func_modifiers or "onlyrole" in func_modifiers or "accesscontrol" in func_modifiers or "auth" in func_modifiers

                    if is_public_or_external and not has_access_control:
                        line_number = source_code.count('\n', 0, match.start()) + 1
                        minting_details.append(f"Potentially permissionless public/external mint function '{match.group(0).split('{')[0].strip()}' found around line {line_number} without apparent strong access control modifiers (e.g., onlyOwner, onlyRole).")
                        suspicious_minting_found = True
                        break
            elif not source_code and mint_selectors_in_bytecode: # No source, but mint selectors present
                minting_details.append("Mint function selectors detected in bytecode, but no source code available for modifier analysis. Assume caution.")
                suspicious_minting_found = True # Higher caution if no source

        if suspicious_minting_found:
            findings.append({
                "vulnerability": "Potential Permissionless/Suspicious Minting",
                "details": " ".join(minting_details) + " Ensure minting functions are adequately access-controlled.",
                "severity_score_impact": 25
            })
            risk_score_deductions += 25
        elif minting_details: # Mint functions exist but maybe not suspicious, still good to note
             findings.append({
                "vulnerability": "Minting Functions Present",
                "details": " ".join(minting_details) + " Minting functions are present. Review their logic and access control.",
                "severity_score_impact": 5 # Low impact if just informational
            })
            risk_score_deductions += 5


        # Calculate final risk score (0-100, lower is better)
        # We are adding deductions, so final score is 100 - deductions.
        final_risk_score = max(0, 100 - risk_score_deductions)

        return {
            "contract_address": contract_address_str,
            "contract_name": contract_name,
            "risk_score": final_risk_score,
            "findings": findings,
            "analysis_summary": {
                "reentrancy_detected": any("Reentrancy" in f["vulnerability"] for f in findings),
                "unchecked_calls_detected": any("Unchecked External Call" in f["vulnerability"] for f in findings),
                "centralized_ownership_detected": is_centralized,
                "suspicious_minting_detected": suspicious_minting_found,
                "owner_address_identified": owner_address_from_slot if owner_address_from_slot != "Unknown" else None
            },
            "source_code_analyzed": bool(source_code),
            "bytecode_snippet": bytecode[:256] + "..." if bytecode else "N/A",
        }

# Example Usage:
if __name__ == "__main__":
    engine = SmartContractRiskEngine()

    # Example: WAVAX on Avalanche C-Chain
    # target_contract = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" # WAVAX
    # Example: Trader Joe: JOE token
    target_contract = "0x6e84a6216eA6dACC71eE8E6b0a5B7322EEbC0fDd"
    # Example: A contract that might have some of these issues (hypothetical)
    # For testing, you might deploy a vulnerable contract to a testnet.
    # target_contract = "YOUR_TEST_CONTRACT_ADDRESS_HERE"

    if not SNOWTRACE_API_KEY:
        print("\n[IMPORTANT] SNOWTRACE_API_KEY is not set in your .env file.")
        print("Source code analysis will be limited. Please get an API key from https_//snowtrace.io/apis\n")

    analysis_results = engine.analyze_contract(target_contract)

    print("\n--- Smart Contract Risk Analysis ---")
    print(f"Contract Address: {analysis_results['contract_address']}")
    print(f"Contract Name: {analysis_results['contract_name']}")
    print(f"Risk Score: {analysis_results['risk_score']}/100 (Lower is better if 100-deductions, or higher is better if score = deductions)")
    print(f"Source Code Analyzed: {analysis_results['source_code_analyzed']}")

    print("\nFindings:")
    if analysis_results['findings']:
        for finding in analysis_results['findings']:
            print(f"  - Vulnerability: {finding['vulnerability']}")
            print(f"    Details: {finding['details']}")
            print(f"    Severity Score Impact: {finding['severity_score_impact']}")
    else:
        print("  No specific vulnerabilities flagged by basic heuristics.")

    print("\nAnalysis Summary:")
    for key, value in analysis_results['analysis_summary'].items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")

    # print(f"\nBytecode Snippet: {analysis_results['bytecode_snippet']}")

