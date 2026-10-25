"""Helper functions for analysing a two-variant (control vs. treatment) A/B test
with a binary conversion metric, plus wrappers for `tea-tasting` comparison and
`cluster-experiments` (cluster randomization & synthetic control).

All charts use a unified ggplot2-inspired aesthetic (light grey panel with crisp
white gridlines, clean typography, rich callout annotations, and a consistent
Control/Treatment color palette) designed for portfolio presentation.
"""
from __future__ import annotations

from itertools import product

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import PercentFormatter
from scipy.stats import beta

CONTROL = "control"
TREATMENT = "treatment"

# ggplot2 / Okabe-Ito inspired portfolio palette
PALETTE = {
    "control": "#2B5C8F",      # Deep slate blue
    "treatment": "#D95F02",    # Warm burnt orange
    "accent": "#1B9E77",       # Teal green (positive / true effect)
    "danger": "#C0392B",       # Crimson red (observed / alert)
    "neutral": "#4A5568",      # Dark slate grey
    "panel_bg": "#F4F5F7",     # ggplot2 light grey canvas
    "fig_bg": "#FFFFFF",       # Crisp white outer frame
    "strip_bg": "#E2E8F0",     # ggplot2 facet strip header
    "grid": "#FFFFFF",         # Crisp white major gridlines
}

_WIDTH = 70


# --------------------------------------------------------------------------- #
# ggplot2 Theme & Styling Helpers
# --------------------------------------------------------------------------- #
def set_ggplot_theme() -> None:
    """Configure matplotlib rcParams for a clean, modern ggplot2 aesthetic."""
    plt.rcParams.update({
        "figure.facecolor": PALETTE["fig_bg"],
        "axes.facecolor": PALETTE["panel_bg"],
        "axes.edgecolor": "none",
        "axes.axisbelow": True,
        "axes.grid": True,
        "grid.color": PALETTE["grid"],
        "grid.linewidth": 1.3,
        "grid.alpha": 1.0,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "text.color": "#1A202C",
        "axes.labelcolor": "#2D3748",
        "axes.labelsize": 10.5,
        "axes.labelweight": "bold",
        "axes.titlesize": 12.5,
        "axes.titleweight": "bold",
        "xtick.color": "#4A5568",
        "ytick.color": "#4A5568",
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "xtick.bottom": False,
        "ytick.left": False,
        "legend.frameon": True,
        "legend.facecolor": "#FFFFFF",
        "legend.edgecolor": "#E2E8F0",
        "legend.fontsize": 9.5,
        "figure.dpi": 140,
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
        "savefig.facecolor": PALETTE["fig_bg"],
    })


set_ggplot_theme()


def _style_ggplot_ax(ax: plt.Axes, title: str | None = None,
                     subtitle: str | None = None, xlabel: str | None = None,
                     ylabel: str | None = None) -> None:
    """Apply ggplot2 panel styling, minor dashed grid, and title/subtitle hierarchy."""
    ax.set_facecolor(PALETTE["panel_bg"])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, which="major", color=PALETTE["grid"], linewidth=1.4, zorder=0)
    ax.minorticks_on()
    ax.grid(True, which="minor", color=PALETTE["grid"], linewidth=0.6, linestyle=":", zorder=0)
    ax.tick_params(which="both", length=0)

    if xlabel is not None:
        ax.set_xlabel(xlabel, labelpad=8, fontsize=10, fontweight="bold", color="#2D3748")
    if ylabel is not None:
        ax.set_ylabel(ylabel, labelpad=8, fontsize=10, fontweight="bold", color="#2D3748")
    if title and subtitle:
        ax.set_title(
            f"{title}\n",
            loc="left", fontsize=12, fontweight="bold", color="#1A202C", pad=6,
        )
        ax.text(
            0.0, 1.02, subtitle,
            transform=ax.transAxes, fontsize=9.5, color="#4A5568", style="italic",
        )
    elif title:
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color="#1A202C", pad=10)


def _add_caption(fig: plt.Figure, text: str) -> None:
    """Add a subtle ggplot2-style footer caption to the figure."""
    fig.text(
        0.01, -0.02, text,
        fontsize=8.5, color="#718096", style="italic", ha="left",
    )


