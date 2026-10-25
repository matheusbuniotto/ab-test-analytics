"""Helper functions for analysing a two-variant (control vs. treatment) A/B test
with a binary conversion metric, plus wrappers for `tea-tasting` comparison and
`cluster-experiments` (cluster randomization & synthetic control).

Every analysis function prints a short, readable report AND returns a dict/DataFrame
with the raw numbers, so results can be reused programmatically.
"""
from __future__ import annotations

from itertools import product

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from scipy.stats import beta

CONTROL = "control"
TREATMENT = "treatment"

_WIDTH = 64


# --------------------------------------------------------------------------- #
# Printing helpers
# --------------------------------------------------------------------------- #
def _header(title: str) -> None:
    print("=" * _WIDTH)
    print(f" {title}")
    print("=" * _WIDTH)


def _row(label: str, value) -> None:
    print(f"  {label:<28}{value}")


def _verdict(ok: bool, text: str, labels=("PASS", "FAIL")) -> None:
    print("-" * _WIDTH)
    print(f"  [{labels[0] if ok else labels[1]}] {text}")
    print("=" * _WIDTH)


def _split(data: pd.DataFrame, group_column: str, converted_column: str):
    """Return (control, treatment) arrays of 0/1 conversions."""
    c = data.loc[data[group_column] == CONTROL, converted_column].to_numpy()
    t = data.loc[data[group_column] == TREATMENT, converted_column].to_numpy()
    if len(c) == 0 or len(t) == 0:
        raise ValueError(f"Data must contain both '{CONTROL}' and '{TREATMENT}' groups.")
    return c, t


# --------------------------------------------------------------------------- #
# Data quality
# --------------------------------------------------------------------------- #
def check_group_page_consistency(data: pd.DataFrame) -> pd.DataFrame:
    """Cross-tab of group vs. landing page.

    In a clean test, control users only see ``old_page`` and treatment users only
    see ``new_page``. Off-diagonal cells are assignment errors.
    """
    table = pd.crosstab(data["group"], data["landing_page"])
    mismatched = int(table.values.sum() - table.loc[CONTROL, "old_page"] - table.loc[TREATMENT, "new_page"])
    _header("GROUP / LANDING PAGE CONSISTENCY")
    print(table.to_string())
    _verdict(mismatched == 0, f"{mismatched:,} rows where group and landing page disagree")
    return table


# --------------------------------------------------------------------------- #
# Sample Ratio Mismatch
# --------------------------------------------------------------------------- #
def srm_test(control_count: int, treatment_count: int, threshold_p: float = 0.001,
             expected_ratio: float = 0.5) -> dict:
    """Sample Ratio Mismatch (SRM) check via a chi-square goodness-of-fit test.

    Args:
        control_count: Number of users in control.
        treatment_count: Number of users in treatment.
        threshold_p: p-value below which the split is considered broken. The
            industry convention is a strict 0.001 (Kohavi et al.).
        expected_ratio: Expected share of traffic in control (0.5 = 50/50).

    Returns:
        dict with ``chi2``, ``p_value`` and ``valid``.
    """
    observed = np.array([control_count, treatment_count])
    total = observed.sum()
    expected = np.array([total * expected_ratio, total * (1 - expected_ratio)])
    chi2, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
    valid = bool(p_value > threshold_p)

    _header("SAMPLE RATIO MISMATCH (SRM) CHECK")
    _row("Control users:", f"{control_count:,}")
    _row("Treatment users:", f"{treatment_count:,}")
    _row("Difference (C - T):", f"{control_count - treatment_count:+,}")
    _row("Control / Treatment ratio:", f"{control_count / treatment_count:.4f}")
    _row("Chi-square:", f"{chi2:.4f}")
    _row("P-value:", f"{p_value:.4f}  (threshold {threshold_p})")
    _verdict(valid, "Traffic split looks healthy - results can be trusted." if valid
             else "SRM detected - do NOT trust the results until the cause is found.")
    return {"chi2": chi2, "p_value": p_value, "valid": valid}


