import requests
import json
import csv
import os
from datetime import datetime
import time

class GitHubAnalyzer:
    def __init__(self, token):
        """
        Inicializa o analisador de Pull Requests com token de acesso do GitHub
        """

        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.github.com/graphql"
    
    def create_repos_query(self, cursor=None):
        """
        Cria a query GraphQL para buscar os repositórios mais populares
        """
        after_clause = f', after: "{cursor}"' if cursor else ""
        
        query = f"""
        query {{
            search(query: "stars:>1000", type: REPOSITORY, first: 20{after_clause}) {{
                pageInfo {{
                    hasNextPage
                    endCursor
                }}
                nodes {{
                    ... on Repository {{
                        name
                        owner {{
                            login
                        }}
                        stargazerCount
                        primaryLanguage {{
                            name
                        }}
                        pullRequests (states: [MERGED, CLOSED]) {{
                            totalCount
                        }}
                        url
                    }}
                }}
            }}
        }}
        """
        return query
    
    def create_prs_query(self, owner, name, cursor=None):
        """
        Cria a query GraphQL para buscar PRs de um repositório específico
        Ordena por número de reviews (descendente)
        """
        after_clause = f', after: "{cursor}"' if cursor else ""
        
        query = f"""
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                pullRequests(states: [MERGED, CLOSED], first:20{after_clause}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                    nodes {{
                        number
                        title
                        state
                        createdAt
                        closedAt
                        mergedAt
                        author {{
                            login
                        }}
                        mergeable
                        baseRefName
                        headRefName
                        additions
                        deletions
                        changedFiles
                        comments {{
                            totalCount
                        }}
                        reviews {{
                            totalCount
                        }}
                        reviewRequests {{
                            totalCount
                        }}
                        commits {{
                            totalCount
                        }}
                        labels(first: 10) {{
                            nodes {{
                                name
                            }}
                        }}
                        reviewDecision
                        isDraft
                        assignees {{
                            totalCount
                        }}
                        participants {{
                            totalCount
                        }}
                        files(first: 1) {{
                            nodes {{
                                path
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        return query
    
    def make_request(self, query):
        """
        Faz a requisição GraphQL para a API do GitHub
        """

        payload = {"query": query}
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("ERRO: Token inválido ou expirado!")
                print("Verifique se seu token GitHub está correto e tem as permissões necessárias.")
                return None
            elif response.status_code == 403:
                print("ERRO: Rate limit atingido ou permissões insuficientes!")
                print("Aguarde alguns minutos ou verifique as permissões do token.")
                return None
            elif response.status_code >= 500:
                print(f"ERRO: Problema temporário no servidor GitHub (Código {response.status_code})")
                print("Tente novamente em alguns minutos.")
                return None
            else:
                print(f"Erro na requisição: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
            return None
    
    def calculate_pr_lifetime_hours(self, created_at, closed_at):
        """
        Calcula o tempo de vida do PR em horas
        """
        if not closed_at:
            return None

        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        closed_date = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
        return (closed_date - created_date).total_seconds() / 3600
    
    def calculate_time_to_merge_hours(self, created_at, merged_at):
        """
        Calcula o tempo até merge em horas
        """
        if not merged_at:
            return None
        
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        merged_date = datetime.fromisoformat(merged_at.replace('Z', '+00:00'))
        return (merged_date - created_date).total_seconds() / 3600
    
    def extract_labels(self, labels_data):
        """
        Extrai nomes das labels
        """
        if not labels_data or not labels_data.get('nodes'):
            return []
        return [label['name'] for label in labels_data['nodes']]
    
    def collect_popular_repositories(self, limit=200):
        """
        Coleta repositórios populares com pelo menos 100 PRs
        """
        repositories = []
        cursor = None
        collected = 0
        
        print(f"Buscando repositórios populares com 100+ PRs...")
        print(f"Alvo: {limit} repositórios válidos")
        
        while collected < limit:
            query = self.create_repos_query(cursor)
            response_data = self.make_request(query)
            
            if not response_data or 'data' not in response_data:
                print("Erro ao obter dados da API")
                break
            
            search_results = response_data['data']['search']
            repos = search_results['nodes']
            
            for repo in repos:
                if collected >= limit:
                    break
                    
                # Filtrar repositórios com pelo menos 100 PRs
                pr_count = repo['pullRequests']['totalCount']
                if pr_count >= 100:
                    repo_data = {
                        'name': repo['name'],
                        'owner': repo['owner']['login'],
                        'stars': repo['stargazerCount'],
                        'total_prs': pr_count,
                        'primary_language': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "Unknown",
                        'url': repo['url']
                    }
                    repositories.append(repo_data)
                    collected += 1
                    
                    if collected % 10 == 0:
                        print(f"Coletados {collected}/{limit} repositórios válidos ({(collected/limit)*100:.1f}%)")

            if not search_results['pageInfo']['hasNextPage'] or collected >= limit:
                break
                
            cursor = search_results['pageInfo']['endCursor']
            time.sleep(1)
            
        print(f"\nRESULTADO DA COLETA:")
        print(f"  Total analisados: {collected} repositórios")
        print(f"  Válidos coletados: {len(repositories)} repositórios (>= 100 PRs)")
        if collected > 0:
            print(f"  Taxa de aprovação: {len(repositories)/collected*100:.1f}%")
        else:
            print(f"  Taxa de aprovação: N/A (nenhum repositório analisado)")
        
        return repositories
    
    def process_pull_request_data(self, pr, repo_info):
        """
        Processa os dados de um Pull Request individual
        """
        labels = self.extract_labels(pr.get('labels', {}))
        
        return {
            'name': repo_info['name'],
            'owner': repo_info['owner'],
            'stars': repo_info['stars'],
            'language': repo_info['primary_language'],
            'pr_number': pr['number'],
            'pr_title': pr['title'],
            'pr_state': pr['state'],
            'pr_author': pr['author']['login'] if pr['author'] else 'ghost',
            'pr_created_at': pr['createdAt'],
            'pr_closed_at': pr['closedAt'],
            'pr_merged_at': pr['mergedAt'],
            'pr_is_merged': pr['state'] == 'MERGED',
            'pr_base_branch': pr['baseRefName'],
            'pr_head_branch': pr['headRefName'],
            'pr_additions': pr['additions'],
            'pr_deletions': pr['deletions'],
            'pr_changed_files': pr['changedFiles'],
            'pr_total_changes': pr['additions'] + pr['deletions'],
            'pr_comments_count': pr['comments']['totalCount'],
            'pr_reviews_count': pr['reviews']['totalCount'],
            'pr_review_requests_count': pr['reviewRequests']['totalCount'],
            'pr_commits_count': pr['commits']['totalCount'],
            'pr_participants_count': pr['participants']['totalCount'],
            'pr_assignees_count': pr['assignees']['totalCount'],
            'pr_labels': '|'.join(labels),
            'pr_labels_count': len(labels),
            'pr_review_decision': pr.get('reviewDecision', ''),
            'pr_is_draft': pr.get('isDraft', False),
            'pr_lifetime_hours': self.calculate_pr_lifetime_hours(pr['createdAt'], pr['closedAt']),
            'pr_time_to_merge_hours': self.calculate_time_to_merge_hours(pr['createdAt'], pr['mergedAt']),
            'has_code_review': pr['reviews']['totalCount'] > 0
        }
    
    def collect_pull_requests_data(self, repositories, limit=100):
        """
        Coleta dados de Pull Requests dos repositórios selecionados
        """
        all_prs = []
        total_repos = len(repositories)
        
        print(f"Iniciando coleta de PRs de {total_repos} repositórios...")
        
        for i, repo in enumerate(repositories, 1):
            print(f"Processando repositório {i}/{total_repos}: {repo['owner']}/{repo['name']} ({repo['total_prs']} PRs)")
            
            cursor = None
            collected_prs = 0
            
            while collected_prs < limit:
                query = self.create_prs_query(repo['owner'], repo['name'], cursor)
                response_data = self.make_request(query)

                if not response_data or 'data' not in response_data:
                    print(f"  Erro ao obter PRs de {repo['name']}")
                    break
                
                if not response_data['data']['repository']:
                    print(f"  Repositório {repo['name']} não encontrado")
                    break
                
                pr_data = response_data['data']['repository']['pullRequests']
                prs = pr_data['nodes']
                
                # Filtrar PRs com pelo menos 1 review
                filtered_prs = [pr for pr in prs if pr['reviews']['totalCount'] >= 1]
                
                # Ordenar por número de reviews (descendente)
                filtered_prs.sort(key=lambda x: x['reviews']['totalCount'], reverse=True)
                
                for pr in filtered_prs:
                    if collected_prs >= limit:
                        break
                    
                    try:
                        processed_pr = self.process_pull_request_data(pr, repo)
                        if ((processed_pr['pr_lifetime_hours'] is not None and processed_pr['pr_lifetime_hours'] >= 1) or
                            (processed_pr['pr_time_to_merge_hours'] is not None and processed_pr['pr_time_to_merge_hours'] >= 1)):
                            all_prs.append(processed_pr)
                            collected_prs += 1
                            if collected_prs % 10 == 0:
                                print(f"Coletados {collected_prs}/{limit} PRs ({(collected_prs/limit)*100:.1f}%)")
                    except Exception as e:
                        print(f"  Erro ao processar PR #{pr.get('number', 'Unknown')}: {e}")
                        continue
                
                if not pr_data['pageInfo']['hasNextPage'] or collected_prs >= limit:
                    break
                    
                cursor = pr_data['pageInfo']['endCursor']
                time.sleep(1)
            
            print(f"  PRs {collected_prs} coletados, com code review ({(collected_prs/limit)*100:.1f}%)")
            
            if i % 10 == 0:
                print(f"Progresso geral: {i}/{total_repos} repositórios processados, {len(all_prs)} PRs coletados")
            
            # Pausa entre repositórios para evitar rate limit
            time.sleep(2)
        
        print(f"Coleta finalizada. Total: {len(all_prs)} PRs com pelo menos 1 review")
        
        # Ordenar todos os PRs por número de reviews (descendente)
        all_prs.sort(key=lambda x: x['pr_reviews_count'], reverse=True)
        print(f"PRs ordenados por número de reviews (maior para menor)")
        
        return all_prs
    
    def save_to_csv(self, pull_requests, filename="pull_requests_code_review.csv"):
        """
        Salva os dados dos Pull Requests em arquivo CSV
        """
        if not pull_requests:
            print("Nenhum dado para salvar")
            return
        
        fieldnames = [
            'name', 'owner', 'stars', 'language',
            'pr_number', 'pr_title', 'pr_state', 'pr_author', 
            'pr_created_at', 'pr_closed_at', 'pr_merged_at', 'pr_is_merged',
            'pr_base_branch', 'pr_head_branch', 'pr_additions', 'pr_deletions',
            'pr_changed_files', 'pr_total_changes', 'pr_comments_count',
            'pr_reviews_count', 'pr_review_requests_count', 'pr_commits_count',
            'pr_participants_count', 'pr_assignees_count', 'pr_labels',
            'pr_labels_count', 'pr_review_decision', 'pr_is_draft',
            'pr_lifetime_hours', 'pr_time_to_merge_hours', 'has_code_review'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pull_requests)
        
        print(f"Dados salvos em {filename}")
    
    def print_summary(self, pull_requests):
        """
        Imprime um resumo dos dados de Pull Requests coletados
        """
        if not pull_requests:
            return
        
        print("\n" + "="*60)
        print("RESUMO DOS DADOS DE PULL REQUESTS COLETADOS")
        print("="*60)
        
        total_prs = len(pull_requests)
        merged_prs = sum(1 for pr in pull_requests if pr['pr_is_merged'])
        closed_prs = total_prs - merged_prs
        
        print(f"Total de PRs coletados: {total_prs:,}")
        print(f"PRs merged: {merged_prs:,} ({merged_prs/total_prs*100:.1f}%)")
        print(f"PRs closed (não merged): {closed_prs:,} ({closed_prs/total_prs*100:.1f}%)")
        
        # Estatísticas de reviews
        reviews = [pr['pr_reviews_count'] for pr in pull_requests]
        comments = [pr['pr_comments_count'] for pr in pull_requests]
        participants = [pr['pr_participants_count'] for pr in pull_requests]
        
        print(f"\nEstatísticas de Code Review:")
        print(f"  Reviews por PR - Mediana: {sorted(reviews)[len(reviews)//2]}, Média: {sum(reviews)/len(reviews):.1f}")
        print(f"  Comentários por PR - Mediana: {sorted(comments)[len(comments)//2]}, Média: {sum(comments)/len(comments):.1f}")
        print(f"  Participantes por PR - Mediana: {sorted(participants)[len(participants)//2]}, Média: {sum(participants)/len(participants):.1f}")
        
        # Estatísticas de tempo
        merged_times = [pr['pr_time_to_merge_hours'] for pr in pull_requests if pr['pr_time_to_merge_hours'] is not None]
        if merged_times:
            print(f"\nTempo até merge (horas):")
            print(f"  Mediana: {sorted(merged_times)[len(merged_times)//2]:.1f}h")
            print(f"  Média: {sum(merged_times)/len(merged_times):.1f}h")
        
        # Estatísticas de mudanças
        changes = [pr['pr_total_changes'] for pr in pull_requests]
        files = [pr['pr_changed_files'] for pr in pull_requests]
        
        print(f"\nTamanho dos PRs:")
        print(f"  Linhas alteradas - Mediana: {sorted(changes)[len(changes)//2]:,}, Média: {sum(changes)/len(changes):.0f}")
        print(f"  Arquivos alterados - Mediana: {sorted(files)[len(files)//2]}, Média: {sum(files)/len(files):.1f}")
        
        # Linguagens
        languages = {}
        for pr in pull_requests:
            lang = pr['language']
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"\nTop 10 linguagens:")
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        for lang, count in sorted_langs[:10]:
            print(f"  {lang}: {count} PRs")
        
        # Review decisions
        decisions = {}
        for pr in pull_requests:
            decision = pr['pr_review_decision'] or 'NO_DECISION'
            decisions[decision] = decisions.get(decision, 0) + 1
        
        print(f"\nDecisões de review:")
        for decision, count in sorted(decisions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {decision}: {count} PRs ({count/total_prs*100:.1f}%)")
    
    def analyze_merge_factors(self, pull_requests):
        """
        Analisa fatores que influenciam no merge de Pull Requests
        """

        if not pull_requests:
            return
        
        print("\n" + "="*80)
        print("ANÁLISE DE FATORES QUE INFLUENCIAM NO MERGE DE PULL REQUESTS")
        print("="*80)
        
        merged_prs = [pr for pr in pull_requests if pr['pr_is_merged']]
        closed_prs = [pr for pr in pull_requests if not pr['pr_is_merged']]
        
        print(f"\nCOMPARAÇÃO: PRs MERGED vs CLOSED")
        print(f"Total PRs: {len(pull_requests):,}")
        print(f"PRs Merged: {len(merged_prs):,} ({len(merged_prs)/len(pull_requests)*100:.1f}%)")
        print(f"PRs Closed: {len(closed_prs):,} ({len(closed_prs)/len(pull_requests)*100:.1f}%)")
        
        # Análise por tamanho do PR
        print(f"\nINFLUÊNCIA DO TAMANHO DO PR:")
        merged_changes = [pr['pr_total_changes'] for pr in merged_prs]
        closed_changes = [pr['pr_total_changes'] for pr in closed_prs]
        
        if merged_changes and closed_changes:
            merged_median = sorted(merged_changes)[len(merged_changes)//2]
            closed_median = sorted(closed_changes)[len(closed_changes)//2]
            print(f"  Linhas alteradas - Merged: {merged_median:,} | Closed: {closed_median:,}")
            
            merged_files = [pr['pr_changed_files'] for pr in merged_prs]
            closed_files = [pr['pr_changed_files'] for pr in closed_prs]
            merged_files_median = sorted(merged_files)[len(merged_files)//2]
            closed_files_median = sorted(closed_files)[len(closed_files)//2]
            print(f"  Arquivos alterados - Merged: {merged_files_median} | Closed: {closed_files_median}")
        
        # Análise por atividade de review
        print(f"\nINFLUÊNCIA DA ATIVIDADE DE REVIEW:")
        merged_reviews = [pr['pr_reviews_count'] for pr in merged_prs]
        closed_reviews = [pr['pr_reviews_count'] for pr in closed_prs]
        
        if merged_reviews and closed_reviews:
            merged_rev_median = sorted(merged_reviews)[len(merged_reviews)//2]
            closed_rev_median = sorted(closed_reviews)[len(closed_reviews)//2]
            print(f"  Reviews - Merged: {merged_rev_median} | Closed: {closed_rev_median}")
            
            merged_comments = [pr['pr_comments_count'] for pr in merged_prs]
            closed_comments = [pr['pr_comments_count'] for pr in closed_prs]
            merged_comm_median = sorted(merged_comments)[len(merged_comments)//2]
            closed_comm_median = sorted(closed_comments)[len(closed_comments)//2]
            print(f"  Comentários - Merged: {merged_comm_median} | Closed: {closed_comm_median}")
            
            merged_participants = [pr['pr_participants_count'] for pr in merged_prs]
            closed_participants = [pr['pr_participants_count'] for pr in closed_prs]
            merged_part_median = sorted(merged_participants)[len(merged_participants)//2]
            closed_part_median = sorted(closed_participants)[len(closed_participants)//2]
            print(f"  Participantes - Merged: {merged_part_median} | Closed: {closed_part_median}")
        
        # Análise por linguagem
        print(f"\nINFLUÊNCIA DA LINGUAGEM:")
        lang_stats = {}
        for pr in pull_requests:
            lang = pr['language']
            if lang not in lang_stats:
                lang_stats[lang] = {'total': 0, 'merged': 0}
            lang_stats[lang]['total'] += 1
            if pr['pr_is_merged']:
                lang_stats[lang]['merged'] += 1
        
        # Calcular taxa de merge por linguagem
        lang_merge_rates = []
        for lang, stats in lang_stats.items():
            if stats['total'] >= 10:  # Apenas linguagens com pelo menos 10 PRs
                merge_rate = stats['merged'] / stats['total']
                lang_merge_rates.append((lang, merge_rate, stats['total']))
        
        lang_merge_rates.sort(key=lambda x: x[1], reverse=True)
        
        print(f"  Taxa de merge por linguagem (mín. 10 PRs):")
        for lang, rate, total in lang_merge_rates[:10]:
            print(f"    {lang}: {rate*100:.1f}% ({total} PRs)")
        
        # Análise por decisão de review
        print(f"\nINFLUÊNCIA DA DECISÃO DE REVIEW:")
        decision_stats = {}
        for pr in pull_requests:
            decision = pr['pr_review_decision'] or 'NO_DECISION'
            if decision not in decision_stats:
                decision_stats[decision] = {'total': 0, 'merged': 0}
            decision_stats[decision]['total'] += 1
            if pr['pr_is_merged']:
                decision_stats[decision]['merged'] += 1
        
        for decision, stats in decision_stats.items():
            merge_rate = stats['merged'] / stats['total'] if stats['total'] > 0 else 0
            print(f"  {decision}: {merge_rate*100:.1f}% merge rate ({stats['total']} PRs)")
        
        # Análise por labels
        print(f"\nINFLUÊNCIA DAS LABELS:")
        merged_with_labels = sum(1 for pr in merged_prs if pr['pr_labels_count'] > 0)
        closed_with_labels = sum(1 for pr in closed_prs if pr['pr_labels_count'] > 0)
        
        merged_label_rate = merged_with_labels / len(merged_prs) if merged_prs else 0
        closed_label_rate = closed_with_labels / len(closed_prs) if closed_prs else 0
        
        print(f"  PRs com labels - Merged: {merged_label_rate*100:.1f}% | Closed: {closed_label_rate*100:.1f}%")
        
        merged_labels_median = sorted([pr['pr_labels_count'] for pr in merged_prs])[len(merged_prs)//2] if merged_prs else 0
        closed_labels_median = sorted([pr['pr_labels_count'] for pr in closed_prs])[len(closed_prs)//2] if closed_prs else 0
        print(f"  Quantidade de labels - Merged: {merged_labels_median} | Closed: {closed_labels_median}")
        
        # Análise por popularidade do repositório
        print(f"\nINFLUÊNCIA DA POPULARIDADE DO REPOSITÓRIO:")
        
        # Separar por quartis de estrelas
        all_stars = sorted(list(set(pr['stars'] for pr in pull_requests)))
        if len(all_stars) >= 4:
            q1 = all_stars[len(all_stars)//4]
            q3 = all_stars[3*len(all_stars)//4]
            
            low_star_prs = [pr for pr in pull_requests if pr['stars'] <= q1]
            high_star_prs = [pr for pr in pull_requests if pr['stars'] >= q3]
            
            low_merged = sum(1 for pr in low_star_prs if pr['pr_is_merged'])
            high_merged = sum(1 for pr in high_star_prs if pr['pr_is_merged'])
            
            low_rate = low_merged / len(low_star_prs) if low_star_prs else 0
            high_rate = high_merged / len(high_star_prs) if high_star_prs else 0
            
            print(f"  Repos menos populares (<={q1:,} stars): {low_rate*100:.1f}% merge rate")
            print(f"  Repos mais populares (>={q3:,} stars): {high_rate*100:.1f}% merge rate")
        
        print(f"\n" + "="*80)
        print("CONCLUSÕES SOBRE FATORES DE MERGE")
        print("="*80)
        
        if merged_changes and closed_changes:
            if merged_median < closed_median:
                print("PRs menores têm maior chance de serem merged")
            else:
                print("Tamanho do PR não parece influenciar positivamente no merge")
        
        if merged_reviews and closed_reviews:
            if merged_rev_median > closed_rev_median:
                print("Mais reviews aumentam a chance de merge")
            else:
                print("Número de reviews não parece influenciar no merge")
        
        if merged_label_rate > closed_label_rate:
            print("Uso de labels parece aumentar a chance de merge")
        else:
            print("Uso de labels não parece influenciar no merge")


def load_env_file():
    """
    Carrega variáveis de ambiente de um arquivo .env (opcional)
    """

    try:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    except Exception as e:
        pass


def main():
    """
    Função principal do programa
    """
    load_env_file()
    
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("ERRO: Token do GitHub não encontrado!")
        print("Crie um arquivo .env com: GITHUB_TOKEN=seu_token_aqui")
        return

    analyzer = GitHubAnalyzer(token)

    # Etapa 1: Coletar repositórios populares com 100+ PRs
    print("=== ETAPA 1: Coletando repositórios populares ===")
    repositories = analyzer.collect_popular_repositories(limit=200)
    
    if not repositories:
        print("Falha na coleta de repositórios.")
        return
    
    # Etapa 2: Coletar PRs com code review destes repositórios
    print("\n=== ETAPA 2: Coletando Pull Requests com code review ===")
    pull_requests = analyzer.collect_pull_requests_data(repositories, limit=100)
    
    if pull_requests:
        # Salvar dados
        analyzer.save_to_csv(pull_requests)
        
        # Gerar relatórios
        analyzer.print_summary(pull_requests)
        analyzer.analyze_merge_factors(pull_requests)
        
        print("\n" + "="*60)
        print("DATASET CRIADO COM SUCESSO!")
        print("="*60)
        print(f"Total de PRs coletados: {len(pull_requests):,}")
        print(f"Repositórios analisados: {len(repositories)}")
        print("Arquivo gerado: pull_requests_code_review.csv")
        print("\nO dataset contém PRs com code review dos")
        print("repositórios mais populares do GitHub (>=100 PRs), ordenados por número de reviews.")
        
        # Estatísticas finais
        merged_count = sum(1 for pr in pull_requests if pr['pr_is_merged'])
        print(f"\nEstatísticas finais:")
        print(f"- PRs merged: {merged_count:,} ({merged_count/len(pull_requests)*100:.1f}%)")
        print(f"- PRs closed: {len(pull_requests)-merged_count:,} ({(len(pull_requests)-merged_count)/len(pull_requests)*100:.1f}%)")
        
    else:
        print("Falha na coleta de Pull Requests.")


if __name__ == "__main__":
    main()
