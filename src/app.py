# -*- coding: utf-8 -*-
"""
Sistema de Grade Horaria - front (Flask) ligado ao back (SQLite + grafos).

Como executar (dentro da pasta src):
    pip install -r requirements.txt
    python setup_db.py      # so na primeira vez (cria banco_projeto.db)
    python app.py
    abrir http://127.0.0.1:5000
"""

import csv
import io
import re

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, Response, jsonify
)

import repositorio as repo
from services.gerador import gerar_grade

app = Flask(__name__)
app.secret_key = "chave-de-desenvolvimento-trocar-em-producao"

repo.garantir_esquema()



# ---------------------------------------------------------------- helpers

#Aulas que pertencem ao filtro escolhido (tipo: 'periodo' ou 'professor').
def aulas_do_filtro(tipo, valor):
    turmas = {t["id"]: t for t in repo.turmas()}
    resultado = []
    for aula in repo.aulas():
        turma = turmas.get(aula["turma"])
        if turma is None:
            continue
        if (tipo == "periodo" and turma["periodo"] == int(valor)) or \
           (tipo == "professor" and str(turma["prof_id"]) == str(valor)):
            resultado.append({**aula, "t": {**turma, "sala": aula["sala"]}})
    return resultado


def montar_tabela(aulas):
    """{(dia, horario): aula} usado pelo template para preencher a grade."""
    return {(a["dia"], a["h"]): a for a in aulas}


def montar_catalogo(aulas, disciplinas):
    """Catalogo de disciplinas do bloco 'Informacoes adicionais'."""
    catalogo, vistos = [], set()
    for aula in aulas:
        turma = aula["t"]
        if turma["id"] in vistos:
            continue
        vistos.add(turma["id"])
        catalogo.append({
            "cod": turma["cod"],
            "nome": disciplinas[turma["cod"]]["nome"],
            "cor": disciplinas[turma["cod"]]["cor"],
            "turma": turma["turma"],
            "prof": turma["prof"],
            "periodo": turma["periodo"],
            "sala": turma["sala"],
            "qtd": sum(1 for a in aulas if a["turma"] == turma["id"]),
        })
    return catalogo


#Lê o filtro e aplica: não gerar a grade com periodo e professor preenchidos ao mesmo tempo.
def ler_filtro(origem):
    periodo = (origem.get("periodo") or "").strip()
    professor = (origem.get("professor") or "").strip()

    if periodo and professor:
        return None, None, "Selecione apenas um criterio: periodo OU professor."
    if periodo:
        if not periodo.isdigit() or int(periodo) not in repo.PERIODOS:
            return None, None, "Periodo invalido."
        return "periodo", int(periodo), None
    if professor:
        if not professor.isdigit() or not repo.buscar_professor(int(professor)):
            return None, None, "Professor nao cadastrado."
        return "professor", int(professor), None
    return None, None, None


def maior_sequencia(posicoes):
    """Maior numero de aulas seguidas no mesmo dia, dado [(dia, h), ...]."""
    por_dia = {}
    for dia, h in posicoes:
        por_dia.setdefault(dia, []).append(h)
    maior = 0
    for slots in por_dia.values():
        slots.sort()
        atual = 0
        for i, s in enumerate(slots):
            atual = atual + 1 if i > 0 and s == slots[i - 1] + 1 else 1
            maior = max(maior, atual)
    return maior


