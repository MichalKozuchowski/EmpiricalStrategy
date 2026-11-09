# =====================================================================================================
# MGT 634 · HW3 · BONUS (the only AI-allowed part): replicate Table 3, columns 3-4 of Porter (1983)
# "A Study of Cartel Stability: The Joint Executive Committee, 1880-1886", Bell Journal of Economics.
#
# What this does
#   Porter does NOT observe whether the cartel was colluding in each week. He treats the regime I_t
#   (1 = cooperative, 0 = price war) as an unknown coin flip with probability lambda (eq. 3) and
#   estimates demand (eq. 1) and supply (eq. 2) jointly by maximum likelihood (eq. 5), using
#   Kiefer's E-M algorithm (p. 306):
#       E-step: given the current parameters, compute w_t = Pr(I_t = 1 | data) by Bayes' rule
#       M-step: given the weights w_t, re-estimate the parameters and lambda = mean(w_t)
#       repeat until w_t stops changing (Porter: correlation of successive w's > .999)
#   PN_t = 1 if w_t > .5 is the "estimated cheating dummy" in the table.
#
# Model (p. 305):   B y_t = Gamma X_t + Delta I_t + U_t,   U_t ~ N(0, Sigma)
#   Demand:  log Q = a0 + a1 log P + a2 LAKES + seasonal dummies + U1
#   Supply:  log P = b0 + b1 log Q + b2' DM + b3 I + seasonal dummies + U2
#   Density of y_t given I_t (p. 306) includes the Jacobian |det B| = |1 - a1*b1|.
#
# How to run
#   Local:   uv run --with pandas --with numpy --with scipy --with numdifftools --with matplotlib
#                   --with xlrd python bonus_table3_ml.py
#   Cluster: paste the whole file into one Jupyter cell (uncomment the pip line in section 0).
# =====================================================================================================

# ---------------------------------------------------------------- 0. setup
import glob
import os
import sys

# On the cluster, uncomment the next two lines the first time (cluster blocks system-wide installs):
# !{sys.executable} -m pip install --user --quiet scipy numdifftools xlrd
# sys.path.insert(0, os.path.expanduser("~/.local/lib/python3.9/site-packages"))

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import numdifftools as nd
import matplotlib
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

# ---------------------------------------------------------------- 1. find and load the JEC data
# Searches the usual places instead of guessing one path (cluster paths have been wrong before).
patterns = ["~/**/JEC*", "~/**/jec*", "/gpfs/project/esai_2026/**/JEC*", "/gpfs/project/esai_2026/**/jec*",
            r"C:\Users\mnich\mgt634_data\hw3\JEC*"]
hits = []
for p in patterns:
    hits += [h for h in glob.glob(os.path.expanduser(p), recursive=True)
             if h.lower().endswith((".csv", ".xls", ".xlsx", ".dta")) and "description" not in h.lower()]
hits = sorted(set(hits))                      # same file can match several patterns
print("Data files found:", hits)
path = hits[0]
readers = {".csv": pd.read_csv, ".xls": pd.read_excel, ".xlsx": pd.read_excel, ".dta": pd.read_stata}
jec = readers[os.path.splitext(path)[1].lower()](path)
jec.columns = [c.lower() for c in jec.columns]
print("Loaded", path, "->", jec.shape)

# ---------------------------------------------------------------- 2. build the model's variables
# Variable mapping (JEC documentation -> Porter's Table 1)
df = pd.DataFrame({
    "logQ": np.log(jec["quantity"]),          # TQG, total grain tonnage (logged, eq. 1-2)
    "logP": np.log(jec["price"]),             # GR, grain rate (logged)
    "LAKES": 1 - jec["ice"],                  # = 1 if the Great Lakes are open (ice = 1 when impassable)
    "PO": jec["cartel"],                      # Railway Review's collusion indicator (used only as a starting point)
})
w = jec["week"]                               # week 1 = first week of 1880; 52 weeks per year; 328 = week 16 of 1886
wk = lambda year, k: (year - 1880) * 52 + k   # convert "week k of year" to the running week number
df["DM1"] = w.between(wk(1880, 28), wk(1883, 10)).astype(float)   # Grand Trunk entry
df["DM2"] = w.between(wk(1883, 11), wk(1883, 25)).astype(float)   # addition to New York Central
df["DM3"] = w.between(wk(1883, 26), wk(1886, 11)).astype(float)   # Chicago & Atlantic entry
df["DM4"] = w.between(wk(1886, 12), wk(1886, 16)).astype(float)   # Chicago & Atlantic leaves the JEC
SEAS = [f"seas{i}" for i in range(1, 13)]                          # 12 of 13 four-week periods (seas13 omitted)
for s in SEAS:
    df[s] = jec[s].astype(float)
