import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns

def srm_test(control_count: int, treatment_count: int, treshold_p: float):
    """
    Teste de SRM (Sample Ratio Missmatch):
    
    Realiza o teste Multinomial Goodness of Fit para verificar desequilíbrios entre os grupos de tratamento e controle.

    Parâmetros:
        control_count (int): Número de observações no grupo de controle.
        treatment_count (int): Número de observações no grupo de tratamento.
        treshold_p (float): Valor p máximo desejado.
    Retorna:
        None: A função printa o resultado do teste, incluindo a diferença entre os buckets,
              a razão entre controle e tratamento, o chi-quadrado e p-valor.
    
    """
    observed_counts = np.array([control_count, treatment_count])
    total_counts = observed_counts.sum()
    expected_counts = np.array([total_counts / 2, total_counts / 2])

    chi2, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)

    print(f"Diff. Entre Buckets: {control_count - treatment_count}")
    print(f"Ratio: {(control_count / treatment_count):.4f}")
    print(f"Chi-square: {chi2:.4f}")
    print(f"P-value: {p_value:.4f}")

    if p_value < treshold_p:
        print(f"O teste é inválido por conta de um desbalanço entre as populações. Valor-p > {treshold_p}")
    else:
        print(f"O teste é válido: valor-p < {treshold_p}.")



def calculate_ci(data, group_column, converted_column, confidence=0.95):
    """
    Calcula o intervalo de confiança para a média em cada grupo.

    Parâmetros:
        data (DataFrame): DataFrame contendo os dados.
        group_column (str): Nome da coluna com os buckets.
        convert_column (str): Nome da coluna que representa os dados de conversão (binário).
        confiança (float, opcional): Nível de confiança para o cálculo do intervalo. Por padrão deixamos em 0,95

    Retorna:
        DataFrame: DataFrame com os grupos, média dos dados convertidos, intervalos de confiança e porcentagens de erro.
    """
    result = []

    for group_name, group_data in data.groupby(group_column)[converted_column]:
        n = len(group_data)
        mean = group_data.mean()
        std_err = stats.sem(group_data)
        h = std_err * stats.t.ppf((1 + confidence) / 2, n - 1)

        lower_bound = mean - h
        upper_bound = mean + h

        result.append({
            'Group': group_name,
            'Mean Conversion Rate': round(mean, 4),
            'Confidence Interval': f"[{round(lower_bound, 4)} ({(lower_bound / mean - 1) * 100:.2f}%), {round(upper_bound, 4)} ({(upper_bound / mean - 1) * 100:.2f}%)]",
        })

    result_df = pd.DataFrame(result)
    return result_df




def perform_ab_test_analysis(data):
    """
    Realiza a análise de teste A/B para verificar se a diferença entre os grupos é estatisticamente diferente.

    Parâmetros:
        data: DataFrame com colunas group e converted representando os grupos dos buckets e a coluna binária de conversão.

    Retorna:
        DataFrame: DataFrame com os grupos, média dos dados convertidos, intervalos de confiança e porcentagens de erro.
        
        Nenhum: A função printa os resultados do teste, incluindo a estatística Qui-quadrado, valor-p e conclusão.
              Ele também printa as taxas de conversão, seus erros padrão correspondentes, erros máximos e mínimos para cada grupo.
              Além disso, ele plota as taxas de conversão para cada grupo com barras de erro.
    """

    # Cria tabela cruzada 
    cross_table = pd.crosstab(data['group'], data['converted'])

    # Realiza o teste chi2
    chi2_stat, p_value, dof, expected = stats.chi2_contingency(cross_table)


    # Printa os resultados 
    print(f"Chi-square statistic: {chi2_stat:.4f}")
    print(f"P-value: {p_value:.4f}")

    if p_value < 0.05:
        print("Os grupos possuem conversões estatisticamente diferentes.")
    else:
        print("Os grupos NÃO posuem conversões estatisticamente diferentes.")

    # Calcula a conversão e erro
    control_rate = cross_table.iloc[0, 1] / cross_table.iloc[0].sum()
    treatment_rate = cross_table.iloc[1, 1] / cross_table.iloc[1].sum()

    control_std = (control_rate * (1 - control_rate) / cross_table.iloc[0].sum()) ** 0.5
    treatment_std = (treatment_rate * (1 - treatment_rate) / cross_table.iloc[1].sum()) ** 0.5
    
    # Plota o gráfico de barras com erros
    plt.bar(['Control', 'Treatment'], [control_rate, treatment_rate], yerr=[control_std, treatment_std], capsize=10)
    plt.ylabel('Conversion Rate')
    plt.title('Conversion Rate - Controle vs Tratamento')
    plt.show()
    # Calcula o intervalo de confiança do erro
    return calculate_ci(data, "group", "converted")

    
    
def get_obbs_diff(boot_sample):
    control_sample = boot_sample[boot_sample['group'] == 'control']['converted']
    treatment_sample = boot_sample[boot_sample['group'] == 'treatment']['converted']
    boot_diff = treatment_sample.mean() - control_sample.mean()
    return boot_diff, control_sample.mean(), treatment_sample.mean()

def bootstrap_ab_test(ab_df_uniques, n_bootstraps=1000, confidence=0.95):
    """
    Realiza o teste Bootstrap A/B para verificar se a diferença entre os grupos é estatisticamente diferente.

    Parâmetros:
        ab_df_uniques (DataFrame): DataFrame contendo os dados únicos do usuário com as colunas 'grupo' e 'convertido'.
        n_bootstraps (int, opcional): Número de iterações de bootstrap. O padrão é 1000.
        confiança (float, opcional): Nível de confiança para o cálculo do intervalo. O padrão é 0,95.

    retorna:
        Nada: a função plota a distribuição Bootstrap da diferença entre os grupos de tratamento e controle
              e imprime o intervalo de confiança para as diferenças observadas.
              Ele também imprime o valor-p e conclui se o teste é estatisticamente diferente ou não.
    """

    boot_mean = []
    control_mean = []
    treatment_mean = []

    # Bootstrap Sampling to get the test statistic distribution
    for i in range(n_bootstraps):
        boot_sample = ab_df_uniques.sample(frac=1, replace=True)
        boot_diff, boot_mean_control, boot_mean_treatment = get_obbs_diff(boot_sample)
        boot_mean.append(boot_diff)
        control_mean.append(boot_mean_control)
        treatment_mean.append(boot_mean_treatment)

    # Calculate the confidence interval based on the desired percentage
    confidence_interval = np.percentile(boot_mean, [(1 - confidence) * 100 / 2, (1 + confidence) * 100 / 2])

    # Plota o gráfico normalizado das médias
    bootstrap_plot = pd.DataFrame({"controle": control_mean, "tratamento": treatment_mean})
    bootstrap_plot.plot(kind='kde')
    plt.show()

    
    # Calcula as diferenças observadas
    original_diff, original_mean_control, original_mean_treatment = get_obbs_diff(ab_df_uniques)

    # Calcula as diferenças entre 
    p_value = np.mean(np.array(boot_mean) > original_diff)

    print(f"Bootstrap Diferença Observada: {original_diff:.4f}")
    print(f"p-value: {p_value:.4f}")

    # Checa se o teste é valido de acordo com o valor p
    if p_value < (1 - confidence):
        print("Os grupos possuem conversões estatisticamente diferentes.")
    else:
        print("Os grupos NÃO posuem conversões estatisticamente diferentes.")
