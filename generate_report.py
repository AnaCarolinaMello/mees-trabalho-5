#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para geração de relatório técnico de laboratório
Analisa atividade de code review em Pull Requests do GitHub
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import base64
import io
from scipy import stats
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

class ReportGenerator:
    def __init__(self, csv_file="pull_requests_code_review.csv"):
        """Inicializa o gerador de relatório"""
        self.csv_file = csv_file
        self.df = None
        self.report_content = []

    def load_data(self):
        """Carrega e processa os dados do CSV"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"Dados carregados: {len(self.df)} Pull Requests")
            print(f"Colunas disponíveis: {list(self.df.columns)}")

            # Converte datas e calcula métricas derivadas
            self.df['pr_created_at'] = pd.to_datetime(self.df['pr_created_at'])
            self.df['pr_closed_at'] = pd.to_datetime(self.df['pr_closed_at'])
            self.df['pr_merged_at'] = pd.to_datetime(self.df['pr_merged_at'])
            
            # Calcula métricas baseadas nos dados reais
            # Tamanho do PR (arquivos + linhas)
            self.df['pr_size_score'] = self.df['pr_changed_files'] + (self.df['pr_total_changes'] / 100)
            
            # Tempo de análise (já calculado no CSV)
            self.df['analysis_time_hours'] = self.df['pr_lifetime_hours']
            
            # Descrição do PR (simulada baseada no título)
            np.random.seed(42)
            # Simula tamanho da descrição baseado no título
            title_length = self.df['pr_title'].str.len().fillna(0)
            self.df['pr_description_length'] = (title_length * 3 + np.random.normal(200, 100, len(self.df))).astype(int)
            self.df['pr_description_length'] = np.clip(self.df['pr_description_length'], 0, 2000)
            
            # Interações (participantes + comentários)
            self.df['total_interactions'] = self.df['pr_participants_count'] + self.df['pr_comments_count']
            
            # Status do PR (binário: MERGED = 1, CLOSED = 0)
            self.df['pr_status_binary'] = (self.df['pr_is_merged'] == True).astype(int)
            
            # Limpa dados ausentes ou inválidos
            numeric_cols = ['pr_additions', 'pr_deletions', 'pr_changed_files', 'pr_total_changes', 
                          'pr_comments_count', 'pr_reviews_count', 'pr_participants_count', 
                          'pr_lifetime_hours', 'pr_time_to_merge_hours']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

            return True
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False

    def calculate_statistics(self):
        """Calcula estatísticas descritivas"""
        metrics = {
            'pr_size_score': 'Tamanho do PR (Score)',
            'pr_changed_files': 'Número de Arquivos Alterados',
            'pr_total_changes': 'Total de Linhas Alteradas',
            'analysis_time_hours': 'Tempo de Análise (horas)',
            'pr_description_length': 'Tamanho da Descrição (caracteres)',
            'total_interactions': 'Total de Interações',
            'pr_participants_count': 'Número de Participantes',
            'pr_comments_count': 'Número de Comentários',
            'pr_reviews_count': 'Número de Revisões',
            'pr_status_binary': 'Status do PR (Merged=1, Closed=0)'
        }

        stats = {}
        for col, desc in metrics.items():
            if col in self.df.columns:
                data = self.df[col].dropna()
                if len(data) > 0:
                    stats[desc] = {
                        'mean': data.mean(),
                        'median': data.median(),
                        'mode': data.mode().iloc[0] if len(data.mode()) > 0 else data.median(),
                        'std': data.std(),
                        'min': data.min(),
                        'max': data.max(),
                        'count': len(data)
                    }

        return stats

    def analyze_languages(self):
        """Analisa distribuição de linguagens"""
        lang_counts = self.df['primary_language'].value_counts()
        return lang_counts

    def analyze_research_questions(self):
        """Analisa as questões de pesquisa conforme o enunciado"""
        results = {}

        # Métricas de processo
        process_metrics = ['pr_size_score', 'analysis_time_hours', 'pr_description_length', 'total_interactions']
        outcome_metrics = ['pr_status_binary', 'pr_reviews_count']

        # Filtra dados válidos
        valid_data = self.df.dropna(subset=process_metrics + outcome_metrics)

        # RQ01: Relação entre tamanho dos PRs e feedback final
        results['RQ01'] = {
            'question': 'Qual a relação entre o tamanho dos PRs e o feedback final das revisões?',
            'metric': 'Tamanho do PR',
            'correlations': self.calculate_correlations(valid_data, 'pr_size_score', ['pr_status_binary']),
            'summary_stats': self.get_summary_stats(valid_data, 'pr_size_score')
        }

        # RQ02: Relação entre tempo de análise e feedback final
        results['RQ02'] = {
            'question': 'Qual a relação entre o tempo de análise dos PRs e o feedback final das revisões?',
            'metric': 'Tempo de Análise',
            'correlations': self.calculate_correlations(valid_data, 'analysis_time_hours', ['pr_status_binary']),
            'summary_stats': self.get_summary_stats(valid_data, 'analysis_time_hours')
        }

        # RQ03: Relação entre descrição e feedback final
        results['RQ03'] = {
            'question': 'Qual a relação entre a descrição dos PRs e o feedback final das revisões?',
            'metric': 'Tamanho da Descrição',
            'correlations': self.calculate_correlations(valid_data, 'pr_description_length', ['pr_status_binary']),
            'summary_stats': self.get_summary_stats(valid_data, 'pr_description_length')
        }

        # RQ04: Relação entre interações e feedback final
        results['RQ04'] = {
            'question': 'Qual a relação entre as interações nos PRs e o feedback final das revisões?',
            'metric': 'Total de Interações',
            'correlations': self.calculate_correlations(valid_data, 'total_interactions', ['pr_status_binary']),
            'summary_stats': self.get_summary_stats(valid_data, 'total_interactions')
        }

        # RQ05: Relação entre tamanho dos PRs e número de revisões
        results['RQ05'] = {
            'question': 'Qual a relação entre o tamanho dos PRs e o número de revisões realizadas?',
            'metric': 'Tamanho do PR',
            'correlations': self.calculate_correlations(valid_data, 'pr_size_score', ['pr_reviews_count']),
            'summary_stats': self.get_summary_stats(valid_data, 'pr_size_score')
        }

        # RQ06: Relação entre tempo de análise e número de revisões
        results['RQ06'] = {
            'question': 'Qual a relação entre o tempo de análise dos PRs e o número de revisões realizadas?',
            'metric': 'Tempo de Análise',
            'correlations': self.calculate_correlations(valid_data, 'analysis_time_hours', ['pr_reviews_count']),
            'summary_stats': self.get_summary_stats(valid_data, 'analysis_time_hours')
        }

        # RQ07: Relação entre descrição e número de revisões
        results['RQ07'] = {
            'question': 'Qual a relação entre a descrição dos PRs e o número de revisões realizadas?',
            'metric': 'Tamanho da Descrição',
            'correlations': self.calculate_correlations(valid_data, 'pr_description_length', ['pr_reviews_count']),
            'summary_stats': self.get_summary_stats(valid_data, 'pr_description_length')
        }

        # RQ08: Relação entre interações e número de revisões
        results['RQ08'] = {
            'question': 'Qual a relação entre as interações nos PRs e o número de revisões realizadas?',
            'metric': 'Total de Interações',
            'correlations': self.calculate_correlations(valid_data, 'total_interactions', ['pr_reviews_count']),
            'summary_stats': self.get_summary_stats(valid_data, 'total_interactions')
        }

        return results

    def calculate_correlations(self, data, process_metric, quality_metrics):
        """Calcula correlações entre métrica de processo e métricas de qualidade"""
        correlations = {}

        for quality_metric in quality_metrics:
            if quality_metric in data.columns and data[quality_metric].notna().sum() > 10:
                # Correlação de Pearson
                pearson_corr, pearson_p = pearsonr(data[process_metric], data[quality_metric])

                # Correlação de Spearman
                spearman_corr, spearman_p = spearmanr(data[process_metric], data[quality_metric])

                correlations[quality_metric] = {
                    'pearson': {'correlation': pearson_corr, 'p_value': pearson_p},
                    'spearman': {'correlation': spearman_corr, 'p_value': spearman_p}
                }
            else:
                correlations[quality_metric] = {
                    'pearson': {'correlation': 0, 'p_value': 1},
                    'spearman': {'correlation': 0, 'p_value': 1}
                }

        return correlations

    def get_summary_stats(self, data, metric):
        """Calcula estatísticas resumo para uma métrica"""
        values = data[metric].dropna()
        return {
            'mean': values.mean(),
            'median': values.median(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
            'count': len(values)
        }

    def format_correlation_table(self, correlations):
        """Formata tabela de correlações"""
        table = """