#Verifica se a aula pode ir para o novo dia/horario.
def validar_movimento(aula, dia_destino, h_destino):
    destino = repo.hor_id(dia_destino, h_destino)
    if destino is None:
        return "Horário inexistente."

    turma = repo.buscar_turma(aula["turma"])
    onde = "%s, %s" % (repo.DIAS_LONGO[dia_destino], repo.horarios()[h_destino])

    #Horário bloqueado pelo usuário.
    if (turma["periodo"] in repo.PERIODOS_BLOQUEAVEIS
            and destino in repo.bloqueados_por_periodo().get(turma["periodo"], set())):
        return "%s está bloqueado para turmas do %do período." % (onde, turma["periodo"])

    #Restrição de horario do professor
    for r in repo.restricoes():
        if r["prof_id"] == turma["prof_id"] and r["hor_id"] == destino:
            return "%s tem restrição em %s (%s)." % (turma["prof"], onde, r["motivo"])

    #Limite de aulas seguidas e diárias do professor.
    limites = repo.limites_por_professor().get(turma["prof_id"])
    if limites:
        #Lista as posições de todas as aulas do professor, exceto a que está sendo movida.
        aulas_prof = []
        for a in repo.aulas():
            if a["id"] == aula["id"]:
                continue
            t_aux = repo.buscar_turma(a["turma"])
            if t_aux and t_aux["prof_id"] == turma["prof_id"]:
                aulas_prof.append((a["dia"], a["h"]))

        #Verifica o novo limite diário.
        aulas_no_dia = [h for d, h in aulas_prof if d == dia_destino] + [h_destino]
        if len(aulas_no_dia) > limites["diarias"]:
            return "%s aceita no máximo %d aulas por dia." % (turma["prof"], limites["diarias"])

        #Verifica o limite de seguidas com a função já existente.
        if maior_sequencia(aulas_prof + [(dia_destino, h_destino)]) > limites["seguidas"]:
            return "%s aceita no máximo %d aulas seguidas no mesmo dia." % (
                turma["prof"], limites["seguidas"])

    #Conflitos com as outras aulas no mesmo horario.
    turmas = {t["id"]: t for t in repo.turmas()}
    for outra in repo.aulas():
        if outra["id"] == aula["id"] or outra["hor_id"] != destino:
            continue
        t2 = turmas.get(outra["turma"])
        if t2 is None:
            continue
        if t2["prof_id"] == turma["prof_id"]:
            return "%s já tem aula em %s." % (turma["prof"], onde)
        if (not turma.get("eletiva") and not t2.get("eletiva")
                and turma["periodo"] is not None and t2["periodo"] == turma["periodo"]):
            return "O %do período já tem aula em %s." % (turma["periodo"], onde)
        if t2["dis_id"] == turma["dis_id"]:
            return "Outra turma da mesma disciplina já tem aula em %s." % onde
        if outra["sal_id"] == aula["sal_id"]:
            return "A sala %s já está ocupada em %s." % (aula["sala"], onde)
    return None


# ---------------------------------------------------------------- telas

@app.route("/")
def index():
    tipo, valor, erro = ler_filtro(request.args)
    if erro:
        flash(erro, "erro")

    disciplinas = repo.disciplinas()
    aulas = aulas_do_filtro(tipo, valor) if tipo else []
    titulo = ""
    if tipo == "periodo":
        titulo = "%do periodo" % valor
    elif tipo == "professor":
        prof_obj = repo.buscar_professor(int(valor)) if valor and str(valor).isdigit() else None
        titulo = prof_obj["nome"] if prof_obj else ""

    return render_template(
        "index.html",
        semestre=repo.semestre(),
        periodos=repo.PERIODOS,
        professores=repo.professores_detalhados(),
        dias=repo.DIAS,
        horarios=repo.horarios(),
        disciplinas=disciplinas,
        filtro_tipo=tipo,
        filtro_valor=str(valor) if valor else "",
        titulo=titulo,
        tabela=montar_tabela(aulas),
        catalogo=montar_catalogo(aulas, disciplinas),
        total_aulas=len(aulas),
        modo_edicao=request.args.get("editar") == "1",
    )


@app.route("/gerar", methods=["POST"])
def gerar():
    """Roda o algoritmo do back com os bloqueios e restricoes cadastrados."""
    tipo, valor, _ = ler_filtro(request.form)

    resultado = gerar_grade(
        repo.DB_PATH, repo.SEMESTRE_ID, repo.bloqueados_por_periodo(), repo.restricoes_por_professor(),
        repo.limites_por_professor(), repo.ids_do_algoritmo())

    if resultado.get("sem_horarios"):
        flash("Não é possível gerar a grade: é necessário cadastrar pelo menos um horário.", "erro")
    elif resultado["ok"]:
        flash("Grade gerada com sucesso: %d aulas alocadas." % len(repo.aulas()), "ok")
    elif resultado.get("parcial"):
        flash("Grade gerada parcialmente. Não foi possível alocar: " + "; ".join(resultado["turmas"]), "erro")
    else:
        flash("Erro ao gerar a grade.", "erro")

    return redirect(url_for("index", **({tipo: valor} if tipo else {})))


#Tela de cadastro das turmas do semestre.
@app.route("/turmas")
def turmas():
    return render_template(
        "turmas.html",
        semestre=repo.semestre(),
        turmas=repo.turmas(),
        disciplinas=repo.disciplinas(),
        professores=repo.professores_detalhados(),
    )


def _render_editar_turma(turma, valores):
    return render_template(
        "editar_turma.html",
        semestre=repo.semestre(),
        turma=turma,
        valores=valores,
        disciplinas=repo.disciplinas(),
        professores=repo.professores_detalhados(),
        salas=[s for s in repo.salas() if s["status"] == repo.STATUS_DISPONIVEL],
        tem_alocacoes=bool(repo.salas_da_turma(turma["id"])),
        qtd_aulas=sum(1 for a in repo.aulas() if a["turma"] == turma["id"]),
    )


