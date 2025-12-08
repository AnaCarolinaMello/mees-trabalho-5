#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para geração de relatório técnico do experimento GraphQL vs REST
Baseado no modelo de relatório de laboratório e nos dados experimentais coletados
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import base64
import io
from scipy import stats
from scipy.stats import shapiro, wilcoxon, ttest_rel
import warnings
warnings.filterwarnings('ignore')

class GraphQLvsRESTReportGenerator:
    def __init__(self, csv_file="experiment_data.csv"):
        """Inicializa o gerador de relatório"""
        self.csv_file = csv_file
        self.df = None
        self.analysis_results = {}

    def load_data(self):
        """Carrega e processa os dados do CSV"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"Dados carregados: {len(self.df)} medições")

            # Filtra apenas medições bem-sucedidas
            self.df = self.df[self.df['success'] == True].copy()
            print(f"Medições bem-sucedidas: {len(self.df)}")

            # Converte tipos
            self.df['response_time_ms'] = pd.to_numeric(self.df['response_time_ms'], errors='coerce')
            self.df['response_size_bytes'] = pd.to_numeric(self.df['response_size_bytes'], errors='coerce')

            return True
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False

    def test_normality(self, data: pd.Series):
        """Testa normalidade dos dados usando Shapiro-Wilk"""
        if len(data) < 3:
            return False, 1.0

        sample = data.sample(min(5000, len(data))) if len(data) > 5000 else data

        try:
            stat, p_value = shapiro(sample)
            is_normal = p_value > 0.05
            return is_normal, p_value
        except:
            return False, 0.0

    def analyze_rq1(self):
        """Analisa RQ1: Tempo de Resposta"""
        results = []

        for (repo_owner, repo_name, query_type), group in self.df.groupby(['repository_owner', 'repository_name', 'query_type']):
            graphql_times = group[group['api_type'] == 'graphql']['response_time_ms'].values
            rest_times = group[group['api_type'] == 'rest']['response_time_ms'].values

            if len(graphql_times) > 0 and len(rest_times) > 0:
                results.append({
                    'repository': f"{repo_owner}/{repo_name}",
                    'query_type': query_type,
                    'graphql_mean': np.mean(graphql_times),
                    'rest_mean': np.mean(rest_times),
                    'difference': np.mean(graphql_times) - np.mean(rest_times)
                })

        all_graphql_times = self.df[self.df['api_type'] == 'graphql']['response_time_ms'].values
        all_rest_times = self.df[self.df['api_type'] == 'rest']['response_time_ms'].values

        graphql_stats = {
            'mean': np.mean(all_graphql_times),
            'median': np.median(all_graphql_times),
            'std': np.std(all_graphql_times),
            'min': np.min(all_graphql_times),
            'max': np.max(all_graphql_times),
            'count': len(all_graphql_times)
        }

        rest_stats = {
            'mean': np.mean(all_rest_times),
            'median': np.median(all_rest_times),
            'std': np.std(all_rest_times),
            'min': np.min(all_rest_times),
            'max': np.max(all_rest_times),
            'count': len(all_rest_times)
        }

        graphql_normal, graphql_p = self.test_normality(pd.Series(all_graphql_times))
        rest_normal, rest_p = self.test_normality(pd.Series(all_rest_times))

        paired_differences = [r['difference'] for r in results]

        if len(paired_differences) > 1:
            if graphql_normal and rest_normal:
                t_stat, p_value = ttest_rel(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results]
                )
                test_name = "Teste t pareado"
            else:
                t_stat, p_value = wilcoxon(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results],
                    alternative='two-sided'
                )
                test_name = "Teste de Wilcoxon"

            mean_diff = np.mean(paired_differences)
            std_diff = np.std(paired_differences)
            cohens_d = mean_diff / std_diff if std_diff > 0 else 0

            if p_value < 0.05:
                if mean_diff < 0:
                    conclusion = "GraphQL é significativamente mais rápido que REST"
                else:
                    conclusion = "REST é significativamente mais rápido que GraphQL"
            else:
                conclusion = "Não há diferença significativa entre GraphQL e REST"
        else:
            p_value = 1.0
            conclusion = "Dados insuficientes"
            cohens_d = 0.0
            test_name = 'N/A'

        return {
            'graphql_stats': graphql_stats,
            'rest_stats': rest_stats,
            'test_name': test_name,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'conclusion': conclusion,
            'graphql_normal': graphql_normal,
            'rest_normal': rest_normal,
            'graphql_p': graphql_p,
            'rest_p': rest_p
        }

    def analyze_rq2(self):
        """Analisa RQ2: Tamanho da Resposta"""
        results = []

        for (repo_owner, repo_name, query_type), group in self.df.groupby(['repository_owner', 'repository_name', 'query_type']):
            graphql_sizes = group[group['api_type'] == 'graphql']['response_size_bytes'].values
            rest_sizes = group[group['api_type'] == 'rest']['response_size_bytes'].values

            if len(graphql_sizes) > 0 and len(rest_sizes) > 0:
                results.append({
                    'repository': f"{repo_owner}/{repo_name}",
                    'query_type': query_type,
                    'graphql_mean': np.mean(graphql_sizes),
                    'rest_mean': np.mean(rest_sizes),
                    'difference': np.mean(graphql_sizes) - np.mean(rest_sizes)
                })

        all_graphql_sizes = self.df[self.df['api_type'] == 'graphql']['response_size_bytes'].values
        all_rest_sizes = self.df[self.df['api_type'] == 'rest']['response_size_bytes'].values

        graphql_stats = {
            'mean': np.mean(all_graphql_sizes),
            'median': np.median(all_graphql_sizes),
            'std': np.std(all_graphql_sizes),
            'min': np.min(all_graphql_sizes),
            'max': np.max(all_graphql_sizes),
            'count': len(all_graphql_sizes)
        }

        rest_stats = {
            'mean': np.mean(all_rest_sizes),
            'median': np.median(all_rest_sizes),
            'std': np.std(all_rest_sizes),
            'min': np.min(all_rest_sizes),
            'max': np.max(all_rest_sizes),
            'count': len(all_rest_sizes)
        }

        graphql_normal, graphql_p = self.test_normality(pd.Series(all_graphql_sizes))
        rest_normal, rest_p = self.test_normality(pd.Series(all_rest_sizes))

        paired_differences = [r['difference'] for r in results]

        if len(paired_differences) > 1:
            if graphql_normal and rest_normal:
                t_stat, p_value = ttest_rel(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results]
                )
                test_name = "Teste t pareado"
            else:
                t_stat, p_value = wilcoxon(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results],
                    alternative='two-sided'
                )
                test_name = "Teste de Wilcoxon"

            mean_diff = np.mean(paired_differences)
            std_diff = np.std(paired_differences)
            cohens_d = mean_diff / std_diff if std_diff > 0 else 0

            if p_value < 0.05:
                if mean_diff < 0:
                    conclusion = "GraphQL produz respostas significativamente menores que REST"
                else:
                    conclusion = "REST produz respostas significativamente menores que GraphQL"
            else:
                conclusion = "Não há diferença significativa entre GraphQL e REST"
        else:
            p_value = 1.0
            conclusion = "Dados insuficientes"
            cohens_d = 0.0
            test_name = 'N/A'

        return {
            'graphql_stats': graphql_stats,
            'rest_stats': rest_stats,
            'test_name': test_name,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'conclusion': conclusion,
            'graphql_normal': graphql_normal,
            'rest_normal': rest_normal,
            'graphql_p': graphql_p,
            'rest_p': rest_p
        }

    def analyze_by_query_type(self):
        """Analisa resultados por tipo de consulta"""
        results_by_type = {}

        for query_type in ['simple', 'complex', 'multiple']:
            type_data = self.df[self.df['query_type'] == query_type]

            if len(type_data) > 0:
                graphql_times = type_data[type_data['api_type'] == 'graphql']['response_time_ms'].values
                rest_times = type_data[type_data['api_type'] == 'rest']['response_time_ms'].values

                graphql_sizes = type_data[type_data['api_type'] == 'graphql']['response_size_bytes'].values
                rest_sizes = type_data[type_data['api_type'] == 'rest']['response_size_bytes'].values

                results_by_type[query_type] = {
                    'graphql_time_mean': np.mean(graphql_times) if len(graphql_times) > 0 else 0,
                    'rest_time_mean': np.mean(rest_times) if len(rest_times) > 0 else 0,
                    'graphql_size_mean': np.mean(graphql_sizes) if len(graphql_sizes) > 0 else 0,
                    'rest_size_mean': np.mean(rest_sizes) if len(rest_sizes) > 0 else 0,
                }

        return results_by_type

    def generate_visualizations(self):
        """Gera visualizações dos dados"""
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')

        plt.rcParams['font.family'] = ['DejaVu Sans']

        # 1. Boxplot - Comparação de tempo de resposta
        plt.figure(figsize=(10, 6))
        graphql_times = self.df[self.df['api_type'] == 'graphql']['response_time_ms']
        rest_times = self.df[self.df['api_type'] == 'rest']['response_time_ms']

        plt.boxplot([graphql_times, rest_times], labels=['GraphQL', 'REST'])
        plt.title('Comparação de Tempo de Resposta: GraphQL vs REST', fontsize=14, fontweight='bold')
        plt.ylabel('Tempo de Resposta (ms)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_tempo_resposta.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2. Boxplot - Comparação de tamanho de resposta
        plt.figure(figsize=(10, 6))
        graphql_sizes = self.df[self.df['api_type'] == 'graphql']['response_size_bytes']
        rest_sizes = self.df[self.df['api_type'] == 'rest']['response_size_bytes']

        plt.boxplot([graphql_sizes, rest_sizes], labels=['GraphQL', 'REST'])
        plt.title('Comparação de Tamanho da Resposta: GraphQL vs REST', fontsize=14, fontweight='bold')
        plt.ylabel('Tamanho da Resposta (bytes)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_tamanho_resposta.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 3. Gráfico de barras - Comparação por tipo de consulta
        by_type = self.analyze_by_query_type()

        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        query_types = list(by_type.keys())
        graphql_times_by_type = [by_type[qt]['graphql_time_mean'] for qt in query_types]
        rest_times_by_type = [by_type[qt]['rest_time_mean'] for qt in query_types]

        x = np.arange(len(query_types))
        width = 0.35

        axes[0].bar(x - width/2, graphql_times_by_type, width, label='GraphQL', color='skyblue')
        axes[0].bar(x + width/2, rest_times_by_type, width, label='REST', color='lightcoral')
        axes[0].set_xlabel('Tipo de Consulta')
        axes[0].set_ylabel('Tempo Médio (ms)')
        axes[0].set_title('Tempo de Resposta por Tipo de Consulta')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels([qt.capitalize() for qt in query_types])
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        graphql_sizes_by_type = [by_type[qt]['graphql_size_mean'] for qt in query_types]
        rest_sizes_by_type = [by_type[qt]['rest_size_mean'] for qt in query_types]

        axes[1].bar(x - width/2, graphql_sizes_by_type, width, label='GraphQL', color='skyblue')
        axes[1].bar(x + width/2, rest_sizes_by_type, width, label='REST', color='lightcoral')
        axes[1].set_xlabel('Tipo de Consulta')
        axes[1].set_ylabel('Tamanho Médio (bytes)')
        axes[1].set_title('Tamanho da Resposta por Tipo de Consulta')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([qt.capitalize() for qt in query_types])
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('grafico_por_tipo.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 4. Histograma - Distribuição de tempo
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        axes[0].hist(graphql_times, bins=30, alpha=0.7, color='skyblue', edgecolor='black', label='GraphQL')
        axes[0].hist(rest_times, bins=30, alpha=0.7, color='lightcoral', edgecolor='black', label='REST')
        axes[0].set_xlabel('Tempo de Resposta (ms)')
        axes[0].set_ylabel('Frequência')
        axes[0].set_title('Distribuição de Tempo de Resposta')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        axes[1].hist(graphql_sizes, bins=30, alpha=0.7, color='skyblue', edgecolor='black', label='GraphQL')
        axes[1].hist(rest_sizes, bins=30, alpha=0.7, color='lightcoral', edgecolor='black', label='REST')
        axes[1].set_xlabel('Tamanho da Resposta (bytes)')
        axes[1].set_ylabel('Frequência')
        axes[1].set_title('Distribuição de Tamanho da Resposta')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('grafico_histogramas.png', dpi=300, bbox_inches='tight')
        plt.close()

        print("Visualizações geradas com sucesso!")

    def image_to_base64(self, image_path):
        """Converte imagem para base64 para embedding"""
        try:
            with open(image_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def generate_markdown_report(self):
        """Gera o relatório completo em Markdown"""
        rq1_results = self.analyze_rq1()
        rq2_results = self.analyze_rq2()
        by_type = self.analyze_by_query_type()

        # Conta repositórios únicos
        unique_repos = self.df[['repository_owner', 'repository_name']].drop_duplicates()
        num_repos = len(unique_repos)

        report = f"""# GraphQL vs REST - Um Experimento Controlado