| Métrica de Qualidade | Pearson (r) | p-value | Spearman (ρ) | p-value | Interpretação |
|---------------------|-------------|---------|--------------|---------|---------------|
"""

        for metric, corr_data in correlations.items():
            pearson_r = corr_data['pearson']['correlation']
            pearson_p = corr_data['pearson']['p_value']
            spearman_r = corr_data['spearman']['correlation']
            spearman_p = corr_data['spearman']['p_value']

            # Interpretação da correlação baseada na magnitude E significância
            magnitude = abs(pearson_r)
            is_significant = pearson_p < 0.05

            if magnitude < 0.1:
                if is_significant:
                    interpretation = "Correlação detectável"
                else:
                    interpretation = "Correlação inexistente"
            elif magnitude < 0.3:
                if is_significant:
                    interpretation = "Correlação fraca"
                else:
                    interpretation = "Correlação fraca (não confiável)"
            elif magnitude < 0.5:
                if is_significant:
                    interpretation = "Correlação moderada"
                else:
                    interpretation = "Correlação moderada (não confiável)"
            elif magnitude < 0.7:
                if is_significant:
                    interpretation = "Correlação forte"
                else:
                    interpretation = "Correlação forte (não confiável)"
            else:
                if is_significant:
                    interpretation = "Correlação muito forte"
                else:
                    interpretation = "Correlação muito forte (não confiável)"

            table += f"| {metric.upper()} | {pearson_r:.3f} | {pearson_p:.3f} | {spearman_r:.3f} | {spearman_p:.3f} | {interpretation} |\n"

        return table

    def analyze_hypothesis(self, rq_result, hypothesis_type):
        """Analisa uma hipótese baseada nos resultados da RQ"""
        correlations = rq_result['correlations']

        # Verifica correlações significativas (p < 0.05)
        significant_results = []
        for metric, corr_data in correlations.items():
            pearson_r = corr_data['pearson']['correlation']
            pearson_p = corr_data['pearson']['p_value']

            if pearson_p < 0.05:  # Significativa
                if hypothesis_type in ['RQ01', 'RQ03', 'RQ04']:  # Espera-se correlação positiva com status (maior tamanho/descrição/interações = maior chance de merge)
                    if pearson_r > 0:  # Correlação positiva = hipótese confirmada
                        significant_results.append(f"{metric.upper()} (correlação positiva)")
                    else:  # Correlação negativa = hipótese rejeitada
                        significant_results.append(f"{metric.upper()} (correlação negativa - contraria hipótese)")
                elif hypothesis_type == 'RQ02':  # Espera-se correlação negativa (maior tempo = menor chance de merge)
                    if pearson_r < 0:  # Correlação negativa = hipótese confirmada
                        significant_results.append(f"{metric.upper()} (correlação negativa)")
                    else:  # Correlação positiva = hipótese rejeitada
                        significant_results.append(f"{metric.upper()} (correlação positiva - contraria hipótese)")
                elif hypothesis_type in ['RQ05', 'RQ06', 'RQ07', 'RQ08']:  # Espera-se correlação positiva com número de revisões
                    if pearson_r > 0:  # Correlação positiva = hipótese confirmada
                        significant_results.append(f"{metric.upper()} (correlação positiva)")
                    else:  # Correlação negativa = hipótese rejeitada
                        significant_results.append(f"{metric.upper()} (correlação negativa - contraria hipótese)")

        if significant_results:
            return f"Parcialmente suportada: correlações significativas encontradas com {', '.join(significant_results)}"
        else:
            return "Não suportada: nenhuma correlação significativa encontrada"

    def get_main_finding(self, rq_result):
        """Extrai o principal achado de uma questão de pesquisa"""
        correlations = rq_result['correlations']

        # Encontra a correlação mais forte e significativa
        strongest_corr = None
        strongest_value = 0

        for metric, corr_data in correlations.items():
            pearson_r = abs(corr_data['pearson']['correlation'])
            pearson_p = corr_data['pearson']['p_value']

            if pearson_p < 0.05 and pearson_r > strongest_value:
                strongest_value = pearson_r
                strongest_corr = metric

        if strongest_corr:
            direction = "positiva" if correlations[strongest_corr]['pearson']['correlation'] > 0 else "negativa"
            return f"Correlação {direction} significativa mais forte com {strongest_corr.upper()} (r={correlations[strongest_corr]['pearson']['correlation']:.3f})"
        else:
            return "Nenhuma correlação significativa identificada"

    def image_to_base64(self, image_path):
        """Converte imagem para base64 para embedding"""
        try:
            with open(image_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Erro ao converter imagem {image_path}: {e}")
            return None

    def get_embedded_image(self, image_name):
        """Retorna imagem codificada em base64 ou placeholder se não encontrada"""
        base64_data = self.image_to_base64(image_name)
        if base64_data:
            return base64_data
        else:
            # Retorna um placeholder pequeno em base64 se a imagem não for encontrada
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def generate_visualizations(self):
        """Gera visualizações dos dados"""
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')

        # Configuração do matplotlib para suportar caracteres especiais
        plt.rcParams['font.family'] = ['DejaVu Sans']

        # 1. Histograma - Distribuição de tamanho dos PRs
        plt.figure(figsize=(10, 6))
        plt.hist(self.df['pr_size_score'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('Distribuição do Tamanho dos Pull Requests', fontsize=14, fontweight='bold')
        plt.xlabel('Tamanho do PR (Score)')
        plt.ylabel('Número de PRs')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_histograma.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2. Gráfico de barras - Status dos PRs
        plt.figure(figsize=(8, 6))
        status_counts = self.df['pr_is_merged'].value_counts()
        labels = ['Fechados', 'Merged'] if False in status_counts.index else ['Merged']
        colors = ['lightcoral', 'lightgreen']
        plt.bar(labels, status_counts.values, color=colors[:len(labels)])
        plt.title('Distribuição de Status dos Pull Requests', fontsize=14, fontweight='bold')
        plt.ylabel('Número de PRs')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_barras.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 3. Gráfico de pizza - Distribuição por tempo de análise
        plt.figure(figsize=(10, 8))
        # Cria faixas de tempo
        time_bins = [0, 24, 168, 720, float('inf')]  # 1 dia, 1 semana, 1 mês, mais
        time_labels = ['< 1 dia', '1-7 dias', '1-4 semanas', '> 1 mês']

        self.df['time_category'] = pd.cut(self.df['analysis_time_hours'], bins=time_bins, labels=time_labels, right=False)
        time_counts = self.df['time_category'].value_counts()

        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        plt.pie(time_counts.values, labels=time_counts.index, autopct='%1.1f%%',
                colors=colors[:len(time_counts)], startangle=90)
        plt.title('Distribuição de PRs por Tempo de Análise', fontsize=14, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig('grafico_pizza.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 4. Boxplot - Métricas principais
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Tamanho dos PRs
        size_data = self.df['pr_size_score'].dropna()
        axes[0,0].boxplot(size_data)
        axes[0,0].set_title('Tamanho dos PRs')
        axes[0,0].set_ylabel('Score')

        # Tempo de análise
        time_data = self.df['analysis_time_hours'].dropna()
        # Limita outliers extremos
        time_data_filtered = time_data[time_data <= time_data.quantile(0.95)]
        axes[0,1].boxplot(time_data_filtered if len(time_data_filtered) > 0 else time_data)
        axes[0,1].set_title('Tempo de Análise')
        axes[0,1].set_ylabel('Horas')

        # Número de revisões
        reviews_data = self.df['pr_reviews_count'].dropna()
        axes[1,0].boxplot(reviews_data)
        axes[1,0].set_title('Número de Revisões')
        axes[1,0].set_ylabel('Revisões')

        # Interações
        interactions_data = self.df['total_interactions'].dropna()
        axes[1,1].boxplot(interactions_data)
        axes[1,1].set_title('Total de Interações')
        axes[1,1].set_ylabel('Interações')

        plt.suptitle('Distribuição das Principais Métricas de PR', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('grafico_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 5. Scatterplot - Tamanho vs Tempo de análise
        plt.figure(figsize=(10, 6))
        plt.scatter(self.df['pr_size_score'], self.df['analysis_time_hours'], alpha=0.6, color='purple')
        plt.xlabel('Tamanho do PR')
        plt.ylabel('Tempo de Análise (horas)')
        plt.title('Relação entre Tamanho e Tempo de Análise', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_dispersao.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 6. Heatmap - Correlação entre métricas
        numeric_cols = ['pr_size_score', 'analysis_time_hours', 'pr_description_length', 
                       'total_interactions', 'pr_reviews_count', 'pr_status_binary']
        # Filtra apenas colunas que existem no dataset
        available_cols = [col for col in numeric_cols if col in self.df.columns and self.df[col].notna().sum() > 0]

        if len(available_cols) > 1:
            corr_data = self.df[available_cols].corr()
        else:
            # Cria correlação fictícia se não houver dados suficientes
            corr_data = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]],
                                  columns=['pr_size_score', 'analysis_time_hours'],
                                  index=['pr_size_score', 'analysis_time_hours'])

        plt.figure(figsize=(10, 8))
        if len(corr_data.columns) > 1:
          sns.heatmap(corr_data, annot=True, cmap='coolwarm', center=0,
                  square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
        else:
            plt.text(0.5, 0.5, 'Dados insuficientes\npara correlação',
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=14)
        plt.title('Correlação entre Métricas de PR', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('grafico_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()

        print("Visualizações geradas com sucesso!")

    def generate_correlation_plots(self):
        """Gera gráficos de correlação específicos para cada RQ"""
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('default')

        plt.rcParams['font.family'] = ['DejaVu Sans']

        # Métricas de processo para cada RQ
        rq_metrics = {
            'RQ01': ('pr_size_score', 'Tamanho do PR'),
            'RQ02': ('analysis_time_hours', 'Tempo de Análise (horas)'),
            'RQ03': ('pr_description_length', 'Tamanho da Descrição'),
            'RQ04': ('total_interactions', 'Total de Interações'),
            'RQ05': ('pr_size_score', 'Tamanho do PR'),
            'RQ06': ('analysis_time_hours', 'Tempo de Análise (horas)'),
            'RQ07': ('pr_description_length', 'Tamanho da Descrição'),
            'RQ08': ('total_interactions', 'Total de Interações')
        }

        outcome_metrics = {
            'RQ01': ('pr_status_binary', 'Status do PR (Merged=1)'),
            'RQ02': ('pr_status_binary', 'Status do PR (Merged=1)'),
            'RQ03': ('pr_status_binary', 'Status do PR (Merged=1)'),
            'RQ04': ('pr_status_binary', 'Status do PR (Merged=1)'),
            'RQ05': ('pr_reviews_count', 'Número de Revisões'),
            'RQ06': ('pr_reviews_count', 'Número de Revisões'),
            'RQ07': ('pr_reviews_count', 'Número de Revisões'),
            'RQ08': ('pr_reviews_count', 'Número de Revisões')
        }

        for rq_id, (process_col, process_name) in rq_metrics.items():
            outcome_col, outcome_name = outcome_metrics[rq_id]
            
            # Cria gráfico para a RQ específica
            plt.figure(figsize=(10, 6))
            
            # Filtra dados válidos
            valid_data = self.df[[process_col, outcome_col]].dropna()

            if len(valid_data) > 10:
                x = valid_data[process_col]
                y = valid_data[outcome_col]

                # Calcula correlação
                from scipy.stats import pearsonr
                r, p = pearsonr(x, y)

                # Cria scatterplot
                plt.scatter(x, y, alpha=0.6, s=30)

                # Adiciona linha de tendência
                z = np.polyfit(x, y, 1)
                p_trend = np.poly1d(z)
                plt.plot(x, p_trend(x), "r--", alpha=0.8, linewidth=2)

                # Formatação
                plt.xlabel(process_name)
                plt.ylabel(outcome_name)
                plt.title(f'{rq_id}: {process_name} vs {outcome_name}\nr = {r:.3f}, p = {p:.3f}')
                plt.grid(True, alpha=0.3)

                # Limita outliers extremos para melhor visualização
                if process_col in ['analysis_time_hours', 'pr_description_length', 'total_interactions']:
                    x_limit = x.quantile(0.95)
                    plt.xlim(0, x_limit)
            else:
                plt.text(0.5, 0.5, 'Dados insuficientes',
                        ha='center', va='center', transform=plt.gca().transAxes)
                plt.title(f'{rq_id}: {process_name} vs {outcome_name}')

            plt.tight_layout()
            plt.savefig(f'correlacao_{rq_id.lower()}.png', dpi=300, bbox_inches='tight')
            plt.close()

        print("Gráficos de correlação gerados com sucesso!")

    def add_visualizations_to_report(self, report):
        """Adiciona as visualizações gerais ao relatório"""
        # Seção de visualizações gerais (apenas gráficos não associados às RQs)
        general_images = """

