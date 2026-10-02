#Projeto Teoria dos Grafos

Este projeto realiza a alocação automática de horários e salas de aula utilizando teoria dos grafos e um algoritmo guloso. O sistema lê dados de um banco SQLite, constrói um grafo de conflitos entre turmas e aloca os horários e salas evitando sobreposições de disciplinas, professores ou períodos.

## Pré-requisitos

* Python 3.x instalado.
* Nenhuma biblioteca externa é necessária.



## Como executar o projeto

Para garantir que o banco de dados seja criado e lido no diretório correto, os comandos devem ser executados de dentro da pasta onde os códigos-fonte residem.

Abra o seu terminal na raiz do projeto e execute os seguintes comandos em sequência:

```bash
# 1. Navegue até a pasta do código-fonte
cd src

# 2. Inicialize e popule o banco de dados local
python setup_db.py

# 3. Execute o algoritmo para gerar a grade horária
python main.py

```
