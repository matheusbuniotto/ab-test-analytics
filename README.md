# Análise de teste AB

### Definição do Problema
Nesse pequeno projeto serão utilizados os dados disponíveis no Kaggle, onde temos dados de um teste AB realizado entre 2 variações de uma landing page em um site confidencial. Para tornar o problema mais tangível, irei criar uma hipótese imaginária para tornar essa análise mais tangível. Para isso, suponhamos que recebemos a seguinte demanda do nosso product manager:
```
Olá, Matheus! 
Estou escrevendo para você hoje para discutir uma hipótese para um teste A/B em uma landing page de um website. A minha hipótese é que adicionar uma prova social à landing page aumentará a taxa de conversão.

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

Etapas:
- Definição do problema ✅
- Análise inicial dos dados ✅
- Entendimento das populações ✅
- Teste de SRM (Sample Ratio Missmatch), para detectar possíveis problemas com a distribuição das populações do teste. ✅
- Preparação dos dados (doing)
- Teste estatístico para validar ou invalidar a hipótese inicial
- Análise dos resultados