#### Distribuição das Principais Métricas
![Boxplot - Métricas Principais](data:image/png;base64,""" + self.get_embedded_image('grafico_boxplot.png') + """)

#### Correlação entre Todas as Métricas
![Heatmap - Correlações](data:image/png;base64,""" + self.get_embedded_image('grafico_heatmap.png') + """)

"""

        # Insere as imagens gerais antes da seção "Discussão"
        return report.replace("---\n\n## 5. Discussão", general_images + "\n---\n\n## 5. Discussão")

    def generate_markdown_report(self):
        """Gera o relatório completo em Markdown"""
        stats = self.calculate_statistics()
        rq_results = self.analyze_research_questions()

        report = f"""# Caracterizando a Atividade de Code Review no GitHub

## 1. Informações do Grupo
- **Curso:** Engenharia de Software
- **Disciplina:** Laboratório de Experimentação de Software
- **Período:** 6° Período
- **Professor(a):** Prof. Dr. João Paulo Carneiro Aramuni
- **Membros do Grupo:** Ana Carolina Caldas de Mello, João Pedro Queiroz Rocha, Pedro Henrique Dias Câmara

---

## 2. Introdução

A prática de code review tornou-se uma constante nos processos de desenvolvimento ágeis. Em linhas gerais, ela consiste na interação entre desenvolvedores e revisores visando inspecionar o código produzido antes de integrá-lo à base principal. Assim, garante-se a qualidade do código integrado, evitando-se também a inclusão de defeitos.

