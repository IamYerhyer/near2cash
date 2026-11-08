#!/usr/bin/env python3
"""Reproduce NearLocal's live behaviour from the command line.

One command:  python3 verify.py [near-account]

Uses only the Python standard library and no API keys. Performs the same
calls the browser app makes:

  1. NEAR mainnet RPC        -> live balance of the account (default
                                iamyerhyer.near) and its USDC balance
  2. 1Click API /v0/tokens   -> live NEAR price
  3. 1Click API /v0/quote    -> dry-run quote: 10 NEAR -> USDC on NEAR
  4. open.er-api.com         -> live USD/NGN reference rate
  5. End-to-end: what 10 NEAR becomes in naira, with the 1% service fee
     shown as its own line — the same maths the app displays.

Dry-run quotes are real solver quotes; no funds move. The final bank
payout is a regulated step executed in production by a licensed off-ramp
partner — see README.md.
"""

import base64
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

RPC = "https://rpc.mainnet.near.org"
CLICK = "https://1click.chaindefuser.com"
USDC_NEAR = "nep141:17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1"
ACCOUNT = sys.argv[1] if len(sys.argv) > 1 else "iamyerhyer.near"
FEE = 0.01


def _opener():
    proxies = {}
    for scheme in ("http", "https"):
        p = os.environ.get(scheme + "_proxy") or os.environ.get(scheme.upper() + "_PROXY")
        if p:
            proxies[scheme] = p
    return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))


def _via_curl(url, body):
    # Fallback transport for networks whose proxy drops urllib's POSTs
    # to some hosts (observed on the build VM); curl handles them fine.
    import subprocess
    cmd = ["curl", "-s", "-m", "60", url]
    if body is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if out.returncode != 0 or not out.stdout:
        raise RuntimeError(f"curl transport failed for {url}: {out.stderr.strip()[:120]}")
    return json.loads(out.stdout)


def call(url, body=None):
    req = urllib.request.Request(
        url,
        method="POST" if body is not None else "GET",
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            # some edges reject Python's default urllib user-agent
            "User-Agent": "Mozilla/5.0 (compatible; nearlocal-verify/1.0)",
        },
    )
    last = None
    for _ in range(2):
        try:
            with _opener().open(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            last = e
    try:
        return _via_curl(url, body)
    except Exception:
        raise last


def rpc(method, params):
    out = call(RPC, {"jsonrpc": "2.0", "id": "nn", "method": method, "params": params})
    if "error" in out:
        raise RuntimeError(out["error"])
    return out["result"]


def main():
    acct = rpc("query", {"request_type": "view_account", "account_id": ACCOUNT, "finality": "final"})
    near_bal = int(acct["amount"]) / 1e24
    print(f"1) NEAR RPC: {ACCOUNT} holds {near_bal:.4f} NEAR")

    args = base64.b64encode(json.dumps({"account_id": ACCOUNT}).encode()).decode()
    res = rpc("query", {
        "request_type": "call_function",
        "account_id": "17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1",
        "method_name": "ft_balance_of", "args_base64": args, "finality": "final",
    })
    usdc_bal = int(json.loads(bytes(res["result"]).decode())) / 1e6
    print(f"   USDC balance: {usdc_bal:.2f} USDC")

    tokens = call(CLICK + "/v0/tokens")
    wnear = next(t for t in tokens if t["assetId"] == "nep141:wrap.near")
    print(f"2) 1Click token list: NEAR price ${wnear['price']:.4f} (live)")

    deadline = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    q = call(CLICK + "/v0/quote", {
        "dry": True, "swapType": "EXACT_INPUT", "slippageTolerance": 100,
        "originAsset": "nep141:wrap.near", "depositType": "ORIGIN_CHAIN",
        "destinationAsset": USDC_NEAR, "refundTo": ACCOUNT, "refundType": "INTENTS",
        "recipient": ACCOUNT, "recipientType": "INTENTS",
        "amount": str(10 * 10**24), "deadline": deadline, "depositMode": "SIMPLE",
    })["quote"]
    usd_out = float(q["amountOutUsd"])
    print(f"3) Live quote (dry run): 10 NEAR -> {q['amountOutFormatted']} USDC (~${usd_out:.2f}), ~{q['timeEstimate']}s")

    fx = call("https://open.er-api.com/v6/latest/USD")
    rate = fx["rates"]["NGN"]
    print(f"4) FX reference: NGN {rate:,.2f} per $1 (mid-market, {fx['time_last_update_utc']})")

    gross = usd_out * rate
    fee = gross * FEE
    print(f"5) End-to-end: 10 NEAR -> ${usd_out:.2f} -> NGN {gross:,.0f} gross, fee NGN {fee:,.0f} (1%), bank receives NGN {gross - fee:,.0f}")
    print("OK — the app's live calls reproduce from the command line.")


if __name__ == "__main__":
    main()
