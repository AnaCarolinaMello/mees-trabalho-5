#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para coleta de dados do experimento GraphQL vs REST
Mede tempo de resposta e tamanho das respostas para ambas as APIs
"""

import requests
import json
import time
import os
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import random

class ExperimentCollector:
    def __init__(self, github_token: str):
        """
        Inicializa o coletor de dados do experimento
        
        Args:
            github_token: Token de acesso do GitHub
        """
        self.token = github_token
        self.graphql_url = "https://api.github.com/graphql"
        self.rest_base_url = "https://api.github.com"
        
        self.graphql_headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        self.rest_headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def measure_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Tuple[float, int, Dict]:
        """
        Executa uma query GraphQL e mede tempo e tamanho da resposta
        
        Returns:
            Tuple: (tempo_ms, tamanho_bytes, dados_resposta)
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        start_time = time.perf_counter()
        
        try:
            response = requests.post(
                self.graphql_url,
                headers=self.graphql_headers,
                json=payload,
                timeout=30
            )
            
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            
            # Tamanho da resposta (headers + body)
            response_size = len(response.content) + len(str(response.headers))
            
            response_data = response.json() if response.status_code == 200 else None
            
            return elapsed_ms, response_size, response_data
            
        except Exception as e:
            print(f"Erro na query GraphQL: {e}")
            return None, None, None
    
    def measure_rest_request(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[float, int, Dict]:
        """
        Executa uma requisição REST e mede tempo e tamanho da resposta
        
        Returns:
            Tuple: (tempo_ms, tamanho_bytes, dados_resposta)
        """
        url = f"{self.rest_base_url}{endpoint}"
        
        start_time = time.perf_counter()
        
        try:
            response = requests.get(
                url,
                headers=self.rest_headers,
                params=params,
                timeout=30
            )
            
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            
            # Tamanho da resposta (headers + body)
            response_size = len(response.content) + len(str(response.headers))
            
            response_data = response.json() if response.status_code == 200 else None
            
            return elapsed_ms, response_size, response_data
            
        except Exception as e:
            print(f"Erro na requisição REST: {e}")
            return None, None, None
    
    def get_repository_info_graphql(self, owner: str, name: str) -> str:
        """Gera query GraphQL para obter informações básicas do repositório"""
        query = f"""
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                name
                description
                stargazerCount
                forkCount
                watchers {{
                    totalCount
                }}
                issues {{
                    totalCount
                }}
                pullRequests {{
                    totalCount
                }}
                createdAt
                updatedAt
                primaryLanguage {{
                    name
                }}
            }}
        }}
        """
        return query
    
    def get_repository_info_rest(self, owner: str, name: str) -> Tuple[str, Dict]:
        """Gera endpoint REST para obter informações básicas do repositório"""
        endpoint = f"/repos/{owner}/{name}"
        return endpoint, {}
    
    def get_repository_with_issues_graphql(self, owner: str, name: str, limit: int = 10) -> str:
        """Gera query GraphQL para obter repositório com issues"""
        query = f"""
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                name
                description
                stargazerCount
                issues(first: {limit}) {{
                    totalCount
                    nodes {{
                        number
                        title
                        state
                        createdAt
                        author {{
                            login
                        }}
                        comments {{
                            totalCount
                        }}
                    }}
                }}
            }}
        }}
        """
        return query
    
    def get_repository_with_issues_rest(self, owner: str, name: str, limit: int = 10) -> Tuple[str, Dict]:
        """Gera endpoint REST para obter repositório com issues"""
        endpoint = f"/repos/{owner}/{name}"
        issues_endpoint = f"/repos/{owner}/{name}/issues"
        params = {"per_page": limit, "state": "all"}
        return issues_endpoint, params
    
    def get_multiple_repositories_graphql(self, repos: List[Tuple[str, str]]) -> str:
        """Gera query GraphQL para obter múltiplos repositórios"""
        aliases = []
        for i, (owner, name) in enumerate(repos):
            alias = f"repo{i}"
            aliases.append(f"""
            {alias}: repository(owner: "{owner}", name: "{name}") {{
                name
                description
                stargazerCount
                forkCount
                primaryLanguage {{
                    name
                }}
            }}
            """)
        
        query = f"query {{ {''.join(aliases)} }}"
        return query
    
    def get_multiple_repositories_rest(self, repos: List[Tuple[str, str]]) -> List[Tuple[str, Dict]]:
        """Gera endpoints REST para obter múltiplos repositórios"""
        endpoints = []
        for owner, name in repos:
            endpoint = f"/repos/{owner}/{name}"
            endpoints.append((endpoint, {}))
        return endpoints
    
    def collect_measurement(self, query_type: str, api_type: str, 
                           owner: str, name: str, 
                           additional_params: Optional[Dict] = None) -> Dict:
        """
        Coleta uma medição para um tipo de consulta específico
        
        Args:
            query_type: 'simple', 'complex', 'multiple'
            api_type: 'graphql' ou 'rest'
            owner: Owner do repositório
            name: Nome do repositório
            additional_params: Parâmetros adicionais (ex: limit para issues)
        
        Returns:
            Dict com os dados da medição
        """
        measurement = {
            'timestamp': datetime.now().isoformat(),
            'query_type': query_type,
            'api_type': api_type,
            'repository_owner': owner,
            'repository_name': name,
            'response_time_ms': None,
            'response_size_bytes': None,
            'success': False,
            'error': None
        }
        
        try:
            if api_type == 'graphql':
                if query_type == 'simple':
                    query = self.get_repository_info_graphql(owner, name)
                    time_ms, size_bytes, data = self.measure_graphql_query(query)
                elif query_type == 'complex':
                    limit = additional_params.get('limit', 10) if additional_params else 10
                    query = self.get_repository_with_issues_graphql(owner, name, limit)
                    time_ms, size_bytes, data = self.measure_graphql_query(query)
                elif query_type == 'multiple':
                    repos = additional_params.get('repos', [(owner, name)]) if additional_params else [(owner, name)]
                    query = self.get_multiple_repositories_graphql(repos)
                    time_ms, size_bytes, data = self.measure_graphql_query(query)
                else:
                    raise ValueError(f"Tipo de consulta desconhecido: {query_type}")
            
            elif api_type == 'rest':
                if query_type == 'simple':
                    endpoint, params = self.get_repository_info_rest(owner, name)
                    time_ms, size_bytes, data = self.measure_rest_request(endpoint, params)
                elif query_type == 'complex':
                    limit = additional_params.get('limit', 10) if additional_params else 10
                    endpoint, params = self.get_repository_with_issues_rest(owner, name, limit)
                    time_ms, size_bytes, data = self.measure_rest_request(endpoint, params)
                elif query_type == 'multiple':
                    repos = additional_params.get('repos', [(owner, name)]) if additional_params else [(owner, name)]
                    endpoints = self.get_multiple_repositories_rest(repos)
                    # Para REST, precisamos fazer múltiplas requisições
                    total_time = 0
                    total_size = 0
                    all_data = []
                    for endpoint, params in endpoints:
                        t, s, d = self.measure_rest_request(endpoint, params)
                        if t is not None:
                            total_time += t
                            total_size += s
                            all_data.append(d)
                    time_ms = total_time
                    size_bytes = total_size
                    data = all_data
                else:
                    raise ValueError(f"Tipo de consulta desconhecido: {query_type}")
            else:
                raise ValueError(f"Tipo de API desconhecido: {api_type}")
            
            if time_ms is not None and size_bytes is not None:
                measurement['response_time_ms'] = time_ms
                measurement['response_size_bytes'] = size_bytes
                measurement['success'] = True
            else:
                measurement['error'] = "Falha na requisição"
        
        except Exception as e:
            measurement['error'] = str(e)
        
        return measurement
    
    def run_experiment_trial(self, repositories: List[Tuple[str, str]], 
                            num_replicas: int = 30) -> List[Dict]:
        """
        Executa um trial completo do experimento
        
        Args:
            repositories: Lista de tuplas (owner, name) de repositórios
            num_replicas: Número de réplicas por combinação
        
        Returns:
            Lista com todas as medições coletadas
        """
        all_measurements = []
        query_types = ['simple', 'complex', 'multiple']
        api_types = ['graphql', 'rest']
        
        total_combinations = len(repositories) * len(query_types) * len(api_types) * num_replicas
        current = 0
        
        print(f"Iniciando experimento com {len(repositories)} repositórios")
        print(f"Total de medições: {total_combinations}")
        
        for owner, name in repositories:
            for query_type in query_types:
                # Randomiza ordem dos tratamentos
                api_order = ['graphql', 'rest']
                random.shuffle(api_order)
                
                for api_type in api_order:
                    additional_params = None
                    if query_type == 'complex':
                        additional_params = {'limit': 10}
                    elif query_type == 'multiple':
                        # Para múltiplos repositórios, usa os primeiros 3
                        additional_params = {'repos': repositories[:3]}
                    
                    for replica in range(num_replicas):
                        current += 1
                        if current % 50 == 0:
                            print(f"Progresso: {current}/{total_combinations} ({current/total_combinations*100:.1f}%)")
                        
                        measurement = self.collect_measurement(
                            query_type, api_type, owner, name, additional_params
                        )
                        all_measurements.append(measurement)
                        
                        # Pequena pausa para evitar rate limiting
                        time.sleep(0.1)
        
        print(f"Experimento concluído! Total de medições: {len(all_measurements)}")
        return all_measurements
    
    def save_measurements(self, measurements: List[Dict], filename: str = "experiment_data.csv"):
        """Salva as medições em arquivo CSV"""
        if not measurements:
            print("Nenhuma medição para salvar")
            return
        
        fieldnames = [
            'timestamp', 'query_type', 'api_type', 'repository_owner', 
            'repository_name', 'response_time_ms', 'response_size_bytes', 
            'success', 'error'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for measurement in measurements:
                writer.writerow(measurement)
        
        print(f"Medições salvas em {filename}")
        print(f"Total de medições: {len(measurements)}")
        print(f"Medições bem-sucedidas: {sum(1 for m in measurements if m['success'])}")


def get_popular_repositories(limit: int = 20) -> List[Tuple[str, str]]:
    """
    Retorna uma lista de repositórios populares do GitHub
    Para simplificar, usa uma lista pré-definida
    """
    popular_repos = [
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
    
    return popular_repos[:limit]


def main():
    """Função principal"""
    # Carrega token do GitHub
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("ERRO: Token do GitHub não encontrado!")
        print("Configure a variável de ambiente GITHUB_TOKEN")
        print("Exemplo: set GITHUB_TOKEN=seu_token_aqui")
        return
    
    # Cria coletor
    collector = ExperimentCollector(token)
    
    # Obtém repositórios populares
    repositories = get_popular_repositories(limit=20)
    
    print(f"Repositórios selecionados: {len(repositories)}")
    for owner, name in repositories[:5]:
        print(f"  - {owner}/{name}")
    print("  ...")
    
    # Executa experimento
    measurements = collector.run_experiment_trial(repositories, num_replicas=30)
    
    # Salva resultados
    collector.save_measurements(measurements, "experiment_data.csv")
    
    # Estatísticas básicas
    successful = [m for m in measurements if m['success']]
    if successful:
        graphql_times = [m['response_time_ms'] for m in successful if m['api_type'] == 'graphql']
        rest_times = [m['response_time_ms'] for m in successful if m['api_type'] == 'rest']
        
        graphql_sizes = [m['response_size_bytes'] for m in successful if m['api_type'] == 'graphql']
        rest_sizes = [m['response_size_bytes'] for m in successful if m['api_type'] == 'rest']
        
        print("\n" + "="*60)
        print("ESTATÍSTICAS PRELIMINARES")
        print("="*60)
        print(f"\nTempo de Resposta (ms):")
        print(f"  GraphQL - Média: {sum(graphql_times)/len(graphql_times):.2f}, Mediana: {sorted(graphql_times)[len(graphql_times)//2]:.2f}")
        print(f"  REST    - Média: {sum(rest_times)/len(rest_times):.2f}, Mediana: {sorted(rest_times)[len(rest_times)//2]:.2f}")
        
        print(f"\nTamanho da Resposta (bytes):")
        print(f"  GraphQL - Média: {sum(graphql_sizes)/len(graphql_sizes):.0f}, Mediana: {sorted(graphql_sizes)[len(graphql_sizes)//2]:.0f}")
        print(f"  REST    - Média: {sum(rest_sizes)/len(rest_sizes):.0f}, Mediana: {sorted(rest_sizes)[len(rest_sizes)//2]:.0f}")


if __name__ == "__main__":
    main()