## 1. Informações do Grupo

- **Curso:** Engenharia de Software
- **Disciplina:** Laboratório de Experimentação de Software
- **Período:** 6° Período
- **Professor(a):** Prof. Dr. João Paulo Carneiro Aramuni
- **Membros do Grupo:** [Nome dos membros do grupo]

---

## 2. Introdução

A linguagem de consulta GraphQL, proposta pelo Facebook como metodologia de implementação de APIs Web, representa uma alternativa às populares APIs REST. Baseada em grafos, a linguagem permite que usuários consultem banco de dados na forma de schemas, de modo que se possa exportar a base e realizar consultas num formato definido pelo fornecedor da API. Por outro lado, APIs criados com base em abordagens REST baseiam-se em endpoints: operações pré-definidas que podem ser chamadas por clientes que desejam consultar, deletar, atualizar ou escrever um dado na base.

Desde o seu surgimento, vários sistemas realizaram a migração entre ambas as soluções, mantendo soluções compatíveis REST, mas oferecendo os benefícios da nova linguagem de consulta proposta. Entretanto, não está claro quais os reais benefícios da adoção de uma API GraphQL em detrimento de uma API REST.

Nesse contexto, o objetivo deste laboratório é realizar um experimento controlado para avaliar quantitativamente os benefícios da adoção de uma API GraphQL. Foram analisados **{len(self.df)} medições** em **{num_repos} repositórios** do GitHub, comparando as APIs GraphQL e REST em termos de tempo de resposta e tamanho das respostas.

