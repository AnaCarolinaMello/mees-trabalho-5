# Desenho do Experimento: GraphQL vs REST

## 1. Hipóteses

### Hipótese Nula (H₀)
- **H₀₁**: Não há diferença significativa no tempo de resposta entre consultas GraphQL e REST.
- **H₀₂**: Não há diferença significativa no tamanho das respostas entre consultas GraphQL e REST.

### Hipótese Alternativa (H₁)
- **H₁₁**: Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST.
- **H₁₂**: Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST.

## 2. Variáveis Dependentes

1. **Tempo de Resposta (ms)**: Tempo decorrido desde o envio da requisição até o recebimento completo da resposta.
2. **Tamanho da Resposta (bytes)**: Tamanho total da resposta HTTP recebida, incluindo headers e body.

## 3. Variáveis Independentes

1. **Tipo de API**: GraphQL ou REST (fator com 2 níveis)
2. **Tipo de Consulta**: 
   - Consulta simples (dados básicos)
   - Consulta complexa (dados aninhados)
   - Consulta com múltiplos recursos
3. **Tamanho do Dataset**: Pequeno, Médio, Grande (baseado no número de registros retornados)

## 4. Tratamentos

### Tratamento 1: API GraphQL
- Endpoint: `https://api.github.com/graphql`
- Método: POST
- Headers: Authorization, Content-Type: application/json
- Body: Query GraphQL

### Tratamento 2: API REST
- Endpoint: `https://api.github.com/rest`
- Método: GET/POST (dependendo da operação)
- Headers: Authorization, Accept: application/vnd.github.v3+json
- Parâmetros: Query parameters ou path parameters

## 5. Objetos Experimentais

- **Repositórios GitHub**: Seleção de repositórios populares do GitHub
- **Consultas equivalentes**: Mesmas informações solicitadas via GraphQL e REST
- **Ambiente controlado**: Mesma máquina, mesma rede, mesmas condições

## 6. Tipo de Projeto Experimental

**Experimento Controlado (Within-Subjects Design)**
- Cada objeto experimental (repositório/consulta) é testado com ambos os tratamentos (GraphQL e REST)
- Ordem dos tratamentos randomizada para evitar efeitos de ordem
- Medições repetidas para cada combinação de tratamento e objeto experimental

## 7. Quantidade de Medições

- **Número de repositórios**: 20 repositórios
- **Número de consultas por repositório**: 3 tipos de consulta (simples, complexa, múltiplos recursos)
- **Número de réplicas por consulta**: 30 execuções
- **Total de medições**: 20 repositórios × 3 consultas × 2 tratamentos × 30 réplicas = **3.600 medições**

## 8. Ameaças à Validade

### 8.1 Ameaças à Validade Interna
- **Variação de carga do servidor**: O GitHub pode ter diferentes cargas em diferentes momentos
  - *Mitigação*: Executar medições em horários variados e calcular médias
- **Cache**: Respostas podem ser cacheadas
  - *Mitigação*: Incluir headers para evitar cache ou medir tempo incluindo cache
- **Latência de rede**: Variações na latência de rede podem afetar resultados
  - *Mitigação*: Executar múltiplas réplicas e calcular médias

### 8.2 Ameaças à Validade Externa
- **Generalização**: Resultados podem ser específicos para a API do GitHub
  - *Mitigação*: Documentar limitações e contexto do experimento
- **Escalabilidade**: Resultados podem variar com diferentes tamanhos de dataset
  - *Mitigação*: Testar com diferentes tamanhos de consulta

### 8.3 Ameaças à Validade de Construção
- **Equivalência das consultas**: Consultas GraphQL e REST podem não ser exatamente equivalentes
  - *Mitigação*: Garantir que ambas retornem os mesmos dados
- **Medição de tempo**: Pode incluir overhead de bibliotecas
  - *Mitigação*: Medir tempo de forma consistente para ambos os tratamentos

## 9. Critérios de Sucesso

- **RQ1**: Rejeitar H₀₁ se tempo médio GraphQL < tempo médio REST com p-value < 0.05
- **RQ2**: Rejeitar H₀₂ se tamanho médio GraphQL < tamanho médio REST com p-value < 0.05

## 10. Análise Estatística

- **Teste de normalidade**: Shapiro-Wilk ou Kolmogorov-Smirnov
- **Teste de comparação**: 
  - Se normal: Teste t pareado (paired t-test)
  - Se não normal: Teste de Wilcoxon (Wilcoxon signed-rank test)
- **Tamanho do efeito**: Cohen's d
- **Intervalos de confiança**: 95% de confiança

## 11. Ambiente Experimental

- **Sistema Operacional**: Windows 11
- **Linguagem**: Python 3.x
- **Bibliotecas**: requests, time, statistics, scipy, pandas
- **Rede**: Conexão estável à internet
- **API**: GitHub API v4 (GraphQL) e v3 (REST)