@app.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
def editar_turma(turma_id):
    turma = repo.buscar_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "erro")
        return redirect(url_for("turmas"))

    if request.method == "POST":
        cod = request.form.get("cod")
        codigo = (request.form.get("turma") or "").strip().upper()
        prof_id = request.form.get("prof")
        sala_raw = (request.form.get("sala") or "").strip()
        
        valores = {
            "cod": cod or "", "turma": codigo,
            "prof_id": prof_id or "", "sala": sala_raw,
        }

        if not (cod and len(codigo) == 2 and codigo.isalpha() and prof_id):
            flash("Preencha a disciplina, o professor e um código de exatamente 2 letras para a turma (ex: MA, TG).", "erro")
            return _render_editar_turma(turma, valores)
            
        if sala_raw and not sala_raw.isdigit():
            flash("Sala inválida.", "erro")
            return _render_editar_turma(turma, valores)

        erro, aviso = repo.atualizar_turma(
            turma_id, cod, codigo, prof_id,
            int(sala_raw) if sala_raw else None,
        )
        if erro:
            flash(erro, "erro")
            return _render_editar_turma(turma, valores)

        mensagem = "Turma atualizada com sucesso."
        if aviso:
            mensagem += " " + aviso
        flash(mensagem, "ok")
        return redirect(url_for("turmas"))

    salas_atuais = repo.salas_da_turma(turma_id)
    valores = {
        "cod": turma["cod"],
        "turma": turma["turma"],
        "prof_id": str(turma["prof_id"]),
        "sala": str(salas_atuais[0]["id"]) if len(salas_atuais) == 1 else "",
    }
    return _render_editar_turma(turma, valores)


@app.route("/turmas/nova", methods=["POST"])
def nova_turma():
    cod = request.form.get("cod")
    codigo = (request.form.get("turma") or "").strip().upper() 
    prof_id = request.form.get("prof")

    if not (cod and len(codigo) == 2 and codigo.isalpha() and prof_id):
        flash("Preencha a disciplina, o professor e um código de exatamente 2 letras para a turma (ex: MA, TG).", "erro")
        return redirect(url_for("turmas"))

    erro = repo.criar_turma(cod, codigo, prof_id)
    
    if erro:
        flash(erro, "erro")
    else:
        flash("Turma cadastrada. Use \"Gerar grade\" para alocá-la.", "ok")
    return redirect(url_for("turmas"))


@app.route("/turmas/<int:turma_id>/excluir", methods=["POST"])
def excluir_turma(turma_id):
    repo.excluir_turma(turma_id)
    flash("Turma excluída junto com as aulas associadas à mesma.", "ok")
    return redirect(url_for("turmas"))


def _render_salas(valores=None):
    return render_template(
        "salas.html",
        semestre=repo.semestre(),
        salas=repo.salas(),
        valores=valores or {},
    )


@app.route("/salas", methods=["GET", "POST"])
def salas():
    """Cadastro, disponibilidade e exclusao das salas de aula."""
    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "criar":
            bloco = (request.form.get("bloco") or "").strip()
            numero = (request.form.get("numero") or "").strip()
            valores = {"bloco": bloco, "numero": numero}
            if (not bloco.isalpha() or len(bloco) > 20
                    or not numero.isdigit() or int(numero) <= 0):
                flash("Informe um bloco com letras e um número de sala maior que zero.", "erro")
                return _render_salas(valores)
            erro = repo.criar_sala(bloco, int(numero))
            if erro:
                flash(erro, "erro")
                return _render_salas(valores)
            flash("Sala %s-%s cadastrada." % (bloco.upper(), int(numero)), "ok")
            return redirect(url_for("salas"))

        if acao == "disponibilidade":
            sala_id = request.form.get("sala_id", "")
            status = request.form.get("status")
            motivo = (request.form.get("motivo") or "").strip()
            if (not sala_id.isdigit()
                    or status not in (repo.STATUS_DISPONIVEL, repo.STATUS_INDISPONIVEL)):
                flash("Não foi possível alterar a disponibilidade: dados inválidos.", "erro")
                return redirect(url_for("salas"))
            
            erro, aviso = repo.atualizar_disponibilidade_sala(int(sala_id), status, motivo)
            
            if erro:
                flash(erro, "erro")
            elif status == repo.STATUS_INDISPONIVEL:
                mensagem = "Sala marcada como indisponível."
                if aviso:
                    mensagem += " " + aviso
                flash(mensagem, "ok")
            else:
                flash("Sala marcada como disponível. O motivo anterior foi removido.", "ok")
            return redirect(url_for("salas"))

        if acao == "excluir":
            sala_id = request.form.get("sala_id", "")
            if not sala_id.isdigit():
                flash("Não foi possível excluir: sala inválida.", "erro")
                return redirect(url_for("salas"))
            erro = repo.excluir_sala(int(sala_id))
            if erro:
                flash(erro, "erro")
            else:
                flash("Sala excluída.", "ok")
            return redirect(url_for("salas"))

        flash("Ação inválida para a tela de salas.", "erro")
        return redirect(url_for("salas"))

    return _render_salas()