### 2.1 Questões de Pesquisa

Este experimento busca responder as seguintes perguntas:

**RQ1.** Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST?

**RQ2.** Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST?

---

## 3. Metodologia

### 3.1 Desenho do Experimento

#### A. Hipóteses Nula e Alternativa

**Para RQ1 (Tempo de Resposta):**
- **H₀₁:** Não há diferença significativa no tempo de resposta entre consultas GraphQL e REST.
- **H₁₁:** Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST.

**Para RQ2 (Tamanho da Resposta):**
- **H₀₂:** Não há diferença significativa no tamanho das respostas entre consultas GraphQL e REST.
- **H₁₂:** Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST.

#### B. Variáveis Dependentes

1. **Tempo de Resposta (ms):** Tempo decorrido desde o envio da requisição até o recebimento completo da resposta.
2. **Tamanho da Resposta (bytes):** Tamanho total da resposta HTTP recebida, incluindo headers e body.

#### C. Variáveis Independentes

1. **Tipo de API:** GraphQL ou REST (fator com 2 níveis)
2. **Tipo de Consulta:**
   - Consulta simples (dados básicos do repositório)
   - Consulta complexa (dados aninhados com issues e pull requests)
   - Consulta com múltiplos recursos (repositório + contribuidores)

#### D. Tratamentos

