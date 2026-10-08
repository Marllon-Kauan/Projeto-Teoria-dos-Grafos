"""
Define as disciplinas, armazenando suas propriedades fundamentais.
"""

class Turma:
    def __init__(self, tur_id, tur_codigo, dis_id, dis_codigo, dis_nome, idper_periodo, carga_horaria, pro_id, pro_nome, idsal_sala=None):
        self.tur_id = tur_id                        #ID único da turma.
        self.tur_codigo = tur_codigo                #Código da turma.
        self.dis_id = dis_id                        #ID da disciplina associada.
        self.dis_codigo = dis_codigo                #Código da disciplina.
        self.dis_nome = dis_nome                    #Nome da disciplina.
        self.idper_periodo = idper_periodo          #Período da disciplina.
        self.carga_horaria = carga_horaria          #Carga horária total.
        self.aulas_semanais = carga_horaria // 15   #Converte a carga horária em quantidade de aulas na semana.
        self.pro_id = pro_id                        #ID do professor.
        self.pro_nome = pro_nome                    #Nome do professor.
        self.idsal_sala = idsal_sala                #ID da sala.
        self.dominio_horarios = set()               #Conjunto de horários em que a turma pode ter aula.
        self.horarios_alocados = []                 #Guarda os horários escolhidos.

    def __str__(self):
        return f"Código: {self.tur_codigo} | Disciplina: {self.dis_nome} | Prof: {self.pro_nome}"