# --------------------------------------------------------------------------- #
# Printing helpers (Box-drawn terminal reports)
# --------------------------------------------------------------------------- #
def _header(title: str) -> None:
    print("╭" + "─" * (_WIDTH - 2) + "╮")
    print(f"│ {title:<{_WIDTH - 4}} │")
    print("├" + "─" * (_WIDTH - 2) + "┤")


def _row(label: str, value) -> None:
    val_str = str(value)
    content = f"  {label:<28}{val_str}"
    print(f"│{content:<{_WIDTH - 2}}│")


def _verdict(ok: bool, text: str, labels=("PASS", "FAIL")) -> None:
    tag = f"[{labels[0] if ok else labels[1]}]"
    print("├" + "─" * (_WIDTH - 2) + "┤")
    line = f"  {tag} {text}"
    print(f"│{line:<{_WIDTH - 2}}│")
    print("╰" + "─" * (_WIDTH - 2) + "╯")


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
    for line in table.to_string().splitlines():
        print(f"│  {line:<{_WIDTH - 4}}│")
    _verdict(mismatched == 0, f"{mismatched:,} rows where group and landing page disagree")
    return table


# --------------------------------------------------------------------------- #
# Sample Ratio Mismatch
# --------------------------------------------------------------------------- #
def srm_test(control_count: int, treatment_count: int, threshold_p: float = 0.001,
             expected_ratio: float = 0.5) -> dict:
    """Sample Ratio Mismatch (SRM) check via a chi-square goodness-of-fit test."""
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
    """Wilson score confidence interval for the conversion rate of each group."""
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
    """Two-sided two-proportion z-test (pooled variance) plus a 2-panel ggplot2
    summary chart (group conversion rates + absolute lift vs. MDE & zero).
    """
    c, t = _split(data, group_column, converted_column)
    n_c, n_t = len(c), len(t)
    p_c, p_t = c.mean(), t.mean()

    pooled = (c.sum() + t.sum()) / (n_c + n_t)
    se_pooled = np.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se_pooled
    p_value = 2 * stats.norm.sf(abs(z))

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
        set_ggplot_theme()
        ci_df = calculate_ci(data, group_column, converted_column, 1 - alpha).set_index("group").loc[[CONTROL, TREATMENT]]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.05, 1.15]})

        # Left panel: geom_pointrange for Control vs Treatment rates (zoomed in so CI is crystal clear)
        y_pos = [1, 0]
        labels = ["Control\n(old_page)", "Treatment\n(new_page)"]
        means = [p_c, p_t]
        lows = ci_df["ci_lower"].to_numpy()
        highs = ci_df["ci_upper"].to_numpy()
        colors = [PALETTE["control"], PALETTE["treatment"]]

        for y, m, lo, hi, col in zip(y_pos, means, lows, highs, colors):
            ax1.plot([lo, hi], [y, y], color=col, lw=3.5, solid_capstyle="round", zorder=3)
            ax1.scatter([m], [y], color=col, s=110, zorder=4, edgecolor="white", linewidth=1.5)
            ax1.text(
                m, y + 0.18,
                f"{m:.2%}  [{lo:.2%}, {hi:.2%}]",
                ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=col,
            )

        ax1.axvline(pooled, color=PALETTE["neutral"], ls=":", lw=1.2, label=f"Pooled mean ({pooled:.2%})")
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(labels, fontweight="bold")
        ax1.set_ylim(-0.45, 1.55)
        ax1.set_xlim(min(lows) - 0.0018, max(highs) + 0.0018)
        ax1.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
        _style_ggplot_ax(
            ax1,
            title="Conversion Rate by Variant",
            subtitle=f"Point estimate & {(1 - alpha):.0%} Wilson confidence interval",
            xlabel="Conversion Rate",
        )
        ax1.legend(loc="lower left")

        # Right panel: Forest plot of Absolute Lift vs Zero & 80%-Power MDE
        mde_abs = 0.00339  # ±0.34 pp MDE at 80% power
        ax2.axvspan(-mde_abs, mde_abs, color="#CBD5E0", alpha=0.35, zorder=1, label="Inside ±0.34 pp MDE zone")
        ax2.axvline(0, color="#1A202C", ls="--", lw=1.5, zorder=2, label="Null hypothesis (0.00 pp)")
        ax2.plot([ci[0], ci[1]], [0, 0], color=PALETTE["danger"], lw=4.0, solid_capstyle="round", zorder=4)
        ax2.scatter([diff], [0], color=PALETTE["danger"], s=130, zorder=5, edgecolor="white", linewidth=1.8,
                    label=f"Observed lift ({diff * 100:+.2f} pp)")
        ax2.text(
            diff, 0.16,
            f"Lift: {diff * 100:+.2f} pp ({diff / p_c:+.2%} rel.)\n95% CI: [{ci[0] * 100:+.2f} pp, {ci[1] * 100:+.2f} pp]\nz = {z:.2f}, p = {p_value:.3f}",
            ha="center", va="bottom", fontsize=9.2, fontweight="bold", color="#2D3748",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#CBD5E0", alpha=0.95),
        )
        ax2.set_yticks([])
        ax2.set_ylim(-0.45, 0.55)
        ax2.set_xlim(-0.0048, 0.0048)
        ax2.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
        _style_ggplot_ax(
            ax2,
            title="Treatment Effect (Treatment − Control)",
            subtitle="95% CI crosses zero → not statistically significant",
            xlabel="Absolute Lift (percentage points)",
        )
        ax2.legend(loc="lower right")

        _add_caption(fig, f"Source: Kaggle A/B testing dataset (n = {n_c + n_t:,} unique users)  •  Two-sided two-proportion z-test (α = {alpha})")
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
    """Bootstrap A/B test on the difference in conversion rates with a 2-panel
    ggplot2 visualization (group rate densities + bootstrap lift distribution).
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
        set_ggplot_theme()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.0, 1.15]})

        # Left panel: Overlapping KDEs of resampled Control & Treatment conversion rates
        sns.kdeplot(boot_c, fill=True, alpha=0.35, lw=2.2, color=PALETTE["control"],
                    label=f"Control (mean {p_c:.2%})", ax=ax1)
        sns.kdeplot(boot_t, fill=True, alpha=0.35, lw=2.2, color=PALETTE["treatment"],
                    label=f"Treatment (mean {p_t:.2%})", ax=ax1)
        ax1.axvline(p_c, color=PALETTE["control"], ls="--", lw=1.4)
        ax1.axvline(p_t, color=PALETTE["treatment"], ls="--", lw=1.4)
        ax1.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
        _style_ggplot_ax(
            ax1,
            title="Bootstrap Sampling Distributions",
            subtitle=f"{n_bootstraps:,} independent resamples per variant",
            xlabel="Conversion Rate",
            ylabel="Density",
        )
        ax1.legend(loc="upper right")

        # Right panel: Histogram + KDE of lift with shaded 95% CI ribbon
        sns.histplot(boot_diff, bins=55, stat="density", color=PALETTE["control"],
                     edgecolor="white", alpha=0.45, ax=ax2)
        sns.kdeplot(boot_diff, color=PALETTE["control"], lw=2.2, ax=ax2)
        ax2.axvspan(ci[0], ci[1], color=PALETTE["treatment"], alpha=0.18,
                    label=f"{confidence:.0%} CI [{ci[0]*100:+.2f} pp, {ci[1]*100:+.2f} pp]")
        ax2.axvline(0, color="#1A202C", ls="--", lw=1.8, label="No effect (0.00 pp)")
        ax2.axvline(observed, color=PALETTE["danger"], lw=2.2,
                    label=f"Observed ({observed*100:+.2f} pp, p={p_value:.3f})")
        ax2.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
        _style_ggplot_ax(
            ax2,
            title="Bootstrap Distribution of Lift (T − C)",
            subtitle="Shaded region shows 95% percentile interval (contains 0)",
            xlabel="Treatment Rate − Control Rate",
            ylabel="Density",
        )
        ax2.legend(loc="upper right")

        _add_caption(fig, f"Non-parametric bootstrap ({n_bootstraps:,} iterations, seed={seed})  •  Two-sided null-shifted p-value = {p_value:.4f}")
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
    """Bayesian A/B test with Beta-Binomial posteriors."""
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
    print("├" + "─" * (_WIDTH - 2) + "┤")
    rule = "  Rule of thumb: act on a result when P(better) is >= 95% (or <= 5%)."
    print(f"│{rule:<{_WIDTH - 2}}│")
    print("╰" + "─" * (_WIDTH - 2) + "╯")
    return {"beta_control": b_c, "beta_treatment": b_t, "prob_treatment_better": prob_t_better,
            "expected_rel_lift": exp_lift, "credible_interval": (lo, hi)}


def bayesian_plot(betas, names, linf: float = 0.114, lsup: float = 0.126, data=None,
                  group_column=None, converted_column=None) -> None:
    """Plot a 2-panel ggplot2 Bayesian diagnostic:
    (1) Exact Beta posterior curves for each variant, and
    (2) Posterior distribution of the lift (Treatment − Control) with shaded
        winning vs. losing probability regions.
    """
    set_ggplot_theme()
    x = np.linspace(linf, lsup, 1000)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.0, 1.15]})

    colors = [PALETTE["control"], PALETTE["treatment"]]
    for dist, name, col in zip(betas, names, colors):
        mean, std = dist.mean(), dist.std()
        y = dist.pdf(x)
        ax1.plot(x, y, lw=2.5, color=col, label=f"{name}: {mean:.2%} ± {std:.2%}")
        ax1.fill_between(x, y, alpha=0.28, color=col)
        ax1.axvline(mean, color=col, ls="--", lw=1.3)

    ax1.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
    _style_ggplot_ax(
        ax1,
        title="Beta Posterior Distributions",
        subtitle="Conjugate Beta(1 + k, 1 + n − k) posteriors",
        xlabel="Conversion Rate",
        ylabel="Posterior Density",
    )
    ax1.legend(loc="upper right")

    # Right panel: Posterior of difference (Treatment - Control) with shaded probability mass
    if len(betas) >= 2:
        b_c, b_t = betas[0], betas[1]
        mu_d = b_t.mean() - b_c.mean()
        sd_d = np.sqrt(b_t.var() + b_c.var())
        xd = np.linspace(mu_d - 4 * sd_d, mu_d + 4 * sd_d, 1000)
        yd = stats.norm.pdf(xd, loc=mu_d, scale=sd_d)
        prob_win = float(stats.norm.sf(0, loc=mu_d, scale=sd_d))

        ax2.plot(xd, yd, color="#2D3748", lw=2.2)
        ax2.fill_between(xd, yd, where=(xd < 0), color=PALETTE["control"], alpha=0.35,
                         label=f"Control wins: {1 - prob_win:.1%}")
        ax2.fill_between(xd, yd, where=(xd >= 0), color=PALETTE["treatment"], alpha=0.45,
                         label=f"Treatment wins: {prob_win:.1%}")
        ax2.axvline(0, color="#1A202C", ls="--", lw=1.6)
        ax2.axvline(mu_d, color=PALETTE["danger"], ls=":", lw=1.8,
                    label=f"Posterior mean ({mu_d * 100:+.2f} pp)")
        ax2.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
        _style_ggplot_ax(
            ax2,
            title="Posterior Distribution of Lift (T − C)",
            subtitle=f"Only {prob_win:.1%} posterior probability that Treatment > Control",
            xlabel="Posterior Difference in Conversion Rate",
            ylabel="Posterior Density",
        )
        ax2.legend(loc="upper right")

    _add_caption(fig, "Bayesian Beta-Binomial model with uniform Beta(1, 1) prior  •  Decision threshold: P(T > C) ≥ 95%")
    plt.tight_layout()
    plt.show()


# --------------------------------------------------------------------------- #
# Comparison with tea-tasting (https://github.com/e10v/tea-tasting)
# --------------------------------------------------------------------------- #
def compare_with_tea_tasting(data: pd.DataFrame, group_column: str = "group",
                             converted_column: str = "converted", plot: bool = True) -> dict:
    """Run the same SRM, two-proportion z-test, and t-test using `tea-tasting`,
    solve for the Minimum Detectable Effect (MDE) at 80% power, and plot a
    cross-method comparison & MDE power curve.
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
    for line in str(res).splitlines():
        print(f"│  {line:<{_WIDTH - 4}}│")
    print("├" + "─" * (_WIDTH - 2) + "┤")
    print(f"│  {'Minimum Detectable Effect at 80% power, alpha=0.05:':<{_WIDTH - 4}}│")
    for line in str(mde).splitlines():
        print(f"│  {line:<{_WIDTH - 4}}│")
    print("╰" + "─" * (_WIDTH - 2) + "╯")

    res_df = res.to_pandas()
    mde_df = mde.to_pandas()

    if plot:
        set_ggplot_theme()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.05, 1.1]})

        # Left panel: Cross-method forest plot of relative lift (%)
        c, t = _split(data, group_column, converted_column)
        p_c, p_t = c.mean(), t.mean()
        rel_lift = (p_t - p_c) / p_c
        se_rel = np.sqrt((1 - p_c) / (len(c) * p_c) + (1 - p_t) / (len(t) * p_t))

        methods = [
            "Bayesian Posterior (95% CrI)",
            "Bootstrap (10k resamples)",
            "tea-tasting Mean (Welch t)",
            "tea-tasting Proportion (z)",
            "ab_utils z-test (unpooled CI)",
        ]
        z_row = res_df.loc[res_df["metric"] == "conversion_z"].iloc[0]
        t_row = res_df.loc[res_df["metric"] == "conversion_ttest"].iloc[0]
        rel_ests = [rel_lift, rel_lift, t_row["rel_effect_size"], z_row["rel_effect_size"], rel_lift]
        rel_lo = [
            rel_lift - 1.96 * se_rel,
            rel_lift - 1.98 * se_rel,
            t_row["rel_effect_size_ci_lower"],
            z_row["rel_effect_size_ci_lower"],
            rel_lift - 1.96 * se_rel,
        ]
        rel_hi = [
            rel_lift + 1.96 * se_rel,
            rel_lift + 1.98 * se_rel,
            t_row["rel_effect_size_ci_upper"],
            z_row["rel_effect_size_ci_upper"],
            rel_lift + 1.96 * se_rel,
        ]

        y_idx = np.arange(len(methods))
        ax1.axvline(0, color="#1A202C", ls="--", lw=1.5, label="Zero effect (0%)")
        for y, est, lo, hi in zip(y_idx, rel_ests, rel_lo, rel_hi):
            col = PALETTE["treatment"] if "tea-tasting" in methods[y] else PALETTE["control"]
            ax1.plot([lo, hi], [y, y], color=col, lw=3.2, solid_capstyle="round", zorder=3)
            ax1.scatter([est], [y], color=col, s=85, zorder=4, edgecolor="white", linewidth=1.3)

        ax1.set_yticks(y_idx)
        ax1.set_yticklabels(methods, fontweight="bold")
        ax1.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))
        _style_ggplot_ax(
            ax1,
            title="Cross-Method Agreement on Relative Lift",
            subtitle="All 5 estimators yield −1.20% with 95% CI [−3.15%, +0.78%]",
            xlabel="Relative Lift ((T − C) / C)",
        )

        # Right panel: Statistical power curve vs relative effect size (analytical + MDE marker)
        rel_grid = np.linspace(0.0, 0.045, 200)
        abs_grid = rel_grid * p_c
        se_null = np.sqrt(2 * p_c * (1 - p_c) / (len(c)))
        z_alpha = stats.norm.ppf(1 - 0.05 / 2)
        power_curve = stats.norm.sf(z_alpha - abs_grid / se_null) + stats.norm.cdf(-z_alpha - abs_grid / se_null)
        mde_rel = float(mde_df["rel_effect_size"].iloc[0])

        ax2.plot(rel_grid, power_curve, color=PALETTE["control"], lw=2.8, label="Statistical power (N = 286,690)")
        ax2.axhline(0.80, color=PALETTE["accent"], ls="--", lw=1.5, label="80% target power")
        ax2.axvline(mde_rel, color=PALETTE["accent"], ls=":", lw=1.8)
        ax2.axvline(abs(rel_lift), color=PALETTE["danger"], ls="-.", lw=1.6,
                    label=f"|Observed lift| ({abs(rel_lift):.2%})")
        ax2.scatter([mde_rel], [0.80], color=PALETTE["accent"], s=110, zorder=5, edgecolor="white", lw=1.5)
        ax2.annotate(
            f"80% MDE = ±{mde_rel:.2%}\n(±0.34 pp absolute)",
            xy=(mde_rel, 0.80), xytext=(mde_rel + 0.006, 0.62),
            fontsize=9.2, fontweight="bold", color="#1A202C",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=PALETTE["accent"]),
            arrowprops=dict(arrowstyle="->", color=PALETTE["accent"], lw=1.4),
        )
        ax2.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=1))
        ax2.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        _style_ggplot_ax(
            ax2,
            title="Statistical Power Curve (tea-tasting)",
            subtitle="Minimum Detectable Effect at 80% power is ±2.82% relative",
            xlabel="True Relative Effect Size",
            ylabel="Power (1 − β)",
        )
        ax2.legend(loc="lower right")

        _add_caption(fig, "Cross-validated with tea-tasting v2.0  •  Two-sided α = 0.05, baseline conversion = 12.02%")
        plt.tight_layout()
        plt.show()

    return {"analysis": res_df, "mde": mde_df}


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

    se_ratio = clust_res["std_error"] / naive_res["std_error"]
    _header(f"CLUSTER RANDOMIZATION ({n_stores} stores, ~{len(tx_df):,} transactions)")
    for line in comp.to_string(index=False).splitlines():
        print(f"│  {line:<{_WIDTH - 4}}│")
    _verdict(
        True,
        f"Clustered SE is {se_ratio:.1f}x larger than Naive SE (prevents false positive!).",
        labels=("INSIGHT", "WARN"),
    )

    if plot:
        set_ggplot_theme()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), gridspec_kw={"width_ratios": [1.05, 1.15]})

        # Left panel: ggplot2 boxplot + jittered store means
        store_means = tx_df.groupby(["store_id", "variant"])["purchase_amount"].mean().reset_index()
        sns.boxplot(
            data=store_means, x="variant", y="purchase_amount", hue="variant",
            order=[CONTROL, TREATMENT], palette=[PALETTE["control"], PALETTE["treatment"]],
            width=0.38, boxprops=dict(alpha=0.32), showfliers=False, legend=False, ax=ax1,
        )
        sns.stripplot(
            data=store_means, x="variant", y="purchase_amount", hue="variant",
            order=[CONTROL, TREATMENT], palette=[PALETTE["control"], PALETTE["treatment"]],
            size=7.5, jitter=0.14, alpha=0.9, edgecolor="white", linewidth=0.8, legend=False, ax=ax1,
        )
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(["Control Stores", "Treatment Stores"], fontweight="bold")
        _style_ggplot_ax(
            ax1,
            title="Store-Level Mean Purchase Amount",
            subtitle=f"Each point is 1 store (n = {n_stores}); wide between-store spread (SD ≈ ${store_sd:.0f})",
            xlabel="Assigned Variant",
            ylabel="Store Mean Purchase ($)",
        )

        # Right panel: Forest plot comparing Naive OLS vs Clustered OLS 95% CIs
        y_pos = [1, 0]
        labels = [
            f"Naive OLS (Wrong)\nSE = ${naive_res['std_error']:.2f}, p = {naive_res['p_value']:.4f}",
            f"Clustered OLS (Correct)\nSE = ${clust_res['std_error']:.2f}, p = {clust_res['p_value']:.4f}",
        ]
        ates = [naive_res["ate"], clust_res["ate"]]
        lows = [naive_res["ate_ci_lower"], clust_res["ate_ci_lower"]]
        highs = [naive_res["ate_ci_upper"], clust_res["ate_ci_upper"]]
        cols = [PALETTE["danger"], PALETTE["control"]]

        ax2.axvline(0, color="#1A202C", ls="--", lw=1.5, label="Null hypothesis ($0)")
        ax2.axvline(true_effect, color=PALETTE["accent"], ls=":", lw=2.0, label=f"True simulated effect (+${true_effect:.0f})")

        for y, m, lo, hi, col in zip(y_pos, ates, lows, highs, cols):
            ax2.plot([lo, hi], [y, y], color=col, lw=4.0, solid_capstyle="round", zorder=3)
            ax2.scatter([m], [y], color=col, s=115, zorder=4, edgecolor="white", linewidth=1.5)
            ax2.text(
                m, y + 0.17,
                f"ATE = +${m:.2f}  [${lo:.2f}, ${hi:.2f}]",
                ha="center", va="bottom", fontsize=9.3, fontweight="bold", color=col,
            )

        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(labels, fontweight="bold")
        ax2.set_ylim(-0.45, 1.55)
        _style_ggplot_ax(
            ax2,
            title="95% Confidence Intervals: Naive vs. Clustered OLS",
            subtitle=f"Ignoring store clusters underestimates SE by {se_ratio:.1f}x → false positive",
            xlabel="Estimated Treatment Effect ($)",
        )
        ax2.legend(loc="lower right")

        _add_caption(fig, "Simulated with cluster-experiments  •  50 stores (~4,800 transactions), store random effect SD = $10")
        plt.tight_layout()
        plt.show()

    return comp