**Tratamento 1: API GraphQL**
- Endpoint: `https://api.github.com/graphql`
- Método: POST
- Headers: Authorization (Bearer token), Content-Type: application/json
- Body: Query GraphQL personalizada

**Tratamento 2: API REST**
- Endpoint: `https://api.github.com/repos/{{owner}}/{{repo}}`
- Método: GET
- Headers: Authorization (Bearer token), Accept: application/vnd.github.v3+json
- Parâmetros: Query parameters conforme necessário

#### E. Objetos Experimentais

O objeto dessa pesquisa é comparar a eficiência entre as APIs GraphQL e REST do GitHub. Foram utilizados **{num_repos} repositórios populares** do GitHub como objetos experimentais.

#### F. Tipo de Projeto Experimental

**Experimento Controlado Within-Subjects (Medidas Repetidas)**

- Cada repositório foi testado com ambos os tratamentos (GraphQL e REST)
- Ordem dos tratamentos randomizada para evitar efeitos de ordem
- Múltiplas réplicas para cada combinação de tratamento e objeto experimental

#### G. Quantidade de Medições

- **Número de repositórios:** {num_repos} repositórios
- **Número de tipos de consulta:** 3 (simples, complexa, múltiplos recursos)
- **Número de réplicas por consulta:** 30 execuções
- **Total de medições realizadas:** {len(self.df)} medições bem-sucedidas

#### H. Ameaças à Validade

**Ameaças à Validade Interna:**
- **Variação de carga do servidor:** O GitHub pode ter diferentes cargas em diferentes momentos
  - *Mitigação:* Executar medições em horários variados e calcular médias
- **Cache:** Respostas podem ser cacheadas pelo servidor ou pela rede
  - *Mitigação:* Realizar múltiplas medições e análise estatística robusta
- **Latência de rede:** Variações na latência de rede podem afetar resultados
  - *Mitigação:* Executar múltiplas réplicas (30 por combinação)

**Ameaças à Validade Externa:**
- **Generalização:** Resultados podem ser específicos para a API do GitHub
  - *Limitação:* Documentar contexto específico do experimento
- **Representatividade:** Repositórios selecionados podem não representar todos os casos de uso
  - *Mitigação:* Usar repositórios populares e variados

**Ameaças à Validade de Construto:**
- **Equivalência das consultas:** Consultas GraphQL e REST podem não ser exatamente equivalentes
  - *Mitigação:* Garantir que ambas retornem os mesmos dados essenciais
- **Medição de tempo:** Pode incluir overhead de bibliotecas
  - *Mitigação:* Medir tempo de forma consistente para ambos os tratamentos

### 3.2 Ambiente Experimental

- **Sistema Operacional:** Windows 11
- **Linguagem:** Python 3.x
- **Bibliotecas:** requests, pandas, numpy, scipy, matplotlib, seaborn
- **Rede:** Conexão estável à internet
- **API:** GitHub API v4 (GraphQL) e v3 (REST)
- **Data da coleta:** {datetime.now().strftime('%d/%m/%Y')}

### 3.3 Procedimento de Coleta

1. Para cada repositório selecionado:
   - Executar consulta simples via GraphQL (30 réplicas)
   - Executar consulta simples via REST (30 réplicas)
   - Executar consulta complexa via GraphQL (30 réplicas)
   - Executar consulta complexa via REST (30 réplicas)
   - Executar consulta múltipla via GraphQL (30 réplicas)
   - Executar consulta múltipla via REST (30 réplicas)
2. Para cada requisição:
   - Medir tempo de resposta com `time.perf_counter()`
   - Medir tamanho da resposta (headers + body)
   - Registrar sucesso/falha da requisição
3. Armazenar todos os dados em CSV para análise posterior

### 3.4 Análise Estatística

