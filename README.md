# A/B Test Analysis: Landing Page Social Proof

🇧🇷 [Versão em português](README.pt-BR.md)

A end-to-end A/B test analysis on a real dataset ([Kaggle](https://www.kaggle.com/datasets/zhangluyuan/ab-testing), ~294k users): data quality checks, Sample Ratio Mismatch, and three statistical approaches (frequentist, bootstrap, Bayesian) that lead to one business recommendation.

> **TL;DR:** the new landing page did **not** improve conversion (12.02% → 11.87%, p = 0.23). The result is statistically inconclusive, and there's only an ~12% probability that the new page is better.

## The problem

The product manager's hypothesis: *adding social proof to the landing page will increase the conversion rate.* Control sees the old page, treatment sees the new page with social proof. The metric is binary conversion (`converted`).

## What's in the repo

| File | Purpose |
|---|---|
| [`analysis.ipynb`](analysis.ipynb) | The full, executed analysis |
| [`ab_utils.py`](ab_utils.py) | Reusable functions: SRM, CIs, z-test, bootstrap, Bayesian test, plots |
| `data/ab_data.csv` | Experiment data (user, timestamp, group, page, converted) |
| [`README.pt-BR.md`](README.pt-BR.md) | Original Portuguese write-up |

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

Or use the helpers on your own data (needs `group` = `control`/`treatment` and a 0/1 `converted` column):

```python
from ab_utils import srm_test, perform_ab_test_analysis, bootstrap_ab_test, bayesian_ab_test

srm_test(control_count, treatment_count)   # is the traffic split healthy?
perform_ab_test_analysis(df)               # two-proportion z-test + CI of the lift
bootstrap_ab_test(df)                      # resampling, no distributional assumptions
bayesian_ab_test(df)                       # P(treatment > control)
```

Each function prints a compact report and returns a dict with the numbers.

## Analysis

### 1. Data quality
- 294,478 rows, no missing values, no fully duplicated rows.
- **3,894 `user_id`s appear more than once** (7,788 rows); 1,895 of them were exposed to *both* variants.
- **3,893 rows have a group/page mismatch** (control users seeing `new_page` or vice versa).

We drop every row of a repeated user (no rule exists to pick the "right" one). This also removes every mismatch, leaving **286,690 users**.

```
 GROUP / LANDING PAGE CONSISTENCY   (after cleaning)
landing_page  new_page  old_page
control              0    143293
treatment       143397         0
  [PASS] 0 rows where group and landing page disagree
```

### 2. Sample Ratio Mismatch
```
 SAMPLE RATIO MISMATCH (SRM) CHECK
  Control users:              143,293
  Treatment users:            143,397
  Difference (C - T):         -104
  Control / Treatment ratio:  0.9993
  Chi-square:                 0.0377
  P-value:                    0.8460  (threshold 0.001)
  [PASS] Traffic split looks healthy - results can be trusted.
```

### 3. Frequentist: two-proportion z-test
```
  Control rate:               12.0173%  (n=143,293)
  Treatment rate:             11.8726%  (n=143,397)
  Absolute lift:              -0.1447%
  Relative lift:              -1.20%
  95% CI of difference:       [-0.3821%, +0.0927%]
  z-statistic:                -1.1945
  P-value (two-sided):        0.2323  (alpha 0.05)
  [NOT SIGNIFICANT] No statistically significant difference between the groups.
```
![Conversion rates](plots/conversion_ci.png)

### 4. Bootstrap (10,000 resamples)
```
  Observed difference:        -0.1447%
  95% bootstrap CI:           [-0.3882%, +0.0932%]
  P-value (two-sided):        0.2324  (alpha 0.05)
  [NOT SIGNIFICANT] No statistically significant difference (the CI contains 0).
```
![Bootstrap](plots/bootstrap_plot.png)

### 5. Bayesian (Beta-Binomial, uniform prior)
```
  P(treatment > control):     11.6%
  P(control > treatment):     88.4%
  Expected relative lift:     -1.20%
  95% credible interval:      [-0.3825%, +0.0937%]  (absolute)
```
![Bayes](plots/bayes.png)

## Conclusion

All three methods agree. The treatment converts slightly *less* than control, but the difference is well within noise: both intervals include 0 and the plausible lift is at most about +0.1 percentage points. **There is no evidence the new landing page improves conversion**, so it shouldn't be rolled out on conversion grounds alone.

Caveat: no power analysis is available for this dataset, so a true effect smaller than the interval width can't be ruled out.

## What changed in this version

A review of the original code fixed several correctness problems:

- **Bootstrap p-value was wrong.** It used `mean(boot_diff > observed)`, but the bootstrap distribution is centered on the observed value, so that is always ~0.5 regardless of the data. It now uses a two-sided p-value from the null-centered distribution.
- **Bayesian result was mislabeled.** `calc_prob_between(treatment, control)` returns P(treatment > control) = 11.6%, but it was reported as the probability of *losing*. The correct reading is 11.6% chance of winning, 88.4% of losing.
- **Bayesian probability** used a slow, numerically fragile closed-form sum; it's now a seeded Monte Carlo estimate, plus a credible interval.
- **Bayesian plot** showed variance as `±`; it now shows the standard deviation, and no longer depends on unused arguments.
- **Chi-square test applied Yates' correction implicitly** and relied on row order; replaced by an explicit two-proportion z-test with a CI for the lift.
- **Confidence intervals** used a t-interval on a binary metric; they now use the Wilson score interval.
- **SRM threshold** 0.005 → the conventional 0.001, and typo `treshold_p` → `threshold_p`.
- **Added a group/landing-page consistency check** that the original analysis lacked.
- Reproducible seeds, and all prints/plots/docstrings are in English.

## References
- [Trustworthy Online Controlled Experiments](https://www.amazon.com/Trustworthy-Online-Controlled-Experiments-Practical-ebook/dp/B0845Y3DJV): Kohavi, Tang, Xu
- [Detecting and avoiding bucket imbalance in A/B tests](https://blog.twitter.com/engineering/en_us/a/2015/detecting-and-avoiding-bucket-imbalance-in-ab-tests): Twitter Engineering
- [Bayesian A/B Testing with Python](https://towardsdatascience.com/bayesian-a-b-testing-with-python-the-easy-guide-d638f89e0b8a)