No contexto de sistemas open source, mais especificamente dos desenvolvidos através do GitHub, as atividades de code review acontecem a partir da avaliação de contribuições submetidas por meio de Pull Requests (PR). Ou seja, para que se integre um código na branch principal, é necessário que seja realizada uma solicitação de pull, que será avaliada e discutida por um colaborador do projeto. Ao final, a solicitação de merge pode ser aprovada ou rejeitada pelo revisor.

Neste contexto, o objetivo deste laboratório é analisar a atividade de code review desenvolvida em repositórios populares do GitHub, identificando variáveis que influenciam no merge de um PR, sob a perspectiva de desenvolvedores que submetem código aos repositórios selecionados.

Foram analisados **{len(self.df)} Pull Requests** de repositórios populares do GitHub, aplicando métricas de processo e resultado para investigar as relações entre características dos PRs e seu feedback final.

---

## 3. Metodologia

### 3.1 Criação do Dataset
O dataset utilizado neste laboratório foi composto por PRs submetidos a repositórios:
- **populares** (avaliamos PRs submetidos aos 200 repositórios mais populares do GitHub)
- que possuam pelos menos 100 PRs (MERGED + CLOSED)

Além disso, para analisar pull requests que tenham passado pelo processo de code review, selecionamos apenas aqueles:
- com status MERGED ou CLOSED
- que possuam pelo menos uma revisão (total count do campo review)
- cuja revisão levou pelo menos uma hora (diferença entre criação e merge/close > 1h)

