PRAGMA foreign_keys = ON;

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
    idper_periodo INT,
    FOREIGN KEY (idper_periodo) REFERENCES per_periodo (per_id)
);

CREATE TABLE tur_turma (
    tur_id INT PRIMARY KEY,
    tur_codigo VARCHAR(2),
    idpro_professor INT,
    iddis_disciplina INT,
    idsem_semestre INT,
    FOREIGN KEY (idpro_professor) REFERENCES pro_professor (pro_id),
    FOREIGN KEY (iddis_disciplina) REFERENCES dis_disciplina (dis_id),
    FOREIGN KEY (idsem_semestre) REFERENCES sem_semestre (sem_id),
    UNIQUE (tur_codigo, idsem_semestre)
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
    idhor_horario INT,
    FOREIGN KEY (idtur_turma) REFERENCES tur_turma (tur_id),
    FOREIGN KEY (idsal_sala) REFERENCES sal_sala (sal_id),
    FOREIGN KEY (idhor_horario) REFERENCES hor_horario (hor_id)
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

INSERT INTO dis_disciplina (dis_id, dis_nome, dis_codigo, dis_eletiva, dis_cargaHoraria, idper_periodo) VALUES
(1, 'Mineração de Dados', 'CCMP0078', 1, 60, 9),
(2, 'Aprendizagem de Máquina', 'CCMP0123', 0, 60, 7),
(3, 'Sistemas de Comunicação', 'CCMP0076', 0, 60, 6),
(4, 'Algoritmos e Estruturas de Dados', 'CCMP0110', 0, 60, 4),
(5, 'Projeto Final de Curso', 'CCMP0030', 0, 60, 8),
(6, 'Controle de Processos', 'ELET0024', 0, 60, 8),
(7, 'Redes de Computadores 2', 'ELET0071', 0, 60, 8),
(8, 'Elementos de Robótica', 'CCMP0125', 0, 60, 8),
(9, 'Sinais e Sistemas', 'CCMP0071', 0, 60, 5),
(10, 'Redes de Computadores 1', 'ELET0070', 0, 60, 7),
(11, 'Pesquisa Operacional', 'CCMP0122', 0, 60, 7),
(12, 'Teoria da Computação', 'CCMP0039', 0, 60, 5),
(13, 'Teoria dos Grafos', 'CCMP0116', 0, 30, 5),
(14, 'Computação Natural', 'CCMP0082', 1, 60, 9),
(15, 'Gestão de TIC e Empreendedorismo', 'CCMP0126', 0, 30, 9),
(16, 'Projeto em Engenharia da Computação', 'CCMP0173', 0, 30, 8),
(17, 'Informática, Economia e Sociedade', 'CCMP0085', 0, 30, 4),
(18, 'Formação de Empreendedores', 'ADMT0002', 1, 60, 10),
(19, 'Programação Imperativa', 'CCMP0084', 0, 60, 2),
(20, 'Sistemas Multimídia', 'CCMP0172', 0, 45, 5),
(21, 'Análise e Projeto de Software', 'CCMP0074', 0, 60, 6),
(22, 'Inteligência Artificial', 'CCMP0015', 0, 60, 6),
(23, 'Metodologia Científica', 'LETR0009', 0, 30, 5),
(24, 'Sistemas Embarcados', 'CCMP0124', 0, 60, 8),
(25, 'Organização de Computadores', 'CCMP0025', 0, 60, 6),
(26, 'Conversão Eletromecânica de Energia', 'ELET0025', 1, 60, 10),
(27, 'Linguagem de Programação Orientada a Objetos', 'CCMP0068', 0, 60, 3),
(28, 'Fundamentos de Programação', 'CCMP0104', 0, 60, 1),
(29, 'Processamento Digital de Imagem', 'CCMP0026', 1, 60, 10),
(30, 'Gerência de Projeto', 'CCMP0012', 1, 60, 9),
(31, 'Introdução à Engenharia', 'ENGE0002', 0, 30, 1),
(32, 'Matemática Discreta', 'CCMP0111', 0, 60, 4),
(33, 'Compiladores', 'CCMP0006', 0, 60, 6),
(34, 'Banco de Dados', 'CCMP0005', 0, 60, 7),
(35, 'Engenharia de Requisitos', 'CCMP0132', 1, 60, 10),
(36, 'Modelagem Analítica', 'CCMP0081', 1, 60, 10),
(37, 'Redes Neurais', 'CCMP0032', 1, 60, 10),
(38, 'Eletrônica para Computação', 'CCMP0073', 0, 60, 5),
(39, 'Automação Industrial', 'CCMP0127', 0, 60, 9),
(40, 'Materiais e Dispositivos Semicondutores', 'CCMP0109', 0, 60, 3),
(41, 'Lógica', 'CCMP0067', 0, 60, 3),
(42, 'Circuitos Elétricos', 'CCMP0090', 0, 60, 4),
(43, 'Arquitetura de Computadores', 'CCMP0003', 0, 60, 7),
(44, 'Eletrônica Digital', 'CCMP0119', 0, 90, 6),
(45, 'Métodos Formais', 'CCMP0023', 1, 60, 9),
(46, 'Sistemas Operacionais', 'ELET0079', 0, 60, 7),
(47, 'Interface Humano-Computador', 'CCMP0079', 0, 60, 8),
(48, 'Engenharia de Software', 'CCMP0010', 0, 60, 5);

INSERT INTO hor_horario (hor_id, hor_diaSemana, hor_slot, hor_horaInicio, hor_horaFim) VALUES
(1, 2, 'A', 710, 800),
(2, 2, 'B', 800, 850),
(3, 2, 'C', 850, 940),
(4, 2, 'D', 940, 1030),
(5, 2, 'E', 1030, 1120),
(6, 2, 'F', 1120, 1210),
(7, 2, 'G', 1210, 1300),
(8, 2, 'H', 1300, 1350),
(9, 2, 'I', 1350, 1440),
(10, 2, 'J', 1440, 1530),
(11, 2, 'K', 1530, 1620),
(12, 2, 'L', 1620, 1710),
(13, 3, 'A', 710, 800),
(14, 3, 'B', 800, 850),
(15, 3, 'C', 850, 940),
(16, 3, 'D', 940, 1030),
(17, 3, 'E', 1030, 1120),
(18, 3, 'F', 1120, 1210),
(19, 3, 'G', 1210, 1300),
(20, 3, 'H', 1300, 1350),
(21, 3, 'I', 1350, 1440),
(22, 3, 'J', 1440, 1530),
(23, 3, 'K', 1530, 1620),
(24, 3, 'L', 1620, 1710),
(25, 4, 'A', 710, 800),
(26, 4, 'B', 800, 850),
(27, 4, 'C', 850, 940),
(28, 4, 'D', 940, 1030),
(29, 4, 'E', 1030, 1120),
(30, 4, 'F', 1120, 1210),
(31, 4, 'G', 1210, 1300),
(32, 4, 'H', 1300, 1350),
(33, 4, 'I', 1350, 1440),
(34, 4, 'J', 1440, 1530),
(35, 4, 'K', 1530, 1620),
(36, 4, 'L', 1620, 1710),
(37, 5, 'A', 710, 800),
(38, 5, 'B', 800, 850),
(39, 5, 'C', 850, 940),
(40, 5, 'D', 940, 1030),
(41, 5, 'E', 1030, 1120),
(42, 5, 'F', 1120, 1210),
(43, 5, 'G', 1210, 1300),
(44, 5, 'H', 1300, 1350),
(45, 5, 'I', 1350, 1440),
(46, 5, 'J', 1440, 1530),
(47, 5, 'K', 1530, 1620),
(48, 5, 'L', 1620, 1710),
(49, 6, 'A', 710, 800),
(50, 6, 'B', 800, 850),
(51, 6, 'C', 850, 940),
(52, 6, 'D', 940, 1030),
(53, 6, 'E', 1030, 1120),
(54, 6, 'F', 1120, 1210),
(55, 6, 'G', 1210, 1300),
(56, 6, 'H', 1300, 1350),
(57, 6, 'I', 1350, 1440),
(58, 6, 'J', 1440, 1530),
(59, 6, 'K', 1530, 1620),
(60, 6, 'L', 1620, 1710);

INSERT INTO tur_turma (tur_id, tur_codigo, idpro_professor, iddis_disciplina, idsem_semestre) VALUES
(1, 'MD', 1, 1, 2),   -- Mineração de Dados
(2, 'AM', 2, 2, 2),   -- Aprendizagem de Máquina
(3, 'SC', 3, 3, 2),   -- Sistemas de Comunicação
(4, 'AE', 4, 4, 2),   -- Algoritmos e Estruturas de Dados
(5, 'PF', 4, 5, 2),   -- Projeto Final de Curso
(6, 'CP', 5, 6, 2),   -- Controle de Processos
(7, 'RB', 5, 7, 2),   -- Redes de Computadores 2 (Redes B)
(8, 'ER', 7, 8, 2),   -- Elementos de Robótica
(9, 'SS', 7, 9, 2),   -- Sinais e Sistemas
(10, 'RA', 8, 10, 2), -- Redes de Computadores 1 (Redes A)
(11, 'PO', 9, 11, 2), -- Pesquisa Operacional
(12, 'TC', 9, 12, 2), -- Teoria da Computação
(13, 'TG', 9, 13, 2), -- Teoria dos Grafos
(14, 'CN', 10, 14, 2),-- Computação Natural
(15, 'GT', 11, 15, 2),-- Gestão de TIC e Empreendedorismo
(16, 'PE', 11, 16, 2),-- Projeto em Engenharia da Computação
(17, 'IE', 11, 17, 2),-- Informática, Economia e Sociedade
(18, 'FE', 11, 18, 2),-- Formação de Empreendedores
(19, 'PI', 12, 19, 2),-- Programação Imperativa
(20, 'SM', 12, 20, 2),-- Sistemas Multimídia
(21, 'AP', 13, 21, 2),-- Análise e Projeto de Software
(22, 'IA', 14, 22, 2),-- Inteligência Artificial
(23, 'MC', 14, 23, 2),-- Metodologia Científica
(24, 'SE', 15, 24, 2),-- Sistemas Embarcados
(25, 'OC', 15, 25, 2),-- Organização de Computadores
(26, 'CE', 16, 26, 2),-- Conversão Eletromecânica de Energia
(27, 'LP', 17, 27, 2),-- Linguagem de Prog. Orientada a Objetos
(28, 'FP', 17, 28, 2),-- Fundamentos de Programação
(29, 'PD', 17, 29, 2),-- Processamento Digital de Imagem
(30, 'GP', 18, 30, 2),-- Gerência de Projeto
(31, 'IN', 18, 31, 2),-- Introdução à Engenharia
(32, 'MT', 19, 32, 2),-- Matemática Discreta
(33, 'CO', 19, 33, 2),-- Compiladores
(34, 'BD', 20, 34, 2),-- Banco de Dados
(35, 'EQ', 20, 35, 2),-- Engenharia de Requisitos
(36, 'MA', 21, 36, 2),-- Modelagem Analítica
(37, 'RN', 21, 37, 2),-- Redes Neurais
(38, 'EC', 22, 38, 2),-- Eletrônica para Computação
(39, 'AI', 22, 39, 2),-- Automação Industrial
(40, 'MS', 22, 40, 2),-- Materiais e Dispositivos Semicondutores
(41, 'LG', 23, 41, 2),-- Lógica
(42, 'CI', 24, 42, 2),-- Circuitos Elétricos
(43, 'AC', 25, 43, 2),-- Arquitetura de Computadores
(44, 'ED', 25, 44, 2),-- Eletrônica Digital
(45, 'MF', 26, 45, 2),-- Métodos Formais
(46, 'SO', 26, 46, 2),-- Sistemas Operacionais
(47, 'IH', 26, 47, 2),-- Interface Humano-Computador
(48, 'ES', 6, 48, 2); -- Engenharia de Software

INSERT INTO alo_alocacaoHorarioSala (alo_id, idtur_turma, idsal_sala, idhor_horario) VALUES
(1, 1, NULL, 39),
(2, 1, NULL, 40),
(3, 1, NULL, 41),
(4, 1, NULL, 42),
(5, 2, NULL, 15),
(6, 2, NULL, 16),
(7, 2, NULL, 17),
(8, 2, NULL, 18),
(9, 3, NULL, 51),
(10, 3, NULL, 52),
(11, 3, NULL, 53),
(12, 3, NULL, 54),
(13, 4, NULL, 37),
(14, 4, NULL, 38),
(15, 4, NULL, 39),
(16, 4, NULL, 40),
(17, 5, NULL, 43),
(18, 5, NULL, 44),
(19, 5, NULL, 45),
(20, 5, NULL, 46),
(21, 6, NULL, 3),
(22, 6, NULL, 4),
(23, 6, NULL, 5),
(24, 6, NULL, 6),
(25, 7, NULL, 51),
(26, 7, NULL, 52),
(27, 7, NULL, 53),
(28, 7, NULL, 54),
(29, 8, NULL, 15),
(30, 8, NULL, 16),
(31, 8, NULL, 49),
(32, 8, NULL, 50),
(33, 9, NULL, 17),
(34, 9, NULL, 18),
(35, 9, NULL, 51),
(36, 9, NULL, 52),
(37, 10, NULL, 27),
(38, 10, NULL, 28),
(39, 10, NULL, 29),
(40, 10, NULL, 30),
(41, 11, NULL, 25),
(42, 11, NULL, 26),
(43, 11, NULL, 49),
(44, 11, NULL, 50),
(45, 12, NULL, 37),
(46, 12, NULL, 38),
(47, 12, NULL, 39),
(48, 12, NULL, 40),
(49, 13, NULL, 41),
(50, 13, NULL, 42),
(51, 14, NULL, 3),
(52, 14, NULL, 4),
(53, 14, NULL, 5),
(54, 14, NULL, 6),
(55, 15, NULL, 25),
(56, 15, NULL, 26),
(57, 16, NULL, 27),
(58, 16, NULL, 28),
(59, 17, NULL, 29),
(60, 17, NULL, 30),
(61, 18, NULL, 33),
(62, 18, NULL, 34),
(63, 18, NULL, 35),
(64, 18, NULL, 36),
(65, 19, NULL, 39),
(66, 19, NULL, 40),
(67, 19, NULL, 41),
(68, 19, NULL, 42),
(69, 20, NULL, 29),
(70, 20, NULL, 30),
(71, 20, NULL, 31),
(72, 21, NULL, 1),
(73, 21, NULL, 2),
(74, 21, NULL, 3),
(75, 21, NULL, 4),
(76, 22, NULL, 13),
(77, 22, NULL, 14),
(78, 22, NULL, 15),
(79, 22, NULL, 16),
(80, 23, NULL, 5),
(81, 23, NULL, 6),
(82, 24, NULL, 1),
(83, 24, NULL, 2),
(84, 24, NULL, 25),
(85, 24, NULL, 26),
(86, 25, NULL, 5),
(87, 25, NULL, 6),
(88, 25, NULL, 29),
(89, 25, NULL, 30),
(90, 26, NULL, 13),
(91, 26, NULL, 14),
(92, 26, NULL, 37),
(93, 26, NULL, 38),
(94, 27, NULL, 3),
(95, 27, NULL, 4),
(96, 27, NULL, 27),
(97, 27, NULL, 28),
(98, 28, NULL, 5),
(99, 28, NULL, 6),
(100, 28, NULL, 29),
(101, 28, NULL, 30),
(102, 29, NULL, 31),
(103, 29, NULL, 32),
(104, 29, NULL, 33),
(105, 29, NULL, 34),
(106, 30, NULL, 53),
(107, 30, NULL, 54),
(108, 30, NULL, 55),
(109, 30, NULL, 56),
(110, 31, NULL, 21),
(111, 31, NULL, 22),
(112, 32, NULL, 15),
(113, 32, NULL, 16),
(114, 32, NULL, 51),
(115, 32, NULL, 52),
(116, 33, NULL, 17),
(117, 33, NULL, 18),
(118, 33, NULL, 41),
(119, 33, NULL, 42),
(120, 34, NULL, 3),
(121, 34, NULL, 4),
(122, 34, NULL, 39),
(123, 34, NULL, 40),
(124, 35, NULL, 5),
(125, 35, NULL, 6),
(126, 35, NULL, 41),
(127, 35, NULL, 42),
(128, 36, NULL, 25),
(129, 36, NULL, 26),
(130, 36, NULL, 39),
(131, 36, NULL, 40),
(132, 37, NULL, 27),
(133, 37, NULL, 28),
(134, 37, NULL, 37),
(135, 37, NULL, 38),
(136, 38, NULL, 3),
(137, 38, NULL, 4),
(138, 38, NULL, 27),
(139, 38, NULL, 28),
(140, 39, NULL, 15),
(141, 39, NULL, 16),
(142, 39, NULL, 17),
(143, 39, NULL, 18),
(144, 40, NULL, 5),
(145, 40, NULL, 6),
(146, 40, NULL, 29),
(147, 40, NULL, 30),
(148, 41, NULL, 15),
(149, 41, NULL, 16),
(150, 41, NULL, 17),
(151, 41, NULL, 18),
(152, 42, NULL, 25),
(153, 42, NULL, 26),
(154, 42, NULL, 27),
(155, 42, NULL, 28),
(156, 43, NULL, 13),
(157, 43, NULL, 14),
(158, 43, NULL, 51),
(159, 43, NULL, 52),
(160, 44, NULL, 25),
(161, 44, NULL, 26),
(162, 44, NULL, 27),
(163, 44, NULL, 28),
(164, 44, NULL, 49),
(165, 44, NULL, 50),
(166, 45, NULL, 1),
(167, 45, NULL, 2),
(168, 45, NULL, 3),
(169, 45, NULL, 4),
(170, 46, NULL, 5),
(171, 46, NULL, 6),
(172, 46, NULL, 37),
(173, 46, NULL, 38),
(174, 47, NULL, 39),
(175, 47, NULL, 40),
(176, 47, NULL, 41),
(177, 47, NULL, 42),
(178, 48, NULL, 13),
(179, 48, NULL, 14),
(180, 48, NULL, 15),
(181, 48, NULL, 16);