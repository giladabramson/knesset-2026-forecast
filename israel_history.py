# How wrong were Israeli final-week poll averages, 2015-2022? (Wikipedia poll tables; exit polls excluded;
# 2022 also excludes Channel 14 to match the 2026 model's filter.)
#   - per-party seat error (result - poll mean), Likud and the Netanyahu bloc specifically
#   - threshold flips (polled in on average, finished out, or vice versa)
#   - an estimate of the shared ("systematic") error SYS used by blend.py: E[(r-m)^2 / (m/20)] = SYS^2
import numpy as np
import pandas as pd

S = lambda x: 0.0 if isinstance(x, str) else float(x)   # sub-threshold "(2.1%)" -> 0 seats

DATA = {
    "2015": dict(
        parties=["Likud", "Yisrael Beiteinu", "Yesh Atid", "Labor", "Jewish Home", "Shas", "UTJ", "Meretz", "Joint List", "Otzma/Yachad", "Kulanu"],
        bloc=["Likud", "Yisrael Beiteinu", "Jewish Home", "Shas", "UTJ", "Otzma/Yachad", "Kulanu"],
        polls=[[22,5,12,26,11,7,6,5,13,5,8],[20,5,12,24,12,7,7,5,13,5,10],[21,6,11,25,11,9,6,5,13,4,9],[21,4,13,25,11,7,6,5,13,5,10],
               [23,6,12,25,11,7,7,4,12,4,9],[22,5,12,26,12,7,6,5,13,4,8],[22,6,12,25,11,8,7,4,12,4,9],[21,5,13,24,12,7,7,5,13,4,9],
               [20,6,12,24,12,9,6,5,13,4,9],[21,5,13,24,13,7,7,5,12,5,8],[21,4,12,24,11,7,6,6,13,5,11],[21,6,12,24,13,7,7,6,12,4,8],
               [21,5,14,24,12,7,6,5,13,4,9],[21,6,12,25,13,7,6,5,13,4,8],[26,7,12,21,13,8,8,5,12,0,8]],
        result=[30,6,11,24,8,7,6,5,13,0,10]),
    "2019-04": dict(
        parties=["Likud", "Labor", "Blue & White", "Kulanu", "Ra'am-Balad", "Shas", "UTJ", "URWP", "Yisrael Beiteinu", "Meretz", "Hadash-Ta'al", "New Right", "Gesher", "Zehut"],
        bloc=["Likud", "Kulanu", "Shas", "UTJ", "URWP", "Yisrael Beiteinu", "New Right", "Zehut"],
        polls=[[31,9,30,4,"x",5,6,5,4,6,9,6,"x",5],[28,8,32,5,4,6,6,5,4,5,7,5,"x",5],[29,14,28,4,5,5,6,7,"x",5,6,5,"x",6],
               [30,10,27,5,4,5,6,7,4,5,7,5,"x",5],[29,10,30,"x",4,5,6,7,4,6,8,6,"x",5],[27,9,28,5,4,6,6,6,5,5,6,5,4,4],
               [26,11,30,5,4,5,7,5,4,5,7,6,"x",5],[27,10,32,6,"x",5,8,6,"x",8,6,6,"x",6],[31,8,30,5,4,4,6,6,"x",6,8,6,"x",6],
               [26,10,30,5,4,5,7,5,5,5,7,6,"x",5],[31,10,28,"x",4,6,6,8,"x",5,7,7,"x",8],[28,11,28,4,4,5,6,7,4,5,6,6,"x",6],
               [27,9,29,5,4,6,7,6,4,5,7,6,"x",5]],
        result=[35,6,35,4,4,8,8,5,5,4,6,0,0,0]),
    "2019-09": dict(
        parties=["Likud", "Blue & White", "Joint List", "Shas", "UTJ", "Yamina", "Labor-Gesher", "Yisrael Beiteinu", "Dem. Union", "Otzma Yehudit"],
        bloc=["Likud", "Shas", "UTJ", "Yamina", "Otzma Yehudit"],
        polls=[[32,32,12,6,7,9,4,9,5,4],[32,32,10,7,8,8,5,8,6,4],[33,32,11,7,8,7,4,9,5,4],[33,32,12,8,7,9,5,8,6,"x"],
               [36,32,10,7,8,9,4,9,5,"x"],[33,32,12,8,7,9,4,9,6,"x"],[31,33,11,7,8,9,5,7,5,4],[33,31,12,7,7,7,6,9,4,4],
               [31,32,11,6,7,9,5,9,6,4],[31,32,9,7,7,9,6,9,6,4],[31,32,10,7,7,9,5,9,6,4],[32,33,9,6,7,9,6,8,6,4]],
        result=[32,33,13,9,7,7,6,8,5,0]),
    "2020": dict(
        parties=["Blue & White", "Likud", "Joint List", "Emet", "Shas", "Yisrael Beiteinu", "UTJ", "Yamina", "Otzma"],
        bloc=["Likud", "Shas", "UTJ", "Yamina", "Otzma"],
        polls=[[34,35,14,8,9,6,7,7,"x"],[33,33,15,9,8,7,7,8,"x"],[33,35,14,9,8,6,8,7,"x"],[34,34,13,9,9,7,7,7,"x"],
               [33,33,14,9,8,7,7,9,"x"],[34,35,14,8,8,6,8,7,"x"],[33,35,13,9,9,6,8,7,"x"],[34,34,13,9,8,7,8,7,"x"],
               [32,34,14,9,8,8,7,8,"x"],[33,34,14,10,8,7,7,7,"x"],[32,33,14,10,8,8,7,8,"x"],[34,35,14,9,8,7,7,6,"x"],
               [33,34,13,10,8,7,8,7,"x"]],
        result=[33,36,15,7,9,7,7,6,0]),
    "2021": dict(
        parties=["Likud", "Yesh Atid", "Blue & White", "Joint List", "Shas", "UTJ", "Yisrael Beiteinu", "Meretz", "Ra'am", "Yamina", "New Hope", "Labor", "Religious Zionist"],
        bloc=["Likud", "Shas", "UTJ", "Religious Zionist"],
        polls=[[30,18,4,8,8,7,6,4,4,10,10,6,5],[32,18,4,8,8,7,7,4,4,9,9,6,4],[30,19,5,8,8,6,8,4,4,10,8,5,5],
               [32,17,7,7,9,7,9,4,4,8,7,4,5],[31,19,4,8,8,7,7,4,4,9,9,5,5],[31,19,4,8,8,7,7,4,4,9,9,5,5],
               [29,18,4,10,9,7,8,5,"x",10,10,5,5],[30,18,4,8,8,7,7,4,4,10,10,6,4],[28,20,4,8,7,7,7,4,4,11,10,5,5],
               [28,20,4,8,6,7,7,4,4,11,9,6,6]],
        result=[30,17,8,6,9,7,7,6,4,7,6,7,6]),
    "2022": dict(
        parties=["Likud", "Yesh Atid", "National Unity", "Shas", "Jewish Home", "Labor", "UTJ", "Yisrael Beiteinu", "RZP-OY", "Hadash-Ta'al", "Meretz", "Ra'am", "Balad"],
        bloc=["Likud", "Shas", "UTJ", "RZP-OY"],
        polls=[[30,27,10,8,"x",6,7,5,15,4,4,4,"x"],[31,25,11,8,"x",5,7,6,14,4,5,4,"x"],[31,25,11,9,"x",5,7,6,14,4,4,4,"x"],
               [31,24,11,8,"x",6,7,6,14,4,5,4,"x"],[31,25,12,9,"x",4,6,6,14,4,5,4,"x"],[30,25,11,9,"x",6,7,5,15,4,4,4,"x"],
               [32,25,12,9,"x",5,7,5,13,4,4,4,"x"],[31,25,13,8,"x",5,7,6,12,4,5,4,"x"],[31,27,11,8,"x",4,7,6,14,4,4,4,"x"],
               [31,24,12,8,"x",5,7,6,14,4,5,4,"x"],[32,24,13,8,"x",5,7,5,13,4,5,4,"x"],[32,23,12,8,"x",5,7,6,14,4,5,4,"x"],
               [31,24,12,9,"x",5,7,6,13,4,5,4,"x"]],
        result=[32,24,12,11,0,4,7,6,14,5,0,5,0]),
}