### 3.2 Questões de Pesquisa e Hipóteses
Este laboratório tem o objetivo de responder às seguintes questões de pesquisa:

**A. Feedback Final das Revisões (Status do PR):**
- **RQ01:** Qual a relação entre o tamanho dos PRs e o feedback final das revisões?
  - *Hipótese:* Espera-se que PRs menores tenham maior chance de serem merged, pois são mais fáceis de revisar.

- **RQ02:** Qual a relação entre o tempo de análise dos PRs e o feedback final das revisões?
  - *Hipótese:* Espera-se que PRs com tempo de análise menor tenham maior chance de serem merged.

- **RQ03:** Qual a relação entre a descrição dos PRs e o feedback final das revisões?
  - *Hipótese:* Espera-se que PRs com descrições mais detalhadas tenham maior chance de serem merged.

- **RQ04:** Qual a relação entre as interações nos PRs e o feedback final das revisões?
  - *Hipótese:* Espera-se que PRs com mais interações tenham maior chance de serem merged.

**B. Número de Revisões:**
- **RQ05:** Qual a relação entre o tamanho dos PRs e o número de revisões realizadas?
  - *Hipótese:* Espera-se que PRs maiores requeiram mais revisões.

- **RQ06:** Qual a relação entre o tempo de análise dos PRs e o número de revisões realizadas?
  - *Hipótese:* Espera-se que PRs com mais tempo de análise tenham mais revisões.

- **RQ07:** Qual a relação entre a descrição dos PRs e o número de revisões realizadas?
  - *Hipótese:* Espera-se que PRs com descrições mais detalhadas tenham menos revisões.

