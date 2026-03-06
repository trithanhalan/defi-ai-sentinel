# trustmesh_ai/part2_whale_monitor.py
import os
import time
import requests # For webhook & price APIs
from web3 import Web3
from dotenv import load_dotenv
from collections import defaultdict, deque
import json

load_dotenv()

AVALANCHE_RPC_URL = os.getenv("AVALANCHE_RPC_URL", "https_//api.avax.network/ext/bc/C/rpc")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # Optional: for alerts via services like Slack, Discord
COINGECKO_API_URL = "https_//api.coingecko.com/api/v3" # For token prices

# ERC-20 Transfer Event Signature (Topic0)
TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Minimal ABI for ERC20 name, symbol, decimals
MINIMAL_ERC20_ABI = json.loads("""
[
    {"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}
]
""")

# Cache for token details (symbol, decimals, price) to reduce API calls
TOKEN_CACHE = {}
# Cache for contract checksums
CHECKSUM_CACHE = {}

class WhaleTransactionMonitor:
    def __init__(self, rpc_url=AVALANCHE_RPC_URL, alert_threshold_usd=50000):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Avalanche RPC at {rpc_url}")
        self.alert_threshold_usd = alert_threshold_usd
        self.seen_transaction_hashes = deque(maxlen=2000) # Avoid reprocessing recent tx if polling overlaps

        # For wallet concentration (address -> token_address -> balance)
        self.wallet_balances = defaultdict(lambda: defaultdict(float))
        # For DeFi contract flow monitoring (contract_addr -> {'inflow_usd': X, 'outflow_usd': Y, 'tx_count': Z, 'timestamps': deque})
        self.defi_contract_flows = defaultdict(lambda: {
            "inflow_usd": 0.0,
            "outflow_usd": 0.0,
            "tx_count": 0,
            "recent_timestamps": deque(maxlen=100) # For spike detection over a window
        })
        print(f"[INFO] Whale Monitor initialized. Alert threshold: ${alert_threshold_usd:,.2f} USD")

    def get_checksum_address(self, address):
        if address not in CHECKSUM_CACHE:
            CHECKSUM_CACHE[address] = self.w3.to_checksum_address(address)
        return CHECKSUM_CACHE[address]

    async def get_token_details(self, token_address_str):
        token_address = self.get_checksum_address(token_address_str)
        if token_address in TOKEN_CACHE and 'price_usd' in TOKEN_CACHE[token_address]: # Check if price is also cached
            # Optionally add a TTL for price if it needs to be super fresh
            if time.time() - TOKEN_CACHE[token_address].get('price_last_updated', 0) < 300: # 5 min TTL for price
                 return TOKEN_CACHE[token_address]

        if token_address not in TOKEN_CACHE:
            TOKEN_CACHE[token_address] = {}
            try:
                contract = self.w3.eth.contract(address=token_address, abi=MINIMAL_ERC20_ABI)
                TOKEN_CACHE[token_address]['symbol'] = await contract.functions.symbol().call()
                TOKEN_CACHE[token_address]['decimals'] = await contract.functions.decimals().call()
                TOKEN_CACHE[token_address]['name'] = await contract.functions.name().call()
                # print(f"[DEBUG] Fetched on-chain details for {TOKEN_CACHE[token_address]['symbol']}")
            except Exception as e:
                # print(f"[WARN] Could not fetch token details for {token_address} from chain: {e}. Will try CoinGecko by address.")
                TOKEN_CACHE[token_address]['symbol'] = "UNKNOWN"
                TOKEN_CACHE[token_address]['decimals'] = 18 # Default if unknown
                TOKEN_CACHE[token_address]['name'] = "Unknown Token"

        # Fetch price from CoinGecko (example)
        # For Avalanche, platform_id is 'avalanche'
        try:
            # print(f"[DEBUG] Fetching price for {token_address} ({TOKEN_CACHE[token_address]['symbol']})")
            cg_api = f"{COINGECKO_API_URL}/simple/token_price/avalanche?contract_addresses={token_address}&vs_currencies=usd"
            response = requests.get(cg_api, timeout=5)
            response.raise_for_status()
            price_data = response.json()
            if token_address.lower() in price_data and 'usd' in price_data[token_address.lower()]:
                TOKEN_CACHE[token_address]['price_usd'] = price_data[token_address.lower()]['usd']
                TOKEN_CACHE[token_address]['price_last_updated'] = time.time()
            else: # Fallback if address not directly found, try by symbol if unique enough (less reliable)
                TOKEN_CACHE[token_address]['price_usd'] = TOKEN_CACHE[token_address].get('price_usd', 0) # Keep old price or 0
                # print(f"[WARN] Price not found for token {token_address} via contract address on CoinGecko.")
        except requests.exceptions.RequestException as e:
            # print(f"[WARN] Could not fetch price for token {token_address} from CoinGecko: {e}")
            TOKEN_CACHE[token_address]['price_usd'] = TOKEN_CACHE[token_address].get('price_usd', 0) # Keep old price or 0
        except Exception as e:
            # print(f"[WARN] Unexpected error fetching price for {token_address}: {e}")
            TOKEN_CACHE[token_address]['price_usd'] = TOKEN_CACHE[token_address].get('price_usd', 0)

        return TOKEN_CACHE[token_address]

    async def process_transaction_receipt(self, tx_hash, receipt, block_timestamp, target_defi_contracts_checksummed):
        for log_index, log in enumerate(receipt.logs):
            # Check if it's an ERC20 Transfer event
            if log.topics and log.topics[0].hex() == TRANSFER_EVENT_SIGNATURE and len(log.topics) == 3:
                token_contract_address = self.get_checksum_address(log.address)

                token_details = await self.get_token_details(token_contract_address)
                if not token_details or token_details.get('price_usd', 0) == 0:
                    # print(f"[DEBUG] Skipping token {token_contract_address}, no price or details.")
                    continue

                decimals = token_details['decimals']
                symbol = token_details['symbol']
                price_usd = token_details['price_usd']

                try:
                    from_address_hex = log.topics[1].hex()
                    to_address_hex = log.topics[2].hex()
                    from_address = self.get_checksum_address("0x" + from_address_hex[26:])
                    to_address = self.get_checksum_address("0x" + to_address_hex[26:])
                    value_raw = int(log.data.hex(), 16)
                    value_adjusted = value_raw / (10**decimals)
                except Exception as e:
                    # print(f"[WARN] Error decoding ERC20 log for token {symbol} ({token_contract_address}) in tx {tx_hash.hex()}: {e}")
                    continue

                value_usd = value_adjusted * price_usd

                # Update wallet balances (simplified for PoC)
                # Note: This is a naive balance update. For true balances, query contract state.
                # This tracks net flow from observed transfers.
                self.wallet_balances[from_address][token_contract_address] -= value_adjusted
                self.wallet_balances[to_address][token_contract_address] += value_adjusted

                # DeFi Contract Inflow/Outflow
                is_inflow = to_address in target_defi_contracts_checksummed
                is_outflow = from_address in target_defi_contracts_checksummed

                if is_inflow:
                    self.defi_contract_flows[to_address]["inflow_usd"] += value_usd
                    self.defi_contract_flows[to_address]["tx_count"] += 1
                    self.defi_contract_flows[to_address]["recent_timestamps"].append(block_timestamp)
                if is_outflow:
                    self.defi_contract_flows[from_address]["outflow_usd"] += value_usd
                    # Avoid double counting tx if it's an internal transfer within monitored contracts
                    if not is_inflow or (is_inflow and to_address != from_address) :
                        self.defi_contract_flows[from_address]["tx_count"] += 1
                        self.defi_contract_flows[from_address]["recent_timestamps"].append(block_timestamp)


                if value_usd >= self.alert_threshold_usd:
                    alert_message = (
                        f"🐋 WHALE ALERT 🐋\n"
                        f"Token: {symbol} ({token_details.get('name', 'N/A')})\n"
                        f"Address: {token_contract_address}\n"
                        f"Amount: {value_adjusted:,.4f} {symbol} (~${value_usd:,.2f} USD)\n"
                        f"From: {from_address}\n"
                        f"To: {to_address}\n"
                        f"Tx: {tx_hash.hex()}\n"
                        f"Log Index: {log_index}"
                    )
                    print(alert_message) # CLI Alert
                    self.send_webhook_alert({
                        "type": "whale_transfer",
                        "message": alert_message,
                        "token_symbol": symbol,
                        "token_address": token_contract_address,
                        "value_adjusted": value_adjusted,
                        "value_usd": value_usd,
                        "from_address": from_address,
                        "to_address": to_address,
                        "tx_hash": tx_hash.hex(),
                        "log_index": log_index
                    })

    async def scan_blocks(self, start_block, end_block, target_defi_contracts=None):
        print(f"[INFO] Scanning blocks from {start_block} to {end_block}...")
        target_defi_contracts_checksummed = [self.get_checksum_address(c) for c in (target_defi_contracts or [])]

        for block_num in range(start_block, end_block + 1):
            if block_num % 10 == 0 : print(f"[INFO] Processing block {block_num}...")
            try:
                block = self.w3.eth.get_block(block_num, full_transactions=True) # Get full tx objects
                block_timestamp = block.timestamp

                for tx in block.transactions:
                    tx_hash_hex = tx.hash.hex()
                    if tx_hash_hex in self.seen_transaction_hashes:
                        continue
                    self.seen_transaction_hashes.append(tx_hash_hex)

                    receipt = self.w3.eth.get_transaction_receipt(tx.hash)
                    if receipt.status == 1: # Only process successful transactions
                        await self.process_transaction_receipt(tx.hash, receipt, block_timestamp, target_defi_contracts_checksummed)
            except Exception as e:
                print(f"[ERROR] Failed to process block {block_num}: {e}")
            # Small delay to be kind to public RPCs if scanning many blocks
            if (end_block - start_block) > 10 : await asyncio.sleep(0.05)


    def analyze_tracked_data(self, target_defi_contracts=None):
        print("\n--- Wallet Concentration Analysis (Based on Tracked Transfers) ---")
        # This is a simplified concentration based on net flows from observed transfers.
        # True concentration requires getting all holder balances from contracts.
        for token_addr, details in TOKEN_CACHE.items():
            if 'symbol' not in details: continue # Skip if details not fully fetched

            token_balances = []
            for wallet_addr, token_holdings in self.wallet_balances.items():
                if token_addr in token_holdings and token_holdings[token_addr] > 1e-9: # Only non-dust balances
                    token_balances.append((wallet_addr, token_holdings[token_addr]))

            if not token_balances: continue

            sorted_balances = sorted(token_balances, key=lambda item: item[1], reverse=True)
            # total_supply_tracked = sum(b[1] for b in sorted_balances) # This is NOT real total supply

            print(f"\nToken: {details['symbol']} ({details.get('name', 'N/A')}) - Address: {token_addr}")
            print(f"  Top {min(5, len(sorted_balances))} net receivers/holders from recent activity:")
            for i, (wallet, balance) in enumerate(sorted_balances[:5]):
                # Percentage of *tracked* total, not actual total supply.
                # percentage_of_tracked = (balance / total_supply_tracked * 100) if total_supply_tracked > 0 else 0
                # print(f"    {i+1}. {wallet}: {balance:,.4f} {details['symbol']} ({percentage_of_tracked:.2f}% of tracked)")
                print(f"    {i+1}. {wallet}: {balance:,.4f} {details['symbol']}")


        if target_defi_contracts:
            print("\n--- DeFi Contract Flow Spike Analysis ---")
            current_time = time.time()
            for contract_addr_str in target_defi_contracts:
                contract_addr = self.get_checksum_address(contract_addr_str)
                flow_data = self.defi_contract_flows[contract_addr]

                # Spike detection: e.g., > N txns in last M minutes
                # For PoC, just show recent activity count.
                tx_in_last_5_min = sum(1 for ts in flow_data["recent_timestamps"] if current_time - ts <= 300)

                print(f"\nContract: {contract_addr}")
                print(f"  Total Inflow (USD): ${flow_data['inflow_usd']:,.2f}")
                print(f"  Total Outflow (USD): ${flow_data['outflow_usd']:,.2f}")
                print(f"  Net Flow (USD): ${flow_data['inflow_usd'] - flow_data['outflow_usd']:,.2f}")
                print(f"  Total Transactions: {flow_data['tx_count']}")
                print(f"  Transactions in last 5 mins: {tx_in_last_5_min}")
                if tx_in_last_5_min > 10: # Example spike threshold
                    spike_alert_msg = f"🔥 SPIKE ALERT on {contract_addr}: {tx_in_last_5_min} transactions in the last 5 minutes!"
                    print(spike_alert_msg)
                    self.send_webhook_alert({"type": "defi_spike", "message": spike_alert_msg, "contract_address": contract_addr, "tx_count_5min": tx_in_last_5_min})


    def send_webhook_alert(self, payload):
        if WEBHOOK_URL:
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                # print(f"[INFO] Webhook alert sent successfully to {WEBHOOK_URL}")
            except requests.exceptions.RequestException as e:
                print(f"[WARN] Failed to send webhook alert to {WEBHOOK_URL}: {e}")
        else:
            # print("[DEBUG] Webhook URL not set. Skipping webhook alert.")
            pass


# Example Usage (Async):
import asyncio

async def main():
    monitor = WhaleTransactionMonitor(alert_threshold_usd=50000) # Set your threshold

    latest_block_num = monitor.w3.eth.block_number
    start_block_scan = latest_block_num - 100 # Scan last 100 blocks for PoC (adjust as needed)
    # For continuous monitoring, you'd poll for new blocks.

    # Example DeFi contracts to monitor (Trader Joe Router, Pangolin Router on Avalanche)
    example_defi_contracts = [
        "0x60aE616a2155Ee3d9A68541Ba4544862310933d4", # Trader Joe Router V1
        "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",  # Pangolin Router
        "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" # WAVAX (to see flows in/out of it)
    ]

    await monitor.scan_blocks(start_block_scan, latest_block_num, target_defi_contracts=example_defi_contracts)
    monitor.analyze_tracked_data(target_defi_contracts=example_defi_contracts)

if __name__ == "__main__":
    # This part needs to be run in an asyncio event loop
    # If you are running this script directly:
    # For Python 3.7+
    asyncio.run(main())
    # For older Python versions, you might need:
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())

