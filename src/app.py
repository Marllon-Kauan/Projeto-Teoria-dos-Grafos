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

def aulas_do_filtro(tipo, valor):
    """Aulas que pertencem ao filtro escolhido (tipo: 'periodo' ou 'professor')."""
    turmas = {t["id"]: t for t in repo.turmas()}
    resultado = []
    for aula in repo.aulas():
        turma = turmas.get(aula["turma"])
        if turma is None:
            continue
        if (tipo == "periodo" and turma["periodo"] == int(valor)) or \
           (tipo == "professor" and turma["prof"] == valor):
            # a sala pertence a aula (o back escolhe a sala por alocacao)
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


def ler_filtro(origem):
    """
    Le o filtro (querystring ou formulario) e aplica a regra: nao pode gerar a
    grade com periodo e professor preenchidos ao mesmo tempo.
    Retorna (tipo, valor, erro).
    """
    periodo = (origem.get("periodo") or "").strip()
    professor = (origem.get("professor") or "").strip()

    if periodo and professor:
        return None, None, "Selecione apenas um criterio: periodo OU professor."
    if periodo:
        if not periodo.isdigit() or int(periodo) not in repo.PERIODOS:
            return None, None, "Periodo invalido."
        return "periodo", int(periodo), None
    if professor:
        if professor not in repo.professores():
            return None, None, "Professor nao cadastrado."
        return "professor", professor, None
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


def validar_movimento(aula, dia_destino, h_destino):
    """
    Verifica se a aula pode ir para o novo dia/horario.
    Retorna None quando pode, ou a mensagem do impedimento.
    """
    destino = repo.hor_id(dia_destino, h_destino)
    if destino is None:
        return "Horario inexistente."

    turma = repo.buscar_turma(aula["turma"])
    onde = "%s, %s" % (repo.DIAS_LONGO[dia_destino], repo.horarios()[h_destino])

    # 1) horario bloqueado pelo usuario (vale so para o 1o ao 4o periodo)
    if (turma["periodo"] in repo.PERIODOS_BLOQUEAVEIS
            and destino in repo.bloqueados_por_periodo().get(turma["periodo"], set())):
        return "%s esta bloqueado para turmas do %do periodo." % (onde, turma["periodo"])

    # 2) restricao de horario do professor
    for r in repo.restricoes():
        if r["prof_id"] == turma["prof_id"] and r["hor_id"] == destino:
            return "%s tem restricao em %s (%s)." % (turma["prof"], onde, r["motivo"])

    # 2b) limite de aulas seguidas no mesmo dia pedido pelo professor
    limite = repo.max_seguidas_por_professor().get(turma["prof_id"])
    if limite:
        da_turma = [(a["dia"], a["h"]) for a in repo.aulas()
                    if a["turma"] == turma["id"] and a["id"] != aula["id"]]
        if maior_sequencia(da_turma + [(dia_destino, h_destino)]) > limite:
            return "%s aceita no maximo %d aulas seguidas no mesmo dia (%s)." % (
                turma["prof"], limite, turma["cod"])

    # 3) conflitos com as outras aulas no mesmo horario
    turmas = {t["id"]: t for t in repo.turmas()}
    for outra in repo.aulas():
        if outra["id"] == aula["id"] or outra["hor_id"] != destino:
            continue
        t2 = turmas.get(outra["turma"])
        if t2 is None:
            continue
        if t2["prof_id"] == turma["prof_id"]:
            return "%s ja tem aula em %s." % (turma["prof"], onde)
        if turma["periodo"] is not None and t2["periodo"] == turma["periodo"]:
            return "O %do periodo ja tem aula em %s." % (turma["periodo"], onde)
        if t2["dis_id"] == turma["dis_id"]:
            return "Outra turma da mesma disciplina ja tem aula em %s." % onde
        if outra["sal_id"] == aula["sal_id"]:
            return "A sala %s ja esta ocupada em %s." % (aula["sala"], onde)
    return None


# ---------------------------------------------------------------- telas

@app.route("/")
def index():
    """Tela principal: filtro de pesquisa + grade + informacoes adicionais."""
    tipo, valor, erro = ler_filtro(request.args)
    if erro:
        flash(erro, "erro")

    disciplinas = repo.disciplinas()
    aulas = aulas_do_filtro(tipo, valor) if tipo else []
    titulo = ""
    if tipo == "periodo":
        titulo = "%do periodo" % valor
    elif tipo == "professor":
        titulo = valor

    return render_template(
        "index.html",
        semestre=repo.semestre(),
        periodos=repo.PERIODOS,
        professores=repo.professores(),
        dias=repo.DIAS,
        horarios=repo.horarios(),
        disciplinas=disciplinas,
        filtro_tipo=tipo,
        filtro_valor=valor,
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
        repo.max_seguidas_por_professor(), repo.ids_do_algoritmo())

    if resultado["ok"]:
        flash("Grade gerada com sucesso: %d aulas alocadas." % len(repo.aulas()), "ok")
    elif resultado.get("parcial"):
        #Mostra o aviso de grade parcial e lista as turmas não alocadas.
        flash("Grade gerada parcialmente. Não foi possível alocar: " + "; ".join(resultado["turmas"]), "erro")
    else:
        flash("Erro ao gerar a grade.", "erro")

    return redirect(url_for("index", **({tipo: valor} if tipo else {})))


