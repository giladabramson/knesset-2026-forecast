# Inverse-variance blend of the poll model and Polymarket, party by party.
#   polls:      mean = momentum forecast (model.py settings); variance = weighted spread of the individual polls
#   Polymarket: mean/variance of the normalised seat-bracket distribution (incl. within-bracket spread)
#   weight on Polymarket = (1/v_pm) / (1/v_pm + 1/v_poll); then threshold + largest-remainder allocation.
import re
import sys

import numpy as np
import pandas as pd

import model as M

# systematic poll error (seats, for a 20-seat party); 0 = trust the between-poll spread only
SYS = float(sys.argv[1]) if __name__ == "__main__" and len(sys.argv) > 1 else 0.0


def bracket_value_var(label):
    """Representative seat value and within-bracket variance of a bracket label."""
    s = label.replace(" ", "")
    if s.startswith("<"):
        k = int(s[1:])
        return (3.0, 0.5) if k <= 4 else (k - 2.5, 2.0)      # "<4" = misses the threshold (~3 seat-eq)
    if s.endswith("+"):
        k = int(s[:-1])
        return k + 1.5, 2.0                                    # open upper tail
    nums = [int(x) for x in re.findall(r"\d+", s)]
    a, b = nums[0], nums[-1]
    return (a + b) / 2, ((b - a + 1) ** 2 - 1) / 12


def pm_dist(party):
    ev = M.pm[M.pm["slug"] == f"israel-election-{M.SLUG[party]}-of-seats"]
    if ev.empty:
        return None
    labels = [g if isinstance(g, str) else q for g, q in zip(ev["group"], ev["question"])]
    p = ev["yes"].to_numpy(float)
    p = p / p.sum()
    vals, inner = zip(*(bracket_value_var(l) for l in labels))
    vals, inner = np.array(vals), np.array(inner)
    mean = (p * vals).sum()
    var = (p * (inner + (vals - mean) ** 2)).sum()
    below = p[np.array([l.replace(" ", "") == "<4" for l in labels])].sum()
    return mean, var, 1 - below


poll_mean = M.forecast(True)
rows, blended = [], {}
for party in M.PARTIES:
    y = M.df[party].to_numpy(float)
    ok = ~np.isnan(y)
    v_poll = np.average((y[ok] - np.average(y[ok], weights=M.w[ok])) ** 2, weights=M.w[ok]) if ok.any() else np.nan
    v_poll = max(v_poll, 0.25)                                 # floor: pollsters round to whole seats
    v_poll += SYS ** 2 * (poll_mean[party] / 20)               # shared (systematic) poll error, scaled to party size
    pmd = pm_dist(party) if party in M.SLUG else None
    if pmd is None:
        blended[party] = poll_mean[party]
        rows.append([party, poll_mean[party], np.sqrt(v_poll), None, None, 0.0, poll_mean[party], None])
        continue
    m_pm, v_pm, p_pass = pmd
    w_pm = (1 / v_pm) / (1 / v_pm + 1 / v_poll)
    blended[party] = (1 - w_pm) * poll_mean[party] + w_pm * m_pm
    rows.append([party, poll_mean[party], np.sqrt(v_poll), m_pm, np.sqrt(v_pm), w_pm, blended[party], p_pass])

seats_poll = M.allocate(poll_mean)
seats_blend = M.allocate(blended)
tab = pd.DataFrame(rows, columns=["party", "polls", "polls_sd", "polymarket", "pm_sd", "weight_pm", "blend", "pm_P(pass)"])
tab["seats_polls"] = tab["party"].map(seats_poll)
tab["SEATS_BLEND"] = tab["party"].map(seats_blend)
tab = tab.sort_values(["SEATS_BLEND", "blend"], ascending=False)
pd.set_option("display.float_format", lambda v: f"{v:.2f}")
print(tab.to_string(index=False))

# poll-side probability of clearing the threshold, for the borderline parties
for party in ["Amcha Yisrael", "Reserv.-NEP"]:
    y = M.df[party].to_numpy(float); ok = ~np.isnan(y)
    print(f"{party}: share of (momentum-weighted) polls putting it in = {np.average(y[ok] >= 4, weights=M.w[ok]):.0%}")
for name, s in (("polls", seats_poll), ("blend", seats_blend)):
    g = sum(s[p] for p in M.GOV); a = sum(s[p] for p in M.ARAB)
    print(f"Blocs ({name}): government {g}, opposition {120 - g - a}, Arab {a}")
tab.to_csv(M.HERE / "forecast_blend.csv", index=False)