- **Estatísticas descritivas:** Média, mediana, desvio padrão, mínimo e máximo
- **Teste de normalidade:** Shapiro-Wilk (α = 0.05)
- **Teste de comparação:**
  - Se dados normais: Teste t pareado
  - Se dados não normais: Teste de Wilcoxon
- **Tamanho do efeito:** Cohen's d
- **Nível de significância:** α = 0.05

---

## 4. Resultados

### 4.1 Estatísticas Descritivas

#### 4.1.1 Tempo de Resposta

**GraphQL:**
- Média: {rq1_results['graphql_stats']['mean']:.2f} ms
- Mediana: {rq1_results['graphql_stats']['median']:.2f} ms
- Desvio Padrão: {rq1_results['graphql_stats']['std']:.2f} ms
- Mínimo: {rq1_results['graphql_stats']['min']:.2f} ms
- Máximo: {rq1_results['graphql_stats']['max']:.2f} ms
- N = {rq1_results['graphql_stats']['count']}

**REST:**
- Média: {rq1_results['rest_stats']['mean']:.2f} ms
- Mediana: {rq1_results['rest_stats']['median']:.2f} ms
- Desvio Padrão: {rq1_results['rest_stats']['std']:.2f} ms
- Mínimo: {rq1_results['rest_stats']['min']:.2f} ms
- Máximo: {rq1_results['rest_stats']['max']:.2f} ms
- N = {rq1_results['rest_stats']['count']}

**Diferença de médias:** {rq1_results['graphql_stats']['mean'] - rq1_results['rest_stats']['mean']:.2f} ms

#### 4.1.2 Tamanho da Resposta

**GraphQL:**
- Média: {rq2_results['graphql_stats']['mean']:.0f} bytes ({rq2_results['graphql_stats']['mean']/1024:.2f} KB)
- Mediana: {rq2_results['graphql_stats']['median']:.0f} bytes ({rq2_results['graphql_stats']['median']/1024:.2f} KB)
- Desvio Padrão: {rq2_results['graphql_stats']['std']:.0f} bytes
- Mínimo: {rq2_results['graphql_stats']['min']:.0f} bytes
- Máximo: {rq2_results['graphql_stats']['max']:.0f} bytes
- N = {rq2_results['graphql_stats']['count']}

**REST:**
- Média: {rq2_results['rest_stats']['mean']:.0f} bytes ({rq2_results['rest_stats']['mean']/1024:.2f} KB)
- Mediana: {rq2_results['rest_stats']['median']:.0f} bytes ({rq2_results['rest_stats']['median']/1024:.2f} KB)
- Desvio Padrão: {rq2_results['rest_stats']['std']:.0f} bytes
- Mínimo: {rq2_results['rest_stats']['min']:.0f} bytes
- Máximo: {rq2_results['rest_stats']['max']:.0f} bytes
- N = {rq2_results['rest_stats']['count']}

**Diferença de médias:** {rq2_results['graphql_stats']['mean'] - rq2_results['rest_stats']['mean']:.0f} bytes

### 4.2 Análise por Tipo de Consulta

| Tipo de Consulta | Tempo GraphQL (ms) | Tempo REST (ms) | Tamanho GraphQL (bytes) | Tamanho REST (bytes) |
|------------------|-------------------|-----------------|------------------------|---------------------|"""

        for query_type, data in by_type.items():
            report += f"\n| {query_type.capitalize()} | {data['graphql_time_mean']:.2f} | {data['rest_time_mean']:.2f} | {data['graphql_size_mean']:.0f} | {data['rest_size_mean']:.0f} |"

        report += f"""

### 4.3 RQ1: Tempo de Resposta

#### 4.3.1 Teste de Normalidade

- **GraphQL:** {'Normal' if rq1_results['graphql_normal'] else 'Não Normal'} (p = {rq1_results['graphql_p']:.4f})
- **REST:** {'Normal' if rq1_results['rest_normal'] else 'Não Normal'} (p = {rq1_results['rest_p']:.4f})

#### 4.3.2 Teste Estatístico

**Teste utilizado:** {rq1_results['test_name']}

- **p-value:** {rq1_results['p_value']:.4f}
- **Cohen's d:** {rq1_results['cohens_d']:.4f}
- **Conclusão:** {rq1_results['conclusion']}

#### 4.3.3 Interpretação

Com base no teste estatístico ({'Teste t pareado' if rq1_results['graphql_normal'] and rq1_results['rest_normal'] else 'Teste de Wilcoxon'}), {
    'rejeitamos a hipótese nula (p < 0.05)' if rq1_results['p_value'] < 0.05 else 'não rejeitamos a hipótese nula (p ≥ 0.05)'
}. O tamanho do efeito (Cohen's d = {rq1_results['cohens_d']:.4f}) indica um efeito {
    'muito pequeno' if abs(rq1_results['cohens_d']) < 0.2 else
    'pequeno' if abs(rq1_results['cohens_d']) < 0.5 else
    'médio' if abs(rq1_results['cohens_d']) < 0.8 else 'grande'
}.

