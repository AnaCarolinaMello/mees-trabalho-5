#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Visualização - Experimento GraphQL vs REST
Gera gráficos e tabelas para análise dos resultados
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuração do estilo
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'seaborn-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class ExperimentDashboard:
    def __init__(self, csv_file: str = "experiment_data.csv"):
        """
        Inicializa o dashboard
        
        Args:
            csv_file: Caminho para o arquivo CSV com os dados do experimento
        """
        self.csv_file = csv_file
        self.df = None
        self.output_dir = Path("dashboard_output")
        self.output_dir.mkdir(exist_ok=True)
    
    def load_data(self) -> bool:
        """Carrega os dados do CSV"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"Dados carregados: {len(self.df)} medições")
            
            # Filtra apenas medições bem-sucedidas
            self.df = self.df[self.df['success'] == True].copy()
            print(f"Medições bem-sucedidas: {len(self.df)}")
            
            # Converte tipos
            self.df['response_time_ms'] = pd.to_numeric(self.df['response_time_ms'], errors='coerce')
            self.df['response_size_bytes'] = pd.to_numeric(self.df['response_size_bytes'], errors='coerce')
            
            # Cria coluna combinada para identificação
            self.df['repository'] = self.df['repository_owner'] + '/' + self.df['repository_name']
            
            return True
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False
    
    def plot_response_time_comparison(self):
        """Gráfico 1: Comparação de tempo de resposta - Boxplot"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Boxplot
        data_to_plot = [
            self.df[self.df['api_type'] == 'graphql']['response_time_ms'].dropna(),
            self.df[self.df['api_type'] == 'rest']['response_time_ms'].dropna()
        ]
        
        bp = axes[0].boxplot(data_to_plot, labels=['GraphQL', 'REST'], patch_artist=True)
        bp['boxes'][0].set_facecolor('#3498db')
        bp['boxes'][1].set_facecolor('#e74c3c')
        axes[0].set_ylabel('Tempo de Resposta (ms)', fontsize=12)
        axes[0].set_title('Distribuição do Tempo de Resposta\nGraphQL vs REST', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        
        # Violin plot
        sns.violinplot(data=self.df, x='api_type', y='response_time_ms', ax=axes[1], palette=['#3498db', '#e74c3c'])
        axes[1].set_xlabel('Tipo de API', fontsize=12)
        axes[1].set_ylabel('Tempo de Resposta (ms)', fontsize=12)
        axes[1].set_title('Distribuição Detalhada do Tempo de Resposta', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'response_time_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Gráfico salvo: response_time_comparison.png")
    
    def plot_response_size_comparison(self):
        """Gráfico 2: Comparação de tamanho da resposta - Boxplot"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Boxplot
        data_to_plot = [
            self.df[self.df['api_type'] == 'graphql']['response_size_bytes'].dropna() / 1024,  # KB
            self.df[self.df['api_type'] == 'rest']['response_size_bytes'].dropna() / 1024  # KB
        ]
        
        bp = axes[0].boxplot(data_to_plot, labels=['GraphQL', 'REST'], patch_artist=True)
        bp['boxes'][0].set_facecolor('#2ecc71')
        bp['boxes'][1].set_facecolor('#f39c12')
        axes[0].set_ylabel('Tamanho da Resposta (KB)', fontsize=12)
        axes[0].set_title('Distribuição do Tamanho da Resposta\nGraphQL vs REST', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        
        # Violin plot
        df_kb = self.df.copy()
        df_kb['response_size_kb'] = df_kb['response_size_bytes'] / 1024
        sns.violinplot(data=df_kb, x='api_type', y='response_size_kb', ax=axes[1], palette=['#2ecc71', '#f39c12'])
        axes[1].set_xlabel('Tipo de API', fontsize=12)
        axes[1].set_ylabel('Tamanho da Resposta (KB)', fontsize=12)
        axes[1].set_title('Distribuição Detalhada do Tamanho da Resposta', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'response_size_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Gráfico salvo: response_size_comparison.png")
    
    def plot_by_query_type(self):
        """Gráfico 3: Comparação por tipo de consulta"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        query_types = ['simple', 'complex', 'multiple']
        query_labels = ['Simples', 'Complexa', 'Múltiplos Recursos']
        
        # Tempo por tipo de consulta
        time_data = []
        for qt in query_types:
            graphql_times = self.df[(self.df['api_type'] == 'graphql') & (self.df['query_type'] == qt)]['response_time_ms'].dropna()
            rest_times = self.df[(self.df['api_type'] == 'rest') & (self.df['query_type'] == qt)]['response_time_ms'].dropna()
            time_data.append([graphql_times, rest_times])
        
        # Boxplot de tempo por tipo
        positions = [1, 2, 3]
        width = 0.6
        for i, (qt, label) in enumerate(zip(query_types, query_labels)):
            graphql_data = time_data[i][0]
            rest_data = time_data[i][1]
            
            bp1 = axes[0, 0].boxplot([graphql_data], positions=[positions[i] - width/2], widths=width/2, 
                                    patch_artist=True, labels=[f'{label}\nGraphQL'])
            bp2 = axes[0, 0].boxplot([rest_data], positions=[positions[i] + width/2], widths=width/2, 
                                     patch_artist=True, labels=[f'{label}\nREST'])
            bp1['boxes'][0].set_facecolor('#3498db')
            bp2['boxes'][0].set_facecolor('#e74c3c')
        
        axes[0, 0].set_xticks(positions)
        axes[0, 0].set_xticklabels(query_labels)
        axes[0, 0].set_ylabel('Tempo de Resposta (ms)', fontsize=12)
        axes[0, 0].set_title('Tempo de Resposta por Tipo de Consulta', fontsize=14, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Tamanho por tipo de consulta
        size_data = []
        for qt in query_types:
            graphql_sizes = self.df[(self.df['api_type'] == 'graphql') & (self.df['query_type'] == qt)]['response_size_bytes'].dropna() / 1024
            rest_sizes = self.df[(self.df['api_type'] == 'rest') & (self.df['query_type'] == qt)]['response_size_bytes'].dropna() / 1024
            size_data.append([graphql_sizes, rest_sizes])
        
        for i, (qt, label) in enumerate(zip(query_types, query_labels)):
            graphql_data = size_data[i][0]
            rest_data = size_data[i][1]
            
            bp1 = axes[0, 1].boxplot([graphql_data], positions=[positions[i] - width/2], widths=width/2, 
                                    patch_artist=True)
            bp2 = axes[0, 1].boxplot([rest_data], positions=[positions[i] + width/2], widths=width/2, 
                                     patch_artist=True)
            bp1['boxes'][0].set_facecolor('#2ecc71')
            bp2['boxes'][0].set_facecolor('#f39c12')
        
        axes[0, 1].set_xticks(positions)
        axes[0, 1].set_xticklabels(query_labels)
        axes[0, 1].set_ylabel('Tamanho da Resposta (KB)', fontsize=12)
        axes[0, 1].set_title('Tamanho da Resposta por Tipo de Consulta', fontsize=14, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Médias de tempo
        time_means = []
        for qt in query_types:
            graphql_mean = self.df[(self.df['api_type'] == 'graphql') & (self.df['query_type'] == qt)]['response_time_ms'].mean()
            rest_mean = self.df[(self.df['api_type'] == 'rest') & (self.df['query_type'] == qt)]['response_time_ms'].mean()
            time_means.append({'GraphQL': graphql_mean, 'REST': rest_mean})
        
        x = np.arange(len(query_labels))
        width = 0.35
        graphql_means = [tm['GraphQL'] for tm in time_means]
        rest_means = [tm['REST'] for tm in time_means]
        
        axes[1, 0].bar(x - width/2, graphql_means, width, label='GraphQL', color='#3498db')
        axes[1, 0].bar(x + width/2, rest_means, width, label='REST', color='#e74c3c')
        axes[1, 0].set_xlabel('Tipo de Consulta', fontsize=12)
        axes[1, 0].set_ylabel('Tempo Médio (ms)', fontsize=12)
        axes[1, 0].set_title('Tempo Médio de Resposta por Tipo', fontsize=14, fontweight='bold')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(query_labels)
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Médias de tamanho
        size_means = []
        for qt in query_types:
            graphql_mean = self.df[(self.df['api_type'] == 'graphql') & (self.df['query_type'] == qt)]['response_size_bytes'].mean() / 1024
            rest_mean = self.df[(self.df['api_type'] == 'rest') & (self.df['query_type'] == qt)]['response_size_bytes'].mean() / 1024
            size_means.append({'GraphQL': graphql_mean, 'REST': rest_mean})
        
        graphql_size_means = [sm['GraphQL'] for sm in size_means]
        rest_size_means = [sm['REST'] for sm in size_means]
        
        axes[1, 1].bar(x - width/2, graphql_size_means, width, label='GraphQL', color='#2ecc71')
        axes[1, 1].bar(x + width/2, rest_size_means, width, label='REST', color='#f39c12')
        axes[1, 1].set_xlabel('Tipo de Consulta', fontsize=12)
        axes[1, 1].set_ylabel('Tamanho Médio (KB)', fontsize=12)
        axes[1, 1].set_title('Tamanho Médio da Resposta por Tipo', fontsize=14, fontweight='bold')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(query_labels)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comparison_by_query_type.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Gráfico salvo: comparison_by_query_type.png")
    
    def plot_scatter_comparison(self):
        """Gráfico 4: Scatter plot - Tempo vs Tamanho"""
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        graphql_data = self.df[self.df['api_type'] == 'graphql']
        rest_data = self.df[self.df['api_type'] == 'rest']
        
        # Scatter plot - Tempo vs Tamanho
        axes[0].scatter(graphql_data['response_time_ms'], graphql_data['response_size_bytes'] / 1024, 
                       alpha=0.5, label='GraphQL', color='#3498db', s=30)
        axes[0].scatter(rest_data['response_time_ms'], rest_data['response_size_bytes'] / 1024, 
                       alpha=0.5, label='REST', color='#e74c3c', s=30)
        axes[0].set_xlabel('Tempo de Resposta (ms)', fontsize=12)
        axes[0].set_ylabel('Tamanho da Resposta (KB)', fontsize=12)
        axes[0].set_title('Relação entre Tempo e Tamanho da Resposta', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Histograma comparativo - Tempo
        axes[1].hist(graphql_data['response_time_ms'].dropna(), bins=50, alpha=0.6, 
                   label='GraphQL', color='#3498db', edgecolor='black')
        axes[1].hist(rest_data['response_time_ms'].dropna(), bins=50, alpha=0.6, 
                   label='REST', color='#e74c3c', edgecolor='black')
        axes[1].set_xlabel('Tempo de Resposta (ms)', fontsize=12)
        axes[1].set_ylabel('Frequência', fontsize=12)
        axes[1].set_title('Distribuição do Tempo de Resposta', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'scatter_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Gráfico salvo: scatter_comparison.png")
    
    def generate_summary_table(self):
        """Gera tabela resumo das estatísticas"""
        summary_data = []
        
        for api_type in ['graphql', 'rest']:
            data = self.df[self.df['api_type'] == api_type]
            
            summary_data.append({
                'API': api_type.upper(),
                'Tempo Médio (ms)': f"{data['response_time_ms'].mean():.2f}",
                'Tempo Mediano (ms)': f"{data['response_time_ms'].median():.2f}",
                'Desvio Padrão Tempo (ms)': f"{data['response_time_ms'].std():.2f}",
                'Tamanho Médio (KB)': f"{data['response_size_bytes'].mean() / 1024:.2f}",
                'Tamanho Mediano (KB)': f"{data['response_size_bytes'].median() / 1024:.2f}",
                'Desvio Padrão Tamanho (KB)': f"{data['response_size_bytes'].std() / 1024:.2f}",
                'Número de Medições': len(data)
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Salva como CSV
        summary_df.to_csv(self.output_dir / 'summary_statistics.csv', index=False)
        print("Tabela salva: summary_statistics.csv")
        
        # Salva como HTML
        html_table = summary_df.to_html(index=False, classes='table table-striped')
        with open(self.output_dir / 'summary_statistics.html', 'w', encoding='utf-8') as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Estatísticas Resumo - GraphQL vs REST</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Estatísticas Resumo - Experimento GraphQL vs REST</h1>
    {html_table}
</body>
</html>
""")
        print("Tabela HTML salva: summary_statistics.html")
        
        return summary_df
    
    def generate_detailed_table_by_query_type(self):
        """Gera tabela detalhada por tipo de consulta"""
        detailed_data = []
        
        for api_type in ['graphql', 'rest']:
            for query_type in ['simple', 'complex', 'multiple']:
                data = self.df[(self.df['api_type'] == api_type) & (self.df['query_type'] == query_type)]
                
                if len(data) > 0:
                    detailed_data.append({
                        'API': api_type.upper(),
                        'Tipo de Consulta': query_type,
                        'Tempo Médio (ms)': f"{data['response_time_ms'].mean():.2f}",
                        'Tempo Mediano (ms)': f"{data['response_time_ms'].median():.2f}",
                        'Tamanho Médio (KB)': f"{data['response_size_bytes'].mean() / 1024:.2f}",
                        'Tamanho Mediano (KB)': f"{data['response_size_bytes'].median() / 1024:.2f}",
                        'Número de Medições': len(data)
                    })
        
        detailed_df = pd.DataFrame(detailed_data)
        detailed_df.to_csv(self.output_dir / 'detailed_statistics_by_query_type.csv', index=False)
        print("Tabela detalhada salva: detailed_statistics_by_query_type.csv")
        
        return detailed_df
    
    def generate_all_visualizations(self):
        """Gera todas as visualizações"""
        print("="*60)
        print("GERANDO DASHBOARD DE VISUALIZAÇÃO")
        print("="*60)
        
        if not self.load_data():
            print("Erro ao carregar dados. Verifique se o arquivo existe.")
            return
        
        print("\nGerando gráficos...")
        self.plot_response_time_comparison()
        self.plot_response_size_comparison()
        self.plot_by_query_type()
        self.plot_scatter_comparison()
        
        print("\nGerando tabelas...")
        summary_table = self.generate_summary_table()
        detailed_table = self.generate_detailed_table_by_query_type()
        
        print("\n" + "="*60)
        print("DASHBOARD GERADO COM SUCESSO!")
        print("="*60)
        print(f"\nArquivos salvos em: {self.output_dir}")
        print("\nGráficos:")
        print("  - response_time_comparison.png")
        print("  - response_size_comparison.png")
        print("  - comparison_by_query_type.png")
        print("  - scatter_comparison.png")
        print("\nTabelas:")
        print("  - summary_statistics.csv")
        print("  - summary_statistics.html")
        print("  - detailed_statistics_by_query_type.csv")
        
        print("\n" + "="*60)
        print("RESUMO ESTATÍSTICO")
        print("="*60)
        print("\n" + summary_table.to_string(index=False))


def main():
    """Função principal"""
    dashboard = ExperimentDashboard("experiment_data.csv")
    dashboard.generate_all_visualizations()


if __name__ == "__main__":
    main()