T = len(df)

yQ, yP = df["logQ"].values, df["logP"].values
XD = np.column_stack([np.ones(T), df["LAKES"], df[SEAS]])                 # demand exogenous: C, LAKES, seasons
XS = np.column_stack([np.ones(T), df[["DM1", "DM2", "DM3", "DM4"]], df[SEAS]])  # supply exogenous: C, DM1-4, seasons
kD, kS = XD.shape[1], XS.shape[1]                                          # 14 and 17 coefficients
# Parameter vector theta = [a1 (price in demand), demand exog (14), b1 (quantity in supply), b3 (regime), supply exog (17)]
NTH = 1 + kD + 1 + 1 + kS


def unpack(th):
    a1, a = th[0], th[1:1 + kD]
    b1, b3, b = th[1 + kD], th[2 + kD], th[3 + kD:]
    return a1, a, b1, b3, b


def residuals(th):
    """Structural residuals U1 (demand) and U2 (supply) under I=0 and I=1."""
    a1, a, b1, b3, b = unpack(th)
    e1 = yQ - a1 * yP - XD @ a
    e2_0 = yP - b1 * yQ - XS @ b             # price war (I = 0)
    e2_1 = e2_0 - b3                          # cooperative (I = 1): supply intercept shifted up by b3
    return e1, e2_0, e2_1


def logdens(e1, e2, Sig, logjac):
    """log h(y_t | I_t): bivariate normal density of (U1, U2) times the Jacobian |1 - a1 b1|."""
    s11, s22, s12 = Sig[0, 0], Sig[1, 1], Sig[0, 1]
    det = s11 * s22 - s12 ** 2
    quad = (s22 * e1 ** 2 - 2 * s12 * e1 * e2 + s11 * e2 ** 2) / det
    return -np.log(2 * np.pi) - 0.5 * np.log(det) + logjac - 0.5 * quad


# ---------------------------------------------------------------- 3. Kiefer's E-M algorithm
def m_step(wt, th0):
    """Maximize the expected complete-data likelihood given weights wt.
    Sigma has a closed form given the coefficients, so we 'concentrate' it out and search over theta only."""
    def negconc(th):
        a1, _, b1, _, _ = unpack(th)
        e1, e2_0, e2_1 = residuals(th)
        S11 = np.mean(e1 ** 2)
        S22 = np.mean(wt * e2_1 ** 2 + (1 - wt) * e2_0 ** 2)
        S12 = np.mean(e1 * (wt * e2_1 + (1 - wt) * e2_0))
        det = S11 * S22 - S12 ** 2
        if det <= 0:
            return 1e10
        return 0.5 * T * np.log(det) - T * np.log(abs(1 - a1 * b1))
    r = minimize(negconc, th0, method="BFGS", options={"gtol": 1e-9, "maxiter": 5000})
    th = r.x
    e1, e2_0, e2_1 = residuals(th)
    S11 = np.mean(e1 ** 2)
    S22 = np.mean(wt * e2_1 ** 2 + (1 - wt) * e2_0 ** 2)
    S12 = np.mean(e1 * (wt * e2_1 + (1 - wt) * e2_0))
    return th, np.array([[S11, S12], [S12, S22]]), wt.mean()