**Resposta à RQ1:** {rq1_results['conclusion']}

#### 4.3.4 Visualizações

![Comparação de Tempo de Resposta](data:image/png;base64,{self.image_to_base64('grafico_tempo_resposta.png')})

### 4.4 RQ2: Tamanho da Resposta

#### 4.4.1 Teste de Normalidade

- **GraphQL:** {'Normal' if rq2_results['graphql_normal'] else 'Não Normal'} (p = {rq2_results['graphql_p']:.4f})
- **REST:** {'Normal' if rq2_results['rest_normal'] else 'Não Normal'} (p = {rq2_results['rest_p']:.4f})

#### 4.4.2 Teste Estatístico

**Teste utilizado:** {rq2_results['test_name']}

- **p-value:** {rq2_results['p_value']:.4f}
- **Cohen's d:** {rq2_results['cohens_d']:.4f}
- **Conclusão:** {rq2_results['conclusion']}

#### 4.4.3 Interpretação

Com base no teste estatístico ({'Teste t pareado' if rq2_results['graphql_normal'] and rq2_results['rest_normal'] else 'Teste de Wilcoxon'}), {
    'rejeitamos a hipótese nula (p < 0.05)' if rq2_results['p_value'] < 0.05 else 'não rejeitamos a hipótese nula (p ≥ 0.05)'
}. O tamanho do efeito (Cohen's d = {rq2_results['cohens_d']:.4f}) indica um efeito {
    'muito pequeno' if abs(rq2_results['cohens_d']) < 0.2 else
    'pequeno' if abs(rq2_results['cohens_d']) < 0.5 else
    'médio' if abs(rq2_results['cohens_d']) < 0.8 else 'grande'
}.

**Resposta à RQ2:** {rq2_results['conclusion']}

#### 4.4.4 Visualizações

![Comparação de Tamanho da Resposta](data:image/png;base64,{self.image_to_base64('grafico_tamanho_resposta.png')})

### 4.5 Análise Comparativa por Tipo de Consulta

![Comparação por Tipo de Consulta](data:image/png;base64,{self.image_to_base64('grafico_por_tipo.png')})

### 4.6 Distribuições

![Histogramas de Distribuição](data:image/png;base64,{self.image_to_base64('grafico_histogramas.png')})

---

## 5. Discussão

### 5.1 Interpretação dos Resultados

#### 5.1.1 Tempo de Resposta (RQ1)

{rq1_results['conclusion']}. A diferença média observada foi de {abs(rq1_results['graphql_stats']['mean'] - rq1_results['rest_stats']['mean']):.2f} ms, com {'GraphQL sendo' if rq1_results['graphql_stats']['mean'] < rq1_results['rest_stats']['mean'] else 'REST sendo'} {abs((rq1_results['graphql_stats']['mean'] - rq1_results['rest_stats']['mean']) / rq1_results['rest_stats']['mean'] * 100):.1f}% {'mais rápido' if rq1_results['graphql_stats']['mean'] < rq1_results['rest_stats']['mean'] else 'mais lento'}.

Possíveis explicações para esses resultados:
- {'GraphQL permite otimizar queries e reduzir overhead de múltiplas requisições' if rq1_results['graphql_stats']['mean'] < rq1_results['rest_stats']['mean'] else 'REST pode ter vantagem de caching mais eficiente no servidor'}
- {'A flexibilidade do GraphQL pode ter custo de processamento adicional no servidor' if rq1_results['graphql_stats']['mean'] > rq1_results['rest_stats']['mean'] else 'GraphQL permite buscar apenas os dados necessários, reduzindo processamento'}
- Implementação específica da API do GitHub pode favorecer um dos modelos

#### 5.1.2 Tamanho da Resposta (RQ2)

{rq2_results['conclusion']}. A diferença média observada foi de {abs(rq2_results['graphql_stats']['mean'] - rq2_results['rest_stats']['mean']):.0f} bytes ({abs(rq2_results['graphql_stats']['mean'] - rq2_results['rest_stats']['mean'])/1024:.2f} KB), com {'GraphQL produzindo' if rq2_results['graphql_stats']['mean'] < rq2_results['rest_stats']['mean'] else 'REST produzindo'} {abs((rq2_results['graphql_stats']['mean'] - rq2_results['rest_stats']['mean']) / rq2_results['rest_stats']['mean'] * 100):.1f}% {'respostas menores' if rq2_results['graphql_stats']['mean'] < rq2_results['rest_stats']['mean'] else 'respostas maiores'}.

Possíveis explicações:
- {'GraphQL permite selecionar apenas os campos necessários, reduzindo payload' if rq2_results['graphql_stats']['mean'] < rq2_results['rest_stats']['mean'] else 'REST pode retornar dados pré-processados mais compactos'}
- {'APIs REST frequentemente retornam campos desnecessários (over-fetching)' if rq2_results['graphql_stats']['mean'] < rq2_results['rest_stats']['mean'] else 'GraphQL pode incluir overhead de metadados na resposta'}
- Formato de serialização e compressão podem influenciar resultados

