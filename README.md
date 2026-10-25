# A/B Test Analysis: Landing Page Social Proof (+ `tea-tasting` & `cluster-experiments`)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Methodology](https://img.shields.io/badge/Methods-Frequentist%20%7C%20Bootstrap%20%7C%20Bayesian-2B5C8F)
![tea-tasting](https://img.shields.io/badge/Cross--Check-tea--tasting-D95F02)
![cluster-experiments](https://img.shields.io/badge/Clustered%20%26%20Synthetic%20Control-cluster--experiments-1B9E77)

🇧🇷 [Versão em português](README.pt-BR.md)

An end-to-end experimentation portfolio project on a real dataset ([Kaggle](https://www.kaggle.com/datasets/zhangluyuan/ab-testing), ~294k users): experiment planning & metric hierarchy, **Type M (Magnitude) & Type S (Sign) error audit**, data quality & leakage checks, Sample Ratio Mismatch (SRM), three statistical paradigms (frequentist, non-parametric bootstrap, Bayesian), cross-validation & MDE power analysis via [`tea-tasting`](https://github.com/e10v/tea-tasting), and **Cluster Randomization** + **Synthetic Control** experiments via [`cluster-experiments`](https://david26694.github.io/cluster-experiments/). All visualizations use a unified **ggplot2-styled** diagnostic layout.

> **Executive Summary:** the new landing page did **not** improve conversion (`12.02%` → `11.87%`, `−0.14 pp` absolute / `−1.20%` relative, `p = 0.232`). With 286,690 clean users (~22 days of traffic), the experiment had 80% power to detect a **±0.34 pp (±2.84% relative)** lift, and Bayesian inference gives only an **11.6% probability** that the treatment beats control. **Recommendation: do not ship.**

> [!NOTE]
> **Project Evolution (4 Years Later):** The first version of this repository was written almost four years ago as a foundational user-level A/B test study. Since then, after running and leading Data and Product teams through hundreds of production experiments, I revisited this repo to incorporate hard-earned lessons from real-world experimentation at scale:
> - **Pre-experiment rigor:** metric hierarchies (OEC, diagnostic, and guardrail metrics), choosing **Superiority vs. Non-Inferiority** hypotheses, and **MDE sample-size planning**.
> - **The "Winner's Curse" in low-power tests:** a deep dive into **Type M (Magnitude) and Type S (Sign) errors**, building on the article I wrote for the Asaas Data & Engineering blog ([*O Erro Secreto: O Erro Tipo M em Testes A/B*](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01)).
> - **Modern experimentation stack:** cross-checking estimates and power curves with [`tea-tasting`](https://github.com/e10v/tea-tasting), plus handling network spillover and regional/store rollouts via **Cluster Randomization (`clustered_ols`)** and **Synthetic Control** with [`cluster-experiments`](https://david26694.github.io/cluster-experiments/).

---

## Executive Scorecard

| Stage / Method | Key Metric | Result | Threshold / CI | Verdict |
|---|---|---|---|---|
| **0. Experiment Design** | Target MDE & Runtime | `±0.34 pp` (`±2.84%` rel.) | `N = 286,690` (~22 days, `80%` power, `α = 0.05`) | **PRE-SPECIFIED** |
| **0.4 Type M / Type S** | Exaggeration at `80%` MDE vs `+0.5%` | `1.12×` (at MDE) vs `4.84×` (at `+0.5%`) | Prevents the "Winner's Curse" in small lifts | **GUARDED AT ≥2.84%** |
| **1. Data Hygiene** | Contaminated / mismatched rows | `7,788` rows (`2.64%`) dropped | `0` mismatches in `286,690` clean users | **PASS** |
| **2. SRM Check** | Control / Treatment split | `143,293` vs `143,397` (`0.9993`) | `χ² = 0.0377`, `p = 0.8460` (`> 0.001`) | **PASS** |
| **3. Frequentist (z-test)** | Absolute / Relative lift | `−0.14 pp` (`−1.20%`) | 95% CI `[−0.38 pp, +0.09 pp]`, `p = 0.2323` | **NOT SIGNIFICANT** |
| **4. Bootstrap (10k)** | Resampled lift | `−0.14 pp` (`−1.20%`) | 95% CI `[−0.39 pp, +0.09 pp]`, `p = 0.2324` | **NOT SIGNIFICANT** |
| **5. Bayesian (Beta)** | `P(Treatment > Control)` | `11.6%` (`88.4%` Control wins) | 95% CrI `[−0.38 pp, +0.09 pp]` | **DO NOT SHIP** |
| **6. `tea-tasting` MDE** | Sensitivity / Power check | `±0.34 pp` (`±2.84%` relative) | 80% power, two-sided `α = 0.05` | **WELL-POWERED** |
| **7. Clustered OLS** | Store-randomized SE ratio | `SE = $2.92` vs Naive `$0.64` | `4.5x` SE inflation (`p = 0.5017` vs `0.0023`) | **PREVENTS FALSE POSITIVE** |
| **8. Synthetic Control** | 1-treated-cluster FPR (`effect=0`) | `0%` FPR (`100%` power at `+10`) | Clustered OLS has `75%` FPR at `effect=0` | **REQUIRED FOR N=1 CLUSTER** |

---

## Repository Structure

| File | Description |
|---|---|
| [`analysis.ipynb`](analysis.ipynb) | Full, executed notebook with planning framework, Type M/S audit, code, box-drawn reports, and ggplot2 charts |
| [`ab_utils.py`](ab_utils.py) | Reusable toolkit: ggplot2 theme, SRM, Wilson CIs, z-test, bootstrap, Bayesian test, Type M/S analysis, `tea-tasting` & `cluster-experiments` |
| `plots/*.png` | High-resolution two-panel ggplot2 diagnostic charts |
| `data/ab_data.csv` | Raw experiment log (`user_id`, `timestamp`, `group`, `landing_page`, `converted`) |
| [`README.pt-BR.md`](README.pt-BR.md) | Complete Portuguese version of this documentation |

## Quick Start

```bash
pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

Or call the functions directly from Python:

```python
from ab_utils import (
    srm_test,
    perform_ab_test_analysis,
    bootstrap_ab_test,
    bayesian_ab_test,
    compare_with_tea_tasting,
    analyze_type_m_s_errors,
    run_cluster_randomization_example,
    run_synthetic_control_example,
)

srm_test(control_count, treatment_count)   # chi-square SRM check (threshold p = 0.001)
perform_ab_test_analysis(df)               # two-proportion z-test + 2-panel ggplot2 forest chart
bootstrap_ab_test(df)                      # 10k binomial bootstrap + sampling/lift density plots
bayesian_ab_test(df)                       # Beta-Binomial posterior + winning probability
compare_with_tea_tasting(df)               # tea-tasting cross-check + MDE power curve
analyze_type_m_s_errors(df)                # Gelman & Carlin Type M (exaggeration) & Type S (sign) audit
run_cluster_randomization_example()        # Naive OLS vs. Clustered OLS on store-randomized data
run_synthetic_control_example()            # Synthetic Control vs. Clustered OLS (1 treated cluster)
```

---

## Part I — User-Level Landing Page Experiment

### 0. Experiment Planning Phase: Hypothesis, Metric Hierarchy, Test Type & MDE

Before writing any analysis code, a trustworthy experiment starts with a **Planning Phase** triggered by the Product Manager's request:

```text
Hi Matheus!
I'd like to test a hypothesis on our landing page: adding social proof ("98% of customers are
satisfied", "Recommended by Forbes, CNN, and The New York Times", "Over 1M happy customers")
will build trust and increase our conversion rate.

To test this, we'll split incoming visitors 50/50 between the current landing page (control)
and the new version with social proof (treatment) and compare conversion rates.
```

Following Kohavi et al. (*Trustworthy Online Controlled Experiments*) and Georgiev (*Statistical Methods in Online A/B Testing*), we translate this request into a pre-registered experiment specification:

#### 0.1 Metric Hierarchy (Primary, Secondary & Guardrails)
Even though the public Kaggle log only exports the binary `converted` flag, in production we define three tiers of metrics before launch:
- **Primary Decision Metric (OEC):** `Conversion Rate` (`converted` per unique user) — the single metric that determines whether the hypothesis succeeds.
- **Secondary / Diagnostic Metrics:** `Click-Through Rate (CTR)` on the CTA button, `Scroll Depth` (did users actually see the social-proof section?), and `Time to Convert` — used to explain *why* the primary metric moved or stayed flat.
- **Guardrail Metrics:**
  - *Organizational / System Guardrails:* `Sample Ratio Mismatch (SRM)`, `Page Load Latency (p95)` (extra social-proof widgets/images can slow down rendering and hurt conversion), and `Client Error Rate`.
  - *Business Guardrails:* `Bounce Rate`, `Refund / Cancellation Rate`, and `Average Order Value (AOV)` (ensuring urgency/social proof doesn't attract low-intent signups).

#### 0.2 Choosing the Test Type (Superiority vs. Non-Inferiority)
The business goal dictates the statistical hypothesis structure:
- **Superiority Test (used when shipping requires a proven gain):** If adding social proof introduces maintenance cost or visual clutter, we only ship if Treatment **beats** Control ($H_0: \Delta = 0$ vs. $H_1: \Delta \neq 0$, or one-sided $H_1: \Delta > 0$).
- **Non-Inferiority / Equivalence Test (used for redesigns, migrations, or brand updates):** If the new landing page is required for brand alignment or a tech-stack migration, we don't need it to *increase* conversion — we only need to prove it doesn't hurt conversion by more than a pre-agreed **non-inferiority margin** $-\Delta_{\text{NI}}$ (e.g., $H_0: p_T - p_C \le -0.25\text{ pp}$ vs. $H_1: p_T - p_C > -0.25\text{ pp}$). Looking at our observed 95% CI `[−0.38 pp, +0.09 pp]`, the new page fails a superiority test, and would only pass a non-inferiority test if leadership tolerated up to a `−0.40 pp` (`−3.3%` relative) drop.

#### 0.3 Defining the MDE & Sample Size (*A Priori* vs. Retrospective Sensitivity)
The **Minimum Detectable Effect (MDE)** is the smallest true lift worth detecting at a target statistical power ($1 - \beta = 80\%$) and significance level ($\alpha = 0.05$). It is a **planning parameter chosen before the test**, balancing business ROI against traffic constraints (~13,030 clean users/day in this dataset, baseline $p_0 \approx 12.0\%$):

| Target Relative MDE | Absolute Lift ($\Delta$) | Required Total Sample ($N$) | Est. Runtime (~13k users/day) | Practical Trade-off |
|---|---|---|---|---|
| **±1.00%** | `±0.12 pp` | `2,312,270` | ~177 days (~25 weeks) | Too slow for a UI copy test; requires CUPED or higher traffic |
| **±2.00%** | `±0.24 pp` | `580,545` | ~45 days (~6.5 weeks) | High precision, moderate runtime |
| **±2.84% (This Dataset)** | **`±0.34 pp`** | **`286,690`** | **22 days (~3 full weeks)** | **Sweet spot: 3 weekly cycles, detects ≥2.84% lift at 80% power** |
| **±5.00%** | `±0.60 pp` | `94,072` | ~7.2 days (1 full week) | Fast screening for bold redesigns |
| **±10.00%** | `±1.20 pp` | `24,007` | ~2 days *(extend to 7d)* | Never stop at 2 days — always run at least 1–2 full weekly cycles |

> [!IMPORTANT]
> **Why we never rely on "observed post-hoc power":** As Georgiev emphasizes, plugging a noisy observed effect (`−0.14 pp`) into a power formula after the test is statistically meaningless. Instead, when auditing an existing dataset of $N = 286,690$, we compute the **retrospective sensitivity MDE (`±0.34 pp` / `±2.84%`)** to answer: *"What effect size was this experiment well-powered to detect?"* Because `±2.84%` is well below the typical 3%–5% bar for a landing-page change, a non-significant result (`p = 0.232`) is a well-powered null, not an underpowered guess.

#### 0.4 Beyond Type I & Type II: Type M (Magnitude) & Type S (Sign) Errors ("The Winner's Curse")
Most experimentation teams only track **Type I ($\alpha$)** and **Type II ($\beta$)** errors. However, one of the most expensive mistakes I have seen leading Product and Data teams — and the subject of my Asaas Engineering blog post, [***O Erro Secreto: O Erro Tipo M em Testes A/B***](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01) (building on Gelman & Carlin, 2014) — happens when an **underpowered experiment gets "lucky" and crosses $p < 0.05$**:

1. **Type M Error (Magnitude / Exaggeration Ratio, $\mathbb{E}[|\hat{\Delta}| \mid p < 0.05] / |\Delta_{\text{true}}|$):** Because the significance filter requires $|\hat{\Delta}| > 1.96 \times \text{SE}$ (`±1.98%` relative lift in our dataset), any small true effect (say `+0.50%`) that achieves $p < 0.05$ **must** have experienced a massive positive noise spike. Conditional on being statistically significant, the reported lift is **guaranteed to be inflated** — often by **2.5× to 9.5×** (the **Winner's Curse**). Teams then bake that exaggerated lift into revenue forecasts and wonder why cumulative product gains never show up in the P&L.
2. **Type S Error (Sign Error, $P(\text{wrong sign} \mid p < 0.05)$):** When power is very low, a significant result has a non-trivial probability of pointing in the **exact opposite direction** of the true effect (e.g., at a true `+0.25%` lift, nearly **24% of statistically significant results are negative**!).

Running `analyze_type_m_s_errors(ab_clean)` quantifies the exact risk profile for our dataset's standard error ($\text{SE}_{\text{rel}} = 1.01\%$):

```text
╭────────────────────────────────────────────────────────────────────╮
│ TYPE M (MAGNITUDE) & TYPE S (SIGN) ERROR AUDIT                     │
├────────────────────────────────────────────────────────────────────┤
│  True Rel. Lift True Abs. Lift Power Type S (Wrong Sign) Type M (Exaggeration) Avg. Winner Reported│
│          +0.25%       +0.03 pp  5.7%              23.92%                 9.52x               +2.38%│
│          +0.50%       +0.06 pp  7.8%               8.98%                 4.84x               +2.42%│
│          +1.00%       +0.12 pp 16.7%               0.95%                 2.52x               +2.52%│
│          +1.50%       +0.18 pp 31.7%               0.09%                 1.76x               +2.64%│
│          +2.00%       +0.24 pp 50.8%               0.01%                 1.40x               +2.79%│
│          +2.84%       +0.34 pp 80.2%               0.00%                 1.12x               +3.19%│
│          +5.00%       +0.60 pp 99.9%               0.00%                 1.00x               +5.00%│
├────────────────────────────────────────────────────────────────────┤
│  [INSIGHT] Underpowered 'winners' exaggerate true lift by 2.5x–9.5x (Winner's Curse!).│
╰────────────────────────────────────────────────────────────────────╯
```
![Type M & Type S Errors](plots/type_m_s_errors.png)

- **Takeaway for Experimentation Leaders:** Powering an experiment to $\ge 80\%$ at a realistic MDE (`+2.84%` here) doesn't just protect against false negatives ($\beta$) — it drives the **Type M exaggeration ratio down to `1.12×`** and **Type S error to `0.00%`**, ensuring that when you celebrate a winner, the reported lift is real.

---

### 1. Data Hygiene & Variant Consistency
- **294,478** raw rows (`2017-01-02` to `2017-01-24`, ~22 days), zero missing values, zero exact duplicate rows.
- **3,894 `user_id`s appear more than once** (7,788 rows, `2.64%` of traffic), and **1,895 users were exposed to both variants** (`control` and `treatment`), violating unit-level independence.
- **3,893 rows have a group/page mismatch** (`control` seeing `new_page` or `treatment` seeing `old_page`). Dropping all repeated `user_id`s eliminates every mismatch and leaves **286,690 unique users**:

```text
╭────────────────────────────────────────────────────────────────────╮
│ GROUP / LANDING PAGE CONSISTENCY                                   │
├────────────────────────────────────────────────────────────────────┤
│  landing_page  new_page  old_page                                  │
│  group                                                             │
│  control              0    143293                                  │
│  treatment       143397         0                                  │
├────────────────────────────────────────────────────────────────────┤
│  [PASS] 0 rows where group and landing page disagree               │
╰────────────────────────────────────────────────────────────────────╯
```

### 2. Sample Ratio Mismatch (SRM)
```text
╭────────────────────────────────────────────────────────────────────╮
│ SAMPLE RATIO MISMATCH (SRM) CHECK                                  │
├────────────────────────────────────────────────────────────────────┤
│  Control users:              143,293                               │
│  Treatment users:            143,397                               │
│  Difference (C - T):         -104                                  │
│  Control / Treatment ratio:  0.9993                                │
│  Chi-square:                 0.0377                                │
│  P-value:                    0.8460  (threshold 0.001)             │
├────────────────────────────────────────────────────────────────────┤
│  [PASS] Traffic split looks healthy - results can be trusted.      │
╰────────────────────────────────────────────────────────────────────╯
```

### 3. Frequentist Analysis: Two-Proportion z-Test & Wilson CIs
```text
╭────────────────────────────────────────────────────────────────────╮
│ FREQUENTIST TEST: TWO-PROPORTION Z-TEST                            │
├────────────────────────────────────────────────────────────────────┤
│  Control rate:               12.0173%  (n=143,293)                 │
│  Treatment rate:             11.8726%  (n=143,397)                 │
│  Absolute lift:              -0.1447%                              │
│  Relative lift:              -1.20%                                │
│  95% CI of difference:       [-0.3821%, +0.0927%]                  │
│  z-statistic:                -1.1945                               │
│  P-value (two-sided):        0.2323  (alpha 0.05)                  │
├────────────────────────────────────────────────────────────────────┤
│  [NOT SIGNIFICANT] No statistically significant difference between the groups.│
╰────────────────────────────────────────────────────────────────────╯
```
![Frequentist Conversion Rate & Lift](plots/conversion_ci.png)

### 4. Non-Parametric Bootstrap (10,000 Resamples)
```text
╭────────────────────────────────────────────────────────────────────╮
│ BOOTSTRAP TEST                                                     │
├────────────────────────────────────────────────────────────────────┤
│  Resamples:                  10,000  (seed=42)                     │
│  Observed difference:        -0.1447%                              │
│  95% bootstrap CI:           [-0.3882%, +0.0932%]                  │
│  P-value (two-sided):        0.2324  (alpha 0.05)                  │
├────────────────────────────────────────────────────────────────────┤
│  [NOT SIGNIFICANT] No statistically significant difference (the CI contains 0).│
╰────────────────────────────────────────────────────────────────────╯
```
![Bootstrap Distributions](plots/bootstrap_plot.png)

### 5. Bayesian Inference (Conjugate Beta-Binomial)
```text
╭────────────────────────────────────────────────────────────────────╮
│ BAYESIAN TEST (Beta-Binomial, uniform prior)                       │
├────────────────────────────────────────────────────────────────────┤
│  P(treatment > control):     11.6%                                 │
│  P(control > treatment):     88.4%                                 │
│  Expected relative lift:     -1.20%                                │
│  95% credible interval:      [-0.3825%, +0.0937%]  (absolute)      │
├────────────────────────────────────────────────────────────────────┤
│  Rule of thumb: act on a result when P(better) is >= 95% (or <= 5%).│
╰────────────────────────────────────────────────────────────────────╯
```
![Bayesian Posteriors](plots/bayes.png)

### 6. Cross-Check & Statistical Power Curve (`tea-tasting`)

Cross-validating with [`tea-tasting`](https://github.com/e10v/tea-tasting) (`SampleRatio`, `Proportion`, and `Mean`) confirms our exact estimates and plots the sensitivity **Minimum Detectable Effect (MDE)** curve at 80% power (`α = 0.05`):

```text
╭────────────────────────────────────────────────────────────────────╮
│ TEA-TASTING CROSS-CHECK & POWER (MDE)                              │
├────────────────────────────────────────────────────────────────────┤
│  metric           control treatment rel_effect_size rel_effect_size_ci pvalue│
│  srm               143293    143397               -             [-, -]  0.847│
│  conversion_z       0.120     0.119           -1.2%     [-3.1%, 0.78%]  0.232│
│  conversion_ttest   0.120     0.119           -1.2%     [-3.1%, 0.78%]  0.232│
├────────────────────────────────────────────────────────────────────┤
│  Minimum Detectable Effect at 80% power, alpha=0.05:               │
│  metric     power effect_size rel_effect_size  n_obs               │
│  conversion   80%     0.00339            2.8% 286690               │
╰────────────────────────────────────────────────────────────────────╯
```
![tea-tasting Cross-Check & Power Curve](plots/tea_tasting_power.png)

---

## Part II — Clustered Experiments & Synthetic Control (`cluster-experiments`)

When user-level randomization isn't possible due to network spillover or operational constraints (e.g., store layouts, city-level pricing, regional rollouts), randomization happens at the **cluster level**. Ignoring that structure severely underestimates standard errors and inflates false positives.

### 7. Cluster Randomization: Naive OLS vs. Clustered OLS
Adapted from the [`cluster-experiments` Cluster Randomization guide](https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html): 50 stores are randomized to control or treatment (`+$5` true effect, store random effect `SD = $10` across ~4,823 transactions). Naive OLS treats transactions as independent, underestimating the standard error by **4.5x** and declaring a false positive (`p = 0.0023`), whereas Clustered OLS accounts for intra-store correlation (`p = 0.5017`):

```text
╭────────────────────────────────────────────────────────────────────╮
│ CLUSTER RANDOMIZATION (50 stores, ~4,823 transactions)             │
├────────────────────────────────────────────────────────────────────┤
│                          Method  ATE ($)  Std. Error ($)  p-value          95% CI│
│    Naive OLS (ignores clusters)     1.96            0.64   0.0023  [$0.70, $3.23]│
│  Clustered OLS (store-level SE)     1.96            2.92   0.5017 [$-3.77, $7.69]│
├────────────────────────────────────────────────────────────────────┤
│  [INSIGHT] Clustered SE is 4.5x larger than Naive SE (prevents false positive!).│
╰────────────────────────────────────────────────────────────────────╯
```
![Cluster Randomization](plots/cluster_randomization.png)

### 8. Synthetic Control vs. Clustered OLS (Single Treated Cluster)
Adapted from the [`cluster-experiments` Synthetic Control guide](https://david26694.github.io/cluster-experiments/synthetic_control.html): when **only 1 cluster** receives treatment (e.g., a single city or country launch), even Clustered OLS breaks down — its false-positive rate at `effect = 0` spikes to **75%** instead of the nominal 5%. **Synthetic Control** builds a counterfactual from pre-intervention donor clusters, keeping the false-positive rate at **0%** at `effect = 0` while reaching **100% power** for true effects of `+10` and above:

```text
╭────────────────────────────────────────────────────────────────────╮
│ SYNTHETIC CONTROL vs. CLUSTERED OLS (1 treated cluster)            │
├────────────────────────────────────────────────────────────────────┤
│  Point estimate mean (true=+10):10.27  (sd=1.64)                   │
├────────────────────────────────────────────────────────────────────┤
│   Effect size  Synthetic Control power  Clustered OLS power        │
│             0                    0.000                 0.75        │
│             5                    0.625                 1.00        │
│            10                    1.000                 1.00        │
│            15                    1.000                 1.00        │
│            20                    1.000                 1.00        │
├────────────────────────────────────────────────────────────────────┤
│  [INSIGHT] At effect=0 (FPR): Synthetic Control=0% vs Clustered OLS=75%!│
╰────────────────────────────────────────────────────────────────────╯
```
![Synthetic Control](plots/synthetic_control.png)

---

## References
- [O Erro Secreto: O Erro Tipo M em Testes A/B](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01) — Matheus Buniotto (*Estação Asaas / Asaas Data & Engineering Blog*)
- [Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing](https://www.amazon.com/Trustworthy-Online-Controlled-Experiments-Practical-ebook/dp/B0845Y3DJV) — Ron Kohavi, Diane Tang, Ya Xu
- [Statistical Methods in Online A/B Testing: Statistics for data-driven business decisions and risk management in e-commerce](https://www.amazon.com/Statistical-Methods-Online-Testing-data-driven/dp/1694079725) — Georgi Z. Georgiev
- [Beyond Power Calculations: Assessing Type S (Sign) and Type M (Magnitude) Errors](https://doi.org/10.1177/1745691614551642) — Andrew Gelman, John Carlin (2014)
- [`tea-tasting`: statistical analysis of A/B tests in Python](https://github.com/e10v/tea-tasting) — Evgeny Ivanov
- [`cluster-experiments`: Cluster Randomization](https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html) & [Synthetic Control](https://david26694.github.io/cluster-experiments/synthetic_control.html) — David Masip
- [Detecting and avoiding bucket imbalance in A/B tests](https://blog.twitter.com/engineering/en_us/a/2015/detecting-and-avoiding-bucket-imbalance-in-ab-tests) — Twitter Engineering
