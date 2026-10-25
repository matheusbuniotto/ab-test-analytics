# Análise de teste A/B com prova social em landing page

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Methodology](https://img.shields.io/badge/M%C3%A9todos-Frequentista%20%7C%20Bootstrap%20%7C%20Bayesiano-2B5C8F)
![tea-tasting](https://img.shields.io/badge/Valida%C3%A7%C3%A3o-tea--tasting-D95F02)
![cluster-experiments](https://img.shields.io/badge/Clusterizado%20%26%20Controle%20Sint%C3%A9tico-cluster--experiments-1B9E77)

[English version](README.md)

Este projeto executa uma análise completa de teste A/B sobre o [dataset público do Kaggle](https://www.kaggle.com/datasets/zhangluyuan/ab-testing) com 294.478 linhas. O repositório cobre planejamento pré-experimento, definição de métricas, auditoria de Erros Tipo M e Tipo S, limpeza de dados, verificação de Sample Ratio Mismatch, teste z frequentista, bootstrap não-paramétrico e inferência Bayesiana conjugada. Em seguida, valida os estimadores com [`tea-tasting`](https://github.com/e10v/tea-tasting) e simula experimentos com randomização por cluster e controle sintético usando [`cluster-experiments`](https://david26694.github.io/cluster-experiments/). Todos os gráficos seguem um layout unificado inspirado em ggplot2.

> **Resumo.** A nova landing page não aumentou a conversão. A taxa passou de `12.02%` no controle para `11.87%` no tratamento, uma diferença absoluta de `−0.14 pp` e relativa de `−1.20%`, com `p = 0.232`. Com 286.690 usuários únicos coletados em 22 dias, o teste tinha 80% de poder estatístico para detectar um efeito mínimo, ou MDE, de `±0.34 pp`, equivalente a `±2.84%` relativo. A distribuição posterior Bayesiana indica `11.6%` de probabilidade de o tratamento superar o controle. A recomendação é não implementar a mudança.

> [!NOTE]
> **Por que atualizei este repositório quatro anos depois.** Escrevi a primeira versão deste repositório há quase quatro anos como um estudo inicial de teste A/B no nível do usuário. Desde então, rodei e liderei times de Dados e Produto em centenas de experimentos em produção. Esta atualização incorpora o que mais fez diferença prática nessas revisões:
> - **Desenho pré-experimento.** Definir métrica primária de decisão, métricas secundárias diagnósticas e guardrails antes do lançamento. Escolher entre testes de superioridade e não-inferioridade conforme o objetivo do produto e dimensionar a amostra pelo MDE.
> - **Auditoria de Erros Tipo M e Tipo S.** Testes com baixo poder estatístico que cruzam `p < 0.05` exageram a magnitude do efeito real e podem inverter o sinal. A seção 0.4 aplica na prática o artigo que escrevi para o blog de Dados e Engenharia do Asaas, [*O Erro Secreto: O Erro Tipo M em Testes A/B*](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01).
> - **Validação com bibliotecas modernas e experimentos clusterizados.** Conferimos os estimadores e a curva de poder com [`tea-tasting`](https://github.com/e10v/tea-tasting) e modelamos randomização por lojas e controle sintético com [`cluster-experiments`](https://david26694.github.io/cluster-experiments/).

---

## Painel de resultados

| Etapa | Métrica | Resultado | Limiar ou intervalo de 95% | Veredito |
|---|---|---|---|---|
| **0. Planejamento** | MDE alvo e duração | `±0.34 pp`, `±2.84%` relativo | `N = 286.690`, 22 dias, `80%` poder, `α = 0.05` | **PRÉ-ESPECIFICADO** |
| **0.4 Erro Tipo M e S** | Exagero no MDE de `80%` vs `+0.5%` | `1.12×` no MDE, `4.84×` em `+0.5%` | Limita a inflação de magnitude a `1.12×` | **PROTEGIDO EM ≥2.84%** |
| **1. Higiene dos dados** | Linhas repetidas ou inconsistentes | `7.788` linhas, `2.64%` removidas | `0` inconsistências em `286.690` usuários | **PASS** |
| **2. Teste de SRM** | Divisão controle vs tratamento | `143.293` vs `143.397`, razão `0.9993` | `χ² = 0.0377`, `p = 0.8460`, limiar `0.001` | **PASS** |
| **3. Teste z frequentista** | Lift absoluto e relativo | `−0.14 pp`, `−1.20%` relativo | IC 95% `[−0.38 pp, +0.09 pp]`, `p = 0.2323` | **NÃO SIGNIFICATIVO** |
| **4. Bootstrap 10k** | Lift reamostrado | `−0.14 pp`, `−1.20%` relativo | IC 95% `[−0.39 pp, +0.09 pp]`, `p = 0.2324` | **NÃO SIGNIFICATIVO** |
| **5. Bayesiano Beta** | `P(Tratamento > Controle)` | `11.6%` vs `88.4%` controle | CrI 95% `[−0.38 pp, +0.09 pp]` | **NÃO LANÇAR** |
| **6. `tea-tasting` MDE** | Sensibilidade e curva de poder | `±0.34 pp`, `±2.84%` relativo | 80% de poder, bicaudal `α = 0.05` | **BEM DIMENSIONADO** |
| **7. OLS clusterizado** | Razão de erro padrão entre lojas | `EP = $2.92` vs naive `$0.64` | Razão de `4.5x`, `p = 0.5017` vs `0.0023` | **EVITA FALSO POSITIVO** |
| **8. Controle sintético** | Falso positivo com 1 cluster tratado | `0%` FPR, `100%` poder em `+10` | OLS clusterizado tem `75%` FPR em `efeito = 0` | **ESSENCIAL PARA N=1 CLUSTER** |

---

## Arquivos do repositório

| Arquivo | Descrição |
|---|---|
| [`analysis.ipynb`](analysis.ipynb) | Notebook executado com planejamento, auditoria Tipo M e Tipo S, testes estatísticos e gráficos |
| [`ab_utils.py`](ab_utils.py) | Funções para o tema ggplot2, teste de SRM, IC de Wilson, teste z, bootstrap, modelo Bayesiano, auditoria Tipo M e Tipo S, `tea-tasting` e `cluster-experiments` |
| `plots/*.png` | Sete gráficos diagnósticos de dois painéis estilo ggplot2 |
| `data/ab_data.csv` | Log bruto do experimento com `user_id`, `timestamp`, `group`, `landing_page` e `converted` |
| [`README.md`](README.md) | Documentação principal em inglês |

## Como executar

```bash
pip install -r requirements.txt
jupyter notebook analysis.ipynb
```

Você também pode chamar as funções diretamente em Python:

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

srm_test(control_count, treatment_count)
perform_ab_test_analysis(df)
bootstrap_ab_test(df)
bayesian_ab_test(df)
compare_with_tea_tasting(df)
analyze_type_m_s_errors(df)
run_cluster_randomization_example()
run_synthetic_control_example()
```

---

## Parte I. Experimento da landing page no nível do usuário

### 0. Fase de planejamento do experimento

Antes de escrever o código de análise, traduzimos o pedido do gerente de produto em uma especificação pré-registrada:

```text
Olá, Matheus!
Gostaria de testar uma hipótese na nossa landing page: adicionar prova social ("98% dos nossos
clientes estão satisfeitos", "Recomendado pela Forbes, CNN e The New York Times", "Mais de 1 milhão
de clientes satisfeitos") vai aumentar a confiança dos visitantes e elevar a taxa de conversão.

Para testar essa hipótese, vamos dividir os visitantes 50/50 entre a página atual (controle) e a
nova versão com prova social (tratamento) e comparar as taxas de conversão.
```

Seguindo Kohavi et al. em *Trustworthy Online Controlled Experiments* e Georgiev em *Statistical Methods in Online A/B Testing*, o plano define as métricas, o tipo de hipótese e o tamanho amostral antes do início do tráfego.

#### 0.1 Hierarquia de métricas

O arquivo público do Kaggle traz apenas a coluna binária `converted`, mas um teste em produção acompanha três grupos de métricas:

- **Métrica primária de decisão.** A taxa de conversão por usuário único, registrada em `converted`, define se a hipótese foi validada.
- **Métricas secundárias diagnósticas.** Taxa de clique no botão principal, profundidade de scroll até a seção de prova social e tempo até a conversão ajudam a explicar por que a conversão subiu ou ficou estável.
- **Métricas de guardrail.** Guardrails de sistema monitoram Sample Ratio Mismatch, latência p95 de carregamento da página e taxa de erro no cliente, já que imagens ou scripts extras podem atrasar a renderização. Guardrails de negócio monitoram bounce rate, taxa de cancelamento ou estorno e ticket médio para evitar que o apelo de prova social traga cadastros de baixa retenção.

#### 0.2 Escolha entre teste de superioridade e não-inferioridade

O objetivo de produto define as hipóteses nula e alternativa:

- **Teste de superioridade.** Quando uma mudança adiciona custo de manutenção ou elementos visuais à página, só implementamos se o tratamento superar o controle, testando $H_0: \Delta = 0$ contra $H_1: \Delta \neq 0$, ou unilateral $H_1: \Delta > 0$.
- **Teste de não-inferioridade.** Quando a nova página é necessária por rebranding, exigência regulatória ou migração de frontend, ela não precisa aumentar a conversão. Basta provar que ela não reduz a conversão além de uma margem pré-acordada $-\Delta_{\text{NI}}$, testando $H_0: p_T - p_C \le -\Delta_{\text{NI}}$ contra $H_1: p_T - p_C > -\Delta_{\text{NI}}$. Com o nosso intervalo de confiança de 95% observado em `[−0.38 pp, +0.09 pp]`, a nova página falha no teste de superioridade e só passaria em não-inferioridade se o time aceitasse uma queda de pelo menos `−0.40 pp`, ou `−3.3%` relativo.

#### 0.3 Definição do MDE e tamanho amostral

O Efeito Mínimo Detectável, ou MDE, é o menor ganho real que justifica o lançamento com 80% de poder estatístico, $1 - \beta = 0.80$, e 5% de nível de significância, $\alpha = 0.05$. O time escolhe o MDE no planejamento equilibrando retorno de negócio e volume de tráfego, que neste dataset é de 13.031 usuários limpos por dia sobre uma conversão base de `12.0%`:

| MDE relativo alvo | Lift absoluto $\Delta$ | Amostra total necessária $N$ | Duração estimada a 13k usuários/dia | Trade-off prático |
|---|---|---|---|---|
| **±1.00%** | `±0.12 pp` | `2.312.270` | 177 dias, 25 semanas | Lento demais para ajuste de copy sem redução de variância via CUPED |
| **±2.00%** | `±0.24 pp` | `580.545` | 45 dias, 6,5 semanas | Alta precisão, duração moderada |
| **±2.84%, este dataset** | **`±0.34 pp`** | **`286.690`** | **22 dias, 3 semanas completas** | **Cobre 3 ciclos semanais e detecta ≥2.84% com 80% de poder** |
| **±5.00%** | `±0.60 pp` | `94.072` | 7,2 dias, 1 semana completa | Triagem rápida para mudanças grandes de layout |
| **±10.00%** | `±1.20 pp` | `24.007` | 2 dias, estender para 7 dias | Sempre rodar ao menos uma semana inteira para capturar dias úteis e fim de semana |

> [!IMPORTANT]
> **Por que calculamos o MDE de sensibilidade retrospectiva em vez de poder observado pós-teste.** Georgiev demonstra que substituir o efeito ruidoso observado de `−0.14 pp` na fórmula de poder após o término do teste não traz informação nova, pois o poder pós-hoc é apenas uma função direta do valor-p. Ao auditar um dataset histórico com $N = 286.690$, calculamos o MDE de sensibilidade de `±0.34 pp`, ou `±2.84%` relativo, para saber qual tamanho de efeito a amostra conseguia detectar com 80% de poder. Como `±2.84%` é menor que o ganho de 3% a 5% normalmente exigido em mudanças de landing page, o resultado não-significativo com `p = 0.232` representa uma ausência de efeito bem dimensionada.

#### 0.4 Erros Tipo M de magnitude e Tipo S de sinal

Cálculos tradicionais de amostra olham apenas para os Erros Tipo I, $\alpha$, e Tipo II, $\beta$. Na prática, um dos erros mais caros em experimentação acontece quando um teste com baixo poder estatístico cruza $p < 0.05$ por sorte. Detalhei esse mecanismo no artigo que escrevi para o blog de Dados e Engenharia do Asaas, [*O Erro Secreto: O Erro Tipo M em Testes A/B*](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01), com base em Gelman e Carlin de 2014:

1. **Erro Tipo M, fator de exagero $\mathbb{E}[|\hat{\Delta}| \mid p < 0.05] / |\Delta_{\text{real}}|$.** Um teste bicaudal com $\alpha = 0.05$ só declara significância quando a estimativa supera $1.96 \times \text{EP}$, o que equivale a `±1.98%` relativo neste dataset. Se o efeito verdadeiro de uma feature for pequeno, como `+0.50%`, a única forma de o teste atingir $p < 0.05$ é contar com um pico de ruído amostral que jogue a estimativa acima de `+1.98%`. Condicionado a ser estatisticamente significativo, o ganho reportado será sempre inflado, com média de **4.84×** o efeito real em `+0.50%` e **9.52×** em `+0.25%`. Times que somam esses ganhos inflados nas metas financeiras nunca veem esse resultado chegar ao P&L.
2. **Erro Tipo S, probabilidade de sinal trocado $P(\text{sinal oposto} \mid p < 0.05)$.** Quando o poder estatístico é muito baixo, um resultado significativo também pode apontar na direção oposta ao efeito real. Para um efeito verdadeiro de `+0.25%`, **23.92%** dos resultados estatisticamente significativos têm sinal negativo.

A função `analyze_type_m_s_errors(ab_clean)` calcula as taxas exatas de Erro Tipo M e Tipo S para o erro padrão relativo do nosso experimento de $\text{EP}_{\text{rel}} = 1.01\%$:

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
![Erros Tipo M e Tipo S](plots/type_m_s_errors.png)

Dimensionar o experimento para 80% de poder no MDE de `+2.84%` reduz o fator de exagero do Erro Tipo M para `1.12×` e derruba o Erro Tipo S para `0.00%`.

---

### 1. Higiene dos dados e consistência das variantes

A tabela bruta tem 294.478 linhas registradas entre `2017-01-02` e `2017-01-24`, sem valores nulos e sem linhas duplicadas. Porém, 3.894 valores de `user_id` aparecem mais de uma vez, somando 7.788 linhas, ou `2.64%` do total. Entre esses usuários repetidos, 1.895 passaram tanto por `control` quanto por `treatment`, e 3.893 linhas apresentam divergência entre `group` e `landing_page`.

Como o dataset não informa a regra de atribuição para escolher qual linha manter, removemos todas as ocorrências de qualquer `user_id` repetido. Isso elimina todas as 3.893 divergências e preserva **286.690 usuários únicos**:

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

### 2. Verificação de Sample Ratio Mismatch

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

### 3. Teste z frequentista de duas proporções e intervalos de Wilson

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
![Taxa de conversão e lift frequentista](plots/conversion_ci.png)

### 4. Bootstrap não-paramétrico com 10.000 reamostragens

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
![Distribuições bootstrap](plots/bootstrap_plot.png)

### 5. Inferência Bayesiana com modelo conjugado Beta-Binomial

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
![Posteriores Bayesianas](plots/bayes.png)

### 6. Validação cruzada e curva de poder com `tea-tasting`

Executamos o [`tea-tasting`](https://github.com/e10v/tea-tasting) usando `SampleRatio`, `Proportion` e `Mean` sobre a mesma base limpa para conferir as estimativas e calcular o MDE com 80% de poder em `α = 0.05`:

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
![Validação tea-tasting e curva de poder](plots/tea_tasting_power.png)

---

## Parte II. Experimentos clusterizados e controle sintético com `cluster-experiments`

A randomização por usuário falha quando o tratamento de um indivíduo afeta outros no mesmo mercado ou quando a operação exige ativar lojas, cidades ou regiões inteiras de uma só vez. Quando o sorteio ocorre por cluster, as transações dentro do mesmo cluster são correlacionadas. Ignorar essa correlação subestima o erro padrão e infla os falsos positivos.

### 7. Randomização por cluster comparando OLS naive e OLS clusterizado

Seguindo o [guia de randomização por cluster do `cluster-experiments`](https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html), simulamos 50 lojas sorteadas entre controle e tratamento com efeito real de `+$5` e variação entre lojas de `DP = $10` ao longo de 4.823 transações. O OLS naive trata as 4.823 transações como independentes, subestima o erro padrão em **4.5x** e acusa um falso positivo com `p = 0.0023`. O OLS clusterizado agrupa o erro padrão por `store_id` e retorna `p = 0.5017`:

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
![Randomização por cluster](plots/cluster_randomization.png)

### 8. Controle sintético vs OLS clusterizado com um único cluster tratado

Seguindo o [guia de controle sintético do `cluster-experiments`](https://david26694.github.io/cluster-experiments/synthetic_control.html), simulamos 18 clusters durante 30 dias onde apenas **um cluster** recebe o tratamento a partir do dia 15. Com apenas uma unidade tratada, o estimador de variância robusta por cluster falha e o OLS clusterizado apresenta **75% de falsos positivos** quando `efeito = 0`. O controle sintético ajusta pesos sobre os clusters doadores no período pré-intervenção, mantendo os falsos positivos em **0%** quando `efeito = 0` e atingindo **100% de poder** para efeitos reais a partir de `+10`:

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
![Controle sintético](plots/synthetic_control.png)

---

## Referências

- Matheus Buniotto, [O Erro Secreto: O Erro Tipo M em Testes A/B](https://medium.com/estacao-asaas/o-erro-secreto-o-erro-tipo-m-em-testes-a-b-e5593833bc01), *Estação Asaas / Blog de Dados e Engenharia do Asaas*.
- Ron Kohavi, Diane Tang e Ya Xu, [Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing](https://www.amazon.com/Trustworthy-Online-Controlled-Experiments-Practical-ebook/dp/B0845Y3DJV).
- Georgi Z. Georgiev, [Statistical Methods in Online A/B Testing: Statistics for data-driven business decisions and risk management in e-commerce](https://www.amazon.com/Statistical-Methods-Online-Testing-data-driven/dp/1694079725).
- Andrew Gelman e John Carlin, 2014, [Beyond Power Calculations: Assessing Type S and Type M Errors](https://doi.org/10.1177/1745691614551642).
- Evgeny Ivanov, [`tea-tasting`: statistical analysis of A/B tests in Python](https://github.com/e10v/tea-tasting).
- David Masip, [`cluster-experiments`: Cluster Randomization](https://david26694.github.io/cluster-experiments/examples/cluster_randomization.html) e [Synthetic Control](https://david26694.github.io/cluster-experiments/synthetic_control.html).
- Twitter Engineering, [Detecting and avoiding bucket imbalance in A/B tests](https://blog.twitter.com/engineering/en_us/a/2015/detecting-and-avoiding-bucket-imbalance-in-ab-tests).