@app.route("/turmas")
def turmas():
    """Tela de cadastro das turmas do semestre."""
    return render_template(
        "turmas.html",
        semestre=repo.semestre(),
        turmas=repo.turmas(),
        disciplinas=repo.disciplinas(),
        professores=repo.professores(),
    )


def _render_editar_turma(turma, valores):
    salas_atuais = repo.salas_da_turma(turma["id"])
    return render_template(
        "editar_turma.html",
        semestre=repo.semestre(),
        turma=turma,
        valores=valores,
        disciplinas=repo.disciplinas(),
        professores=repo.professores(),
        salas=repo.salas(),
        tem_alocacoes=bool(salas_atuais),
        qtd_aulas=sum(1 for a in repo.aulas() if a["turma"] == turma["id"]),
    )


@app.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
def editar_turma(turma_id):
    """Edicao de turma (CT09): codigo, disciplina, professor e sala."""
    turma = repo.buscar_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "erro")
        return redirect(url_for("turmas"))

    if request.method == "POST":
        cod = request.form.get("cod")
        codigo = (request.form.get("turma") or "").strip()
        prof = request.form.get("prof")
        sala_raw = (request.form.get("sala") or "").strip()
        valores = {
            "cod": cod or "", "turma": codigo,
            "prof": prof or "", "sala": sala_raw,
        }

        if not (cod and codigo.isdigit() and prof):
            flash("Preencha a disciplina, o professor e o código numérico da turma.", "erro")
            return _render_editar_turma(turma, valores)
        if sala_raw and not sala_raw.isdigit():
            flash("Sala inválida.", "erro")
            return _render_editar_turma(turma, valores)

        erro, aviso = repo.atualizar_turma(
            turma_id, cod, int(codigo), prof,
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
        "prof": turma["prof"],
        "sala": str(salas_atuais[0]["id"]) if len(salas_atuais) == 1 else "",
    }
    return _render_editar_turma(turma, valores)


@app.route("/turmas/nova", methods=["POST"])
def nova_turma():
    cod = request.form.get("cod")
    codigo = (request.form.get("turma") or "").strip()
    prof = request.form.get("prof")

    if not (cod and codigo.isdigit() and prof):
        flash("Preencha a disciplina, o professor e o código numerico da turma.", "erro")
        return redirect(url_for("turmas"))

    erro = repo.criar_turma(cod, int(codigo), prof)
    if erro:
        flash(erro, "erro")
    else:
        flash("Turma cadastrada. Use \"Gerar grade\" para alocá-la.", "ok")
    return redirect(url_for("turmas"))


@app.route("/turmas/<int:turma_id>/excluir", methods=["POST"])
def excluir_turma(turma_id):
    repo.excluir_turma(turma_id)
    flash("Turma excluida junto com as aulas associadas a mesma.", "ok")
    return redirect(url_for("turmas"))


@app.route("/restricoes")
def restricoes():
    """Restricoes de horario dos professores + horarios bloqueados."""
    periodo_bloqueio = request.args.get("periodo", default=1, type=int)
    if periodo_bloqueio not in repo.PERIODOS_BLOQUEAVEIS:
        periodo_bloqueio = 1
    bloqueios = repo.bloqueados_por_periodo()
    return render_template(
        "restricoes.html",
        semestre=repo.semestre(),
        restricoes=repo.restricoes(),
        professores=repo.professores(),
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
    prof = request.form.get("prof")
    maximo = request.form.get("max")
    if not (prof in repo.professores() and maximo in ("2", "3")
            and repo.salvar_preferencia(prof, int(maximo))):
        flash("Escolha o professor e o limite de aulas seguidas.", "erro")
        return redirect(url_for("restricoes"))
    flash("Preferência salva. Use \"Gerar grade\" para aplicá-la.", "ok")
    return redirect(url_for("restricoes"))


@app.route("/preferencias/<int:pro_id>/excluir", methods=["POST"])
def excluir_preferencia(pro_id):
    repo.excluir_preferencia(pro_id)
    flash("Preferência removida.", "ok")
    return redirect(url_for("restricoes"))


@app.route("/restricoes/nova", methods=["POST"])
def nova_restricao():
    prof = request.form.get("prof")
    dia = request.form.get("dia")
    h = request.form.get("h")
    motivo = (request.form.get("motivo") or "").strip()

    if not (prof in repo.professores() and dia in repo.DIAS and h and h.isdigit()
            and repo.criar_restricao(prof, dia, int(h), motivo or "Não informado")):
        flash("Preencha todos os campos da restrição.", "erro")
        return redirect(url_for("restricoes"))

    flash("Restrição adicionada. Use \"Gerar grade\" para aplicá-la.", "ok")
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
        return jsonify(ok=False, mensagem="Dados invalidos para a alteracao."), 400

    erro = validar_movimento(aula, dia, h)
    if erro:
        return jsonify(ok=False, mensagem="Alteracao recusada. " + erro)

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


if __name__ == "__main__":
    app.run(debug=True)