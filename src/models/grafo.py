"""
Implementa a estrutura dos grafos onde as turmas são os vértices e as restrições formam as arestas.
"""

class GrafoSemestre:
    #Recebe o identificador do semestre.
    def __init__(self, id_semestre):
        self.id_semestre = id_semestre    #Armazena o ID do semestre.
        self.vertice_turmas = {}          #Dicionário armazenando os objetos turma (vértices).
        self.adjacencias = {}             #Dicionário guardando os conflitos (arestas).

    #Adiciona uma nova turma ao grafo.
    def add_vertice(self, turma):
        self.vertice_turmas[turma.tur_id] = turma #Salva o objeto turma usando o ID como chave.

        if turma.tur_id not in self.adjacencias: #Se a turma ainda não tem uma lista de vizinhos, cria um dicionário vazio.
            self.adjacencias[turma.tur_id] = {}

    #Registra que duas turmas não podem ocorrer ao mesmo tempo.
    def add_aresta(self, id_turma1, id_turma2, motivos):
        self.adjacencias[id_turma1][id_turma2] = motivos #Registra a turma 2 como vizinha da turma 1.
        self.adjacencias[id_turma2][id_turma1] = motivos #Registra a turma 1 como vizinha da turma 2 (grafo não-direcionado)

    #Conta quantos conflitos uma determinada turma possui.
    def obter_grau(self, tur_id):
        #Retorna o número de chaves (vizinhos) no dicionário de adjacências da turma.
        return len(self.adjacencias.get(tur_id, {}))