# --------------------------------------------------------------------------- #
# Confidence intervals
# --------------------------------------------------------------------------- #
def calculate_ci(data: pd.DataFrame, group_column: str, converted_column: str,
                 confidence: float = 0.95) -> pd.DataFrame:
    """Wilson score confidence interval for the conversion rate of each group.

    The Wilson interval is the recommended choice for proportions: unlike the
    normal/t interval it never leaves [0, 1] and has good coverage for small
    samples or rates close to 0 or 1.

    Returns:
        DataFrame with users, conversions, rate, CI bounds and the CI half-width
        relative to the rate.
    """
    z = stats.norm.ppf((1 + confidence) / 2)
    rows = []
    for name, grp in data.groupby(group_column)[converted_column]:
        n, k = len(grp), int(grp.sum())
        p = k / n
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
        rows.append({
            "group": name,
            "users": n,
            "conversions": k,
            "conversion_rate": round(p, 4),
            "ci_lower": round(centre - half, 4),
            "ci_upper": round(centre + half, 4),
            "ci_half_width_rel": f"±{half / p * 100:.2f}%" if p > 0 else "n/a",
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Frequentist test: two-proportion z-test
# --------------------------------------------------------------------------- #
def perform_ab_test_analysis(data: pd.DataFrame, group_column: str = "group",
                             converted_column: str = "converted", alpha: float = 0.05,
                             plot: bool = True) -> dict:
    """Two-sided two-proportion z-test (pooled variance) plus a CI for the lift.

    Args:
        data: DataFrame with one row per user.
        group_column: Column holding 'control' / 'treatment'.
        converted_column: Binary (0/1) conversion column.
        alpha: Significance level.
        plot: Draw a bar chart with CI error bars.

    Returns:
        dict with rates, absolute/relative lift, z, p-value, CI of the difference
        and ``significant``.
    """
    c, t = _split(data, group_column, converted_column)
    n_c, n_t = len(c), len(t)
    p_c, p_t = c.mean(), t.mean()

    pooled = (c.sum() + t.sum()) / (n_c + n_t)
    se_pooled = np.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se_pooled
    p_value = 2 * stats.norm.sf(abs(z))

    # CI for the difference uses the unpooled standard error
    se_diff = np.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    diff = p_t - p_c
    ci = (diff - z_crit * se_diff, diff + z_crit * se_diff)
    significant = bool(p_value < alpha)

    _header("FREQUENTIST TEST: TWO-PROPORTION Z-TEST")
    _row("Control rate:", f"{p_c:.4%}  (n={n_c:,})")
    _row("Treatment rate:", f"{p_t:.4%}  (n={n_t:,})")
    _row("Absolute lift:", f"{diff:+.4%}")
    _row("Relative lift:", f"{diff / p_c:+.2%}")
    _row(f"{(1 - alpha):.0%} CI of difference:", f"[{ci[0]:+.4%}, {ci[1]:+.4%}]")
    _row("z-statistic:", f"{z:.4f}")
    _row("P-value (two-sided):", f"{p_value:.4f}  (alpha {alpha})")
    _verdict(significant, "Statistically significant difference." if significant
             else "No statistically significant difference between the groups.",
             labels=("SIGNIFICANT", "NOT SIGNIFICANT"))

    if plot:
        ci_df = calculate_ci(data, group_column, converted_column, 1 - alpha)
        ci_df = ci_df.set_index("group").loc[[CONTROL, TREATMENT]]
        rates = ci_df["conversion_rate"].to_numpy()
        err = np.vstack([rates - ci_df["ci_lower"].to_numpy(), ci_df["ci_upper"].to_numpy() - rates])
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["Control", "Treatment"], rates, yerr=err, capsize=10, color=["#4C72B0", "#DD8452"])
        ax.set_ylabel("Conversion rate")
        ax.set_title(f"Conversion rate with {(1 - alpha):.0%} confidence intervals")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))
        plt.tight_layout()
        plt.show()

    return {"control_rate": p_c, "treatment_rate": p_t, "abs_lift": diff, "rel_lift": diff / p_c,
            "z": z, "p_value": p_value, "ci_diff": ci, "significant": significant}


# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #
def bootstrap_ab_test(data: pd.DataFrame, group_column: str = "group",
                      converted_column: str = "converted", n_bootstraps: int = 10_000,
                      confidence: float = 0.95, seed: int | None = 42, plot: bool = True) -> dict:
    """Bootstrap A/B test on the difference in conversion rates.

    Each group is resampled independently (keeping group sizes fixed). Because a
    binary metric only needs the number of conversions, each resample is drawn
    from a binomial with the observed rate, which is equivalent to resampling the
    rows but orders of magnitude faster.

    * The percentile CI of (treatment - control) comes from the bootstrap
      distribution.
    * The two-sided p-value is the share of the bootstrap distribution, shifted to
      be centred on zero (the null hypothesis), that is at least as extreme as the
      observed difference.
    """
    c, t = _split(data, group_column, converted_column)
    n_c, n_t = len(c), len(t)
    p_c, p_t = c.mean(), t.mean()
    rng = np.random.default_rng(seed)

    boot_c = rng.binomial(n_c, p_c, n_bootstraps) / n_c
    boot_t = rng.binomial(n_t, p_t, n_bootstraps) / n_t
    boot_diff = boot_t - boot_c
    observed = p_t - p_c

    alpha = 1 - confidence
    ci = np.percentile(boot_diff, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    centred = boot_diff - boot_diff.mean()
    p_value = float(np.mean(np.abs(centred) >= abs(observed)))
    significant = bool(p_value < alpha)

    if plot:
        fig, ax = plt.subplots(figsize=(7, 4))
        sns.histplot(boot_diff, bins=60, stat="density", color="#4C72B0", alpha=0.6, ax=ax)
        ax.axvline(0, color="black", ls="--", label="No effect (0)")
        ax.axvline(observed, color="#C44E52", label=f"Observed ({observed:+.4f})")
        ax.axvspan(ci[0], ci[1], color="#DD8452", alpha=0.2, label=f"{confidence:.0%} CI")
        ax.set_title(f"Bootstrap distribution of the lift ({n_bootstraps:,} resamples)")
        ax.set_xlabel("Treatment rate - Control rate")
        ax.legend()
        plt.tight_layout()
        plt.show()

    _header("BOOTSTRAP TEST")
    _row("Resamples:", f"{n_bootstraps:,}  (seed={seed})")
    _row("Observed difference:", f"{observed:+.4%}")
    _row(f"{confidence:.0%} bootstrap CI:", f"[{ci[0]:+.4%}, {ci[1]:+.4%}]")
    _row("P-value (two-sided):", f"{p_value:.4f}  (alpha {alpha:.2f})")
    _verdict(significant, "Statistically significant difference." if significant
             else "No statistically significant difference (the CI contains 0).",
             labels=("SIGNIFICANT", "NOT SIGNIFICANT"))
    return {"observed_diff": observed, "ci": tuple(ci), "p_value": p_value,
            "significant": significant, "boot_diff": boot_diff}


# --------------------------------------------------------------------------- #
# Bayesian
# --------------------------------------------------------------------------- #
def posterior(data: pd.DataFrame, group: str, group_column: str = "group",
              converted_column: str = "converted", prior=(1, 1)):
    """Beta posterior for a group's conversion rate (default prior: uniform Beta(1, 1))."""
    conv = data.loc[data[group_column] == group, converted_column]
    k, n = int(conv.sum()), len(conv)
    return beta(prior[0] + k, prior[1] + n - k)


def calc_prob_between(beta_a, beta_b, n_samples: int = 1_000_000, seed: int | None = 42) -> float:
    """Monte Carlo estimate of P(rate_A > rate_B) for two Beta posteriors."""
    rng = np.random.default_rng(seed)
    a = beta_a.rvs(n_samples, random_state=rng)
    b = beta_b.rvs(n_samples, random_state=rng)
    return float(np.mean(a > b))


def calc_beta_peak(a: float, b: float) -> float:
    """Mode of a Beta(a, b) distribution (valid for a, b > 1)."""
    return (a - 1) / (a + b - 2)


def bayesian_ab_test(data: pd.DataFrame, group_column: str = "group",
                     converted_column: str = "converted", n_samples: int = 1_000_000,
                     seed: int | None = 42, credible: float = 0.95) -> dict:
    """Bayesian A/B test with Beta-Binomial posteriors.

    Reports P(treatment > control), expected relative lift, and a credible
    interval for the absolute difference.
    """
    b_c = posterior(data, CONTROL, group_column, converted_column)
    b_t = posterior(data, TREATMENT, group_column, converted_column)
    rng = np.random.default_rng(seed)
    s_c = b_c.rvs(n_samples, random_state=rng)
    s_t = b_t.rvs(n_samples, random_state=rng)
    diff = s_t - s_c
    prob_t_better = float(np.mean(diff > 0))
    exp_lift = float(np.mean(diff / s_c))
    lo, hi = np.percentile(diff, [(1 - credible) / 2 * 100, (1 + credible) / 2 * 100])

    _header("BAYESIAN TEST (Beta-Binomial, uniform prior)")
    _row("P(treatment > control):", f"{prob_t_better:.1%}")
    _row("P(control > treatment):", f"{1 - prob_t_better:.1%}")
    _row("Expected relative lift:", f"{exp_lift:+.2%}")
    _row(f"{credible:.0%} credible interval:", f"[{lo:+.4%}, {hi:+.4%}]  (absolute)")
    print("-" * _WIDTH)
    print("  Rule of thumb: act on a result when P(better) is >= 95% (or <= 5%).")
    print("=" * _WIDTH)
    return {"beta_control": b_c, "beta_treatment": b_t, "prob_treatment_better": prob_t_better,
            "expected_rel_lift": exp_lift, "credible_interval": (lo, hi)}


def bayesian_plot(betas, names, linf: float = 0, lsup: float = 1, data=None,
                  group_column=None, converted_column=None) -> None:
    """Plot the Beta posterior densities of each group.

    ``data``, ``group_column`` and ``converted_column`` are accepted only for
    backward compatibility and are ignored.
    """
    x = np.linspace(linf, lsup, 1000)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for dist, name in zip(betas, names):
        mean, std = dist.mean(), dist.std()
        ax.plot(x, dist.pdf(x), label=f"{name}: {mean:.4f} ± {std:.4f} (1 sd)")
        ax.fill_between(x, dist.pdf(x), alpha=0.2)
    ax.set_xlabel("Conversion rate")
    ax.set_ylabel("Posterior density")
    ax.set_title("Posterior distributions of the conversion rate")
    ax.legend(loc="upper right", frameon=False)
    plt.tight_layout()
    plt.show()


# --------------------------------------------------------------------------- #
# Comparison with tea-tasting (https://github.com/e10v/tea-tasting)
# --------------------------------------------------------------------------- #
def compare_with_tea_tasting(data: pd.DataFrame, group_column: str = "group",
                             converted_column: str = "converted") -> dict:
    """Run the same SRM, two-proportion z-test, and t-test using `tea-tasting`,
    plus solve for the Minimum Detectable Effect (MDE) at 80% power.
    """
    import tea_tasting as tt

    exp = tt.Experiment(
        srm=tt.SampleRatio(),
        conversion_z=tt.Proportion(converted_column, method="norm", correction=False),
        conversion_ttest=tt.Mean(converted_column),
        variant=group_column,
    )
    res = exp.analyze(data, control=CONTROL)
    power_exp = tt.Experiment(conversion=tt.Mean(converted_column), variant=group_column)
    mde = power_exp.solve_power(data, "rel_effect_size")

    _header("TEA-TASTING CROSS-CHECK & POWER (MDE)")
    print(res)
    print("-" * _WIDTH)
    print("  Minimum Detectable Effect at 80% power, alpha=0.05:")
    print(mde)
    print("=" * _WIDTH)
    return {"analysis": res.to_pandas(), "mde": mde.to_pandas()}


# --------------------------------------------------------------------------- #
# Cluster Randomization & Synthetic Control (cluster-experiments)
# --------------------------------------------------------------------------- #
def run_cluster_randomization_example(n_stores: int = 50, transactions_per_store: int = 100,
                                      true_effect: float = 5.0, store_sd: float = 10.0,
                                      seed: int = 42, plot: bool = True) -> pd.DataFrame:
    """Simulate a store-level cluster-randomized experiment and compare Naive OLS
    (ignoring clusters) vs. Clustered OLS (cluster-robust standard errors).

    Adapted from:
    https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html
    """
    from cluster_experiments import AnalysisPlan, SimpleMetric, Variant

    rng = np.random.default_rng(seed)
    stores = pd.DataFrame({
        "store_id": range(n_stores),
        "variant": rng.choice([CONTROL, TREATMENT], n_stores),
    })

    tx_list = []
    for _, store in stores.iterrows():
        n_tx = rng.poisson(transactions_per_store)
        eff = true_effect if store["variant"] == TREATMENT else 0.0
        store_eff = rng.normal(0.0, store_sd)
        amounts = rng.normal(50.0 + eff + store_eff, 20.0, n_tx).clip(min=0.0)
        tx_list.append(pd.DataFrame({
            "store_id": store["store_id"],
            "variant": store["variant"],
            "purchase_amount": amounts,
        }))
    tx_df = pd.concat(tx_list, ignore_index=True)

    metrics = [SimpleMetric(alias="purchase_amount", name="purchase_amount")]
    variants = [Variant(name=CONTROL, is_control=True), Variant(name=TREATMENT, is_control=False)]

    naive_res = AnalysisPlan.from_metrics(
        metrics=metrics, variants=variants, variant_col="variant", analysis_type="ols"
    ).analyze(tx_df).to_dataframe().iloc[0]

    clust_res = AnalysisPlan.from_metrics(
        metrics=metrics, variants=variants, variant_col="variant",
        analysis_type="clustered_ols", analysis_config={"cluster_cols": ["store_id"]}
    ).analyze(tx_df).to_dataframe().iloc[0]

    comp = pd.DataFrame([
        {
            "Method": "Naive OLS (ignores clusters)",
            "ATE ($)": round(naive_res["ate"], 2),
            "Std. Error ($)": round(naive_res["std_error"], 2),
            "p-value": round(naive_res["p_value"], 4),
            "95% CI": f"[${naive_res['ate_ci_lower']:.2f}, ${naive_res['ate_ci_upper']:.2f}]",
        },
        {
            "Method": "Clustered OLS (store-level SE)",
            "ATE ($)": round(clust_res["ate"], 2),
            "Std. Error ($)": round(clust_res["std_error"], 2),
            "p-value": round(clust_res["p_value"], 4),
            "95% CI": f"[${clust_res['ate_ci_lower']:.2f}, ${clust_res['ate_ci_upper']:.2f}]",
        },
    ])

    _header(f"CLUSTER RANDOMIZATION ({n_stores} stores, ~{len(tx_df):,} transactions)")
    print(comp.to_string(index=False))
    print("-" * _WIDTH)
    se_ratio = clust_res["std_error"] / naive_res["std_error"]
    print(f"  Clustered SE is {se_ratio:.1f}x larger than Naive SE due to intra-store correlation.")
    print("=" * _WIDTH)

    if plot:
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        store_means = tx_df.groupby(["store_id", "variant"])["purchase_amount"].mean().reset_index()
        sns.stripplot(data=store_means, x="variant", y="purchase_amount", hue="variant",
                      palette=["#4C72B0", "#DD8452"], size=7, jitter=0.18, alpha=0.85,
                      legend=False, ax=axes[0])
        axes[0].set_title("Store-level mean purchase amount (each dot = 1 store)")
        axes[0].set_xlabel("Variant")
        axes[0].set_ylabel("Mean purchase amount ($)")

        methods = ["Naive OLS\n(wrong)", "Clustered OLS\n(correct)"]
        ates = [naive_res["ate"], clust_res["ate"]]
        ci_half = [naive_res["ate_ci_upper"] - naive_res["ate"],
                   clust_res["ate_ci_upper"] - clust_res["ate"]]
        axes[1].errorbar(ates, methods, xerr=ci_half, fmt="o", color="#C44E52",
                         ecolor="#4C72B0", elinewidth=2.5, capsize=6, markersize=7)
        axes[1].axvline(0, color="black", ls="--", lw=1, label="Zero effect")
        axes[1].axvline(true_effect, color="#55A868", ls=":", lw=1.5, label=f"True effect (+${true_effect:.0f})")
        axes[1].set_title("95% CI: Naive OLS vs. Clustered OLS")
        axes[1].set_xlabel("Estimated treatment effect ($)")
        axes[1].legend(loc="lower right")
        plt.tight_layout()
        plt.show()

    return comp


def run_synthetic_control_example(n_clusters: int = 15, effects=(0, 5, 10, 15, 20),
                                  n_simulations: int = 30, seed: int = 42,
                                  plot: bool = True) -> pd.DataFrame:
    """Run a single-treated-cluster experiment and compare Synthetic Control vs.
    Clustered OLS power curves (including false-positive rate at effect = 0).

    Adapted from:
    https://david26694.github.io/cluster-experiments/synthetic_control.html
    """
    from cluster_experiments.experiment_analysis import ClusteredOLSAnalysis, SyntheticControlAnalysis
    from cluster_experiments.perturbator import ConstantPerturbator
    from cluster_experiments.power_analysis import PowerAnalysis, PowerAnalysisWithPreExperimentData
    from cluster_experiments.random_splitter import FixedSizeClusteredSplitter

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-01", "2022-01-30", freq="D")
    clusters = [f"Cluster {i}" for i in range(n_clusters)]
    df_sc = pd.DataFrame(list(product(clusters, dates)), columns=["cluster", "date"])
    df_sc["target"] = rng.normal(100.0, 10.0, size=len(df_sc))
    intervention_date = "2022-01-15"

    splitter = FixedSizeClusteredSplitter(n_treatment_clusters=1, cluster_cols=["cluster"])
    perturbator = ConstantPerturbator(average_effect=10)
    sc_analysis = SyntheticControlAnalysis(
        cluster_cols=["cluster"], time_col="date", intervention_date=intervention_date
    )
    pw_sc = PowerAnalysisWithPreExperimentData(
        splitter=splitter, analysis=sc_analysis, n_simulations=n_simulations,
        perturbator=perturbator, seed=seed
    )
    point_estimates = list(pw_sc.simulate_point_estimate(df_sc))
    p_synth = pw_sc.power_line(df_sc, average_effects=list(effects), n_jobs=1, verbose=False)

    ols_analysis = ClusteredOLSAnalysis(cluster_cols=["cluster"])
    pw_ols = PowerAnalysis(
        perturbator=perturbator, splitter=splitter, analysis=ols_analysis,
        n_simulations=max(n_simulations, 80), seed=seed
    )
    p_ols = pw_ols.power_line(
        df_sc.query(f"date > '{intervention_date}'"),
        average_effects=list(effects), n_jobs=1, verbose=False
    )

    power_df = pd.DataFrame({
        "Effect size": list(effects),
        "Synthetic Control power": [float(p_synth[e]) for e in effects],
        "Clustered OLS power": [float(p_ols[e]) for e in effects],
    })

    _header("SYNTHETIC CONTROL vs. CLUSTERED OLS (1 treated cluster)")
    _row("Point estimate mean (true=+10):", f"{np.mean(point_estimates):.2f}  (sd={np.std(point_estimates):.2f})")
    print("-" * _WIDTH)
    print(power_df.to_string(index=False))
    print("-" * _WIDTH)
    print(f"  At effect=0 (false-positive rate): Synthetic Control = {power_df.iloc[0, 1]:.0%}, "
          f"Clustered OLS = {power_df.iloc[0, 2]:.0%} (breaks with 1 treated cluster!).")
    print("=" * _WIDTH)

    if plot:
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
        sns.histplot(point_estimates, bins=14, color="#4C72B0", alpha=0.65, ax=axes[0])
        axes[0].axvline(10.0, color="#C44E52", ls="--", lw=2, label="True effect (+10)")
        axes[0].axvline(np.mean(point_estimates), color="#55A868", lw=2,
                        label=f"Mean estimate ({np.mean(point_estimates):.2f})")
        axes[0].set_title("Synthetic Control point estimates (true = +10)")
        axes[0].set_xlabel("Estimated effect")
        axes[0].legend()

        axes[1].plot(power_df["Effect size"], power_df["Synthetic Control power"],
                     marker="o", lw=2.2, color="#4C72B0", label="Synthetic Control")
        axes[1].plot(power_df["Effect size"], power_df["Clustered OLS power"],
                     marker="s", lw=2.2, ls="--", color="#C44E52", label="Clustered OLS (1 treated cluster)")
        axes[1].axhline(0.05, color="black", ls=":", lw=1, label="Nominal alpha (5%)")
        axes[1].yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        axes[1].set_title("Power curve & false-positive rate at effect = 0")
        axes[1].set_xlabel("True effect size")
        axes[1].set_ylabel("Rejection rate (Power)")
        axes[1].legend(loc="lower right")
        plt.tight_layout()
        plt.show()

    return power_df
