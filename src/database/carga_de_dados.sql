CREATE TABLE sal_sala (
    sal_id INT PRIMARY KEY,
    sal_bloco VARCHAR(20),
    sal_numero INT
);
 
CREATE TABLE pro_professor (
    pro_id INT PRIMARY KEY,
    pro_nome VARCHAR(150),
    pro_email VARCHAR(150)
);
 
CREATE TABLE per_periodo (
    per_id INT PRIMARY KEY,
    per_nome VARCHAR(100)
);
 
CREATE TABLE sem_semestre (
    sem_id INT PRIMARY KEY,
    sem_qualSemestre INT
);
 
CREATE TABLE dis_disciplina (
    dis_id INT PRIMARY KEY,
    dis_nome VARCHAR(150),
    dis_codigo VARCHAR(15),
    dis_eletiva INT,
    dis_cargaHoraria INT,
    idper_periodo INT
);
 
CREATE TABLE tur_turma (
    tur_id INT PRIMARY KEY,
    tur_codigo INT,
    idpro_professor INT,
    iddis_disciplina INT,
    idsem_semestre INT
);
 
CREATE TABLE hor_horario (
    hor_id INT PRIMARY KEY,
    hor_diaSemana INT,
    hor_slot VARCHAR(1),
    hor_horaInicio INT,
    hor_horaFim INT
);
 
CREATE TABLE alo_alocacaoHorarioSala (
    alo_id INT PRIMARY KEY,
    idtur_turma INT,
    idsal_sala INT,
    idhor_horario INT
);
 
 
INSERT INTO pro_professor (pro_id, pro_nome, pro_email) VALUES
(1, 'Alexandre Magno Andrade Maciel', 'email@upe.br'),
(2, 'Byron Leite Dantas Bezerra', 'email@upe.br'),
(3, 'Carmelo Jose Albanez Bastos Filho', 'email@upe.br'),
(4, 'Cleyton Mario de Oliveira Rodrigues', 'email@upe.br'),
(5, 'Daniel Augusto Ribeiro Chaves', 'email@upe.br'),
(6, 'Wylliams Barbosa Santos', 'email@upe.br'),
(7, 'Diego José Rátiva Millan', 'email@upe.br'),
(8, 'Edison de Queiroz Albuquerque', 'email@upe.br'),
(9, 'Eliane Loyola', 'email@upe.br'),
(10, 'Fernando Buarque de Lima Neto', 'email@upe.br'),
(11, 'Genésio Gomes da Cruz Neto', 'email@upe.br'),
(12, 'Hemir da Cunha Santiago', 'email@upe.br'),
(13, 'Joabe Bezerra de Jesus Junior', 'email@upe.br'),
(14, 'Joao Fausto Lorenzato de Oliveira', 'email@upe.br'),
(15, 'José Paulo Gonçalves de Oliveira', 'email@upe.br'),
(16, 'José Raimundo Lima Junior', 'email@upe.br'),
(17, 'Leandro Honorato De Souza Silva', 'email@upe.br'),
(18, 'Liliane Sheyla Da Silva Fonseca', 'email@upe.br'),
(19, 'Luis Carlos de Souza Menezes', 'email@upe.br'),
(20, 'Maria Lencastre Pinheiro de Menezes e Cruz', 'email@upe.br'),
(21, 'Meuser Jorge Silva Valenca', 'email@upe.br'),
(22, 'Ricardo Ataide de Lima', 'email@upe.br'),
(23, 'Roberta Andrade de Araujo Fagundes', 'email@upe.br'),
(24, 'Sérgio Campello Oliveira', 'email@upe.br'),
(25, 'Sergio Murilo Maciel Fernandes', 'email@upe.br'),
(26, 'Tarciana Dias da Silva', 'email@upe.br');
 