#Restricoes de horario dos professores + horarios bloqueados.
@app.route("/restricoes")
def restricoes():
    periodo_bloqueio = request.args.get("periodo", default=1, type=int)
    if periodo_bloqueio not in repo.PERIODOS_BLOQUEAVEIS:
        periodo_bloqueio = 1
    bloqueios = repo.bloqueados_por_periodo()
    return render_template(
        "restricoes.html",
        semestre=repo.semestre(),
        restricoes=repo.restricoes(),
        professores=repo.professores_detalhados(),
        dias=repo.DIAS,
        dias_longo=repo.DIAS_LONGO,
        horarios=repo.horarios(),
        ids=repo.ids_por_dia_h(),
        bloqueados=bloqueios[periodo_bloqueio],
        periodo_bloqueio=periodo_bloqueio,
        periodos_bloqueaveis=repo.PERIODOS_BLOQUEAVEIS,
        preferencias=repo.preferencias(),
    )


@app.route("/preferencias/nova", methods=["POST"])
def nova_preferencia():
    prof_id = request.form.get("prof")
    max_seg = request.form.get("max_seg")
    max_dia = request.form.get("max_dia")
    
    if prof_id and prof_id.isdigit() and repo.buscar_professor(int(prof_id)) and max_seg in ("2", "3") and max_dia in ("2", "4"):
        repo.salvar_preferencia(int(prof_id), int(max_seg), int(max_dia))
        flash("Preferência salva. Use \"Gerar grade\" para aplicá-la.", "ok")
    else:
        flash("Escolha o professor e os limites corretamente.", "erro")
    return redirect(url_for("restricoes"))

@app.route("/preferencias/<int:pro_id>/excluir", methods=["POST"])
def excluir_preferencia(pro_id):
    repo.excluir_preferencia(pro_id)
    flash("Preferência removida.", "ok")
    return redirect(url_for("restricoes"))


@app.route("/restricoes/nova", methods=["POST"])
def nova_restricao():
    prof_id = request.form.get("prof")
    dia = request.form.get("dia")
    h = request.form.get("h")
    motivo = (request.form.get("motivo") or "").strip()

    horarios_validos = [str(i) for i in range(len(repo.horarios()))] + ["todos"]

    if not (prof_id and prof_id.isdigit() and repo.buscar_professor(int(prof_id)) and dia in repo.DIAS and h in horarios_validos):
        flash("Preencha todos os campos da restrição.", "erro")
        return redirect(url_for("restricoes"))

    status = repo.criar_restricao(int(prof_id), dia, h, motivo or "Não informado")

    if status == "atualizado":
        flash("Esta restrição já existia. O motivo foi atualizado com sucesso. Use \"Gerar grade\" para aplicar.", "ok")
    elif status == "criado":
        flash("Restrição adicionada. Use \"Gerar grade\" para aplicar.", "ok")
    else:
        flash("Erro ao salvar a restrição. Tente novamente.", "erro")

    return redirect(url_for("restricoes"))


@app.route("/restricoes/<int:restricao_id>/excluir", methods=["POST"])
def excluir_restricao(restricao_id):
    repo.excluir_restricao(restricao_id)
    flash("Restrição excluída.", "ok")
    return redirect(url_for("restricoes"))


@app.route("/restricoes/bloqueios", methods=["POST"])
def salvar_bloqueios():
    periodo = request.form.get("periodo", "1")
    if not periodo.isdigit() or int(periodo) not in repo.PERIODOS_BLOQUEAVEIS:
        flash("Selecione um período válido para salvar os bloqueios.", "erro")
        return redirect(url_for("restricoes", periodo=1))
    periodo = int(periodo)
    ids = {int(v) for v in request.form.getlist("bloq") if v.isdigit()}
    salvos = repo.salvar_bloqueados(periodo, ids)
    flash("%d horário(s) bloqueado(s) para o %do período. Use \"Gerar grade\" para aplicar."
          % (len(salvos), periodo), "ok")
    return redirect(url_for("restricoes", periodo=periodo))


# ---------------------------------------------------------------- edicao

@app.route("/editar/mover", methods=["POST"])
def mover_aula():
    """
    Move uma aula para outro dia/horario.
    So aplica a alteracao se passar na verificacao das restricoes.
    """
    corpo = request.get_json(silent=True) or {}
    aula_id = corpo.get("aula_id")
    dia = corpo.get("dia")
    h = corpo.get("h")

    aula = next((a for a in repo.aulas() if a["id"] == aula_id), None)
    if (aula is None or dia not in repo.DIAS or not isinstance(h, int)
            or not 0 <= h < len(repo.horarios())):
        return jsonify(ok=False, mensagem="Dados inválidos para a alteração."), 400

    erro = validar_movimento(aula, dia, h)
    if erro:
        return jsonify(ok=False, mensagem="Alteração recusada. " + erro)

    repo.mover_aula(aula["id"], repo.hor_id(dia, h))
    turma = repo.buscar_turma(aula["turma"])
    return jsonify(ok=True, mensagem="%s movida para %s, %s." % (
        turma["cod"], repo.DIAS_LONGO[dia], repo.horarios()[h]))


