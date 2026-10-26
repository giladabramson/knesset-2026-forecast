# Knesset 2026 forecast: momentum-weighted polls × Polymarket

A forecast of the 27 October 2026 Knesset election, made for the HUJI Department of Statistics & Data Science election-forecast competition (systematic track). Author: Gilad Abramson.

## Forecast

| Party | Seats |
|---|---|
| Yashar | 22 |
| Likud | 21 |
| Together | 14 |
| Dems | 10 |
| Joint List | 9 |
| Otzma Yehudit | 8 |
| Shas | 8 |
| Yisrael Beiteinu | 8 |
| RZP–Zehut | 7 |
| UTJ | 7 |
| Ra'am | 6 |
| Amcha Yisrael, Reservists–NEP, Blue & White, others | 0 |

- **Blocs:** government 51, opposition 54, Arab parties 15.
- **Turnout:** 74%.
- Machine-readable: [`FINAL_submission.csv`](FINAL_submission.csv).

## Method

1. **Polls ([`model.py`](model.py)).**
   - Data: all October 2026 seat polls ([`polls_oct2026.csv`](polls_oct2026.csv), from Wikipedia), excluding Channel 14 and i24NEWS.
   - Seat-equivalents: each poll is converted to seat-equivalents. A sub-threshold "(2.4%)" entry counts as pct × 1.2.
   - Momentum weights: exponential with a 3-day half-life, multiplied by √(sample size).
   - Trend: a damped (×0.5) two-week linear trend, extrapolated to election day.
2. **Polymarket ([`fetch_polymarket.py`](fetch_polymarket.py)).**
   - Every open seat-bracket market, pulled from the public gamma API on 2026-10-26 ([`polymarket_events.json`](polymarket_events.json)).
   - Bracket prices are normalised into a distribution, giving a mean and variance per party.
3. **Shared poll error ([`israel_history.py`](israel_history.py)).**
   - Data: final-10-day polls compared with results in the 2015–2022 Israeli elections.
   - Likud was under-polled by +2.9 seats on average. The Netanyahu bloc by +1.0.
   - Estimated shared poll error: about 3.7 seats for a 20-seat party.
   - All 5 threshold flips went the same way: polled in, finished out.
4. **Blend ([`blend.py`](blend.py), [`blend_corr.py`](blend_corr.py)).**
   - Combination: per party, a minimum-variance combination of the poll forecast (between-poll spread plus the shared error) and the Polymarket distribution.
   - Correlation: the errors are assumed to correlate (ρ = 0.5), because the market partly follows the polls.
   - Liquidity: the market weight is shrunk by min(1, √(volume / $1M)).
   - Resulting market weight: Likud ≈ 32%, smaller parties 5–12%.
   - Threshold: decisions follow the polls only (borderline parties stay out). Seats are allocated by largest remainder above 3.25%.
5. **Robustness ([`sensitivity.py`](sensitivity.py)).**
   - Half-lives from 0.5 days to no decay, with or without trend.
   - Correlation from ρ = 0 to 0.7.
   - Across all of these the result moves by at most one seat per party.
6. **Turnout.** The Polymarket turnout market's expected value is about 72.7%; the modal bracket is 74%+. Adjusted up to 74%.

## External check (not in code)

Polls vs Polymarket vs results in the UK 2024, France 2024, Germany 2025, US 2020/2024, Canada 2025, Australia 2025, the Netherlands 2023/2025, Brazil 2022/2026, Argentina 2023 and Hungary 2026. Findings:
- A shared poll error of 2–4 points is normal.
- The market adds information on large, liquid questions (the UK seat brackets were all correct).
- The market is overconfident on thin and threshold questions (Germany 2025: 35% that FDP clears 5%; it got 4.3%).
- The market favourite won 10 of 13 times, at an average price of 78%.

## Run

```
pip install numpy pandas requests
python fetch_polymarket.py      # refresh market data (optional; a snapshot is included)
python model.py                 # poll-only forecast
python blend_corr.py 0.5        # final blended forecast -> FINAL_submission.csv
python sensitivity.py [low]     # momentum sensitivity
python israel_history.py        # historical poll errors
```

Data sources: [Wikipedia: 2026 Israeli election polling](https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Israeli_legislative_election), the Wikipedia polling pages for 2015–2022, and [Polymarket](https://polymarket.com) (public API).