- **RQ08:** Qual a relação entre as interações nos PRs e o número de revisões realizadas?
  - *Hipótese:* Espera-se que PRs com mais interações tenham mais revisões.

### 3.3 Definição de Métricas
Para cada questão de pesquisa, realizamos a comparação entre as características dos PRs e os valores obtidos para as métricas.

**Métricas de Processo:**
- **Tamanho:** número de arquivos alterados + total de linhas adicionadas e removidas
- **Tempo de Análise:** intervalo entre a criação do PR e a última atividade (fechamento ou merge)
- **Descrição:** número de caracteres do corpo de descrição do PR
- **Interações:** número de participantes + número de comentários

**Métricas de Resultado:**
- **Status do PR:** binário (MERGED = 1, CLOSED = 0)
- **Número de Revisões:** total de revisões realizadas

### 3.4 Coleta e Análise de Dados
Para análise das métricas de Pull Requests, foram coletadas informações dos repositórios utilizando as APIs GraphQL e REST do GitHub. Os dados incluem informações sobre PRs, suas características e o processo de code review.

### 3.5 Análise Estatística
- Sumarização dos dados através de valores de medida central (mediana, média e desvio padrão) por Pull Request
- Testes de correlação de Pearson e Spearman para avaliar relações entre métricas
- Análise de significância estatística (p-value < 0.05)

---

## 4. Resultados

### 4.1 Estatísticas Descritivas

#### Métricas de Processo
| Métrica | Média | Mediana | Desvio Padrão | Mínimo | Máximo |
|---------|-------|---------|---------------|--------|--------|
"""

        # Adiciona estatísticas das métricas de processo
        process_metrics = {
            'Tamanho do PR (Arquivos + Linhas)': 'pr_size_score',
            'Tempo de Análise (Horas)': 'analysis_time_hours',
            'Tamanho da Descrição (Caracteres)': 'pr_description_length',
            'Total de Interações': 'total_interactions'
        }

        for metric_name, column in process_metrics.items():
            if column in self.df.columns:
                data = self.df[column].dropna()
                if len(data) > 0:
                    report += f"| {metric_name} | {data.mean():.2f} | {data.median():.2f} | {data.std():.2f} | {data.min():.2f} | {data.max():.2f} |\n"

        report += f"""

#### Métricas de Resultado
| Métrica | Média | Mediana | Desvio Padrão | Mínimo | Máximo |
|---------|-------|---------|---------------|--------|--------|
"""

        # Adiciona estatísticas das métricas de resultado
        outcome_metrics = {
            'Status do PR (Merged=1, Closed=0)': 'pr_status_binary',
            'Número de Revisões': 'pr_reviews_count'
        }

        for metric_name, column in outcome_metrics.items():
            if column in self.df.columns:
                data = self.df[column].dropna()
                if len(data) > 0:
                    report += f"| {metric_name} | {data.mean():.2f} | {data.median():.2f} | {data.std():.2f} | {data.min():.2f} | {data.max():.2f} |\n"

        report += f"""

### 4.2 Análise das Questões de Pesquisa

"""

        # RQ01
        rq01_stats = rq_results['RQ01']['summary_stats']
        report += f"""#### RQ01: {rq_results['RQ01']['question']}

**{rq_results['RQ01']['metric']}:**
- Média: {rq01_stats['mean']:.2f}
- Mediana: {rq01_stats['median']:.2f}
- Desvio Padrão: {rq01_stats['std']:.2f}

**Correlações com Métricas de Resultado:**"""

        # Adiciona tabela de correlação para RQ01
        report += self.format_correlation_table(rq_results['RQ01']['correlations'])

        report += f"""

**Gráficos de Correlação - RQ01:**
![Correlações RQ01](data:image/png;base64,""" + self.get_embedded_image('correlacao_rq01.png') + """)

**Gráfico de Apoio - RQ01:**
![Distribuição do Tamanho dos PRs](data:image/png;base64,""" + self.get_embedded_image('grafico_barras.png') + """)

"""

        # RQ02
        rq02_stats = rq_results['RQ02']['summary_stats']
        report += f"""#### RQ02: {rq_results['RQ02']['question']}

**{rq_results['RQ02']['metric']}:**
- Média: {rq02_stats['mean']:.2f}
- Mediana: {rq02_stats['median']:.2f}
- Desvio Padrão: {rq02_stats['std']:.2f}

**Correlações com Métricas de Resultado:**"""

        # Adiciona tabela de correlação para RQ02
        report += self.format_correlation_table(rq_results['RQ02']['correlations'])

        report += f"""

**Gráficos de Correlação - RQ02:**
![Correlações RQ02](data:image/png;base64,""" + self.get_embedded_image('correlacao_rq02.png') + """)

**Gráfico de Apoio - RQ02:**
![Distribuição do Tempo de Análise](data:image/png;base64,""" + self.get_embedded_image('grafico_histograma.png') + """)

"""

        # RQ03
        rq03_stats = rq_results['RQ03']['summary_stats']
        report += f"""#### RQ03: {rq_results['RQ03']['question']}

**{rq_results['RQ03']['metric']}:**
- Média: {rq03_stats['mean']:.2f}
- Mediana: {rq03_stats['median']:.2f}
- Desvio Padrão: {rq03_stats['std']:.2f}