# ---------------------------------------------------------------- exportacao

def _texto_celula(aula, disciplinas):
    t = aula["t"]
    return "%s %s - %s - Sala %s - %s" % (
        t["cod"], t["turma"], disciplinas[t["cod"]]["nome"], t["sala"], t["prof"])


@app.route("/exportar/csv")
def exportar_csv():
    """Exporta em CSV a grade que esta sendo visualizada."""
    tipo, valor, erro = ler_filtro(request.args)
    if erro or not tipo:
        flash(erro or "Gere uma grade antes de exportar.", "erro")
        return redirect(url_for("index"))

    disciplinas = repo.disciplinas()
    tabela = montar_tabela(aulas_do_filtro(tipo, valor))

    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["Grade horaria", str(valor), "Semestre", repo.semestre()])
    escritor.writerow([])
    escritor.writerow(["Horario"] + repo.DIAS)

    for i, faixa in enumerate(repo.horarios()):
        linha = [faixa]
        for dia in repo.DIAS:
            aula = tabela.get((dia, i))
            linha.append(_texto_celula(aula, disciplinas) if aula else "")
        escritor.writerow(linha)

    nome = "grade_%s_%s.csv" % (str(valor).replace(" ", "_"), repo.semestre())
    return Response(
        saida.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=%s" % nome},
    )


@app.route("/exportar/pdf")
def exportar_pdf():
    """Exporta em PDF a grade que esta sendo visualizada (usa reportlab)."""
    tipo, valor, erro = ler_filtro(request.args)
    if erro or not tipo:
        flash(erro or "Gere uma grade antes de exportar.", "erro")
        return redirect(url_for("index"))

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    except ImportError:
        flash("Instale o reportlab para exportar PDF: pip install reportlab", "erro")
        return redirect(url_for("index", **{tipo: valor}))

    disciplinas = repo.disciplinas()
    tabela = montar_tabela(aulas_do_filtro(tipo, valor))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm)
    estilos = getSampleStyleSheet()
    celula = estilos["BodyText"]
    celula.fontSize = 7
    celula.leading = 9

    conteudo = [
        Paragraph("Grade horaria - %s" % valor, estilos["Heading2"]),
        Paragraph("Semestre %s" % repo.semestre(), estilos["Normal"]),
        Spacer(1, 6 * mm),
    ]

    linhas = [["Horario"] + repo.DIAS]
    for i, faixa in enumerate(repo.horarios()):
        linha = [Paragraph(faixa, celula)]
        for dia in repo.DIAS:
            aula = tabela.get((dia, i))
            if aula:
                t = aula["t"]
                linha.append(Paragraph("<b>%s %s</b><br/>%s<br/>Sala %s - %s" % (
                    t["cod"], t["turma"], disciplinas[t["cod"]]["nome"],
                    t["sala"], t["prof"]), celula))
            else:
                linha.append("")
        linhas.append(linha)

    largura = doc.width
    col_dia = (largura * 0.87) / len(repo.DIAS)
    tab = Table(linhas, colWidths=[largura * 0.13] + [col_dia] * len(repo.DIAS), repeatRows=1)
    tab.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BCC5BB")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0EFE8")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F1F3F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
    ]))
    conteudo.append(tab)
    doc.build(conteudo)

    nome = "grade_%s_%s.pdf" % (str(valor).replace(" ", "_"), repo.semestre())
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=%s" % nome},
    )


#Cadastro de professores.

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def email_valido(email):
    return bool(re.match(EMAIL_REGEX, email or ""))


def _render_professores(valores=None):
    return render_template(
        "professores.html",
        semestre=repo.semestre(),
        professores=repo.professores_detalhados(),
        valores=valores or {},
    )


def _render_disciplinas(valores=None):
    return render_template(
        "disciplinas.html",
        semestre=repo.semestre(),
        disciplinas=list(repo.disciplinas().values()),
        periodos=repo.PERIODOS,
        valores=valores or {},
    )

