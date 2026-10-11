# KATARINA HPP Studio Lite — Offline Demo

A demonstration for pricing a menu based on recipes, packaging, overhead, estimated waste, and target **gross margin**. Developed separately as a shareable sample: it is not the full commercial HPP Studio and not a claim of a completed sale.

## Use

Unzip the archive, then open **index.html** in Chrome/Edge or a current browser. No installation, external JavaScript, login, API key, or server is needed. Use **Cadangkan JSON** to retain data; browser local storage may be deleted. Import the file later using **Impor cadangan**. CSV is for reference, not an official tax/accounting report.

## Calculation

For each ingredient: `price of package / package quantity * quantity used * (1 + waste percentage / 100)`. All ingredients + per-serving packaging + overhead per batch = batch cost. Batch cost ÷ number of portions = HPP per portion. Recommended price = HPP ÷ (1 − target gross margin), rounded **up** to the next Rp500.

All numbers are Indonesian rupiah. Package quantity and usage must use the **same unit**, e.g. ml/ml, grams/grams. Do not enter a margin of 100%; maximum is 99%. Remember transaction/platform costs, taxes and refunds where relevant.

## Scope and limitations

- No cloud storage, multi-device sync, payment collection, POS, billing, or accounting integration.
- Not protected against all browser deletion; data stays on user's own device until explicitly exported.
- Input values are not validated against commodity-market prices; waste estimate is simplified.
- CSV field prefixes that can be interpreted as formulas by spreadsheet apps are escaped.
- Private client data should not be shared as a public screenshot or uploaded to public repositories.

## Commercialization

Use as a demo for customization inquiries, not as an official product checkout. Sales listing setup, delivery, payment, refund and support policies must be completed separately.