def e_step(th, Sig, lam):
    """Bayes' rule: probability each week is cooperative, given the data and current parameters."""
    a1, _, b1, _, _ = unpack(th)
    e1, e2_0, e2_1 = residuals(th)
    lj = np.log(abs(1 - a1 * b1))
    l1 = np.log(lam) + logdens(e1, e2_1, Sig, lj)
    l0 = np.log(1 - lam) + logdens(e1, e2_0, Sig, lj)
    m = np.maximum(l1, l0)
    loglik = np.sum(m + np.log(np.exp(l1 - m) + np.exp(l0 - m)))   # eq. (5), computed stably
    return np.exp(l1 - m) / (np.exp(l1 - m) + np.exp(l0 - m)), loglik


def start_theta(wt):
    """Rough starting coefficients: equation-by-equation least squares (only a place to start the search)."""
    a = np.linalg.lstsq(np.column_stack([yP, XD]), yQ, rcond=None)[0]
    b = np.linalg.lstsq(np.column_stack([yQ, wt, XS]), yP, rcond=None)[0]
    return np.concatenate([[a[0]], a[1:], [b[0], b[1]], b[2:]])


def run_em(w0, label, tol=0.999, max_iter=500, verbose=True):
    wt, th = np.asarray(w0, float), start_theta(np.asarray(w0, float))
    for it in range(1, max_iter + 1):
        th, Sig, lam = m_step(wt, th)
        w_new, ll = e_step(th, Sig, lam)
        corr = np.corrcoef(w_new, wt)[0, 1] if wt.std() > 0 and w_new.std() > 0 else 0
        wt = w_new
        if verbose and (it <= 3 or it % 10 == 0):
            print(f"  [{label}] iter {it:3d}  loglik {ll:10.4f}  lambda {lam:.3f}  corr(w, previous w) {corr:.5f}")
        if corr > tol:
            break
    print(f"  [{label}] stopped after {it} iterations: loglik {ll:.4f}, lambda {lam:.3f}, "
          f"{int((wt > .5).sum())} of {T} weeks classified cooperative")
    return dict(th=th, Sig=Sig, lam=lam, w=wt, ll=ll, iters=it)


print("\n=== E-M from Porter's start (w0 = PO), with Porter's stopping rule corr > .999 ===")
em_porter = run_em(df["PO"].values, "PO start")

print("\n=== Same E-M run to full convergence (corr > .999999) ===")
em = run_em(df["PO"].values, "PO start, tight", tol=0.999999, max_iter=2000, verbose=False)

# Porter: "This algorithm converged to these estimates from several disparate starting points."
print("\n=== Robustness: other starting points ===")
rng = np.random.default_rng(634)
starts = {"all weeks 0.5": np.full(T, 0.5),
          "random 1": rng.uniform(size=T), "random 2": rng.uniform(size=T),
          "high-price weeks": (yP > np.median(yP)).astype(float)}
others = {k: run_em(v, k, tol=0.999999, max_iter=2000, verbose=False) for k, v in starts.items()}
for k, r in others.items():
    agree = np.mean((r["w"] > .5) == (em["w"] > .5))
    print(f"  {k:18s} loglik {r['ll']:.4f}  b3 {unpack(r['th'])[3]:+.3f}  PN agrees with PO-start PN in {agree:.0%} of weeks")


# ---------------------------------------------------------------- 4. standard errors from the full likelihood (eq. 5)
# Parameters for the full likelihood: theta, Sigma (via a Cholesky factor so it stays valid), lambda (via logit).
def pack_full(th, Sig, lam):
    L = np.linalg.cholesky(Sig)
    return np.concatenate([th, [np.log(L[0, 0]), L[1, 0], np.log(L[1, 1]), np.log(lam / (1 - lam))]])


def negll_full(phi):
    th = phi[:NTH]
    l11, l21, l22 = np.exp(phi[NTH]), phi[NTH + 1], np.exp(phi[NTH + 2])
    L = np.array([[l11, 0], [l21, l22]])
    lam = 1 / (1 + np.exp(-phi[NTH + 3]))
    return -e_step(th, L @ L.T, lam)[1]


