import csv
import io
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case
from formaturas_app import db
from formaturas_app.models import Formando, Parente

turmas_bp = Blueprint('turmas', __name__)

@turmas_bp.route('/')
@login_required
def index():
    db.session.expire_all()
    
    # Consulta para obter dados consolidados por turma.
    # Atenção: O count dos alunos usa DISTINCT para evitar duplicação gerada por outerjoin com Parente.
    turmas_data = db.session.query(
        Formando.turma,
        func.count(func.distinct(Formando.id)).label('alunos_count'),
        func.count(Parente.id).label('parentes_count'),
        func.coalesce(func.sum(case((Parente.comprou_foto, 1), else_=0)), 0).label('fotos_compradas_count')
    ).outerjoin(Parente, Parente.formando_id == Formando.id) \
     .group_by(Formando.turma) \
     .order_by(Formando.turma.asc()).all()

    # Totais globais – note que agora fazemos JOIN para excluir possíveis órfãos
    total_turmas  = len(turmas_data)
    total_alunos  = db.session.query(func.count(Formando.id)).scalar() or 0
    total_parentes = db.session.query(func.count(Parente.id))\
                      .join(Formando).scalar() or 0
    total_fotos   = db.session.query(
        func.coalesce(func.sum(case((Parente.comprou_foto, 1), else_=0)), 0)
    ).join(Formando).scalar() or 0

    return render_template('turmas/index.html',
                           turmas=turmas_data,
                           total_turmas=total_turmas,
                           total_alunos=total_alunos,
                           total_parentes=total_parentes,
                           total_fotos_compradas=total_fotos,
                           active_page='turmas')

@turmas_bp.route('/nova_turma', methods=['GET', 'POST'])
@login_required
def nova_turma():
    db.session.expire_all()
    
    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado!', 'danger')
            return redirect(url_for('turmas.nova_turma', active_page='turmas'))

        arquivo = request.files['arquivo']
        nome_arquivo = secure_filename(arquivo.filename).lower()
        exts_validas = ('.csv', '.xls', '.xlsx')
        if not any(nome_arquivo.endswith(ext) for ext in exts_validas):
            flash('Formato inválido! Envie CSV, XLS ou XLSX.', 'danger')
            return redirect(url_for('turmas.nova_turma', active_page='turmas'))

        if nome_arquivo.endswith('.csv'):
            conteudo = arquivo.read().decode('utf-8', errors='replace')
            linhas = conteudo.splitlines()
            if not linhas:
                flash('Arquivo CSV vazio!', 'danger')
                return redirect(url_for('turmas.nova_turma', active_page='turmas'))
            _import_csv(linhas)
            return redirect(url_for('turmas.index', active_page='turmas'))
        else:
            conteudo_bin = arquivo.read()
            try:
                df = pd.read_excel(io.BytesIO(conteudo_bin))
            except Exception as e:
                flash(f'Erro ao ler planilha: {e}', 'danger')
                return redirect(url_for('turmas.nova_turma', active_page='turmas'))

            df.columns = df.columns.str.strip().str.lower()
            if 'turma' not in df.columns or 'aluno' not in df.columns:
                flash('Planilha deve ter colunas "Turma" e "Aluno".', 'danger')
                return redirect(url_for('turmas.nova_turma', active_page='turmas'))

            contador = 0
            for _, row in df.iterrows():
                t = str(row['turma']).strip()
                a = str(row['aluno']).strip()
                if t and a:
                    f = Formando(turma=t, aluno=a)
                    db.session.add(f)
                    contador += 1
            db.session.commit()
            flash(f'Importação Excel ok! {contador} registros inseridos.', 'success')
            return redirect(url_for('turmas.index', active_page='turmas'))
    return render_template('turmas/importar.html', active_page='turmas')

def _import_csv(linhas):
    reader = csv.reader(linhas)
    header = next(reader, None)
    if not header:
        flash('Não foi possível ler o cabeçalho do CSV!', 'danger')
        return

    header_norm = [col.strip().lower() for col in header]
    if 'turma' not in header_norm or 'aluno' not in header_norm:
        flash('CSV deve ter colunas "Turma" e "Aluno".', 'danger')
        return

    idx_turma = header_norm.index('turma')
    idx_aluno = header_norm.index('aluno')
    contador = 0
    for row in reader:
        if len(row) <= max(idx_turma, idx_aluno):
            continue
        t = row[idx_turma].strip()
        a = row[idx_aluno].strip()
        if t and a:
            f = Formando(turma=t, aluno=a)
            db.session.add(f)
            contador += 1
    db.session.commit()
    flash(f'Importação CSV ok! {contador} registros inseridos.', 'success')

