#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para executar o experimento completo
Facilita a execução em etapas
"""

import os
import sys
from pathlib import Path

def check_token():
    """Verifica se o token do GitHub está configurado"""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        # Tenta carregar de arquivo .env
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        token = line.split('=', 1)[1].strip()
                        os.environ['GITHUB_TOKEN'] = token
                        return True
        return False
    return True

def main():
    """Função principal"""
    print("="*60)
    print("EXPERIMENTO GRAPHQL VS REST")
    print("="*60)
    print("\nEste script facilita a execução do experimento em etapas.\n")
    
    if not check_token():
        print("ERRO: Token do GitHub não encontrado!")
        print("\nConfigure o token de uma das seguintes formas:")
        print("1. Variável de ambiente: set GITHUB_TOKEN=seu_token")
        print("2. Arquivo .env: GITHUB_TOKEN=seu_token")
        return
    
    print("Token do GitHub encontrado!\n")
    
    print("Escolha uma opção:")
    print("1. Coletar dados do experimento (Lab05S01/S02)")
    print("2. Analisar dados coletados (Lab05S02)")
    print("3. Gerar dashboard de visualização (Lab05S03)")
    print("4. Executar tudo (coleta + análise + dashboard)")
    print("5. Gerar dados de exemplo para testes")
    
    choice = input("\nDigite o número da opção: ").strip()
    
    if choice == '1':
        print("\nIniciando coleta de dados...")
        from experiment_collector import main as collector_main
        collector_main()
    
    elif choice == '2':
        print("\nIniciando análise estatística...")
        if not Path('experiment_data.csv').exists():
            print("ERRO: Arquivo experiment_data.csv não encontrado!")
            print("Execute primeiro a opção 1 para coletar dados.")
            return
        from experiment_analyzer import main as analyzer_main
        analyzer_main()
    
    elif choice == '3':
        print("\nGerando dashboard...")
        if not Path('experiment_data.csv').exists():
            print("ERRO: Arquivo experiment_data.csv não encontrado!")
            print("Execute primeiro a opção 1 para coletar dados.")
            return
        from dashboard import main as dashboard_main
        dashboard_main()
    
    elif choice == '4':
        print("\nExecutando experimento completo...")
        print("\n[1/3] Coletando dados...")
        from experiment_collector import main as collector_main
        collector_main()
        
        if Path('experiment_data.csv').exists():
            print("\n[2/3] Analisando dados...")
            from experiment_analyzer import main as analyzer_main
            analyzer_main()
            
            print("\n[3/3] Gerando dashboard...")
            from dashboard import main as dashboard_main
            dashboard_main()
            
            print("\n" + "="*60)
            print("EXPERIMENTO CONCLUÍDO COM SUCESSO!")
            print("="*60)
        else:
            print("ERRO: Falha na coleta de dados. Verifique os logs acima.")
    
    elif choice == '5':
        print("\nGerando dados de exemplo...")
        from generate_sample_data import main as sample_main
        sample_main()
    
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    main()


