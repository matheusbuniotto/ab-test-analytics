# A/B Test Analysis: Landing Page Social Proof (+ `tea-tasting` & `cluster-experiments`)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Methodology](https://img.shields.io/badge/Methods-Frequentist%20%7C%20Bootstrap%20%7C%20Bayesian-2B5C8F)
![tea-tasting](https://img.shields.io/badge/Cross--Check-tea--tasting-D95F02)
![cluster-experiments](https://img.shields.io/badge/Clustered%20%26%20Synthetic%20Control-cluster--experiments-1B9E77)

🇧🇷 [Versão em português](README.pt-BR.md)

An end-to-end experimentation portfolio project on a real dataset ([Kaggle](https://www.kaggle.com/datasets/zhangluyuan/ab-testing), ~294k users): data quality & leakage audits, Sample Ratio Mismatch (SRM), three statistical paradigms (frequentist, non-parametric bootstrap, Bayesian), cross-validation & MDE power analysis via [`tea-tasting`](https://github.com/e10v/tea-tasting), and **Cluster Randomization** + **Synthetic Control** experiments via [`cluster-experiments`](https://david26694.github.io/cluster-experiments/). All visualizations use a unified **ggplot2-styled** diagnostic layout.

> **Executive Summary:** the new landing page did **not** improve conversion (`12.02%` → `11.87%`, `−0.14 pp` absolute / `−1.20%` relative, `p = 0.232`). With 286,690 clean users, the experiment had 80% power to detect a **±0.34 pp (±2.84% relative)** lift, and Bayesian inference gives only an **11.6% probability** that the treatment beats control. **Recommendation: do not ship.**

---

## Executive Scorecard

| Stage / Method | Key Metric | Result | Threshold / CI | Verdict |
|---|---|---|---|---|
| **1. Data Hygiene** | Contaminated / mismatched rows | `7,788` rows (`2.64%`) dropped | `0` mismatches in `286,690` clean users | **PASS** |
| **2. SRM Check** | Control / Treatment split | `143,293` vs `143,397` (`0.9993`) | `χ² = 0.0377`, `p = 0.8460` (`> 0.001`) | **PASS** |
| **3. Frequentist (z-test)** | Absolute / Relative lift | `−0.14 pp` (`−1.20%`) | 95% CI `[−0.38 pp, +0.09 pp]`, `p = 0.2323` | **NOT SIGNIFICANT** |
| **4. Bootstrap (10k)** | Resampled lift | `−0.14 pp` (`−1.20%`) | 95% CI `[−0.39 pp, +0.09 pp]`, `p = 0.2324` | **NOT SIGNIFICANT** |
| **5. Bayesian (Beta)** | `P(Treatment > Control)` | `11.6%` (`88.4%` Control wins) | 95% CrI `[−0.38 pp, +0.09 pp]` | **DO NOT SHIP** |
| **6. `tea-tasting` MDE** | Minimum Detectable Effect | `±0.34 pp` (`±2.84%` relative) | 80% power, two-sided `α = 0.05` | **WELL-POWERED** |
| **7. Clustered OLS** | Store-randomized SE ratio | `SE = $2.92` vs Naive `$0.64` | `4.5x` SE inflation (`p = 0.5017` vs `0.0023`) | **PREVENTS FALSE POSITIVE** |
| **8. Synthetic Control** | 1-treated-cluster FPR (`effect=0`) | `0%` FPR (`100%` power at `+10`) | Clustered OLS has `75%` FPR at `effect=0` | **REQUIRED FOR N=1 CLUSTER** |

---

## Repository Structure

| File | Description |
|---|---|
| [`analysis.ipynb`](analysis.ipynb) | Full, executed notebook with all code, box-drawn reports, and ggplot2-styled charts |
| [`ab_utils.py`](ab_utils.py) | Reusable toolkit: ggplot2 theme, SRM, Wilson CIs, z-test, bootstrap, Bayesian test, `tea-tasting` & `cluster-experiments` wrappers |
| `plots/*.png` | High-resolution two-panel ggplot2 diagnostic charts |
| `data/ab_data.csv` | Raw experiment log (`user_id`, `timestamp`, `group`, `landing_page`, `converted`) |
| [`README.pt-BR.md`](README.pt-BR.md) | Original Portuguese write-up |

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
    run_cluster_randomization_example,
    run_synthetic_control_example,
)

srm_test(control_count, treatment_count)   # chi-square SRM check (threshold p = 0.001)
perform_ab_test_analysis(df)               # two-proportion z-test + 2-panel ggplot2 forest chart
bootstrap_ab_test(df)                      # 10k binomial bootstrap + sampling/lift density plots
bayesian_ab_test(df)                       # Beta-Binomial posterior + winning probability
compare_with_tea_tasting(df)               # tea-tasting cross-check + MDE power curve
run_cluster_randomization_example()        # Naive OLS vs. Clustered OLS on store-randomized data
run_synthetic_control_example()            # Synthetic Control vs. Clustered OLS (1 treated cluster)
```

---

## Part I — User-Level Landing Page Experiment

### 1. Data Hygiene & Variant Consistency
- **294,478** raw rows, zero missing values, zero exact duplicate rows.
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

Cross-validating with [`tea-tasting`](https://github.com/e10v/tea-tasting) (`SampleRatio`, `Proportion`, and `Mean`) confirms our exact estimates and adds the **Minimum Detectable Effect (MDE)** at 80% power (`α = 0.05`):

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
- [Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing](https://www.amazon.com/Trustworthy-Online-Controlled-Experiments-Practical-ebook/dp/B0845Y3DJV) — Ron Kohavi, Diane Tang, Ya Xu
- [Statistical Methods in Online A/B Testing: Statistics for data-driven business decisions and risk management in e-commerce](https://www.amazon.com/Statistical-Methods-Online-Testing-data-driven/dp/1694079725) — Georgi Z. Georgiev
- [`tea-tasting`: statistical analysis of A/B tests in Python](https://github.com/e10v/tea-tasting) — Evgeny Ivanov
- [`cluster-experiments`: Cluster Randomization](https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html) & [Synthetic Control](https://david26694.github.io/cluster-experiments/synthetic_control.html) — David Masip
- [Detecting and avoiding bucket imbalance in A/B tests](https://blog.twitter.com/engineering/en_us/a/2015/detecting-and-avoiding-bucket-imbalance-in-ab-tests) — Twitter Engineering
