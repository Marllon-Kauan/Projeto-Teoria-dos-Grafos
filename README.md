Sistema de Gestão e Geração de Grade Horária Acadêmica


Visão Geral e Propósito

O Sistema de Grade Horária é uma aplicação web desenvolvida para resolver o problema de alocação e otimização de horários e salas de aula para cursos universitários (baseado no currículo de Engenharia da Computação da UPE - Universidade de Pernambuco).
O agendamento manual de turmas frequentemente resulta em conflitos de horários de professores, alocação simultânea da mesma sala, estouro de carga diária e choque de disciplinas do mesmo período. Esta aplicação resolve esses desafios utilizando Teoria dos Grafos (modelando turmas como vértices e restrições operacionais como arestas) e um algoritmo de coloração de grafos com busca em largura (BFS) para distribuição automatizada e eficiente dos horários.
Stack Tecnológica Principal:
Linguagem: Python 3.11+
Framework Web: Flask (Jinja2 Templates)
Banco de Dados: SQLite3 (Persistência relacional de turmas, professores, salas e alocações)
Frontend: HTML5, CSS3 (Variáveis CSS e CSS Grid responsivo) e JavaScript (Vanilla JS com manipuladores dinâmicos para edição drag-and-drop e seleções em lote)
Geração de Relatórios: ReportLab (Exportação nativa da grade em formato PDF)
Pré-requisitos e Dependências
Antes de instalar e executar a aplicação, certifique-se de ter as seguintes ferramentas instaladas em seu ambiente de desenvolvimento:
Git: v2.30+ (para clonar o repositório)
Python: v3.11 ou superior
Pip: Gerenciador de pacotes do Python (geralmente incluso no Python)
Virtualenv / venv: Módulo para isolamento de ambiente (recomendado)
Guia Passo-a-Passo de Instalação e Execução
Siga os passos abaixo no seu terminal para clonar o projeto, configurar as dependências, popular o banco de dados e iniciar o servidor em ambiente local.
1. Clonar o repositório
git clone https://github.com/Marllon-Kauan/Projeto-Teoria-dos-Grafos.git
cd Projeto-Teoria-dos-Grafos
2. Criar e ativar o ambiente virtual (venv)
no Linux / macOS:
python3 -m venv venv
source venv/bin/activate
no Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
3. Instalar pacotes e dependências
pip install -r requirements.txt
4. Inicializar e popular o banco de dados
Execute o script de setup para criar o banco de dados SQLite (banco_projeto.db) e carregar os dados iniciais de salas, professores, períodos e disciplinas:
cd src
python setup_db.py
5. Iniciar o servidor local
Inicie a aplicação web via Flask (ainda dentro da pasta src):
python app.py
Acesse a aplicação no seu navegador através do endereço: http://127.0.0.1:5000
Configuração
A aplicação não lê arquivo .env. As configurações ficam no código:
SECRET_KEY: definida em src/app.py (trocar antes de colocar em produção).
Banco de dados: src/banco_projeto.db, definido em DB_PATH no src/repositorio.py.
Semestre ativo: SEMESTRE_ID no src/repositorio.py (usado também pelo verificar_regras.py).
Execução de Testes e Licença
Execução de Testes e Validação de Regras
A aplicação conta com uma suíte de verificação automatizada para validar a integridade da grade horária gerada e garantir que nenhuma regra do algoritmo de grafos foi violada (ex: sobreposição de horários do mesmo professor, choque de salas ou estouro do limite de aulas consecutivas).
Testes automatizados (pytest)
Na raiz do projeto, com o ambiente virtual ativo e o banco já criado (passo 4):
pip install pytest
python -m pytest -q
Os testes de tests/test_qa_grade.py usam um banco temporário e não alteram o banco_projeto.db.

Para rodar a verificação de regras no banco de dados após gerar a grade (dentro da pasta src):
# Executa a verificação utilizando o limite padrão de 2 aulas seguidas
python verificar_regras.py

# Caso deseje testar com um limite customizado de aulas seguidas (ex: 3 aulas):
python verificar_regras.py 3
O script avaliará as seguintes restrições:
Conflitos de professores no mesmo horário.
Conflitos de turmas do mesmo período no mesmo horário.
Alocação dupla da mesma sala.
Respeito às restrições cadastrais de professores e aos horários bloqueados de cada período (eletivas não sofrem bloqueio).
Limites de aulas seguidas e de aulas por dia cadastrados para cada professor.
Cumprimento exato da carga horária semanal.



Licença
Este projeto é disponibilizado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
MIT License

Copyright (c) 2026 Sistema de Grade Horária

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
