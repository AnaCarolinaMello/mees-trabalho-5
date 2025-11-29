# Resumo da Implementação - Experimento GraphQL vs REST

## Arquivos Criados

### 1. Documentação

-**`Planing.md`**: Desenho completo do experimento com todas as definições necessárias

-**`README_EXPERIMENTO.md`**: Documentação completa do projeto

### 2. Scripts de Coleta e Execução

-**`experiment_collector.py`**: Script principal para coleta de dados do experimento

- Implementa medições de tempo e tamanho para GraphQL e REST
- Suporta 3 tipos de consultas (simples, complexa, múltiplos recursos)
- Executa 30 réplicas por combinação
- Salva resultados em CSV

-**`run_experiment.py`**: Script auxiliar para executar o experimento em etapas

- Interface interativa
- Verifica token do GitHub
- Permite executar coleta, análise ou dashboard separadamente

-**`generate_sample_data.py`**: Gera dados de exemplo para testes

- Útil para testar dashboard e análise sem executar experimento completo
- Simula dados realistas baseados em parâmetros configuráveis

### 3. Scripts de Análise

-**`experiment_analyzer.py`**: Análise estatística completa

- Teste de normalidade (Shapiro-Wilk)
- Teste t pareado ou Wilcoxon conforme necessário
- Cálculo de tamanho do efeito (Cohen's d)
- Análise por tipo de consulta
- Gera relatório em texto

### 4. Dashboard de Visualização

-**`dashboard.py`**: Gera visualizações completas

- Gráficos comparativos (boxplots, violin plots)
- Análise por tipo de consulta
- Scatter plots e histogramas
- Tabelas de estatísticas descritivas
- Exporta em PNG, CSV e HTML

## Estrutura do Experimento

### Variáveis Dependentes

1.**Tempo de Resposta (ms)**: Medido com `time.perf_counter()`

2.**Tamanho da Resposta (bytes)**: Inclui headers + body

### Variáveis Independentes

1.**Tipo de API**: GraphQL ou REST

2.**Tipo de Consulta**: simple, complex, multiple

### Design Experimental

-**Tipo**: Experimento controlado (Within-Subjects)

-**Repositórios**: 20 repositórios populares do GitHub

-**Réplicas**: 30 por combinação

-**Total**: ~3.600 medições

## Questões de Pesquisa

### RQ1: Tempo de Resposta

-**H₀**: Não há diferença significativa no tempo de resposta

-**H₁**: GraphQL é mais rápido que REST

-**Análise**: Teste t pareado ou Wilcoxon

### RQ2: Tamanho da Resposta

-**H₀**: Não há diferença significativa no tamanho

-**H₁**: GraphQL produz respostas menores

-**Análise**: Teste t pareado ou Wilcoxon

## Como Usar

### Execução Rápida

```bash

# 1. Configure o token

setGITHUB_TOKEN=seu_token


# 2. Execute o script principal

pythonrun_experiment.py


# 3. Escolha a opção desejada

```

### Execução Manual por Etapas

#### Coleta de Dados

```bash

pythonexperiment_collector.py

```

#### Análise Estatística

```bash

pythonexperiment_analyzer.py

```

#### *Dashboard*

```bash

pythondashboard.py

```

### Testes com Dados de Exemplo

```bash

# Gera dados simulados

pythongenerate_sample_data.py


# Testa análise

pythonexperiment_analyzer.py


# Testa dashboard

pythondashboard.py

```

## Saídas Geradas

### Dados

-`experiment_data.csv`: Dados brutos de todas as medições

### Análise

-`analysis_summary.txt`: Resumo estatístico das análises

### *Dashboard* (`dashboard_output/`)

-`response_time_comparison.png`: Comparação de tempo

-`response_size_comparison.png`: Comparação de tamanho

-`comparison_by_query_type.png`: Análise por tipo

-`scatter_comparison.png`: Relação tempo vs tamanho

-`summary_statistics.csv`: Tabela resumo

-`summary_statistics.html`: Tabela resumo HTML

-`detailed_statistics_by_query_type.csv`: Estatísticas detalhadas

## Dependências

Todas as dependências estão em `requirements.txt`:

- requests: Para requisições HTTP
- pandas: Manipulação de dados
- numpy: Cálculos numéricos
- matplotlib: Gráficos
- seaborn: Visualizações estatísticas
- scipy: Testes estatísticos

## Observações Importantes

1.**Rate Limiting**: O GitHub tem limites de requisições. O script inclui pausas, mas o experimento completo pode levar 1-2 horas.

2.**Token Necessário**: É obrigatório ter um token do GitHub com permissões `public_repo`.

3.**Equivalência de Consultas**: As consultas GraphQL e REST foram projetadas para retornar dados equivalentes, mas podem haver pequenas diferenças.

4.**Ambiente**: Os resultados podem variar com condições de rede e carga do servidor.

## Próximos Passos

1.**Executar Coleta**: Execute `experiment_collector.py` para coletar dados reais

2.**Analisar Resultados**: Execute `experiment_analyzer.py` para análise estatística

3.**Gerar Dashboard**: Execute `dashboard.py` para visualizações

4.**Documentar**: Use os resultados para escrever o relatório final