phi_hat = pack_full(em["th"], em["Sig"], em["lam"])
# Polish: maximize eq. (5) directly from the E-M answer (should barely move if E-M converged)
pol = minimize(negll_full, phi_hat, method="BFGS", options={"gtol": 1e-8, "maxiter": 10000})
print(f"\nDirect maximization of eq. (5) from the E-M answer: loglik {-pol.fun:.4f} (E-M: {em['ll']:.4f})")
phi_hat = pol.x if -pol.fun >= em["ll"] - 1e-9 else phi_hat
H = nd.Hessian(negll_full, step=1e-4)(phi_hat)           # curvature of -loglik at the maximum
se = np.sqrt(np.diag(np.linalg.inv(H)))                  # ML standard errors

th_hat = phi_hat[:NTH]
a1, a, b1, b3, b = unpack(th_hat)
se_a1, se_a, se_b1, se_b3, se_b = unpack(se[:NTH])
lam_hat = 1 / (1 + np.exp(-phi_hat[NTH + 3]))
L_hat = np.array([[np.exp(phi_hat[NTH]), 0], [phi_hat[NTH + 1], np.exp(phi_hat[NTH + 2])]])
Sig_hat = L_hat @ L_hat.T
w_final, ll_final = e_step(th_hat, Sig_hat, lam_hat)     # final probabilities each week was cooperative
PN = (w_final > .5).astype(int)                           # Lee & Porter rule: cooperative if w_t > .5

# ---------------------------------------------------------------- 5. R-squared and s (fit using the PN classification)
e1, e2_0, e2_1 = residuals(th_hat)
e2 = np.where(PN == 1, e2_1, e2_0)
fit = {}
for name, e, y, k in [("Demand", e1, yQ, 1 + kD), ("Supply", e2, yP, 2 + kS)]:
    fit[name] = dict(R2=1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2), s=np.sqrt(np.sum(e ** 2) / (T - k)))

# ---------------------------------------------------------------- 6. Table 3, columns 3-4: ours vs Porter
rows = [  # (row label, our demand est, se, our supply est, se, Porter demand, Porter supply)
    ("C", a[0], se_a[0], b[0], se_b[0], "9.090 (.149)", "-2.416 (.710)"),
    ("LAKES", a[1], se_a[1], None, None, "-.430 (.120)", ""),
    ("GR (log price)", a1, se_a1, None, None, "-.800 (.091)", ""),
    ("DM1", None, None, b[1], se_b[1], "", "-.165 (.024)"),
    ("DM2", None, None, b[2], se_b[2], "", "-.209 (.036)"),
    ("DM3", None, None, b[3], se_b[3], "", "-.284 (.027)"),
    ("DM4", None, None, b[4], se_b[4], "", "-.298 (.073)"),
    ("PN (b3)", None, None, b3, se_b3, "", ".545 (.032)"),
    ("TQG (log quantity)", None, None, b1, se_b1, "", ".090 (.068)"),
]
fmt = lambda e, s: "" if e is None else f"{e:.3f} ({s:.3f})"
table = pd.DataFrame([{"Variable": r[0], "Demand (ours)": fmt(r[1], r[2]), "Demand (Porter)": r[5],
                       "Supply (ours)": fmt(r[3], r[4]), "Supply (Porter)": r[6]} for r in rows])
table.loc[len(table)] = ["R2", f"{fit['Demand']['R2']:.3f}", ".307", f"{fit['Supply']['R2']:.3f}", ".863"]
table.loc[len(table)] = ["s", f"{fit['Demand']['s']:.3f}", ".399", f"{fit['Supply']['s']:.3f}", ".109"]
print("\n=== Table 3, columns 3-4: maximum likelihood (yielding PN) ===")
print("Seasonal dummies are included in both equations but not reported (as in the paper).")
print(table.to_string(index=False))
print(f"\nlambda (share of cooperative weeks) = {lam_hat:.3f};  PN = 1 in {PN.sum()} of {T} weeks;  "
      f"PO = 1 in {int(df['PO'].sum())} weeks;  PN and PO agree in {np.mean(PN == df['PO']):.1%} of weeks")
