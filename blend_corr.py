# Blend weights that account for (a) correlated errors between polls and Polymarket and (b) market liquidity.
#   Optimal weight on the market for two correlated estimates (min-variance combination):
#     w = (sp^2 - rho*sp*sm) / (sp^2 + sm^2 - 2*rho*sp*sm), clipped to [0, 1]
#   then shrunk by liquidity: w *= min(1, sqrt(volume / 1e6)).
import sys

import numpy as np
import pandas as pd

import blend as B   # reuses its poll and Polymarket distributions (prints its own table on import)
import model as M

SYS, RHO = 3.74, float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
vol = M.pm.groupby("slug")["volume"].sum()

eq, rows = {}, []
for party in M.PARTIES:
    y = M.df[party].to_numpy(float); ok = ~np.isnan(y)
    vp = max(np.average((y[ok] - np.average(y[ok], weights=M.w[ok])) ** 2, weights=M.w[ok]), 0.25)
    vp += SYS ** 2 * (B.poll_mean[party] / 20)
    d = B.pm_dist(party) if party in M.SLUG else None
    if d is None or party == "Amcha Yisrael":          # threshold party: polls decide in/out
        eq[party] = B.poll_mean[party] if party != "Amcha Yisrael" else 0.0
        rows.append([party, B.poll_mean[party], None, 0.0, None, eq[party]]); continue
    m, vm, _ = d
    sp, sm = np.sqrt(vp), np.sqrt(vm)
    w = np.clip((vp - RHO * sp * sm) / (vp + vm - 2 * RHO * sp * sm), 0, 1)
    v = vol.get(f"israel-election-{M.SLUG[party]}-of-seats", 0.0)
    liq = min(1.0, np.sqrt(v / 1e6))
    eq[party] = (1 - w * liq) * B.poll_mean[party] + w * liq * m
    rows.append([party, B.poll_mean[party], m, w * liq, round(v / 1e3), eq[party]])

s = M.allocate(eq)
t = pd.DataFrame(rows, columns=["party", "polls", "polymarket", "weight_pm", "volume_k$", "blend"])
t["SEATS"] = t["party"].map(s)
print(f"\n=== rho={RHO}, systematic poll error {SYS} ===")
print(t.sort_values("SEATS", ascending=False).to_string(index=False, float_format=lambda v: f"{v:.2f}"))
g = sum(s[p] for p in M.GOV); a = sum(s[p] for p in M.ARAB)
print(f"Blocs: government {g}, opposition {120 - g - a}, Arab {a}")
if RHO == 0.5:   # the submitted configuration
    pd.Series(s, name="seats").to_csv(M.HERE / "FINAL_submission.csv", index_label="party")
    (M.HERE / "FINAL_submission.csv").open("a", encoding="utf-8").write("turnout_%,74\n")