rows, flips = [], []
for year, d in DATA.items():
    P = np.array([[S(v) for v in p] for p in d["polls"]])
    mean = P.mean(axis=0)
    for i, party in enumerate(d["parties"]):
        r = d["result"][i]
        rows.append(dict(election=year, party=party, poll_mean=mean[i], result=r, error=r - mean[i],
                         bloc=party in d["bloc"], n_polls=len(P)))
        share_in = (P[:, i] > 0).mean()
        if (share_in >= 0.5) != (r > 0):
            flips.append(f"{year} {party}: in {share_in:.0%} of final polls (mean {mean[i]:.1f}) -> result {r}")
df = pd.DataFrame(rows)

print("Likud: final-poll mean vs result")
lik = df[df.party == "Likud"][["election", "poll_mean", "result", "error"]]
print(lik.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
print(f"  mean signed error {lik.error.mean():+.2f} seats, mean |error| {lik.error.abs().mean():.2f}")

bloc = df[df.bloc].groupby("election").agg(poll=("poll_mean", "sum"), result=("result", "sum"))
bloc["error"] = bloc.result - bloc.poll
print("\nNetanyahu bloc (right + Haredi): final-poll mean vs result")
print(bloc.to_string(float_format=lambda v: f"{v:.1f}"))
print(f"  mean signed error {bloc.error.mean():+.2f} seats, mean |error| {bloc.error.abs().mean():.2f}")

big = df[df.poll_mean >= 4]
print(f"\nAll parties polled >= 4 seats ({len(big)} party-elections): mean |error| {big.error.abs().mean():.2f} seats")
sys2 = ((big.error ** 2) / (big.poll_mean.clip(lower=4) / 20)).mean()
print(f"Estimated shared poll error for a 20-seat party (blend.py SYS): {np.sqrt(sys2):.2f} seats")
lik_sys = np.sqrt(((lik.error ** 2) / (lik.poll_mean / 20)).mean())
print(f"  same estimate from Likud only: {lik_sys:.2f} seats")

print(f"\nThreshold flips ({len(flips)} in 6 elections):")
for f in flips:
    print("  " + f)
df.to_csv("israel_history_errors.csv", index=False)
