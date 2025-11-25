#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera dados de exemplo para testar o dashboard e análise
Útil para desenvolvimento e testes sem precisar executar o experimento completo
"""

import csv
import random
import numpy as np
from datetime import datetime

def generate_sample_data(num_repos=20, num_replicas=30):
    """
    Gera dados de exemplo simulando resultados do experimento
    
    Args:
        num_repos: Número de repositórios
        num_replicas: Número de réplicas por combinação
    """
    repositories = [
        ('facebook', 'react'),
        ('microsoft', 'vscode'),
        ('tensorflow', 'tensorflow'),
        ('microsoft', 'TypeScript'),
        ('facebook', 'react-native'),
        ('vercel', 'next.js'),
        ('kubernetes', 'kubernetes'),
        ('microsoft', 'PowerToys'),
        ('flutter', 'flutter'),
        ('golang', 'go'),
        ('rust-lang', 'rust'),
        ('pytorch', 'pytorch'),
        ('microsoft', 'terminal'),
        ('facebook', 'create-react-app'),
        ('angular', 'angular'),
        ('vuejs', 'vue'),
        ('nodejs', 'node'),
        ('microsoft', 'vscode-docs'),
        ('microsoft', 'playwright'),
        ('microsoft', 'monaco-editor')
    ]
    
    query_types = ['simple', 'complex', 'multiple']
    api_types = ['graphql', 'rest']
    
    measurements = []
    
    # Parâmetros para simulação realista
    # GraphQL tende a ser mais rápido mas com tamanho similar ou menor
    graphql_time_base = 150  # ms
    rest_time_base = 200     # ms
    
    graphql_size_base = 5000   # bytes
    rest_size_base = 6000     # bytes
    
    for owner, name in repositories[:num_repos]:
        for query_type in query_types:
            for api_type in api_types:
                for replica in range(num_replicas):
                    # Simula variação realista
                    if api_type == 'graphql':
                        # GraphQL: mais rápido, tamanho menor
                        time_ms = np.random.normal(
                            graphql_time_base * (1.2 if query_type == 'complex' else 1.0 if query_type == 'simple' else 1.5),
                            30
                        )
                        size_bytes = np.random.normal(
                            graphql_size_base * (1.3 if query_type == 'complex' else 1.0 if query_type == 'simple' else 2.0),
                            500
                        )
                    else:  # rest
                        # REST: mais lento, tamanho maior
                        time_ms = np.random.normal(
                            rest_time_base * (1.3 if query_type == 'complex' else 1.0 if query_type == 'simple' else 1.8),
                            40
                        )
                        size_bytes = np.random.normal(
                            rest_size_base * (1.4 if query_type == 'complex' else 1.0 if query_type == 'simple' else 2.5),
                            600
                        )
                    
                    # Garante valores positivos
                    time_ms = max(50, time_ms)
                    size_bytes = max(1000, size_bytes)
                    
                    measurement = {
                        'timestamp': datetime.now().isoformat(),
                        'query_type': query_type,
                        'api_type': api_type,
                        'repository_owner': owner,
                        'repository_name': name,
                        'response_time_ms': round(time_ms, 2),
                        'response_size_bytes': int(size_bytes),
                        'success': True,
                        'error': None
                    }
                    measurements.append(measurement)
    
    # Salva em CSV
    fieldnames = [
        'timestamp', 'query_type', 'api_type', 'repository_owner', 
        'repository_name', 'response_time_ms', 'response_size_bytes', 
        'success', 'error'
    ]
    
    filename = 'experiment_data.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(measurements)
    
    print(f"Dados de exemplo gerados: {len(measurements)} medições")
    print(f"Arquivo salvo: {filename}")
    print("\nEstatísticas simuladas:")
    
    graphql_times = [m['response_time_ms'] for m in measurements if m['api_type'] == 'graphql']
    rest_times = [m['response_time_ms'] for m in measurements if m['api_type'] == 'rest']
    
    print(f"  GraphQL - Tempo médio: {np.mean(graphql_times):.2f} ms")
    print(f"  REST    - Tempo médio: {np.mean(rest_times):.2f} ms")
    
    graphql_sizes = [m['response_size_bytes'] for m in measurements if m['api_type'] == 'graphql']
    rest_sizes = [m['response_size_bytes'] for m in measurements if m['api_type'] == 'rest']
    
    print(f"  GraphQL - Tamanho médio: {np.mean(graphql_sizes):.0f} bytes")
    print(f"  REST    - Tamanho médio: {np.mean(rest_sizes):.0f} bytes")


def main():
    """Função principal"""
    print("Gerando dados de exemplo para testes...")
    print("(Estes dados são simulados e não representam medições reais)\n")
    
    generate_sample_data(num_repos=20, num_replicas=30)
    
    print("\nDados gerados! Agora você pode:")
    print("  1. Executar: python experiment_analyzer.py")
    print("  2. Executar: python dashboard.py")


if __name__ == "__main__":
    main()