#Valida e normaliza os campos da tela de disciplinas.
def _disciplina_formulario(origem):
    CODIGO_DISCIPLINA_REGEX = r"^[A-Z]{4}\d{4}$"

    codigo = (origem.get("codigo") or "").strip().upper()
    nome = (origem.get("nome") or "").strip()
    periodo_texto = (origem.get("periodo") or "").strip()
    carga_texto = (origem.get("carga") or "").strip()
    eletiva = origem.get("eletiva") == "1"
    valores = {
        "codigo": codigo, "nome": nome, "periodo": periodo_texto,
        "carga": carga_texto, "eletiva": "1" if eletiva else "0",
    }
    if not codigo or not nome or not carga_texto:
        return valores, None, "Preencha todos os campos obrigatórios."

    if not re.match(CODIGO_DISCIPLINA_REGEX, codigo):
        return valores, None, "O código da disciplina deve conter exatamente 4 letras seguidas de 4 números (ex: CCMP0000), sem espaços ou caracteres especiais."

    try:
        carga = int(carga_texto)
    except ValueError:
        return valores, None, "A carga horária deve ser um número inteiro maior que zero."
    if carga < 15 or carga % 15 != 0:
        return valores, None, "A carga horária deve ser maior ou igual a 15 e múltipla de 15."
    if periodo_texto:
        if not periodo_texto.isdigit() or int(periodo_texto) not in repo.PERIODOS:
            return valores, None, "Selecione um período curricular válido."
        periodo = int(periodo_texto)
    else:
        periodo = None
    if not eletiva and periodo is None:
        return valores, None, "Disciplinas não eletivas exigem um período curricular específico."
    return valores, (codigo, nome, periodo, carga, eletiva), None


def _valores_disciplina(disciplina):
    return {
        "codigo": disciplina["cod"],
        "nome": disciplina["nome"],
        "periodo": "" if disciplina["periodo"] is None else str(disciplina["periodo"]),
        "carga": str(disciplina["carga_horaria"]),
        "eletiva": "1" if disciplina["eletiva"] else "0",
    }

#Tela principal de listagem dos professores.
@app.route("/professores")
def listar_professores():
    return _render_professores()


#Cadastro de novo professor
@app.route("/professores/novo", methods=["POST"])
def novo_professor():
    nome = (request.form.get("nome") or "").strip()
    email = (request.form.get("email") or "").strip()
    valores = {"nome": nome, "email": email}

    if not nome or not email:
        flash("Preencha todos os campos obrigatórios.", "erro")
        return _render_professores(valores)

    if not email_valido(email):
        flash("Informe um e-mail em formato válido (ex: professor@upe.br).", "erro")
        return _render_professores(valores)

    erro = repo.criar_professor(nome, email)
    if erro:
        flash(erro, "erro")
        return _render_professores(valores)
    else:
        flash("Professor cadastrado com sucesso.", "ok")

    return redirect(url_for("listar_professores"))


@app.route("/disciplinas")
def listar_disciplinas():
    return _render_disciplinas()


@app.route("/disciplinas/nova", methods=["POST"])
def nova_disciplina():
    valores, dados, erro = _disciplina_formulario(request.form)
    if erro:
        flash(erro, "erro")
        return _render_disciplinas(valores)
    erro = repo.criar_disciplina(*dados)
    if erro:
        flash(erro, "erro")
        return _render_disciplinas(valores)
    else:
        flash("Disciplina cadastrada com sucesso.", "ok")
        
    return redirect(url_for('listar_disciplinas'))


@app.route("/disciplinas/<int:dis_id>/editar", methods=["GET", "POST"])
def editar_disciplina(dis_id):
    disciplina = repo.buscar_disciplina(dis_id)
    if not disciplina:
        flash("Disciplina não encontrada.", "erro")
        return redirect(url_for("listar_disciplinas"))

    if request.method == "POST":
        valores, dados, erro = _disciplina_formulario(request.form)
        turmas_afetadas = repo.turmas_com_alocacoes_disciplina(dis_id)
        if erro:
            flash(erro, "erro")
            return render_template("editar_disciplina.html", semestre=repo.semestre(), disciplina=disciplina, periodos=repo.PERIODOS, valores=valores, turmas_afetadas=turmas_afetadas)

        #Captura erro e aviso retornados pelo repositório
        confirmar = request.form.get("confirmar_alocacoes") == "1"
        erro, aviso = repo.atualizar_disciplina(dis_id, *dados, confirmar=confirmar)
        if erro:
            flash(erro, "erro")
            return render_template("editar_disciplina.html", semestre=repo.semestre(), disciplina=disciplina, periodos=repo.PERIODOS, valores=valores, turmas_afetadas=turmas_afetadas)

        mensagem = "Disciplina atualizada com sucesso."
        if aviso:
            mensagem += " " + aviso
        flash(mensagem, "ok")
        return redirect(url_for("listar_disciplinas"))

    return render_template("editar_disciplina.html", semestre=repo.semestre(), disciplina=disciplina, periodos=repo.PERIODOS, valores=_valores_disciplina(disciplina), turmas_afetadas=repo.turmas_com_alocacoes_disciplina(dis_id))