#### 5.1.3 Variação por Tipo de Consulta

A análise por tipo de consulta revela padrões interessantes:
- **Consultas simples:** Diferenças podem ser menos significativas
- **Consultas complexas:** GraphQL pode ter maior vantagem ao evitar múltiplas requisições
- **Consultas múltiplas:** Capacidade do GraphQL de agregar dados em uma única requisição pode ser benéfica

### 5.2 Implicações Práticas

Os resultados deste experimento têm implicações para decisões de design de APIs:

1. **Para desenvolvedores de APIs:**
   - Considerar trade-offs entre flexibilidade e performance
   - GraphQL pode ser vantajoso quando clientes precisam de dados customizados
   - REST pode ser preferível para casos de uso bem definidos e estáveis

2. **Para consumidores de APIs:**
   - Avaliar necessidades específicas de cada aplicação
   - Considerar overhead de aprendizado e implementação do GraphQL
   - Analisar perfil de uso (poucos dados vs. dados complexos e aninhados)

3. **Para pesquisadores:**
   - Resultados dependem fortemente da implementação específica
   - Necessidade de replicação em diferentes contextos e APIs
   - Importância de considerar múltiplas métricas de desempenho

### 5.3 Limitações do Estudo

Este estudo possui várias limitações que devem ser consideradas:

1. **Generalização limitada:**
   - Resultados específicos para a API do GitHub
   - Outras APIs podem ter características diferentes
   - Implementações variam significativamente entre plataformas

2. **Fatores externos não controlados:**
   - Variações de carga do servidor do GitHub
   - Latência e condições de rede
   - Possível presença de caching no servidor

3. **Escopo das consultas:**
   - Conjunto limitado de tipos de consulta testados
   - Consultas reais de aplicações podem ser mais diversas
   - Padrões de uso podem diferir significativamente

4. **Métricas avaliadas:**
   - Apenas tempo e tamanho foram medidos
   - Outras métricas (CPU, memória, complexidade) não foram avaliadas
   - Experiência do desenvolvedor e curva de aprendizado não foram consideradas

### 5.4 Ameaças à Validade

**Validade Interna:**
- Variações de carga do servidor mitigadas por múltiplas medições
- Efeitos de cache possíveis mas distribuídos entre tratamentos
- Ordem de execução randomizada para evitar viés sistemático

**Validade Externa:**
- Resultados podem não se aplicar a outras APIs além do GitHub
- Repositórios selecionados podem não representar todos os casos de uso
- Contexto específico (API pública, dados abertos) pode limitar generalização

**Validade de Construto:**
- Equivalência de consultas garantida por design experimental
- Medições consistentes entre tratamentos
- Possível overhead de medição distribuído igualmente

---

## 6. Conclusão

### 6.1 Síntese dos Resultados

Este experimento controlado comparou as APIs GraphQL e REST do GitHub em termos de tempo de resposta e tamanho das respostas. Com base em **{len(self.df)} medições** realizadas em **{num_repos} repositórios**, os principais achados foram:

**RQ1 - Tempo de Resposta:**
{rq1_results['conclusion']} (p = {rq1_results['p_value']:.4f}, d = {rq1_results['cohens_d']:.4f})

**RQ2 - Tamanho da Resposta:**
{rq2_results['conclusion']} (p = {rq2_results['p_value']:.4f}, d = {rq2_results['cohens_d']:.4f})

### 6.2 Contribuições

Este estudo contribui para a literatura sobre comparação de APIs Web ao:

1. Fornecer evidência empírica quantitativa sobre diferenças entre GraphQL e REST
2. Utilizar metodologia experimental rigorosa com múltiplas réplicas
3. Analisar diferentes tipos de consultas e seus efeitos
4. Documentar ambiente e procedimentos para replicação

### 6.3 Trabalhos Futuros

Pesquisas futuras podem expandir este trabalho:

1. **Replicação em outras APIs:**
   - Testar com APIs de diferentes domínios (e-commerce, redes sociais, etc.)
   - Avaliar implementações alternativas de GraphQL e REST
   - Comparar com outras abordagens (gRPC, OData)

2. **Métricas adicionais:**
   - Consumo de CPU e memória no cliente
   - Complexidade de implementação e manutenção
   - Experiência do desenvolvedor e curva de aprendizado
   - Taxa de erro e resiliência

3. **Cenários mais complexos:**
   - Consultas com paginação
   - Operações de escrita (mutations vs POST/PUT/PATCH)
   - Subscriptions em tempo real vs polling
   - Caching e invalidação de cache

4. **Análise longitudinal:**
   - Evolução de performance ao longo do tempo
   - Impacto de mudanças na API
   - Padrões de uso em aplicações reais

### 6.4 Considerações Finais

A escolha entre GraphQL e REST não é simples e depende de múltiplos fatores incluindo:
- Requisitos específicos da aplicação
- Perfil de dados e consultas necessárias
- Expertise da equipe de desenvolvimento
- Infraestrutura e ferramentas disponíveis
- Trade-offs entre flexibilidade e simplicidade

