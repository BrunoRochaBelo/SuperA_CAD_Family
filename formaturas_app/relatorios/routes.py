import csv
from flask import Blueprint, render_template, request, Response, jsonify, flash
from flask_login import login_required, current_user
from formaturas_app import db
from formaturas_app.models import Parente, Formando
import pandas as pd
from io import BytesIO
from datetime import datetime

# Importações do ReportLab para gerar PDFs
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/filtrar', methods=['GET', 'POST'])
@login_required
def filtrar():
    # Alterado: comparar current_user.papel.value para ADM
    if current_user.papel.value != 'ADM':
        return "Acesso negado!", 403

    turmas_opcoes = db.session.query(Formando.turma).distinct().all()
    alunos_opcoes = db.session.query(Formando.aluno).distinct().all()
    cidades_opcoes = db.session.query(Parente.cidade).distinct().all()

    preview_fields = []

    if request.method == 'POST':
        turma = request.form.get('turma')
        aluno = request.form.get('aluno')
        cidade = request.form.get('cidade')
        comprou_foto = request.form.get('comprou_foto')
        export_type = request.form.get('export_type')
        fields = request.form.getlist('fields')
        preview_fields = fields
        file_name = request.form.get('file_name')  # Nome do arquivo fornecido pelo usuário

        query = _build_query(turma, aluno, cidade, comprou_foto)
        resultado = query.all()

        if export_type in ['excel', 'pdf']:
            return gerar_relatorio(resultado, export_type, fields, file_name)
        else:
            flash("Selecione um tipo de exportação.", "danger")

    return render_template('relatorios/filtrar.html',
                           turmas=turmas_opcoes,
                           alunos=alunos_opcoes,
                           cidades=cidades_opcoes,
                           preview_fields=preview_fields,
                           active_page='relatorios')

@relatorios_bp.route('/listar_alunos/<turma>')
@login_required
def listar_alunos(turma):
    if turma == 'TODAS':
        formandos = Formando.query.all()
    else:
        formandos = Formando.query.filter_by(turma=turma).all()
    data = []
    for f in formandos:
        data.append({'aluno': f.aluno})
    return jsonify(data)

@relatorios_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    """
    Retorna as primeiras 3 linhas do resultado para exibir na pré-visualização.
    """
    # Alterado: comparar current_user.papel.value para ADM
    if current_user.papel.value != 'ADM':
        return jsonify({'error': 'Acesso negado.'}), 403

    data = request.json or {}
    turma = data.get('turma')
    aluno = data.get('aluno')
    cidade = data.get('cidade')
    comprou_foto = data.get('comprou_foto')
    fields = data.get('fields', [])

    query = _build_query(turma, aluno, cidade, comprou_foto)
    resultado = query.limit(3).all()  # Pega somente 3 linhas

    preview_data = []
    for p, f in resultado:
        row = {}
        for field in fields:
            row[field] = get_value(p, f, field)
        preview_data.append(row)
    return jsonify({'preview': preview_data})

def _build_query(turma, aluno, cidade, comprou_foto):
    query = db.session.query(Parente, Formando).join(Formando, Parente.formando_id == Formando.id)
    if turma and turma != 'TODAS':
        query = query.filter(Formando.turma == turma)
    if aluno and aluno != 'TODOS':
        query = query.filter(Formando.aluno == aluno)
    if cidade and cidade != 'TODAS':
        query = query.filter(Parente.cidade == cidade)
    if comprou_foto and comprou_foto != 'Todas':
        if comprou_foto == 'Sim':
            query = query.filter(Parente.comprou_foto.is_(True))
        elif comprou_foto == 'Não':
            query = query.filter(Parente.comprou_foto.is_(False))
    return query

def gerar_relatorio(resultado, export_type, fields, file_name):
    if export_type == 'excel':
        return gerar_excel(resultado, fields, file_name)
    else:
        return gerar_pdf(resultado, fields, file_name)

def gerar_excel(resultado, fields, file_name):
    dados = []
    for p, f in resultado:
        linha = {}
        for field in fields:
            linha[field] = get_value(p, f, field)
        dados.append(linha)
    df = pd.DataFrame(dados)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    output.seek(0)
    filename = file_name if file_name else "relatorio"
    return Response(output.read(),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={"Content-Disposition": f"attachment;filename={filename}.xlsx"})

def header_footer(canvas, doc):
    canvas.saveState()
    width, height = letter
    # Cabeçalho
    canvas.setFont('Helvetica-Bold', 10)
    header_text = "Relatório - Formaturas App"
    canvas.drawCentredString(width / 2.0, height - 30, header_text)
    # Rodapé: data/hora e número da página
    canvas.setFont('Helvetica', 8)
    generation_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    footer_text = f"Data de geração: {generation_date}"
    canvas.drawString(30, 30, footer_text)
    page_number_text = f"Página {canvas.getPageNumber()}"
    canvas.drawRightString(width - 30, 30, page_number_text)
    canvas.restoreState()

def gerar_pdf(resultado, fields, file_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título do relatório
    elements.append(Paragraph("Relatório", styles['Title']))
    elements.append(Spacer(1, 12))

    # Monta os dados da tabela (cabeçalho + linhas)
    data = [fields]  # Cabeçalho da tabela
    for p, f in resultado:
        row = []
        for field in fields:
            row.append(get_value(p, f, field))
        data.append(row)

    # Cria a tabela e define o estilo
    table = Table(data, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#202020')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Constrói o PDF com header e rodapé em cada página
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    pdf = buffer.getvalue()
    buffer.close()

    filename = file_name if file_name else "relatorio"
    return Response(pdf, mimetype='application/pdf',
                    headers={"Content-Disposition": f"attachment;filename={filename}.pdf"})

def get_value(p, f, field):
    if field == 'turma':
        return f.turma
    elif field == 'aluno':
        return f.aluno
    elif field == 'parente':
        return p.nome
    elif field == 'cidade':
        return p.cidade
    elif field == 'telefone':
        return p.telefone
    elif field == 'comprou_foto':
        return 'Sim' if p.comprou_foto else 'Não'
    elif field == 'grau':
        return p.grau
    else:
        return ''
