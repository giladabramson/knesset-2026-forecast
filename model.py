# Knesset 2026 forecast: high-momentum poll average (excluding Channel 14 and i24NEWS), cross-checked with Polymarket.
#   1. Each poll -> "seat-equivalents" per party (seats; sub-threshold entries "(2.4%)" -> pct * 1.2).
#   2. Momentum: exponential recency weights (half-life HALF_LIFE days) x sqrt(sample size),
#      plus a damped weighted linear trend over the last TREND_WINDOW days, extrapolated to election day.
#   3. Threshold 3.25% (= 3.9 seat-equivalents): parties below it get 0; the rest share 120 seats (largest remainder).
#   4. Polymarket: expected seats per party from its seat-bracket markets, winner, blocs, turnout.
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
ELECTION = pd.Timestamp("2026-10-27")
HALF_LIFE = 3.0      # days: "high momentum"
TREND_WINDOW = 14    # days of data used for the trend
TREND_DAMP = 0.5     # extrapolate only half of the fitted trend
THRESHOLD_SEATS = 3.25 / 100 * 120
EXCLUDE = {"Channel 14", "i24NEWS"}
PARTIES = ["Likud", "Together", "RZP-Zehut", "Otzma", "Blue & White", "Shas", "UTJ", "Yisrael Beiteinu",
           "Ra'am", "Joint List", "Dems", "Yashar", "Reserv.-NEP", "Amcha Yisrael", "Haredi Public"]
GOV = ["Likud", "RZP-Zehut", "Otzma", "Shas", "UTJ"]
ARAB = ["Ra'am", "Joint List"]


def seat_equiv(cell):
    s = str(cell).strip()
    if re.fullmatch(r"\d+", s):
        return float(s)
    m = re.fullmatch(r"\(<?\s*([\d.]+)%\)", s)
    if m:                                   # sub-threshold vote share; "(<1%)" -> treat as 0.5%
        pct = float(m.group(1)) if "<" not in s else float(m.group(1)) / 2
        return pct / 100 * 120
    return np.nan                           # not polled / not listed


def poll_date(s):
    return pd.Timestamp(str(s).split(" to ")[-1])


df = pd.read_csv(HERE / "polls_oct2026.csv")
df = df[~df["Media outlet"].isin(EXCLUDE)].copy()
df["date"] = df["Fieldwork date"].map(poll_date)
df["n"] = pd.to_numeric(df["Sample size"], errors="coerce").fillna(500)
for p in PARTIES:
    df[p] = df[p].map(seat_equiv)

age = (ELECTION - df["date"]).dt.days.to_numpy(float)
w = 0.5 ** (age / HALF_LIFE) * np.sqrt(df["n"].to_numpy(float))


def forecast(use_trend):
    out = {}
    for p in PARTIES:
        y = df[p].to_numpy(float)
        ok = ~np.isnan(y)
        if ok.sum() == 0:
            out[p] = 0.0
            continue
        level = np.average(y[ok], weights=w[ok])
        if use_trend:
            recent = ok & (age <= TREND_WINDOW + 4)
            if recent.sum() >= 4:
                t = -age[recent]                       # days relative to election day (0)
                slope = np.polyfit(t, y[recent], 1, w=np.sqrt(w[recent]))[0]
                t_bar = np.average(t, weights=w[recent])
                level += TREND_DAMP * slope * (0 - t_bar)
        out[p] = max(level, 0.0)
    return out


def allocate(eq):
    passing = {p: v for p, v in eq.items() if v >= THRESHOLD_SEATS}
    total = sum(passing.values())
    quotas = {p: v / total * 120 for p, v in passing.items()}
    seats = {p: int(np.floor(q)) for p, q in quotas.items()}
    for p in sorted(quotas, key=lambda p: quotas[p] - seats[p], reverse=True)[: 120 - sum(seats.values())]:
        seats[p] += 1
    return {p: seats.get(p, 0) for p in PARTIES}


# ---- Polymarket ---------------------------------------------------------------------------------------
pm = pd.DataFrame(json.loads((HERE / "polymarket_events.json").read_text(encoding="utf-8")))
pm = pm[pm["closed"] != True]
SLUG = {"Likud": "likud", "Together": "together", "RZP-Zehut": "rzp-zehut", "Otzma": "otzma", "Shas": "shas",
        "UTJ": "utj", "Yisrael Beiteinu": "yisrael-beiteinu", "Ra'am": "raam", "Joint List": "joint-list",
        "Dems": "dems", "Yashar": "yashar", "Amcha Yisrael": "amcha-yisrael"}


def bracket_mid(label):
    s = label.lower()
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if "fewer" in s or "less" in s or "<" in s:
        return max(nums[0] - 2, 0) if nums[0] > 4 else nums[0] / 2   # rough tail midpoint
    if "or more" in s or "+" in s:
        return nums[0] + 2
    return sum(nums) / len(nums)


def pm_expected(party):
    ev = pm[pm["slug"] == f"israel-election-{SLUG[party]}-of-seats"]
    if ev.empty:
        return np.nan, ""
    probs = ev["yes"].to_numpy(float)
    mids = np.array([bracket_mid(g or q) for g, q in zip(ev["group"], ev["question"])])
    probs = probs / probs.sum()
    top = ev.iloc[int(np.argmax(ev["yes"].to_numpy(float)))]
    return float((probs * mids).sum()), f"{top['group'] or top['question']} ({top['yes']:.0%})"


def show_event(slug, k=6):
    ev = pm[pm["slug"] == slug].sort_values("yes", ascending=False).head(k)
    label = lambda g, q: (g if isinstance(g, str) and g else q)[:45]
    return ", ".join(f"{label(g, q)} {y:.0%}" for g, q, y in zip(ev["group"], ev["question"], ev["yes"]))


if __name__ == "__main__":
    print(f"Polls used: {len(df)} (excluded {', '.join(sorted(EXCLUDE))}); outlets: {', '.join(sorted(df['Media outlet'].unique()))}")
    print(f"Latest poll {df['date'].max().date()}, half-life {HALF_LIFE} d, trend damp {TREND_DAMP}\n")
    lvl, trd = forecast(False), forecast(True)
    s_lvl, s_trd = allocate(lvl), allocate(trd)
    rows = []
    for p in PARTIES:
        exp, top = pm_expected(p) if p in SLUG else (np.nan, "")
        rows.append([p, round(lvl[p], 1), round(trd[p], 1), s_lvl[p], s_trd[p],
                     None if np.isnan(exp) else round(exp, 1), top])
    tab = pd.DataFrame(rows, columns=["party", "avg_eq", "trend_eq", "seats_avg", "SEATS_FORECAST", "polymarket_E", "polymarket_mode"])
    tab = tab.sort_values("SEATS_FORECAST", ascending=False)
    print(tab.to_string(index=False))
    for name, s in (("avg", s_lvl), ("forecast", s_trd)):
        g = sum(s[p] for p in GOV); a = sum(s[p] for p in ARAB)
        print(f"\nBlocs ({name}): government {g}, opposition {120 - g - a}, Arab parties {a}")
    print("\nPolymarket:")
    for slug in ["israeli-legislative-election-winner", "israel-election-which-bloc-wins-more-seats",
                 "israel-election-any-coalition-wins-a-majority", "israeli-legislative-election-turnout",
                 "who-will-be-the-next-prime-minister-of-israel-after-the-next-election"]:
        print(f"  {slug}: {show_event(slug)}")
    tab.to_csv(HERE / "forecast.csv", index=False)