@turmas_bp.route('/editar_turma/<string:turma>', methods=['GET', 'POST'])
@login_required
def editar_turma(turma):
    db.session.expire_all()
    
    if request.method == 'POST':
        nova_turma = request.form.get('nova_turma')
        if not nova_turma:
            flash('Informe o novo nome da Turma.', 'danger')
            return redirect(url_for('turmas.editar_turma', turma=turma, active_page='turmas'))
        Formando.query.filter_by(turma=turma).update({Formando.turma: nova_turma})
        db.session.commit()
        flash('Turma renomeada!', 'success')
        return redirect(url_for('turmas.editar_turma', turma=nova_turma, active_page='turmas'))

    order = request.args.get('order', 'asc')
    if order == 'desc':
        alunos = Formando.query.filter_by(turma=turma).order_by(Formando.aluno.desc()).all()
    else:
        alunos = Formando.query.filter_by(turma=turma).order_by(Formando.aluno.asc()).all()
    
    return render_template('turmas/editar_turma.html',
                           turma_atual=turma,
                           alunos=alunos,
                           order=order,
                           active_page='turmas')

@turmas_bp.route('/excluir_aluno/<int:id>')
@login_required
def excluir_aluno(id):
    db.session.expire_all()
    aluno = Formando.query.get_or_404(id)
    old_turma = aluno.turma
    db.session.delete(aluno)
    db.session.commit()
    flash('Aluno excluído da Turma!', 'success')
    return redirect(url_for('turmas.editar_turma', turma=old_turma, active_page='turmas'))

@turmas_bp.route('/adicionar_aluno/<string:turma>', methods=['POST'])
@login_required
def adicionar_aluno(turma):
    db.session.expire_all()
    novo_aluno = request.form.get('aluno')
    if not novo_aluno:
        flash('Nome do Aluno é obrigatório.', 'danger')
        return redirect(url_for('turmas.editar_turma', turma=turma, active_page='turmas'))
    f = Formando(turma=turma, aluno=novo_aluno)
    db.session.add(f)
    db.session.commit()
    flash('Aluno adicionado!', 'success')
    return redirect(url_for('turmas.editar_turma', turma=turma, active_page='turmas'))

@turmas_bp.route('/excluir_turma/<string:turma>')
@login_required
def excluir_turma(turma):
    db.session.expire_all()
    Formando.query.filter_by(turma=turma).delete()
    db.session.commit()
    flash('Turma excluída!', 'success')
    return redirect(url_for('turmas.index', active_page='turmas'))

# --- Endpoints para gerenciamento de Parentes ---

@turmas_bp.route('/listar_parents/<int:formando_id>')
@login_required
def listar_parents(formando_id):
    import datetime  # para usar datetime.date
    db.session.expire_all()
    parentes = Parente.query.filter_by(formando_id=formando_id).all()
    data = []
    for p in parentes:
        if p.data_nascimento and isinstance(p.data_nascimento, datetime.date):
            data_nasc = p.data_nascimento.isoformat()
        else:
            data_nasc = ''
        data.append({
            'id': p.id,
            'nome': p.nome,
            'grau': p.grau,
            'cidade': p.cidade,
            'profissao': p.profissao or '',
            'data_nascimento': data_nasc,
            'telefone': p.telefone,
            'comprou_foto': p.comprou_foto
        })
    return jsonify(data)

@turmas_bp.route('/criar_parente', methods=['POST'])
@login_required
def criar_parente():
    db.session.expire_all()
    if current_user.papel.value not in ['ADM', 'EDITOR']:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    data = request.get_json() or {}
    fid = data.get('formando_id')
    if not fid:
        return jsonify({'success': False, 'message': 'Faltou ID do Aluno'}), 400
    p = Parente(
        formando_id=fid,
        nome=data.get('nome', 'Sem nome'),
        grau=data.get('grau', ''),
        cidade=data.get('cidade', ''),
        profissao=data.get('profissao', ''),
        data_nascimento=data.get('data_nascimento', ''),
        telefone=data.get('telefone', '-'),
        comprou_foto=data.get('comprou_foto', False)
    )
    db.session.add(p)
    db.session.commit()
    return listar_parents(fid)

@turmas_bp.route('/editar_parente/<int:parente_id>', methods=['POST'])
@login_required
def editar_parente(parente_id):
    db.session.expire_all()
    if current_user.papel.value not in ['ADM', 'EDITOR']:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    data = request.get_json() or {}
    p = Parente.query.get_or_404(parente_id)
    p.nome = data.get('nome', p.nome)
    p.grau = data.get('grau', p.grau)
    p.cidade = data.get('cidade', p.cidade)
    p.profissao = data.get('profissao', p.profissao)
    p.data_nascimento = data.get('data_nascimento', p.data_nascimento)
    p.telefone = data.get('telefone', p.telefone)
    p.comprou_foto = data.get('comprou_foto', p.comprou_foto)
    db.session.commit()
    return listar_parents(p.formando_id)

@turmas_bp.route('/excluir_parente/<int:parente_id>', methods=['DELETE'])
@login_required
def excluir_parente(parente_id):
    db.session.expire_all()
    if current_user.papel.value not in ['ADM', 'EDITOR']:
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    p = Parente.query.get_or_404(parente_id)
    fid = p.formando_id
    db.session.delete(p)
    db.session.commit()
    return listar_parents(fid)
