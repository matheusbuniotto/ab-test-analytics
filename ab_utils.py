import numpy as np
import scipy.stats as stats

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
