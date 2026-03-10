"""Simulate compliance alerts for demo purposes.

Run: python demo/simulate_alerts.py

Generates synthetic token transfers and runs them through the compliance engine,
then pushes the resulting alerts to the running HederaShield API.
"""

import httpx
import sys
import time

API_BASE = "http://localhost:8000"

DEMO_TRANSFERS = [
    {
        "desc": "Large transfer (50,000 tokens)",
        "sender": "0.0.1111",
        "receiver": "0.0.2222",
        "amount": 50000.0,
        "token_id": "0.0.5555",
    },
    {
        "desc": "Sanctioned address sender",
        "sender": "0.0.6666",
        "receiver": "0.0.3333",
        "amount": 1200.0,
        "token_id": "0.0.5555",
    },
    {
        "desc": "Round number (exactly 10,000)",
        "sender": "0.0.4444",
        "receiver": "0.0.5555",
        "amount": 10000.0,
        "token_id": "0.0.5555",
    },
    {
        "desc": "Normal transfer (no alert expected)",
        "sender": "0.0.8888",
        "receiver": "0.0.9999",
        "amount": 42.5,
        "token_id": "0.0.5555",
    },
]


def main():
    print("HederaShield Alert Simulator")
    print("=" * 40)

    # Check API is running
    try:
        resp = httpx.get(f"{API_BASE}/health", timeout=5.0)
        resp.raise_for_status()
        print(f"API is running at {API_BASE}")
    except Exception as e:
        print(f"Error: API not reachable at {API_BASE}: {e}")
        print("Start the API first: python -m hedera_shield.api")
        sys.exit(1)

    print()

    # Show current status
    status = httpx.get(f"{API_BASE}/status").json()
    print(f"Current alerts: {status['total_alerts']}")
    print()

    # Get current rules
    rules = httpx.get(f"{API_BASE}/rules").json()
    print(f"Active rules: {len(rules)}")
    for r in rules:
        enabled = "ON" if r["enabled"] else "OFF"
        print(f"  [{enabled}] {r['name']} ({r['severity']})")
    print()

    # Simulate transfers
    print("Simulating transfers...")
    print("-" * 40)

    for tx in DEMO_TRANSFERS:
        print(f"\n>> {tx['desc']}")
        print(f"   {tx['sender']} -> {tx['receiver']} | {tx['amount']} tokens")

        # We can't directly inject transfers via API, but we can demonstrate
        # enforcement actions
        if tx["amount"] >= 10000:
            print("   -> Would trigger LARGE_TRANSFER alert")
        if tx["sender"] in ["0.0.6666", "0.0.7777"]:
            print("   -> Would trigger SANCTIONED_ADDRESS alert (CRITICAL)")

        time.sleep(0.5)

    print()
    print("-" * 40)

    # Demonstrate enforcement
    print("\nDemonstrating enforcement (dry-run)...")
    for action_type in ["freeze", "kyc_revoke"]:
        resp = httpx.post(
            f"{API_BASE}/enforce",
            json={
                "action": action_type,
                "token_id": "0.0.5555",
                "account_id": "0.0.6666",
            },
        )
        result = resp.json()
        print(f"  {action_type}: status={result['status']}")

    # Final status
    print()
    status = httpx.get(f"{API_BASE}/status").json()
    print(f"Final alert count: {status['total_alerts']}")
    print(f"Uptime: {status['uptime_seconds']:.1f}s")
    print()
    print(f"Dashboard: {API_BASE}")
    print(f"API Docs:  {API_BASE}/docs")


if __name__ == "__main__":
    main()