@app.route("/disciplinas/<int:dis_id>/excluir", methods=["POST"])
def excluir_disciplina(dis_id):
    confirmar = request.form.get("confirmar") == "1"
    erro, aviso = repo.excluir_disciplina(dis_id, confirmar=confirmar)

    if erro and erro.startswith("CONFIRMACAO_NECESSARIA"):
        flash(erro.replace("CONFIRMACAO_NECESSARIA: ", ""), "erro")
        return render_template(
            "confirmar_exclusao_disciplina.html",
            semestre=repo.semestre(),
            dis_id=dis_id,
            perfis_afetados=aviso
        )
    elif erro:
        flash(erro, "erro")
    else:
        mensagem = "Disciplina excluída com sucesso."
        if aviso:
            mensagem += " " + aviso
        flash(mensagem, "ok")

    return redirect(url_for("listar_disciplinas"))


#Edição dos dados do professor
@app.route("/professores/<int:pro_id>/editar", methods=["GET", "POST"])
def editar_professor(pro_id):
    prof = repo.buscar_professor(pro_id)
    if not prof:
        flash("Professor não encontrado.", "erro")
        return redirect(url_for("listar_professores"))

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")

        if not nome or not email:
            flash("Preencha todos os campos obrigatórios.", "erro")
            valores = {"nome": nome, "email": email}
            return render_template("editar_professor.html", semestre=repo.semestre(), professor=prof, valores=valores)

        if not email_valido(email):
            flash("Informe um e-mail em formato válido (ex: professor@upe.br).", "erro")
            valores = {"nome": nome, "email": email}
            return render_template("editar_professor.html", semestre=repo.semestre(), professor=prof, valores=valores)

        erro = repo.atualizar_professor(pro_id, nome, email)
        if erro:
            flash(erro, "erro")
            valores = {"nome": nome, "email": email}
            return render_template("editar_professor.html", semestre=repo.semestre(), professor=prof, valores=valores)

        flash("Dados do professor atualizados com sucesso.", "ok")
        return redirect(url_for("listar_professores"))

    return render_template("editar_professor.html", semestre=repo.semestre(), professor=prof, valores=prof)


#Exclusão de professor com checagem de turmas e remoção de restrições.
@app.route("/professores/<int:pro_id>/excluir", methods=["POST"])
def excluir_professor(pro_id):
    erro = repo.excluir_professor(pro_id)
    if erro:
        flash(erro, "erro")
    else:
        flash("Professor e suas restrições do semestre ativo foram excluídos com sucesso.", "ok")
    return redirect(url_for("listar_professores"))


#Cadastro de horários
@app.route("/horarios")
def listar_horarios():
    return render_template(
        "horarios.html",
        semestre=repo.semestre(),
        horarios=repo.listar_horarios_cadastrados(),
        valores={}
    )

@app.route("/horarios/novo", methods=["POST"])
def novo_horario():
    inicio = request.form.get("inicio")
    fim = request.form.get("fim")

    erro = repo.criar_horario(inicio, fim)
    if erro:
        flash(erro, "erro")
        return render_template("horarios.html", semestre=repo.semestre(), horarios=repo.listar_horarios_cadastrados(), valores={"inicio": inicio or "", "fim": fim or ""})
    else:
        flash("Horário cadastrado com sucesso. Lembre-se de gerar uma nova grade.", "ok")
    return redirect(url_for("listar_horarios"))

@app.route("/horarios/<int:hor_id>/editar", methods=["GET", "POST"])
def editar_horario(hor_id):
    horario = repo.buscar_horario(hor_id)
    if not horario:
        flash("Horário não encontrado.", "erro")
        return redirect(url_for("listar_horarios"))

    if request.method == "POST":
        inicio = request.form.get("inicio")
        fim = request.form.get("fim")
        
        erro = repo.atualizar_horario(hor_id, inicio, fim)
        if erro:
            flash(erro, "erro")
            return render_template("editar_horario.html", semestre=repo.semestre(), horario=horario, valores={"inicio": inicio or "", "fim": fim or ""})
            
        flash("Horário atualizado com sucesso.", "ok")
        return redirect(url_for("listar_horarios"))

    return render_template("editar_horario.html", semestre=repo.semestre(), horario=horario, valores=horario)

@app.route("/horarios/<int:hor_id>/excluir", methods=["POST"])
def excluir_horario(hor_id):
    erro, aviso = repo.excluir_horario(hor_id)
    if erro:
        flash(erro, "erro")
    else:
        mensagem = "Horário excluído com sucesso."
        if aviso:
            mensagem += " " + aviso
        flash(mensagem, "ok")
    return redirect(url_for("listar_horarios"))


#Perfis Curriculares 

@app.route("/perfis")
def listar_perfis():
    return render_template(
        "perfis.html",
        semestre=repo.semestre(),
        perfis=repo.perfis()
    )