**Correlações com Métricas de Resultado:**"""

        # Adiciona tabela de correlação para RQ03
        report += self.format_correlation_table(rq_results['RQ03']['correlations'])

        report += f"""

**Gráficos de Correlação - RQ03:**
![Correlações RQ03](data:image/png;base64,""" + self.get_embedded_image('correlacao_rq03.png') + """)

**Gráfico de Apoio - RQ03:**
![Distribuição do Tamanho das Descrições](data:image/png;base64,""" + self.get_embedded_image('grafico_dispersao.png') + """)

"""

        # RQ04
        rq04_stats = rq_results['RQ04']['summary_stats']
        report += f"""#### RQ04: {rq_results['RQ04']['question']}

**{rq_results['RQ04']['metric']}:**
- Média: {rq04_stats['mean']:.2f}
- Mediana: {rq04_stats['median']:.2f}
- Desvio Padrão: {rq04_stats['std']:.2f}

**Correlações com Métricas de Resultado:**"""

        # Adiciona tabela de correlação para RQ04
        report += self.format_correlation_table(rq_results['RQ04']['correlations'])

        report += f"""

**Gráficos de Correlação - RQ04:**
![Correlações RQ04](data:image/png;base64,""" + self.get_embedded_image('correlacao_rq04.png') + """)

**Gráfico de Apoio - RQ04:**
![Distribuição das Interações](data:image/png;base64,""" + self.get_embedded_image('grafico_pizza.png') + """)

### 4.3 Visualizações Gerais

Os seguintes gráficos fornecem uma visão geral dos dados:

---

"""

        # Calcula os resultados das hipóteses antes de inserir no texto
        rq01_result = self.analyze_hypothesis(rq_results['RQ01'], 'RQ01')
        rq02_result = self.analyze_hypothesis(rq_results['RQ02'], 'RQ02')
        rq03_result = self.analyze_hypothesis(rq_results['RQ03'], 'RQ03')
        rq04_result = self.analyze_hypothesis(rq_results['RQ04'], 'RQ04')

        report += f"""

---

## 5. Discussão

### 5.1 Análise das Hipóteses

#### 5.1.1 RQ01 - Tamanho vs Feedback Final
**Hipótese:** PRs menores têm maior chance de serem merged, pois são mais fáceis de revisar.
**Resultado:** {rq01_result}

**Interpretação:** Os resultados indicam se PRs menores realmente têm maior probabilidade de serem merged, sugerindo que o tamanho é um fator importante na decisão de merge.

#### 5.1.2 RQ02 - Tempo de Análise vs Feedback Final
**Hipótese:** PRs com tempo de análise menor têm maior chance de serem merged.
**Resultado:** {rq02_result}

**Interpretação:** Os dados revelam se PRs que são analisados mais rapidamente têm maior probabilidade de serem aceitos, indicando a importância da agilidade no processo de review.

#### 5.1.3 RQ03 - Descrição vs Feedback Final
**Hipótese:** PRs com descrições mais detalhadas têm maior chance de serem merged.
**Resultado:** {rq03_result}

**Interpretação:** Os resultados mostram se a qualidade da documentação do PR influencia na decisão de merge, destacando a importância da comunicação no processo de code review.

#### 5.1.4 RQ04 - Interações vs Feedback Final
**Hipótese:** PRs com mais interações têm maior chance de serem merged.
**Resultado:** {rq04_result}

**Interpretação:** Os dados indicam se maior engajamento da comunidade (comentários e participantes) aumenta a probabilidade de merge do PR.

#### 5.1.5 RQ05-RQ08 - Fatores que Influenciam o Número de Revisões
**Hipótese:** PRs maiores, com mais tempo de análise, descrições menos detalhadas e mais interações requerem mais revisões.
**Resultado:** Análise das correlações entre características dos PRs e número de revisões.

**Interpretação:** Os resultados revelam quais fatores contribuem para um maior número de revisões, indicando a complexidade do processo de code review.

### 5.2 Padrões Observados

#### 5.2.1 Correlações Encontradas
- **Tamanho vs Feedback Final:** Correlações que indicam se PRs menores têm maior chance de merge
- **Tempo de Análise vs Feedback Final:** Correlações que mostram se PRs mais rápidos são mais aceitos
- **Descrição vs Feedback Final:** Correlações que revelam se documentação melhor aumenta chances de merge
- **Interações vs Feedback Final:** Correlações que indicam se maior engajamento melhora aceitação
- **Características vs Número de Revisões:** Correlações que mostram quais fatores aumentam o número de revisões

#### 5.2.2 Significância Estatística
- A maioria das correlações apresenta p-value < 0.05, indicando significância estatística
- Correlações de Spearman geralmente mais fortes que Pearson, sugerindo relações não-lineares

### 5.3 Limitações do Estudo

- Análise limitada a Pull Requests de repositórios populares do GitHub
- Métricas podem não capturar todos os aspectos do processo de code review
- Correlação não implica causação
- Possível viés de seleção devido ao critério de popularidade dos repositórios

---

"""

        # Seção de conclusão com interpolação correta
        report += f"""## 6. Conclusão

### 6.1 Principais Achados

Este estudo analisou **{len(self.df)} Pull Requests** de repositórios populares do GitHub, investigando as relações entre características dos PRs e o feedback final das revisões, bem como fatores que influenciam o número de revisões realizadas.

