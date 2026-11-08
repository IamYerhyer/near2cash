# Near2Cash — your NEAR, in your local currency

A NEAR wallet whose home screen answers one question — **"what is this worth in
my money?"** — and whose convert flow takes a NEAR asset to a local-currency
bank payout in a few taps: live balance, live conversion quote through NEAR
Intents, live exchange rate, a full fee breakdown before you confirm, and
payout to your bank. Built in Nigeria, for everywhere: naira is the default
showcase currency, and the same flow prices in 11 currencies.

**NEAR Hackathon 2026 — Real-World Money track.** Solo project by Shuaibu
Yahaya (`iamyerhyer.near`). My second entry; my other entry is the Investment
Thesis dashboard, *Flow, Not Price*
([github.com/IamYerhyer/near-intents-signal](https://github.com/IamYerhyer/near-intents-signal)).

## The problem

Millions of people — across Africa and beyond — earn and hold crypto but spend
in local currency. Getting from NEAR to naira (or cedis, or shillings) today
means P2P markets, opaque rates and counterparty risk. Every wallet shows the
crypto balance first and the fiat value as small print. Near2Cash inverts
that: **your money first, crypto second.**

## Try it (30 seconds, nothing to install)

1. Open the live demo. The wallet loads `iamyerhyer.near` with its **real,
   live balances** — the total in your currency is computed from live prices
   and a live FX rate, not stored anywhere.
2. Type any NEAR account into the box and tap **Load** — the balances are read
   live from NEAR mainnet.
3. Tap **NEAR**, enter `10`, tap **Get live quote**. You get a real quote from
   live Intents solvers, the mid-market ₦/$ rate shown beside the maths, the
   1% service fee as its own line, and the exact amount in your currency the
   bank would receive.
4. Continue to **Review & cash out**, pick a bank, enter any 10-digit account
   number and a name, and confirm — the payout instruction is prepared and
   each step's status is shown honestly.

Switch the currency at the top (NGN, GHS, KES, ZAR, EGP, UGX, TZS, XOF, USD,
EUR, GBP) and every figure re-prices from the same live FX source.

## What is live vs what is the boundary

| Piece | Status |
|---|---|
| Account balances (NEAR + wNEAR, USDC, USDT, bridged ETH) | **Live** — NEAR mainnet RPC, public reads, no keys |
| Asset prices | **Live** — NEAR Intents 1Click token list |
| Asset → USDC conversion quote | **Live** — real solver quotes via the 1Click API (dry run) |
| USD → local currency | **Live** — mid-market reference rate from open.er-api.com, timestamp shown in-app |
| Fee | Modelled at a flat, visible **1%** — its own line, never hidden in the rate |
| Swap execution | Production step — executes against the locked quote with the user's wallet signature |
| **Bank payout** | **Regulated step** — executed in production by a licensed off-ramp partner; the prototype completes everything up to the payout instruction and labels it plainly. No real money is sent to any bank. |

## Verify it yourself

```bash
python3 verify.py            # or: python3 verify.py someaccount.near
```

Standard library only, no keys. It reads the account's live NEAR and USDC
balances via NEAR RPC, pulls the live NEAR price and a real dry-run quote
(10 NEAR → USDC) from the 1Click API, fetches the live USD/NGN rate, and
prints the end-to-end naira figure with the fee broken out — the same calls
and the same maths as the app (the CLI verifies in NGN; the app applies the
identical maths to every supported currency).

## How it works

One self-contained `index.html` — no build step, no server, no keys:

- **Balances:** JSON-RPC `view_account` + `ft_balance_of` against
  `rpc.mainnet.near.org`.
- **Quotes:** `POST /v0/quote` (dry) and `GET /v0/tokens` against
  `1click.chaindefuser.com` — the public NEAR Intents API. Because settlement
  is Intents, assets that arrived on NEAR from other chains land in the same
  cash-out flow.
- **FX:** `open.er-api.com/v6/latest/USD` mid-market reference, fetched fresh;
  the rate and its timestamp are displayed wherever it is used.
- Endpoint bases can be overridden with `?rpc=`, `?click=` and `?fx=` URL
  parameters for self-hosting.

## On competition, honestly

Off-ramps exist (continental exchanges, P2P desks, global on/off-ramp
providers). None is NEAR-native with Intents under the hood, and the P2P route
most Nigerians actually use prices opaquely — the counterparty's spread is the
product. Near2Cash's bet is that **radical rate transparency** (mid-market rate
shown, every fee itemised, live solver quotes instead of a house price) plus
a fiat-first wallet is the version people trust with real money.

## Limitations of this prototype

- Read-only: it cannot sign or move funds; connecting a wallet and executing
  the swap against the locked quote is the next build step.
- Five NEAR assets are listed; the token list the API prices is far larger.
- The FX rate is a mid-market reference, not a tradeable rate; a production
  partner's rate would replace it at the payout step, still displayed.
