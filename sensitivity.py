# How the seat forecast moves as momentum increases (shorter half-life, stronger trend extrapolation).
import numpy as np
import pandas as pd

import model as M

import sys
HIGH = [(3.0, 0.5), (2.0, 0.5), (1.0, 0.5), (0.5, 0.5), (3.0, 1.0), (1.0, 1.0), (0.5, 1.0)]
LOW = [(3.0, 0.5), (5.0, 0.5), (7.0, 0.5), (14.0, 0.5), (1e9, 0.5), (3.0, 0.0), (7.0, 0.0), (1e9, 0.0)]
SETTINGS = LOW if "low" in sys.argv else HIGH
cols = {}
for hl, damp in SETTINGS:
    M.w = 0.5 ** (M.age / hl) * np.sqrt(M.df["n"].to_numpy(float))
    M.TREND_DAMP = damp
    eq = M.forecast(True)
    s = M.allocate(eq)
    gov = sum(s[p] for p in M.GOV)
    arab = sum(s[p] for p in M.ARAB)
    key = f"hl={hl:g}d, trend x{damp:g}"
    cols[key] = {**{p: s[p] for p in M.PARTIES},
                 "Amcha (seat-eq)": round(eq["Amcha Yisrael"], 2), "Reserv. (seat-eq)": round(eq["Reserv.-NEP"], 2),
                 "GOV bloc": gov, "OPP bloc": 120 - gov - arab, "ARAB": arab,
                 "eff. polls": round(M.w.sum() ** 2 / (M.w ** 2).sum(), 1)}
tab = pd.DataFrame(cols)
tab = tab.loc[[p for p in tab.index if not (p in M.PARTIES and (tab.loc[p] == 0).all())]]
print(f"threshold = {M.THRESHOLD_SEATS:.2f} seat-equivalents\n")
print(tab.to_string())