@app.route("/perfis/novo", methods=["GET", "POST"])
def novo_perfil():
    if request.method == "POST":
        nome = request.form.get("nome")
        disciplinas_ids = request.form.getlist("disciplinas")
        erro = repo.criar_perfil(nome, disciplinas_ids)
        if erro:
            flash(erro, "erro")
            return render_template(
                "novo_perfil.html",
                semestre=repo.semestre(),
                disciplinas=list(repo.disciplinas().values()),
                valores={"nome": nome, "disciplinas": disciplinas_ids}
            )
        flash("Perfil curricular cadastrado com sucesso.", "ok")
        return redirect(url_for("listar_perfis"))

    return render_template(
        "novo_perfil.html",
        semestre=repo.semestre(),
        disciplinas=list(repo.disciplinas().values()),
        valores={}
    )


@app.route("/perfis/<int:perfil_id>")
def visualizar_perfil(perfil_id):
    detalhes = repo.detalhar_perfil_por_periodo(perfil_id)
    if not detalhes:
        flash("Perfil curricular não encontrado.", "erro")
        return redirect(url_for("listar_perfis"))

    return render_template(
        "visualizar_perfil.html",
        semestre=repo.semestre(),
        perfil=detalhes,
        periodos=repo.PERIODOS
    )


@app.route("/perfis/<int:perfil_id>/editar", methods=["GET", "POST"])
def editar_perfil(perfil_id):
    prof = repo.buscar_perfil(perfil_id)
    if not prof:
        flash("Perfil curricular não encontrado.", "erro")
        return redirect(url_for("listar_perfis"))

    if request.method == "POST":
        nome = request.form.get("nome")
        disciplinas_ids = request.form.getlist("disciplinas")
        erro = repo.atualizar_perfil(perfil_id, nome, disciplinas_ids)
        if erro:
            flash(erro, "erro")
            return render_template(
                "editar_perfil.html",
                semestre=repo.semestre(),
                perfil=prof,
                disciplinas=list(repo.disciplinas().values()),
                valores={"nome": nome, "disciplinas": disciplinas_ids}
            )
        flash("Perfil curricular atualizado com sucesso.", "ok")
        return redirect(url_for("listar_perfis"))

    return render_template(
        "editar_perfil.html",
        semestre=repo.semestre(),
        perfil=prof,
        disciplinas=list(repo.disciplinas().values()),
        valores={"nome": prof["nome"], "disciplinas": [str(i) for i in prof["disciplinas_ids"]]}
    )


@app.route("/perfis/<int:perfil_id>/excluir", methods=["POST"])
def excluir_perfil(perfil_id):
    erro = repo.excluir_perfil(perfil_id)
    if erro:
        flash(erro, "erro")
    else:
        flash("Perfil curricular excluído com sucesso. As turmas e grades existentes foram preservadas.", "ok")
    return redirect(url_for("listar_perfis"))

#Uso do Perfil na Geração

@app.route("/turmas/carregar_perfil", methods=["GET", "POST"])
def carregar_perfil_turmas():
    perfis_cadastrados = repo.perfis()
    perfil_id = request.args.get("perfil_id") or request.form.get("perfil_id")

    detalhes_perfil = None
    if perfil_id and perfil_id.isdigit():
        detalhes_perfil = repo.detalhar_perfil_por_periodo(int(perfil_id))

    return render_template(
        "configurar_perfil_turmas.html",
        semestre=repo.semestre(),
        perfis=perfis_cadastrados,
        perfil_selecionado=detalhes_perfil,
        professores=repo.professores_detalhados()
    )


@app.route("/turmas/aplicar_perfil", methods=["POST"])
def aplicar_perfil_turmas():
    flash("A aplicação automática de perfis às turmas está temporariamente bloqueada para preservar grades existentes.", "erro")
    return redirect(url_for("carregar_perfil_turmas"))

    # Fluxo preservado para futura ativação após proteção das alocações.
    confirmar = request.form.get("confirmar") == "1"
    
    dis_ids = request.form.getlist("dis_id")
    codigos = request.form.getlist("turma_codigo")
    prof_ids = request.form.getlist("prof_id")

    turmas_config = []
    for d, c, p in zip(dis_ids, codigos, prof_ids):
        if d and c and p:
            turmas_config.append({
                "dis_id": int(d),
                "codigo": c.strip().upper(),
                "prof_id": int(p)
            })

    erro = repo.aplicar_perfil_turmas(turmas_config, confirmar=confirmar)

    if erro and erro.startswith("CONFIRMACAO_NECESSARIA"):
        return render_template(
            "confirmar_substituicao_turmas.html",
            semestre=repo.semestre(),
            turmas_config=turmas_config
        )
    elif erro:
        flash(erro, "erro")
        return redirect(url_for("carregar_perfil_turmas"))

    flash("Configuração de turmas salva. Existem alterações ainda não refletidas na grade exibida; acione 'Gerar grade' para atualizar.", "ok")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