INSERT INTO per_periodo (per_id, per_nome) VALUES
(1, '1º Período'),
(2, '2º Período'),
(3, '3º Período'),
(4, '4º Período'),
(5, '5º Período'),
(6, '6º Período'),
(7, '7º Período'),
(8, '8º Período'),
(9, '9º Período'),
(10, '10º Período');
 
INSERT INTO sem_semestre (sem_id, sem_qualSemestre) VALUES
(1, 1),
(2, 2);
 
INSERT INTO sal_sala (sal_id, sal_bloco, sal_numero) VALUES
(1, 'I', 1),
(2, 'I', 2),
(3, 'I', 3),
(4, 'I', 4),
(5, 'I', 5),
(6, 'I', 6),
(7, 'I', 7),
(8, 'I', 8),
(9, 'I', 9),
(10, 'I', 10),
(11, 'I', 11),
(12, 'I', 12),
(13, 'I', 13),
(14, 'I', 14),
(15, 'I', 15),
(16, 'K', 1),
(17, 'K', 2),
(18, 'K', 3),
(19, 'K', 4),
(20, 'K', 5),
(21, 'K', 6),
(22, 'K', 7),
(23, 'K', 8),
(24, 'K', 9),
(25, 'K', 10),
(26, 'K', 11),
(27, 'K', 12),
(28, 'K', 13),
(29, 'K', 14),
(30, 'K', 15);
 
INSERT INTO hor_horario (hor_id, hor_diaSemana, hor_slot, hor_horaInicio, hor_horaFim) VALUES
-- Segunda
(1, 2, 'A', 710, 800), -- 07:10-08:00 
(2, 2, 'B', 800, 850), -- 08:00-08:50 
(3, 2, 'C', 850, 940),
(4, 2, 'D', 940, 1030),
(5, 2, 'E', 1030, 1120),
(6, 2, 'F', 1120, 1210),
-- Terca
(7, 3, 'A', 710, 800),
(8, 3, 'B', 800, 850),
(9, 3, 'C', 850, 940),
(10, 3, 'D', 940, 1030),
(11, 3, 'E', 1030, 1120),
(12, 3, 'F', 1120, 1210),
-- Quarta
(13, 4, 'A', 710, 800),
(14, 4, 'B', 800, 850),
(15, 4, 'C', 850, 940),
(16, 4, 'D', 940, 1030),
(17, 4, 'E', 1030, 1120),
(18, 4, 'F', 1120, 1210),
-- Quinta
(19, 5, 'A', 710, 800),
(20, 5, 'B', 800, 850),
(21, 5, 'C', 850, 940),
(22, 5, 'D', 940, 1030),
(23, 5, 'E', 1030, 1120),
(24, 5, 'F', 1120, 1210),
-- Sexta
(25, 6, 'A', 710, 800),
(26, 6, 'B', 800, 850),
(27, 6, 'C', 850, 940),
(28, 6, 'D', 940, 1030),
(29, 6, 'E', 1030, 1120),
(30, 6, 'F', 1120, 1210);

 
 
