# Mini-Projeto 1 Avaliativo

Nome: Anderson Chrystian Borba

 ## 1. Descrição do projeto

Este projeto foi desenvolvido para simular uma atividade de Engenharia e Análise de Dados utilizando duas bases públicas da Olist: `olist_products_dataset.csv` e `olist_orders_dataset.csv`.

O objetivo é construir um pequeno pipeline de ETL (*Extract, Transform, Load*) utilizando somente recursos nativos do Python, sem bibliotecas externas como Pandas. O script realiza a leitura dos arquivos CSV, trata valores ausentes, padroniza textos, utiliza Expressões Regulares, formata datas e verifica uma hipótese de negócio relacionada aos pedidos que não possuem data de entrega.

O processamento foi dividido em funções para facilitar a leitura, manutenção e reutilização do código.

## 2. Tecnologias utilizadas

- Python 3
- `csv`
- `re`
- `datetime`
- `pathlib`
- Estruturas nativas do Python:
  - listas;
  - dicionários;
  - condicionais `if`, `elif` e `else`;
  - laços `for` e `while`;
  - funções com `def`;
  - função anônima `lambda`.

Não é necessário instalar nenhuma biblioteca adicional.

## 3. Estrutura do projeto

```text
MineProjeto1/
├── main.py
├── README.md
├── olist_products_dataset.csv
├── olist_orders_dataset.csv
└── saida/
    ├── olist_products_sanitizado.csv
    ├── olist_orders_sanitizado.csv
    ├── orders_entrega_nula.csv
    └── orders_entrega_nula_nao_cancelados.csv
```

A pasta `saida` é criada automaticamente na primeira execução.

## 4. Regras de tratamento implementadas

### 4.1 Produtos

Na tabela de produtos, a coluna `product_category_name` passa pelos seguintes tratamentos:

1. remoção de espaços no início e no fim com `.strip()`;
2. conversão para letras minúsculas com `.lower()`;
3. remoção de caracteres especiais por meio de Expressões Regulares (`re`);
4. substituição de valores nulos ou vazios por `sem categoria`.

As dimensões físicas analisadas são:

- `product_weight_g`;
- `product_length_cm`;
- `product_height_cm`;
- `product_width_cm`.

Para evitar a exclusão de produtos, os valores ausentes dessas colunas são preenchidos com a média dos valores válidos da própria coluna. A média é calculada manualmente, utilizando apenas laços, dicionários e operadores nativos do Python.

Essa decisão preserva os registros disponíveis na base. Em uma aplicação real, antes de utilizar a média seria importante estudar a distribuição dos dados e possíveis *outliers*, pois valores extremos podem influenciar esse tipo de imputação.

### 4.2 Pedidos

Na tabela de pedidos, o script verifica os registros que possuem `order_delivered_customer_date` vazia.

Esses registros são divididos em dois grupos:

- pedidos sem data de entrega com `order_status` igual a `canceled`;
- pedidos sem data de entrega com status diferente de `canceled`.

Dessa forma, o programa consegue testar diretamente a hipótese:

> Toda data de entrega nula ocorre obrigatoriamente porque o pedido foi cancelado?

O resultado da hipótese não é definido previamente no código. Ele é calculado a partir dos próprios registros do arquivo.

Os pedidos com entrega nula ficam disponíveis em:

```text
saida/orders_entrega_nula.csv
```

Os casos que contradizem a hipótese ficam separados em:

```text
saida/orders_entrega_nula_nao_cancelados.csv
```

Isso permite comprovar o resultado da análise diretamente pelos dados.

## 5. Formatação de datas

A coluna `order_approved_at` é lida originalmente no formato:

```text
2017-05-16 15:05:35
```

O módulo nativo `datetime` é utilizado para convertê-la para o padrão brasileiro:

```text
16/05/2017
```

A conversão é feita com:

```python
datetime.strptime()
```

e

```python
strftime()
```

## 6. Como executar

### Passo 1 – Baixar os arquivos CSV

Baixe os seguintes arquivos disponibilizados na base do projeto:

```text
olist_products_dataset.csv
olist_orders_dataset.csv
```

### Passo 2 – Colocar os arquivos na pasta do projeto

Os arquivos devem ficar no mesmo diretório do `main.py`:

```text
main.py
olist_products_dataset.csv
olist_orders_dataset.csv
README.md
```

### Passo 3 – Conferir a instalação do Python

No terminal, execute:

```bash
python --version
```

ou, dependendo do sistema:

```bash
python3 --version
```

### Passo 4 – Executar o projeto

Windows:

```bash
python main.py
```

Linux/macOS:

```bash
python3 main.py
```

### Passo 5 – Conferir o relatório

Ao final, o terminal apresenta um relatório com:

- total de produtos processados;
- categorias nulas corrigidas;
- dimensões físicas corrigidas;
- total de valores nulos tratados;
- médias calculadas para as dimensões;
- total de pedidos processados;
- total de pedidos cancelados;
- quantidade de datas de entrega nulas;
- quantidade de entregas nulas em pedidos cancelados;
- quantidade de entregas nulas em pedidos não cancelados;
- quantidade de datas de aprovação formatadas;
- resultado da hipótese de negócio.


## Resultados ao rodar o main.py:

<img width="1050" height="631" alt="saida execusaocerto" src="https://github.com/user-attachments/assets/ebb030b3-6eeb-4931-ac38-6997b1c0d81a" />

## Resultados obtidos com a base oficial

Após executar o script com os arquivos fornecidos para o mini-projeto, foram obtidos os seguintes resultados:

- **32.951 produtos** processados;
- **610 categorias vazias** substituídas por `sem categoria`;
- **8 valores nulos** encontrados nas dimensões físicas (2 em cada uma das quatro colunas);
- **4 pesos iguais a zero** também foram tratados como inconsistentes;
- **618 valores nulos corrigidos** no total nos produtos;
- **99.441 pedidos** processados;
- **625 pedidos cancelados** identificados;
- **2.965 pedidos** sem `order_delivered_customer_date`;
- desses, apenas **619** possuem status `canceled`;
- **2.346 pedidos** possuem entrega nula e status diferente de `canceled`;
- **99.281 datas de aprovação** foram convertidas para o padrão brasileiro;
- **160 pedidos** não possuem data de aprovação preenchida.

### Resultado da hipótese de negócio

A hipótese foi **refutada**. A ausência de `order_delivered_customer_date` não ocorre exclusivamente em pedidos cancelados. Entre os 2.965 pedidos sem data de entrega, existem registros com os seguintes status:

| Status | Quantidade sem data de entrega |
|---|---:|
| shipped | 1.107 |
| canceled | 619 |
| unavailable | 609 |
| invoiced | 314 |
| processing | 301 |
| delivered | 8 |
| created | 5 |
| approved | 2 |

Portanto, a regra “data de entrega nula significa obrigatoriamente pedido cancelado” não é válida para essa base. O arquivo `saida/orders_entrega_nula_nao_cancelados.csv` contém os **2.346 registros** que comprovam essa conclusão.

## 7. Reflexão teórica – qualidade dos dados e Machine Learning

A qualidade dos dados utilizados no treinamento influencia diretamente a capacidade de generalização de um modelo de Machine Learning. Valores ausentes, categorias escritas de formas diferentes, campos inválidos e inconsistências podem fazer com que o algoritmo aprenda padrões que não representam corretamente o problema real. A limpeza e a padronização reduzem esse ruído e tornam as variáveis mais consistentes antes da etapa de treinamento.

Esse processo também ajuda a reduzir vieses e resultados enganosos. Um modelo treinado com informações incorretas pode se ajustar excessivamente a erros presentes na amostra, contribuindo para *overfitting*, ou pode não encontrar relações importantes entre as variáveis, levando a um desempenho próximo de *underfitting*. Portanto, um pipeline de preparação bem definido não elimina sozinho esses problemas, mas cria uma base muito mais confiável para treinamento, validação e tomada de decisões com Inteligência Artificial.

## 8. Conclusão

O projeto demonstra que é possível realizar tarefas importantes de preparação de dados utilizando somente bibliotecas nativas do Python. Foram aplicados conceitos de leitura estruturada de CSV, tratamento de valores nulos, Regex, manipulação de strings, condicionais, laços, funções, dicionários, tratamento de dados numéricos e formatação temporal.

Além de gerar novas bases sanitizadas, o programa produz evidências para validar uma hipótese de negócio da Olist e apresenta um relatório estatístico manual ao final da execução.

