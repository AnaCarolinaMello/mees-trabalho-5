# Análise de Pull Requests e Code Review no GitHub

## Descrição
Script Python que utiliza GraphQL para analisar a atividade de code review em repositórios populares do GitHub. O objetivo é identificar variáveis que influenciam no merge de Pull Requests, focando em PRs que passaram por processo de code review nos 200 repositórios mais populares do GitHub (com pelo menos 100 PRs).

## Configuração

### 1. Token do GitHub
Antes de executar o script, você precisa gerar e configurar um token pessoal do GitHub:

#### Gerar Token:
1. Acesse: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clique em "Generate new token (classic)"
3. Selecione as permissões necessárias:
   - `public_repo` (para acessar repositórios públicos)
   - `read:org` (para organizações)
4. Copie o token gerado

#### Configurar Token:

**Opção 1 - Variável de Ambiente:**
```bash
# Windows (cmd)
set GITHUB_TOKEN=seu_token_aqui
python main.py

# Windows (PowerShell)
$env:GITHUB_TOKEN='seu_token_aqui'
python main.py

# Linux/Mac
export GITHUB_TOKEN=seu_token_aqui
python main.py
```

**Opção 2 - Arquivo .env (recomendado):**
1. Crie um arquivo `.env` na raiz do projeto
2. Adicione a linha: `GITHUB_TOKEN=seu_token_aqui`
3. Execute normalmente: `python main.py`

Exemplo do arquivo `.env`:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. Dependências
Instale as dependências do projeto:

```bash
# Windows
py -m pip install -r requirements.txt

# Linux/Mac
pip install -r requirements.txt
```

Dependências utilizadas:
- `requests` - Para requisições HTTP à API do GitHub
- `json`, `csv`, `os`, `datetime`, `time` - Bibliotecas padrão do Python

## Execução
```bash
# Windows
py main.py

# Linux/Mac
python main.py
```

## Dados Coletados

O script funciona em duas etapas:

### Etapa 1: Coleta de Repositórios
- Busca os 200 repositórios mais populares do GitHub
- Filtra apenas repositórios com pelo menos 100 Pull Requests

### Etapa 2: Coleta de Pull Requests
- Para cada repositório selecionado, coleta até 50 PRs
- **Critério importante**: Apenas PRs que passaram por code review (têm pelo menos 1 review)
- Coleta PRs nos estados MERGED e CLOSED

### Métricas de Pull Requests Coletadas

#### Informações do Repositório
- `name`, `owner`, `stars`, `language`

#### Informações Básicas do PR
- `pr_number`, `pr_title`, `pr_state`, `pr_author`
- `pr_created_at`, `pr_closed_at`, `pr_merged_at`, `pr_is_merged`
- `pr_base_branch`, `pr_head_branch`

#### Tamanho e Complexidade
- `pr_additions`, `pr_deletions`, `pr_total_changes`
- `pr_changed_files`, `pr_commits_count`

#### Atividade de Code Review
- `pr_reviews_count` - Número de reviews recebidos
- `pr_comments_count` - Número de comentários
- `pr_review_requests_count` - Requests de review
- `pr_participants_count` - Participantes na discussão
- `pr_review_decision` - Decisão final do review (APPROVED, CHANGES_REQUESTED, etc.)

#### Outras Métricas
- `pr_labels`, `pr_labels_count` - Labels aplicadas
- `pr_assignees_count` - Pessoas assignadas
- `pr_is_draft` - Se era um draft PR
- `pr_lifetime_hours` - Tempo total do PR em horas
- `pr_time_to_merge_hours` - Tempo até merge em horas (apenas PRs merged)


## Saída

O script gera:
1. **Arquivo CSV**: `pull_requests_code_review.csv` com dados de PRs que passaram por code review
2. **Resumo no terminal**: Estatísticas básicas dos PRs coletados
3. **Análise de fatores**: Análise detalhada dos fatores que influenciam no merge de PRs

## Queries GraphQL Utilizadas

### Query para Repositórios Populares
```graphql
query {
  search(query: "stars:>1000", type: REPOSITORY, first: 20) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        owner {
          login
        }
        stargazerCount
        primaryLanguage {
          name
        }
        pullRequests {
          totalCount
        }
        url
      }
    }
  }
}
```

### Query para Pull Requests com Code Review
```graphql
query {
  repository(owner: "owner", name: "repo") {
    pullRequests(first: 50, states: [MERGED, CLOSED]) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        state
        createdAt
        closedAt
        mergedAt
        author {
          login
        }
        additions
        deletions
        changedFiles
        comments {
          totalCount
        }
        reviews {
          totalCount
        }
        reviewRequests {
          totalCount
        }
        commits {
          totalCount
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        reviewDecision
        isDraft
        assignees {
          totalCount
        }
        participants {
          totalCount
        }
      }
    }
  }
}
```

## Funcionalidades Implementadas

- Consulta GraphQL para 200 repositórios populares (com 100+ PRs)
- Coleta de Pull Requests com code review
- Filtro automático para PRs que passaram por review
- Análise de fatores que influenciam no merge
- Métricas de tamanho e complexidade dos PRs
- Métricas de atividade de review
- Análise por linguagem de programação
- Análise por decisão de review
- Análise por uso de labels
- Análise por popularidade do repositório
- Export detalhado para CSV
- Relatórios estatísticos completos
- Tratamento de erros e rate limiting
- Progress feedback durante coleta  

## Estrutura do CSV

```csv
name,owner,stars,language,pr_number,pr_title,pr_state,pr_author,pr_created_at,pr_closed_at,pr_merged_at,pr_is_merged,pr_base_branch,pr_head_branch,pr_additions,pr_deletions,pr_changed_files,pr_total_changes,pr_comments_count,pr_reviews_count,pr_review_requests_count,pr_commits_count,pr_participants_count,pr_assignees_count,pr_labels,pr_labels_count,pr_review_decision,pr_is_draft,pr_lifetime_hours,pr_time_to_merge_hours,has_code_review
```

### Análises Disponíveis

O script realiza análises abrangentes sobre os fatores que influenciam no merge de Pull Requests:

1. **Influência do Tamanho**: Compara linhas alteradas e arquivos modificados entre PRs merged vs closed
2. **Influência da Atividade de Review**: Analisa reviews, comentários e participantes
3. **Influência da Linguagem**: Taxa de merge por linguagem de programação
4. **Influência da Decisão de Review**: Como APPROVED, CHANGES_REQUESTED afetam o merge
5. **Influência das Labels**: Uso de labels e sua correlação com merge
6. **Influência da Popularidade**: Comparação entre repositórios mais e menos populares