INSERT INTO dis_disciplina (dis_id, dis_nome, dis_codigo, dis_eletiva, dis_cargaHoraria, idper_periodo) VALUES
(1, 'Mineração de Dados', 'CCMP0078', 1, 60, NULL),
(2, 'Aprendizagem de Máquina', 'CCMP0123', 0, 60, 7),
(3, 'Sistemas de Comunicação', 'CCMP0076', 0, 60, 6),
(4, 'Algoritmos e Estruturas de Dados', 'CCMP0110', 0, 60, 4),
(5, 'Projeto Final de Curso', 'CCMP0030', 0, 60, 10),
(6, 'Controle de Processos', 'ELET0024', 0, 60, 8),
(7, 'Redes de Computadores 2', 'ELET0071', 0, 60, 8),
(8, 'Engenharia de Software', 'CCMP0115', 0, 60, 5),
(9, 'Fundamentos de Programação', 'CCMP0104', 0, 60, 1),
(10, 'Introdução à Engenharia', 'ENGE0002', 0, 30, 1),
(11, 'Programação Imperativa', 'CCMP0084', 0, 60, 2),
(12, 'Linguagem de Programação Orientada a Objetos', 'CCMP0068', 0, 60, 3),
(13, 'Lógica', 'CCMP0067', 0, 60, 3),
(14, 'Materiais e Dispositivos Semicondutores', 'CCMP0109', 0, 60, 3),
(15, 'Matemática Discreta', 'CCMP0111', 0, 60, 4),
(16, 'Circuitos Elétricos', 'CCMP0090', 0, 60, 4),
(17, 'Informática, Economia e Sociedade', 'CCMP0085', 0, 30, 4),
(18, 'Teoria da Computação', 'CCMP0039', 0, 60, 5),
(19, 'Teoria dos Grafos', 'CCMP0116', 0, 30, 5),
(20, 'Sistemas Multimídia', 'CCMP0172', 0, 45, 5),
(21, 'Sinais e Sistemas', 'CCMP0071', 0, 60, 5),
(22, 'Eletrônica para Computação', 'CCMP0073', 0, 60, 5),
(23, 'Metodologia Científica', 'LETR0013', 0, 30, 5),
(24, 'Análise e Projeto de Software', 'CCMP0074', 0, 60, 6),
(25, 'Interface Humano-Computador', 'CCMP0079', 0, 60, 6),
(26, 'Inteligência Artificial e Computacional', 'CCMP0118', 0, 60, 6),
(27, 'Organização de Computadores', 'CCMP0025', 0, 60, 6),
(28, 'Eletrônica Digital', 'CCMP0119', 0, 90, 6),
(29, 'Estágio Supervisionado', 'CCMP0011', 0, 180, 6),
(30, 'Banco de Dados', 'CCMP0005', 0, 60, 7),
(31, 'Pesquisa Operacional', 'CCMP0122', 0, 60, 7),
(32, 'Redes de Computadores 1', 'ELET0070', 0, 60, 7),
(33, 'Arquitetura de Computadores', 'CCMP0003', 0, 60, 7),
(34, 'Sistemas Operacionais', 'CCMP0120', 0, 60, 7),
(35, 'Projeto em Engenharia da Computação', 'CCMP0173', 0, 30, 7),
(36, 'Construção de Compiladores', 'CCMP0117', 0, 60, 8),
(37, 'Elementos de Robótica', 'CCMP0125', 0, 60, 8),
(38, 'Sistemas Embarcados', 'CCMP0124', 0, 60, 8),
(39, 'Automação Industrial', 'CCMP0127', 0, 60, NULL),
(40, 'Gestão de TIC e Empreendedorismo', 'CCMP0126', 0, 30, NULL),
(41, 'Ambiente de Desenvolvimento de Software', 'CCMP0088', 1, 60, NULL),
(42, 'Aplicações em Engenharia de Software', 'CCMP0089', 1, 60, NULL),
(43, 'Arquitetura Avançada de Computadores', 'CCMP0002', 1, 60, NULL),
(44, 'Automação de Máquinas', 'CCMP0135', 1, 60, NULL),
(45, 'Avaliação de Desempenho', 'CCMP0004', 1, 60, NULL),
(46, 'Computação Natural', 'CCMP0082', 1, 60, NULL),
(47, 'Concorrência', 'CCMP0008', 1, 60, NULL),
(48, 'Engenharia de Software Experimental', 'CCMP0083', 1, 60, NULL),
(49, 'Estática', 'FISC0067', 1, 60, NULL),
(50, 'Gerência de Projeto', 'CCMP0012', 1, 60, NULL),
(51, 'Gerência de Redes de Computadores', 'CCMP0013', 1, 60, NULL),
(52, 'Métodos Formais', 'CCMP0023', 1, 60, NULL),
(53, 'Processamento Digital de Imagem', 'CCMP0026', 1, 60, NULL),
(54, 'Projeto de Banco de Dados', 'CCMP0028', 1, 60, NULL),
(55, 'Projeto de Sistemas Operacionais', 'CCMP0031', 1, 60, NULL),
(56, 'Redes Neurais Artificiais', 'CCMP0087', 1, 60, NULL),
(57, 'Segurança da Informação', 'CCMP0091', 1, 60, NULL),
(58, 'Sistemas de Informação', 'CCMP0036', 1, 60, NULL),
(59, 'Computação Gráfica', 'CCMP0007', 1, 60, NULL),
(60, 'Comunicação Digital', 'ELET0018', 1, 60, NULL),
(61, 'Engenharia de Requisitos', 'CCMP0132', 1, 60, NULL),
(62, 'Formação de Empreendedores', 'ADMT0002', 1, 60, NULL),
(63, 'Integração de Sistemas de Automação', 'CCMP0136', 1, 60, NULL),
(64, 'Interface de Voz', 'CCMP0133', 1, 60, NULL),
(65, 'Laboratório de Redes', 'CCMP0134', 1, 60, NULL),
(66, 'Microcontroladores', 'ELET0056', 1, 60, NULL),
(67, 'Modelagem Analítica', 'CCMP0081', 1, 60, NULL),
(68, 'Modelagem e Simulação', 'CCMP0024', 1, 60, NULL),
(69, 'Paradigmas de Linguagens de Programação', 'CCMP0131', 1, 60, NULL),
(70, 'Projetos com Microcontroladores', 'ELET0118', 1, 60, NULL),
(71, 'Prototipação de Circuitos Integrados', 'ELET0068', 1, 60, NULL),
(72, 'Segurança de Redes de Computadores', 'CCMP0033', 1, 60, NULL),
(73, 'Sistemas Distribuídos', 'CCMP0037', 1, 60, NULL),
(74, 'Sistemas Multiagentes', 'CCMP0092', 1, 60, NULL),
(75, 'Teoria da Informação', 'ELET0105', 1, 60, NULL),
(76, 'Tolerância e Falhas', 'CCMP0098', 1, 60, NULL),
(77, 'Verificação e Validação', 'CCMP0130', 1, 60, NULL),
(78, 'Visão Computacional', 'CCMP0093', 1, 60, NULL);
 
INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) VALUES
(1, 2026101, 1, 1, 2), -- Alexandre - Mineração de Dados 
(2, 2026102, 2, 2, 2), -- Byron - Aprendizagem de Máquina 
(3, 2026103, 3, 3, 2), -- Carmelo - Sistemas de Comunicação 
(4, 2026104, 4, 4, 2), -- Cleyton - Algoritmos e Estruturas de Dados 
(5, 2026106, 5, 6, 2), -- Daniel - Controle de Processos 
(6, 2026107, 5, 7, 2), -- Daniel - Redes de Computadores 2 
(7, 2026108, 6, 8, 2); -- Wylliams - Engenharia de Software
 
INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES
(1, 1, 1, 21), -- Mineração de Dados - Quinta C 
(2, 1, 1, 22), -- Mineração de Dados - Quinta D 
(3, 2, 2, 9), -- Aprendizagem de Máquina - Terca C 
(4, 2, 2, 10), -- Aprendizagem de Máquina - Terca D 
(5, 3, 3, 21), -- Sistemas de Comunicação - Quinta C 
(6, 4, 4, 1), -- Algoritmos e Estruturas de Dados - Segunda A 
(7, 4, 4, 2), -- Algoritmos e Estruturas de Dados - Segunda B 
(8, 5, 1, 23), -- Controle de Processos - Quinta E 
(9, 6, 2, 21), -- Redes de Computadores 2 - Quinta C 
(10, 7, 3, 22); -- Engenharia de Software - Quinta D