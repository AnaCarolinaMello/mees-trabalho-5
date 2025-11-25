#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para análise estatística dos dados do experimento GraphQL vs REST
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, wilcoxon, ttest_rel
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

class ExperimentAnalyzer:
    def __init__(self, csv_file: str = "experiment_data.csv"):
        """
        Inicializa o analisador de dados
        
        Args:
            csv_file: Caminho para o arquivo CSV com os dados do experimento
        """
        self.csv_file = csv_file
        self.df = None
        self.results = {}
    
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
            
            return True
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False
    
    def test_normality(self, data: pd.Series) -> Tuple[bool, float]:
        """
        Testa normalidade dos dados usando Shapiro-Wilk
        
        Returns:
            Tuple: (é_normal, p_value)
        """
        if len(data) < 3:
            return False, 1.0
        
        # Limita tamanho da amostra para o teste (máximo 5000)
        sample = data.sample(min(5000, len(data))) if len(data) > 5000 else data
        
        try:
            stat, p_value = shapiro(sample)
            is_normal = p_value > 0.05
            return is_normal, p_value
        except:
            return False, 0.0
    
    def analyze_rq1(self) -> Dict:
        """
        Analisa RQ1: Respostas às consultas GraphQL são mais rápidas que REST?
        
        Returns:
            Dict com resultados da análise
        """
        print("\n" + "="*60)
        print("ANÁLISE RQ1: Tempo de Resposta")
        print("="*60)
        
        # Agrupa por repositório e tipo de consulta para fazer comparação pareada
        results = []
        
        for (repo_owner, repo_name, query_type), group in self.df.groupby(['repository_owner', 'repository_name', 'query_type']):
            graphql_times = group[group['api_type'] == 'graphql']['response_time_ms'].values
            rest_times = group[group['api_type'] == 'rest']['response_time_ms'].values
            
            if len(graphql_times) > 0 and len(rest_times) > 0:
                # Calcula médias para comparação pareada
                graphql_mean = np.mean(graphql_times)
                rest_mean = np.mean(rest_times)
                
                results.append({
                    'repository': f"{repo_owner}/{repo_name}",
                    'query_type': query_type,
                    'graphql_mean': graphql_mean,
                    'rest_mean': rest_mean,
                    'difference': graphql_mean - rest_mean,
                    'graphql_data': graphql_times,
                    'rest_data': rest_times
                })
        
        # Agrega todos os dados para análise geral
        all_graphql_times = self.df[self.df['api_type'] == 'graphql']['response_time_ms'].values
        all_rest_times = self.df[self.df['api_type'] == 'rest']['response_time_ms'].values
        
        # Estatísticas descritivas
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
        
        print(f"\nEstatísticas Descritivas - GraphQL:")
        print(f"  Média: {graphql_stats['mean']:.2f} ms")
        print(f"  Mediana: {graphql_stats['median']:.2f} ms")
        print(f"  Desvio Padrão: {graphql_stats['std']:.2f} ms")
        
        print(f"\nEstatísticas Descritivas - REST:")
        print(f"  Média: {rest_stats['mean']:.2f} ms")
        print(f"  Mediana: {rest_stats['median']:.2f} ms")
        print(f"  Desvio Padrão: {rest_stats['std']:.2f} ms")
        
        # Teste de normalidade
        graphql_normal, graphql_p = self.test_normality(pd.Series(all_graphql_times))
        rest_normal, rest_p = self.test_normality(pd.Series(all_rest_times))
        
        print(f"\nTeste de Normalidade:")
        print(f"  GraphQL: {'Normal' if graphql_normal else 'Não Normal'} (p={graphql_p:.4f})")
        print(f"  REST: {'Normal' if rest_normal else 'Não Normal'} (p={rest_p:.4f})")
        
        # Teste estatístico
        # Para comparação pareada, precisamos dos pares
        paired_differences = []
        for result in results:
            # Para cada grupo, calcula diferença média
            paired_differences.append(result['difference'])
        
        if len(paired_differences) > 1:
            # Teste t pareado ou Wilcoxon
            if graphql_normal and rest_normal:
                # Teste t pareado
                t_stat, p_value = ttest_rel(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results]
                )
                test_name = "Teste t pareado"
            else:
                # Teste de Wilcoxon
                t_stat, p_value = wilcoxon(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results],
                    alternative='two-sided'
                )
                test_name = "Teste de Wilcoxon"
            
            print(f"\n{test_name}:")
            print(f"  Estatística: {t_stat:.4f}")
            print(f"  p-value: {p_value:.4f}")
            
            # Tamanho do efeito (Cohen's d)
            mean_diff = np.mean(paired_differences)
            std_diff = np.std(paired_differences)
            cohens_d = mean_diff / std_diff if std_diff > 0 else 0
            
            print(f"  Cohen's d: {cohens_d:.4f}")
            
            # Interpretação
            if p_value < 0.05:
                if mean_diff < 0:
                    conclusion = "GraphQL é significativamente mais rápido que REST"
                else:
                    conclusion = "REST é significativamente mais rápido que GraphQL"
            else:
                conclusion = "Não há diferença significativa entre GraphQL e REST"
            
            print(f"  Conclusão: {conclusion}")
        else:
            p_value = 1.0
            conclusion = "Dados insuficientes para análise estatística"
            cohens_d = 0.0
        
        return {
            'graphql_stats': graphql_stats,
            'rest_stats': rest_stats,
            'test_name': test_name if len(paired_differences) > 1 else 'N/A',
            'p_value': p_value if len(paired_differences) > 1 else 1.0,
            'cohens_d': cohens_d,
            'conclusion': conclusion,
            'mean_difference': np.mean(paired_differences) if paired_differences else 0,
            'graphql_faster': np.mean(paired_differences) < 0 if paired_differences else False
        }
    
    def analyze_rq2(self) -> Dict:
        """
        Analisa RQ2: Respostas às consultas GraphQL têm tamanho menor que REST?
        
        Returns:
            Dict com resultados da análise
        """
        print("\n" + "="*60)
        print("ANÁLISE RQ2: Tamanho da Resposta")
        print("="*60)
        
        # Agrupa por repositório e tipo de consulta para fazer comparação pareada
        results = []
        
        for (repo_owner, repo_name, query_type), group in self.df.groupby(['repository_owner', 'repository_name', 'query_type']):
            graphql_sizes = group[group['api_type'] == 'graphql']['response_size_bytes'].values
            rest_sizes = group[group['api_type'] == 'rest']['response_size_bytes'].values
            
            if len(graphql_sizes) > 0 and len(rest_sizes) > 0:
                # Calcula médias para comparação pareada
                graphql_mean = np.mean(graphql_sizes)
                rest_mean = np.mean(rest_sizes)
                
                results.append({
                    'repository': f"{repo_owner}/{repo_name}",
                    'query_type': query_type,
                    'graphql_mean': graphql_mean,
                    'rest_mean': rest_mean,
                    'difference': graphql_mean - rest_mean,
                    'graphql_data': graphql_sizes,
                    'rest_data': rest_sizes
                })
        
        # Agrega todos os dados para análise geral
        all_graphql_sizes = self.df[self.df['api_type'] == 'graphql']['response_size_bytes'].values
        all_rest_sizes = self.df[self.df['api_type'] == 'rest']['response_size_bytes'].values
        
        # Estatísticas descritivas
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
        
        print(f"\nEstatísticas Descritivas - GraphQL:")
        print(f"  Média: {graphql_stats['mean']:.0f} bytes ({graphql_stats['mean']/1024:.2f} KB)")
        print(f"  Mediana: {graphql_stats['median']:.0f} bytes ({graphql_stats['median']/1024:.2f} KB)")
        print(f"  Desvio Padrão: {graphql_stats['std']:.0f} bytes")
        
        print(f"\nEstatísticas Descritivas - REST:")
        print(f"  Média: {rest_stats['mean']:.0f} bytes ({rest_stats['mean']/1024:.2f} KB)")
        print(f"  Mediana: {rest_stats['median']:.0f} bytes ({rest_stats['median']/1024:.2f} KB)")
        print(f"  Desvio Padrão: {rest_stats['std']:.0f} bytes")
        
        # Teste de normalidade
        graphql_normal, graphql_p = self.test_normality(pd.Series(all_graphql_sizes))
        rest_normal, rest_p = self.test_normality(pd.Series(all_rest_sizes))
        
        print(f"\nTeste de Normalidade:")
        print(f"  GraphQL: {'Normal' if graphql_normal else 'Não Normal'} (p={graphql_p:.4f})")
        print(f"  REST: {'Normal' if rest_normal else 'Não Normal'} (p={rest_p:.4f})")
        
        # Teste estatístico
        paired_differences = [r['difference'] for r in results]
        
        if len(paired_differences) > 1:
            # Teste t pareado ou Wilcoxon
            if graphql_normal and rest_normal:
                # Teste t pareado
                t_stat, p_value = ttest_rel(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results]
                )
                test_name = "Teste t pareado"
            else:
                # Teste de Wilcoxon
                t_stat, p_value = wilcoxon(
                    [r['graphql_mean'] for r in results],
                    [r['rest_mean'] for r in results],
                    alternative='two-sided'
                )
                test_name = "Teste de Wilcoxon"
            
            print(f"\n{test_name}:")
            print(f"  Estatística: {t_stat:.4f}")
            print(f"  p-value: {p_value:.4f}")
            
            # Tamanho do efeito (Cohen's d)
            mean_diff = np.mean(paired_differences)
            std_diff = np.std(paired_differences)
            cohens_d = mean_diff / std_diff if std_diff > 0 else 0
            
            print(f"  Cohen's d: {cohens_d:.4f}")
            
            # Interpretação
            if p_value < 0.05:
                if mean_diff < 0:
                    conclusion = "GraphQL produz respostas significativamente menores que REST"
                else:
                    conclusion = "REST produz respostas significativamente menores que GraphQL"
            else:
                conclusion = "Não há diferença significativa entre GraphQL e REST"
            
            print(f"  Conclusão: {conclusion}")
        else:
            p_value = 1.0
            conclusion = "Dados insuficientes para análise estatística"
            cohens_d = 0.0
        
        return {
            'graphql_stats': graphql_stats,
            'rest_stats': rest_stats,
            'test_name': test_name if len(paired_differences) > 1 else 'N/A',
            'p_value': p_value if len(paired_differences) > 1 else 1.0,
            'cohens_d': cohens_d,
            'conclusion': conclusion,
            'mean_difference': np.mean(paired_differences) if paired_differences else 0,
            'graphql_smaller': np.mean(paired_differences) < 0 if paired_differences else False
        }
    
    def analyze_by_query_type(self) -> Dict:
        """Analisa resultados por tipo de consulta"""
        print("\n" + "="*60)
        print("ANÁLISE POR TIPO DE CONSULTA")
        print("="*60)
        
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
                
                print(f"\n{query_type.upper()}:")
                print(f"  Tempo - GraphQL: {results_by_type[query_type]['graphql_time_mean']:.2f} ms, REST: {results_by_type[query_type]['rest_time_mean']:.2f} ms")
                print(f"  Tamanho - GraphQL: {results_by_type[query_type]['graphql_size_mean']:.0f} bytes, REST: {results_by_type[query_type]['rest_size_mean']:.0f} bytes")
        
        return results_by_type
    
    def generate_summary_report(self) -> str:
        """Gera um resumo textual dos resultados"""
        rq1_results = self.analyze_rq1()
        rq2_results = self.analyze_rq2()
        by_type = self.analyze_by_query_type()
        
        report = f"""
# Resumo dos Resultados do Experimento GraphQL vs REST

## RQ1: Tempo de Resposta
{self._format_rq_summary(rq1_results, 'tempo de resposta', 'ms')}

## RQ2: Tamanho da Resposta
{self._format_rq_summary(rq2_results, 'tamanho da resposta', 'bytes')}

## Análise por Tipo de Consulta
{self._format_by_type_summary(by_type)}
"""
        return report
    
    def _format_rq_summary(self, results: Dict, metric: str, unit: str) -> str:
        """Formata resumo de uma RQ"""
        graphql_mean = results['graphql_stats']['mean']
        rest_mean = results['rest_stats']['mean']
        p_value = results['p_value']
        conclusion = results['conclusion']
        
        return f"""
- GraphQL: Média = {graphql_mean:.2f} {unit}
- REST: Média = {rest_mean:.2f} {unit}
- Diferença: {graphql_mean - rest_mean:.2f} {unit}
- p-value: {p_value:.4f}
- Conclusão: {conclusion}
"""
    
    def _format_by_type_summary(self, by_type: Dict) -> str:
        """Formata resumo por tipo de consulta"""
        summary = ""
        for query_type, data in by_type.items():
            summary += f"\n{query_type.upper()}:\n"
            summary += f"  Tempo - GraphQL: {data['graphql_time_mean']:.2f} ms, REST: {data['rest_time_mean']:.2f} ms\n"
            summary += f"  Tamanho - GraphQL: {data['graphql_size_mean']:.0f} bytes, REST: {data['rest_size_mean']:.0f} bytes\n"
        return summary


def main():
    """Função principal"""
    analyzer = ExperimentAnalyzer("experiment_data.csv")
    
    if not analyzer.load_data():
        print("Erro ao carregar dados. Verifique se o arquivo experiment_data.csv existe.")
        return
    
    # Executa análises
    rq1_results = analyzer.analyze_rq1()
    rq2_results = analyzer.analyze_rq2()
    by_type = analyzer.analyze_by_query_type()
    
    # Salva resultados
    analyzer.results = {
        'rq1': rq1_results,
        'rq2': rq2_results,
        'by_type': by_type
    }
    
    # Gera relatório
    report = analyzer.generate_summary_report()
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(report)
    
    # Salva relatório
    with open("analysis_summary.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\nRelatório salvo em analysis_summary.txt")


if __name__ == "__main__":
    main()

