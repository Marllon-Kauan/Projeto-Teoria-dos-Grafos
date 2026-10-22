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
git clone https://github.com/usuario/sistema-grade-horaria.git
cd sistema-grade-horaria
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
python setup_db.py
5. Iniciar o servidor local
Inicie a aplicação web via Flask:
python app.py
Acesse a aplicação no seu navegador através do endereço: http://127.0.0.1:5000
Configuração de Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto com base no modelo do arquivo .env.example. Este arquivo define as configurações de execução do Flask e segredos da aplicação.
Exemplo prático de .env.example:
# Configuração da Aplicação Flask
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Chave Secreta para Sessão do Flask (Trocar em ambiente de produção)
SECRET_KEY=chave-secreta-de-desenvolvimento-trocar-em-producao

# Configuração do Servidor Local
PORT=5000
HOST=127.0.0.1

# Caminho do Banco de Dados SQLite
DATABASE_PATH=banco_projeto.db
Descrição das Chaves:
FLASK_APP: Especifica o ponto de entrada principal da aplicação Flask (app.py).
FLASK_ENV: Define o modo de execução da aplicação (development para desenvolvimento local ou production).
FLASK_DEBUG: Habilita o modo de depuração com recarregamento automático em caso de alterações no código (1 para ligado, 0 para desligado).
SECRET_KEY: Chave criptográfica usada pelo Flask para assinar cookies e proteger a sessão do usuário.
PORT e HOST: Definem a porta de escuta e o endereço de rede da aplicação local.
DATABASE_PATH: Especifica o arquivo de banco de dados SQLite utilizado pela aplicação.
Execução de Testes e Licença
Execução de Testes e Validação de Regras
A aplicação conta com uma suíte de verificação automatizada para validar a integridade da grade horária gerada e garantir que nenhuma regra do algoritmo de grafos foi violada (ex: sobreposição de horários do mesmo professor, choque de salas ou estouro do limite de aulas consecutivas).
Para rodar a verificação de regras no banco de dados após gerar a grade:
# Executa a verificação utilizando o limite padrão de 2 aulas seguidas
python verificar_regras.py

# Caso deseje testar com um limite customizado de aulas seguidas (ex: 3 aulas):
python verificar_regras.py 3
O script avaliará as seguintes restrições:
Conflitos de professores no mesmo horário.
Conflitos de turmas do mesmo período no mesmo horário.
Alocação dupla da mesma sala.
Respeito às restrições cadastrais de professores e horários bloqueados.
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