Este experimento fornece dados quantitativos que podem informar essa decisão, mas deve ser considerado junto com outros fatores qualitativos e contextuais.

---

## 7. Referências

1. GitHub GraphQL API Documentation. Disponível em: https://docs.github.com/en/graphql
2. GitHub REST API Documentation. Disponível em: https://docs.github.com/en/rest
3. GraphQL Foundation. GraphQL Specification. Disponível em: https://spec.graphql.org/
4. Fielding, R. T. (2000). Architectural Styles and the Design of Network-based Software Architectures. Doctoral dissertation, University of California, Irvine.
5. Brito, G., Mombach, T., & Valente, M. T. (2019). Migrating to GraphQL: A Practical Assessment. IEEE 26th International Conference on Software Analysis, Evolution and Reengineering (SANER).
6. Wittern, E., Cha, A., Davis, J. C., Baudart, G., & Mandel, L. (2019). An Empirical Study of GraphQL Schemas. IEEE/ACM 41st International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP).

---

## 8. Apêndices

### 8.1 Scripts Utilizados

- `experiment_collector.py`: Script para coleta de dados do experimento
- `experiment_analyzer.py`: Script para análise estatística dos dados
- `generate_experiment_report.py`: Script para geração deste relatório
- `dashboard.py`: Dashboard interativo para visualização dos resultados

### 8.2 Estrutura dos Dados

**Arquivo:** `experiment_data.csv`

Colunas:
- `timestamp`: Data e hora da medição
- `query_type`: Tipo de consulta (simple, complex, multiple)
- `api_type`: Tipo de API (graphql, rest)
- `repository_owner`: Proprietário do repositório
- `repository_name`: Nome do repositório
- `response_time_ms`: Tempo de resposta em milissegundos
- `response_size_bytes`: Tamanho da resposta em bytes
- `success`: Indicador de sucesso da requisição
- `error`: Mensagem de erro (se houver)

### 8.3 Ambiente de Execução

- **Data da coleta:** {datetime.now().strftime('%d/%m/%Y')}
- **Hora da coleta:** {datetime.now().strftime('%H:%M:%S')}
- **Total de medições:** {len(self.df)}
- **Repositórios analisados:** {num_repos}

### 8.4 Código de Consultas

**Exemplo de consulta GraphQL (simples):**
```graphql
query {{
  repository(owner: "facebook", name: "react") {{
    name
    description
    stargazerCount
    forkCount
    issues(states: OPEN) {{
      totalCount
    }}
    pullRequests(states: OPEN) {{
      totalCount
    }}
  }}
}}
```

**Exemplo de consulta REST (equivalente):**
```
GET /repos/facebook/react
```

---

*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*
"""

        return report

    def save_report(self, report_content, filename="relatorio_experimento_graphql_rest.md"):
        """Salva o relatório em arquivo Markdown"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"\nRelatório salvo em: {filename}")
            return True
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")
            return False

    def generate_complete_report(self):
        """Gera o relatório completo com visualizações"""
        print("="*60)
        print("GERADOR DE RELATÓRIO - EXPERIMENTO GRAPHQL VS REST")
        print("="*60)

        print("\n1. Carregando dados...")
        if not self.load_data():
            print("Erro ao carregar dados. Verifique se o arquivo experiment_data.csv existe.")
            return False

        print("\n2. Gerando visualizações...")
        self.generate_visualizations()

        print("\n3. Analisando dados estatisticamente...")
        rq1 = self.analyze_rq1()
        rq2 = self.analyze_rq2()

        print("\n4. Gerando relatório em Markdown...")
        report_content = self.generate_markdown_report()

        print("\n5. Salvando relatório...")
        success = self.save_report(report_content)

        if success:
            print("\n" + "="*60)
            print("RELATÓRIO GERADO COM SUCESSO!")
            print("="*60)
            print("\nArquivos criados:")
            print("- relatorio_experimento_graphql_rest.md (Relatório completo)")
            print("- grafico_tempo_resposta.png (Comparação de tempo)")
            print("- grafico_tamanho_resposta.png (Comparação de tamanho)")
            print("- grafico_por_tipo.png (Análise por tipo de consulta)")
            print("- grafico_histogramas.png (Distribuições)")
            print("="*60)
            print("\nPróximos passos:")
            print("1. Revise o relatório gerado")
            print("2. Adicione os nomes dos membros do grupo na seção 1")
            print("3. Ajuste interpretações conforme necessário")
            print("4. Converta para PDF se necessário")

        return success


def main():
    """Função principal"""
    csv_file = "experiment_data.csv"

    if not Path(csv_file).exists():
        print(f"Erro: Arquivo {csv_file} não encontrado!")
        print("Execute primeiro o script experiment_collector.py para coletar os dados.")
        return

    generator = GraphQLvsRESTReportGenerator(csv_file)
    generator.generate_complete_report()


if __name__ == "__main__":
    main()