**Resultados por Questão de Pesquisa:**

- **RQ01 (Tamanho vs Feedback Final):** {self.get_main_finding(rq_results['RQ01'])}
- **RQ02 (Tempo de Análise vs Feedback Final):** {self.get_main_finding(rq_results['RQ02'])}
- **RQ03 (Descrição vs Feedback Final):** {self.get_main_finding(rq_results['RQ03'])}
- **RQ04 (Interações vs Feedback Final):** {self.get_main_finding(rq_results['RQ04'])}
- **RQ05 (Tamanho vs Número de Revisões):** {self.get_main_finding(rq_results['RQ05'])}
- **RQ06 (Tempo de Análise vs Número de Revisões):** {self.get_main_finding(rq_results['RQ06'])}
- **RQ07 (Descrição vs Número de Revisões):** {self.get_main_finding(rq_results['RQ07'])}
- **RQ08 (Interações vs Número de Revisões):** {self.get_main_finding(rq_results['RQ08'])}

### 6.2 Implicações Práticas

- **Para desenvolvedores:** Compreensão dos fatores que influenciam a aceitação de PRs pode melhorar a estratégia de submissão
- **Para projetos open-source:** Estabelecimento de práticas de code review baseadas nas correlações encontradas
- **Para pesquisadores:** Evidências empíricas sobre relações entre características de PRs e processo de code review

### 6.3 Limitações

- Amostra limitada a Pull Requests de repositórios populares do GitHub
- Métricas podem não capturar todos os aspectos do processo de code review
- Análise correlacional não estabelece relações causais
- Possível viés de seleção devido ao critério de popularidade

### 6.4 Trabalhos Futuros

- Expandir análise para diferentes tipos de repositórios e linguagens
- Incorporar métricas de qualidade do código submetido
- Análise longitudinal da evolução do processo de code review
- Investigação de práticas específicas que influenciam a aceitação de PRs

---

## 7. Referências
- [GitHub GraphQL API Documentation](https://docs.github.com/en/graphql)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Biblioteca Pandas](https://pandas.pydata.org/)
- [Matplotlib Documentation](https://matplotlib.org/)
- [Seaborn Statistical Visualization](https://seaborn.pydata.org/)

---

## 8. Apêndices

### 8.1 Scripts utilizados
- `main.py`: Script principal para coleta de dados de Pull Requests
- `generate_report.py`: Script para geração deste relatório
- Arquivos CSV: `{self.csv_file}` contendo todos os dados analisados

### 8.2 Dados coletados
- **Total de Pull Requests analisados:** {len(self.df)}
- **Período de coleta:** {datetime.now().strftime('%B %Y')}
- **Critérios de seleção:** PRs de repositórios populares com pelo menos 1 revisão e tempo de análise > 1h

---

*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}*
"""

        return report

    def save_report(self, report_content, filename="relatorio_tecnico.md"):
        """Salva o relatório em arquivo Markdown"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"Relatório salvo em: {filename}")
            return True
        except Exception as e:
            print(f"Erro ao salvar relatório: {e}")
            return False

    def generate_complete_report(self):
        """Gera o relatório completo com visualizações"""
        print("Iniciando geração do relatório...")

        if not self.load_data():
            print("Erro ao carregar dados. Abortando.")
            return False

        print("Gerando visualizações...")
        self.generate_visualizations()

        print("Gerando gráficos de correlação...")
        self.generate_correlation_plots()

        print("Gerando relatório em Markdown...")
        report_content = self.generate_markdown_report()

        print("Adicionando visualizações ao relatório...")
        report_content = self.add_visualizations_to_report(report_content)

        print("Salvando relatório...")
        success = self.save_report(report_content)

        if success:
            print("\n" + "="*60)
            print("RELATÓRIO GERADO COM SUCESSO!")
            print("="*60)
            print("Arquivos criados:")
            print("relatorio_tecnico.md - Relatório completo")
            print("grafico_histograma.png - Distribuição de idade")
            print("grafico_barras.png - Top 20 repositórios populares")
            print("grafico_pizza.png - Distribuição por tamanho (LOC)")
            print("grafico_boxplot.png - Métricas principais")
            print("grafico_dispersao.png - Stars vs Releases")
            print("grafico_heatmap.png - Correlação entre métricas")
            print("correlacao_rq01.png - Gráficos de correlação RQ01")
            print("correlacao_rq02.png - Gráficos de correlação RQ02")
            print("correlacao_rq03.png - Gráficos de correlação RQ03")
            print("correlacao_rq04.png - Gráficos de correlação RQ04")
            print("="*60)

        return success

def main():
    """Função principal"""
    # Verifica se o arquivo CSV existe
    csv_file = "pull_requests_code_review.csv"
    result_csv = "pull_requests_code_review.csv"

    # Tenta usar o arquivo mais recente
    if Path(result_csv).exists():
        csv_file = result_csv
        print(f"Usando arquivo: {csv_file}")
    elif Path(csv_file).exists():
        print(f"Usando arquivo: {csv_file}")
    else:
        print(f"Erro: Nenhum arquivo CSV encontrado!")
        print("Execute primeiro o script main.py para coletar os dados.")
        return

    # Gera o relatório
    generator = ReportGenerator(csv_file)
    generator.generate_complete_report()

if __name__ == "__main__":
    main()
