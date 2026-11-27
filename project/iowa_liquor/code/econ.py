"""
econ.py: small, fast estimation helpers used by the analysis scripts (numpy only; cluster-friendly).

  absorb(df, fe_cols, cols, dummy_cols)  exact fixed effects: within-demean by the first FE (e.g. item); other FEs
                                         (month, nest x calendar month) enter as explicit dummies demeaned the same way
                                         (Frisch-Waugh-Lovell gives identical coefficients; no iterative solver)
  tsls(...)                              OLS / 2SLS on demeaned data with cluster-robust (CR1) standard errors
                                         + first-stage partial F and partial R2 for each endogenous regressor
Why not linearmodels / pyhdfe: on ~260k rows with 11k items both were far too slow here (pyhdfe's alternating
projections never converged on nest-month variables). One-way demeaning + ~200 dense dummies is exact and takes seconds.
"""
import numpy as np
import pandas as pd


def absorb(df, fe_cols, cols, dummy_cols=(), drop_singletons=True):
    """
    Exact, iteration-free fixed effects:
      * the FIRST entry of fe_cols (high-dimensional, e.g. item) is removed by within-group demeaning (one pass);
      * every other fixed effect (fe_cols[1:], e.g. month) and every dummy_col (e.g. nest x calendar month) enters as
        explicit dummies that are demeaned within the first FE too (Frisch-Waugh-Lovell => identical coefficients).
    Returns (DataFrame of demeaned cols + dummy columns, kept-row mask, list of dummy names to pass as `controls`).
    """
    g = df[fe_cols[0]]
    keep = (g.map(g.value_counts()) > 1).to_numpy() if drop_singletons else np.ones(len(df), bool)
    sub = df[keep]
    mats, names = [sub[cols].to_numpy(float)], list(cols)
    for dc in list(fe_cols[1:]) + list(dummy_cols):
        D = pd.get_dummies(sub[dc], prefix=str(dc), drop_first=True, dtype=float)
        mats.append(D.to_numpy()); names += list(D.columns)
    A = np.column_stack(mats)
    codes = pd.factorize(sub[fe_cols[0]])[0]
    sums = np.zeros((codes.max() + 1, A.shape[1]))
    np.add.at(sums, codes, A)
    counts = np.bincount(codes)[:, None]
    A = A - (sums / counts)[codes]                              # within-item demeaning
    out = pd.DataFrame(A, columns=names)
    return out, keep, names[len(cols):]


def _coef(A, B):
    """Least-squares coefficients via normal equations (pinv): fast and stable for n ~ 1e5-1e6, k ~ 200."""
    return np.linalg.pinv(A.T @ A) @ (A.T @ B)


def _cluster_cov(X, u, groups, bread):
    """CR1 cluster-robust covariance: bread @ meat @ bread."""
    g = pd.factorize(groups)[0]
    G = g.max() + 1
    scores = np.zeros((G, X.shape[1]))
    np.add.at(scores, g, X * u[:, None])
    n, k = X.shape
    adj = G / (G - 1) * (n - 1) / (n - k)
    return adj * bread @ (scores.T @ scores) @ bread


def cluster_F(dm, endog_var, instruments, controls=(), clusters=None, weights=None):
    """Cluster-robust first-stage F: Wald test that the excluded instruments are jointly zero, divided by their number."""
    r = tsls(dm, endog_var, exog=list(instruments), controls=list(controls), clusters=clusters, weights=weights)
    b = r["table"]["coef"].to_numpy()
    V = r["V_reported"]
    return float(b @ np.linalg.pinv(V) @ b) / len(b)


def tsls(dm, y, exog=(), endog=(), instruments=(), clusters=None, controls=(), weights=None):
    """
    2SLS (or OLS if no endog) on demeaned data dm. `controls` are extra exogenous regressors (e.g. residualized dummies)
    that are included in both stages but not reported. `weights` (optional, constant within the demeaning group, e.g.
    an item's pre-period dollars) gives weighted least squares. Returns dict: 'table' (coef, se, t for exog+endog),
    'first_stage' (partial F and partial R2 of the excluded instruments, per endogenous variable; homoskedastic F --
    use cluster_F for a cluster-robust version), 'n'.
    """
    exog, endog, instruments, controls = list(exog), list(endog), list(instruments), list(controls)
    xnames = exog + endog + controls
    sw = np.sqrt(np.asarray(weights, float)) if weights is not None else np.ones(len(dm))
    Y = dm[y].to_numpy() * sw
    X = dm[xnames].to_numpy() * sw[:, None]
    W = dm[exog + controls].to_numpy() * sw[:, None]            # included exogenous regressors
    if endog:
        Zf = np.column_stack([W, dm[instruments].to_numpy() * sw[:, None]])
        PzX = Zf @ _coef(Zf, X)        # first-stage fitted values
    else:
        PzX = X
    bread = np.linalg.pinv(PzX.T @ PzX)
    b = bread @ (PzX.T @ Y)
    u = Y - X @ b                                               # structural residuals use actual X
    if clusters is not None:
        V = _cluster_cov(PzX, u, clusters, bread)
    else:
        V = bread * (u @ u) / (len(Y) - X.shape[1])
    se = np.sqrt(np.diag(V))
    report = exog + endog
    idx = [xnames.index(c) for c in report]
    table = pd.DataFrame({"coef": b[idx], "se": se[idx], "t": b[idx] / se[idx]}, index=report)
    fs = {}
    for e in endog:
        x = dm[e].to_numpy() * sw
        r_r = x - (W @ _coef(W, x) if W.shape[1] else 0)
        r_u = x - Zf @ _coef(Zf, x)
        q, n, k = len(instruments), len(x), Zf.shape[1]
        F = ((r_r @ r_r - r_u @ r_u) / q) / ((r_u @ r_u) / (n - k))
        fs[e] = {"partial_F": F, "partial_R2": 1 - (r_u @ r_u) / (r_r @ r_r)}
    return {"table": table, "first_stage": pd.DataFrame(fs).T, "n": len(Y), "coef_all": pd.Series(b, index=xnames),
            "V_reported": V[np.ix_(idx, idx)]}
