import csv
from flask import Blueprint, render_template, request, Response, jsonify, flash
from flask_login import login_required, current_user
from formaturas_app import db
from formaturas_app.models import Parente, Formando
from formaturas_app.decorators import exige_turma  # <-- import do decorator
import pandas as pd
from io import BytesIO
from datetime import datetime

# ReportLab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/filtrar', methods=['GET', 'POST'])
@login_required
@exige_turma(
    active_page='relatorios',
    title='Sem turmas cadastradas',
    message='Para gerar relatórios, adicione ao menos uma turma.'
)
def filtrar():
    # Só ADM pode acessar
    if current_user.papel.value != 'ADM':
        return "Acesso negado!", 403

    turmas_opcoes = db.session.query(Formando.turma).distinct().all()
    alunos_opcoes = db.session.query(Formando.aluno).distinct().all()
    cidades_opcoes = db.session.query(Parente.cidade).distinct().all()
    preview_fields = []

    if request.method == 'POST':
        turma        = request.form.get('turma')
        aluno        = request.form.get('aluno')
        cidade       = request.form.get('cidade')
        comprou_foto = request.form.get('comprou_foto')
        export_type  = request.form.get('export_type')
        fields       = request.form.getlist('fields')
        preview_fields = fields
        file_name    = request.form.get('file_name')

        query    = _build_query(turma, aluno, cidade, comprou_foto)
        resultado = query.all()

        if export_type in ['excel', 'pdf']:
            return gerar_relatorio(resultado, export_type, fields, file_name)
        else:
            flash("Selecione um tipo de exportação.", "danger")

    return render_template(
        'relatorios/filtrar.html',
        turmas=turmas_opcoes,
        alunos=alunos_opcoes,
        cidades=cidades_opcoes,
        preview_fields=preview_fields,
        active_page='relatorios'
    )

@relatorios_bp.route('/listar_alunos/<turma>')
@login_required
def listar_alunos(turma):
    if turma == 'TODAS':
        formandos = Formando.query.all()
    else:
        formandos = Formando.query.filter_by(turma=turma).all()
    data = [{'aluno': f.aluno} for f in formandos]
    return jsonify(data)

@relatorios_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    # Só ADM pode acessar
    if current_user.papel.value != 'ADM':
        return jsonify({'error': 'Acesso negado.'}), 403

    data = request.json or {}
    turma        = data.get('turma')
    aluno        = data.get('aluno')
    cidade       = data.get('cidade')
    comprou_foto = data.get('comprou_foto')
    fields       = data.get('fields', [])

    query    = _build_query(turma, aluno, cidade, comprou_foto)
    resultado = query.limit(3).all()

    preview_data = []
    for p, f in resultado:
        row = { field: get_value(p, f, field) for field in fields }
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
        else:
            query = query.filter(Parente.comprou_foto.is_(False))
    return query

def gerar_relatorio(resultado, export_type, fields, file_name):
    if export_type == 'excel':
        return gerar_excel(resultado, fields, file_name)
    return gerar_pdf(resultado, fields, file_name)

def gerar_excel(resultado, fields, file_name):
    dados = []
    for p, f in resultado:
        dados.append({ field: get_value(p, f, field) for field in fields })
    df = pd.DataFrame(dados)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório')
    output.seek(0)
    nome = file_name or "relatorio"
    return Response(
        output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={nome}.xlsx"}
    )

def header_footer(canvas, doc):
    canvas.saveState()
    width, height = letter
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawCentredString(width / 2.0, height - 30, "Relatório - Formaturas App")
    canvas.setFont('Helvetica', 8)
    geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    canvas.drawString(30, 30, f"Data de geração: {geracao}")
    canvas.drawRightString(width - 30, 30, f"Página {canvas.getPageNumber()}")
    canvas.restoreState()

def gerar_pdf(resultado, fields, file_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = [ Paragraph("Relatório", getSampleStyleSheet()['Title']), Spacer(1, 12) ]
    data = [fields] + [
        [ get_value(p, f, field) for field in fields ]
        for p, f in resultado
    ]
    table = Table(data, hAlign='CENTER')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#202020')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('GRID',        (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    nome = file_name or "relatorio"
    return Response(
        pdf,
        mimetype='application/pdf',
        headers={"Content-Disposition": f"attachment;filename={nome}.pdf"}
    )

def get_value(p, f, field):
    if field == 'turma':
        return f.turma
    if field == 'aluno':
        return f.aluno
    if field == 'parente':
        return p.nome
    if field == 'cidade':
        return p.cidade
    if field == 'telefone':
        return p.telefone
    if field == 'comprou_foto':
        return 'Sim' if p.comprou_foto else 'Não'
    if field == 'grau':
        return p.grau
    return ''
