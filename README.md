# Análise de teste AB
Nesse pequeno projeto serão utilizados os dados disponíveis no Kaggle, onde temos dados de um teste AB realizado entre 2 variações de uma landing page em um site confidencial. Para tornar o problema mais tangível, irei criar uma hipótese imaginária para tornar essa análise mais tangível. Então, suponhamos que recebemos a seguinte demanda do nosso product manager:

### Definição do Problema
```
Olá, Matheus! 
Estou escrevendo para você hoje para discutir uma hipótese para um teste A/B em uma landing page do nosso site.
A minha hipótese é que adicionar uma prova social à landing page aumentará a taxa de conversão.

Para testar essa hipótese, criarei duas versões da landing page: uma com uma prova social e outra sem. Vou distribuir as duas versões da landing page para um subconjunto dos nossos visitantes e comparar as taxas de conversão entre as duas versões.

Espero que a versão da landing page com a prova social tenha uma taxa de conversão mais alta do que a versão sem. Isso ocorre porque a prova social é uma forma de mostrar aos visitantes que outras pessoas já compraram o produto e gostaram dele. Isso pode ajudar a construir confiança e credibilidade com os visitantes, e fazê-los mais propensos a comprar também.

Aqui está um exemplo de como eu usaria a prova social nessa landing page:
"98% dos nossos clientes estão satisfeitos com o nosso produto."
"O nosso produto foi recomendado pela Forbes, a CNN e a The New York Times."
"Temos mais de 1 milhão de clientes satisfeitos."
Acredito que a prova social pode ser uma ferramenta poderosa para melhorar as taxas de conversão. Estou animado para testar essa hipótese e ver os resultados.
```

Bom, agora é a hora de destacar o que temos até então:

**Hipótese:**
Adicionar uma prova social à landing page aumentará a taxa de conversão.

**Teste:**
Vamos criar duas versões da landing page: uma com uma prova social e outra sem. Vamos distribuir as duas versões da landing page para um subconjunto de nossos visitantes e comparar as taxas de conversão entre as duas versões.

**Ganho esperado:**
Esperamos que a versão da landing page com a prova social tenha uma taxa de conversão mais alta do que a versão sem. Isso ocorre porque a prova social é uma forma de mostrar aos visitantes que outras pessoas já compraram o produto e gostaram dele. Isso pode ajudar a construir confiança e credibilidade com os visitantes, e fazê-los mais propensos a comprar também.


### Etapas:
- Definição do problema ✅
- Análise inicial dos dados ✅
- Entendimento das populações ✅
- Preparação dos dados ✅
- Teste de SRM (Sample Ratio Missmatch), para detectar possíveis problemas com a distribuição das populações do teste. ✅
- Testes estatístico para validar ou invalidar a hipótese inicial ✅
- Análise dos resultados 

### Análise e conclusões
#### 1. Entendimento dos dados
De início, vamos entender como os dados estão dispostos.
A tabela possui os seguintes campos:
```
Nome do dataframe: ab_df
 #   Column        Non-Null Count   Dtype  Descrição
---  ------        --------------   ----- 
 0   user_id       294478 non-null  int64  Representa o id único do usuário 
 1   timestamp     294478 non-null  object timestamp do momento do acesso do usuário
 2   group         294478 non-null  object grupo de segmentação do teste, podendo ser teste ou controle (treatment / control)
 3   landing_page  294478 non-null  object representa a landing page apresentada ao usuário, dado que é dependente do grupo em que ele se encontra
 4   converted     294478 non-null  int64  valor binário que informa se o usuário converteu ou não (1 ou 0)
```
Tamanho: (294478 linhas, 5 colunas)

Usando a função `ab_df.duplicated().sum()` temos 0 linhas duplicadas

Analisando os dados de maneira geral, estamos interessados em verificar se houve ou não um ganho na taxa de conversão da variante do tratamento, vamos observar em linhas gerais como está disposta a taxa de conversão em cada grupo e no geral.

```
Conversion Rate Geral:  0.1197
Conversion Rate Controle:  0.1204
Conversion Rate Tratamento:  0.1189
```

Anteriormente checamos se não havia nenhuma linha duplicada, agora vamos checar se não houve vazamento ou duplicação de usuários, já que 1 usuário só pode estar em 1 dos dois grupos (teste ou controle) e além disso, a modelagem de nossa tabela faz com que cada linha represente apenas um usuário, portanto vamos remover os usuários duplicados.

#### 2. Limpeza e preparação dos dados

`ab_df['user_id'].duplicated().sum()`
`ab_df['user_id'].duplicated().sum() / len(ab_df)`

Temos 3894 usuários duplicados em nosso dataset, representando cerca de 1,3% do total. Por conta do baixo volume e não termos acesso as regras de negócio/buckets que foram utilizadas no dataset disponibilizado, optei por remover esses usuários e criar um novo dataset sem eles.

```
### Cria lista com usuários duplicados (user_id)
ids_duplicados = ab_df['user_id'].value_counts().sort_values()

### Cria uma lista com os user_id com > 1 ocorrência
ids_duplicados = ids_duplicados[ids_duplicados.values > 1].index 

### Cria novo dataframe sem os usuários duplicados
ab_df_uniques = ab_df[ab_df["user_id"].isin(ids_duplicados) == False]

### Remove colunas desnecessárias para o teste
ab_df_uniques = ab_df_uniques.drop(columns="timestamp")`
```

#### 3. Teste de Sample Ratio Missmatch
Sample Ratio Mismatch, acontece em testes de hipóteses quando as amostras comparadas têm proporções diferentes entre os grupos, no nosso caso controle e tratamento. Isso pode afetar a validade dos resultados do teste. Por isso, é importante garantir que as amostras estejam balanceadsa e sejam representativas para obter conclusões confiáveis.

Para garantir que essas proporções estão balanceadas utilizarei a função que `Srm_test` que utiliza o qui-quadrado para medir se essa relação entre as amostras causa um impacto significativo no experimento:

```
# Roda a função para verificar o desbalanço entre grupos (Sample Ratio Missmatch)
srm_test(control_count, treatment_count, 0.005)

```
Diff. Entre Buckets: 104 usuários\
Ratio: 0.9993\
Chi-square: 0.0377\
P-value: 0.8460\
O teste é válido: valor-p > 0.005.


#### Testes estatísticos


### Referências
[Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing - Ron Kohavi (Author), Diane Tang (Author), Ya Xu (Author)](https://www.amazon.com/Trustworthy-Online-Controlled-Experiments-Practical-ebook/dp/B0845Y3DJV)
[Detecting and avoiding bucket imbalance in A/B tests - Twitter Engineering Blog](https://blog.twitter.com/engineering/en_us/a/2015/detecting-and-avoiding-bucket-imbalance-in-ab-tests)