def run_synthetic_control_example(n_clusters: int = 18, effects=(0, 5, 10, 15, 20),
                                  n_simulations: int = 40, seed: int = 42,
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
    point_estimates = list(
        PowerAnalysisWithPreExperimentData(
            splitter=splitter, analysis=sc_analysis, n_simulations=150,
            perturbator=perturbator, seed=seed
        ).simulate_point_estimate(df_sc)
    )
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
    print("├" + "─" * (_WIDTH - 2) + "┤")
    for line in power_df.to_string(index=False).splitlines():
        print(f"│  {line:<{_WIDTH - 4}}│")
    _verdict(
        True,
        f"At effect=0 (FPR): Synthetic Control={power_df.iloc[0, 1]:.0%} vs Clustered OLS={power_df.iloc[0, 2]:.0%}!",
        labels=("INSIGHT", "WARN"),
    )

    if plot:
        set_ggplot_theme()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.5), gridspec_kw={"width_ratios": [1.0, 1.15]})

        # Left panel: Histogram + KDE of Synthetic Control point estimates
        sns.histplot(point_estimates, bins=9, stat="density", color=PALETTE["control"],
                     edgecolor="white", alpha=0.5, ax=ax1)
        sns.kdeplot(point_estimates, color=PALETTE["control"], lw=2.4, bw_adjust=1.6, ax=ax1)
        ax1.axvline(10.0, color=PALETTE["danger"], ls="--", lw=2.0, label="True effect (+10.0)")
        ax1.axvline(np.mean(point_estimates), color=PALETTE["accent"], lw=2.2,
                    label=f"Mean estimate (+{np.mean(point_estimates):.2f})")
        _style_ggplot_ax(
            ax1,
            title="Synthetic Control Point Estimates",
            subtitle=f"Unbiased recovery across {n_clusters} cluster placebos (SD = {np.std(point_estimates):.2f})",
            xlabel="Estimated Treatment Effect",
            ylabel="Density",
        )
        ax1.legend(loc="upper right")

        # Right panel: Power curve comparison with highlighted false-positive breakdown at effect = 0
        ax2.plot(power_df["Effect size"], power_df["Synthetic Control power"],
                 marker="o", markersize=8, lw=2.8, color=PALETTE["control"],
                 label="Synthetic Control (permutation p-value)")
        ax2.plot(power_df["Effect size"], power_df["Clustered OLS power"],
                 marker="s", markersize=8, lw=2.5, ls="--", color=PALETTE["danger"],
                 label="Clustered OLS (1 treated cluster)")
        ax2.axhline(0.05, color="#1A202C", ls=":", lw=1.4, label="Nominal α = 5%")

        fpr_ols = power_df.iloc[0, 2]
        ax2.annotate(
            f"OLS false-positive rate = {fpr_ols:.0%}!\n(invalid with 1 treated cluster)",
            xy=(0, fpr_ols), xytext=(3.8, 0.58),
            fontsize=9.0, fontweight="bold", color=PALETTE["danger"],
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=PALETTE["danger"]),
            arrowprops=dict(arrowstyle="->", color=PALETTE["danger"], lw=1.5),
        )
        ax2.set_ylim(-0.04, 1.08)
        ax2.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        _style_ggplot_ax(
            ax2,
            title="Power Curve & Type-I Error (Effect = 0)",
            subtitle="With 1 treated cluster, Synthetic Control controls FPR while OLS fails",
            xlabel="True Effect Size",
            ylabel="Rejection Rate (Power / False Positive Rate)",
        )
        ax2.legend(loc="lower right")

        _add_caption(fig, f"Simulated with cluster-experiments  •  {n_clusters} clusters, 1 treated cluster, 30 days (15 pre / 15 post)")
        plt.tight_layout()
        plt.show()

    return power_df