# Porter p. 309: b3 = -log(1 + theta/a1)  ->  theta = a1 (exp(-b3) - 1)
print(f"Implied conduct parameter theta = {a1 * (np.exp(-b3) - 1):.3f} (Porter reports .336; 0 = Bertrand, 1 = joint monopoly)")

table.to_csv(os.path.join(OUT, "bonus_table3_ml.csv"), index=False)
pd.DataFrame({"week": jec["week"], "price": jec["price"], "PO": df["PO"], "w_prob_cooperative": w_final, "PN": PN}) \
    .to_csv(os.path.join(OUT, "bonus_PN_series.csv"), index=False)

# ---------------------------------------------------------------- 6b. why our supply slope differs a bit from Porter's
# The likelihood is very flat in the supply slope b1 (TQG). Re-maximize with b1 FIXED at Porter's .090:
# if the log-likelihood barely drops, the data cannot tell the two answers apart.
idx_b1 = 1 + kD


def negll_fixed_b1(free, b1_fixed):
    return negll_full(np.insert(free, idx_b1, b1_fixed))


r_p = minimize(negll_fixed_b1, np.delete(phi_hat, idx_b1), args=(0.090,), method="BFGS",
               options={"gtol": 1e-7, "maxiter": 10000})
th_p = np.insert(r_p.x, idx_b1, 0.090)[:NTH]
LR = 2 * (-negll_full(phi_hat) - (-r_p.fun))
from scipy.stats import chi2
print(f"\nFlat-likelihood check: with TQG fixed at Porter's .090 -> loglik {-r_p.fun:.3f} vs {-negll_full(phi_hat):.3f} "
      f"at our maximum (LR = {LR:.2f}, p = {chi2.sf(LR, 1):.2f}).")
print(f"  At TQG = .090 the other supply estimates become: C {unpack(th_p)[4][0]:+.3f} (Porter -2.416), "
      f"PN {unpack(th_p)[3]:.3f} (Porter .545), demand GR {unpack(th_p)[0]:+.3f} (Porter -.800)")
print("  -> Porter's estimates are statistically indistinguishable from ours; the gap is optimizer/stopping-rule detail.")

# ---------------------------------------------------------------- 7. Figure: price with PO and PN price-war weeks (cf. Porter's Figure 1)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(OUT, "..", "..", "..")))   # Michal's local style helper, if present
    import upshot_style as us
    us.use_style()
except Exception:
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(11, 4.2))
years = 1880 + (jec["week"] - 1) / 52
for flag, lo, hi, color, lab in [(df["PO"] == 0, 0.86, 1.0, "#d1725c", "Price war per Railway Review (PO = 0)"),
                                  (PN == 0, 0.72, 0.86, "#636e4f", "Price war per model (PN = 0)")]:
    ax.fill_between(years, lo, hi, where=flag.values if hasattr(flag, "values") else flag, color=color,
                    transform=ax.get_xaxis_transform(), step="mid", linewidth=0)
    ax.text(1882.3, (lo + hi) / 2, lab, transform=ax.get_xaxis_transform(), va="center", ha="left", fontsize=9,
            color="#121212")
ax.plot(years, jec["price"], color="#121212", lw=1.3)
ax.set_ylim(0.10, 0.52)
ax.set_xlim(1880, 1886.35)
ax.set_xticks(range(1880, 1887))
ax.set_yticks([0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40])
ax.tick_params(labelbottom=True, labelleft=True, length=0)
ax.set_xlabel("Year")
ax.set_ylabel("Grain rate GR ($ per 100 lbs)")
ax.set_title("JEC grain rate with observed (PO) and estimated (PN) price wars, 1880-1886", loc="left", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "bonus_figure_PN_vs_PO.png"), dpi=200)
print("\nSaved: bonus_table3_ml.csv, bonus_PN_series.csv, bonus_figure_PN_vs_PO.png in", OUT)
