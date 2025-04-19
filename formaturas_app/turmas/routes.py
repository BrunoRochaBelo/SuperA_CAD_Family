import csv
import io
import datetime
import pandas as pd
from io import BytesIO
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import func, case

from formaturas_app import db
from formaturas_app.models import Formando, Parente
from formaturas_app.utils.loggers import logger_access, logger_crud
from formaturas_app.decorators import exige_turma

turmas_bp = Blueprint('turmas', __name__)

@turmas_bp.route('/')
@login_required
@exige_turma(
    active_page='turmas',
    title='Sem turmas cadastradas',
    message='Para visualizar turmas, adicione ao menos uma turma.'
)
def index():
    db.session.expire_all()
    logger_access.info(f"Acesso à página de turmas - usuário: {current_user.email}")

    # Dados consolidados por turma
    turmas_data = (
        db.session
          .query(
              Formando.turma,
              func.count(func.distinct(Formando.id)).label('alunos_count'),
              func.count(Parente.id).label('parentes_count'),
              func.coalesce(
                func.sum(case((Parente.comprou_foto, 1), else_=0)), 0
              ).label('fotos_compradas_count')
          )
          .outerjoin(Parente, Parente.formando_id == Formando.id)
          .group_by(Formando.turma)
          .order_by(Formando.turma.asc())
          .all()
    )

    total_turmas   = len(turmas_data)
    total_alunos   = db.session.query(func.count(Formando.id)).scalar() or 0
    total_parentes = (
        db.session.query(func.count(Parente.id))
                  .join(Formando)
                  .scalar() or 0
    )
    total_fotos = (
        db.session
          .query(func.coalesce(
              func.sum(case((Parente.comprou_foto, 1), else_=0)), 0
          ))
          .join(Formando)
          .scalar() or 0
    )

    return render_template(
        'turmas/index.html',
        turmas=turmas_data,
        total_turmas=total_turmas,
        total_alunos=total_alunos,
        total_parentes=total_parentes,
        total_fotos_compradas=total_fotos,
        active_page='turmas'
    )


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

        # CSV
        if nome_arquivo.endswith('.csv'):
            conteudo = arquivo.read().decode('utf-8', errors='replace')
            linhas = conteudo.splitlines()
            if not linhas:
                flash('Arquivo CSV vazio!', 'danger')
                return redirect(url_for('turmas.nova_turma', active_page='turmas'))
            contador = _import_csv(linhas)
            logger_crud.info(
                f"Importação CSV: {contador} registros por {current_user.email}"
            )
            return redirect(url_for('turmas.index', active_page='turmas'))

        # Excel
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
                db.session.add(Formando(turma=t, aluno=a))
                contador += 1
        db.session.commit()
        flash(f'Importação Excel ok! {contador} registros inseridos.', 'success')
        logger_crud.info(
            f"Importação Excel: {contador} registros por {current_user.email}"
        )
        return redirect(url_for('turmas.index', active_page='turmas'))

    return render_template('turmas/importar.html', active_page='turmas')


def _import_csv(linhas):
    reader = csv.reader(linhas)
    header = next(reader, None)
    if not header:
        flash('Não foi possível ler o cabeçalho do CSV!', 'danger')
        return 0

    cols = [c.strip().lower() for c in header]
    if 'turma' not in cols or 'aluno' not in cols:
        flash('CSV deve ter colunas "Turma" e "Aluno".', 'danger')
        return 0

    idx_t, idx_a = cols.index('turma'), cols.index('aluno')
    contador = 0
    for row in reader:
        if len(row) <= max(idx_t, idx_a):
            continue
        t, a = row[idx_t].strip(), row[idx_a].strip()
        if t and a:
            db.session.add(Formando(turma=t, aluno=a))
            contador += 1
    db.session.commit()
    flash(f'Importação CSV ok! {contador} registros inseridos.', 'success')
    return contador


@turmas_bp.route('/editar_turma/<string:turma>', methods=['GET', 'POST'])
@login_required
def editar_turma(turma):
    db.session.expire_all()
    if request.method == 'POST':
        nova = request.form.get('nova_turma')
        if not nova:
            flash('Informe o novo nome da Turma.', 'danger')
            return redirect(
                url_for('turmas.editar_turma', turma=turma, active_page='turmas')
            )

        Formando.query.filter_by(turma=turma).update({Formando.turma: nova})
        db.session.commit()
        logger_crud.info(
            f"Turma renomeada: '{turma}' → '{nova}' por {current_user.email}"
        )
        flash('Turma renomeada!', 'success')
        return redirect(
            url_for('turmas.editar_turma', turma=nova, active_page='turmas')
        )

    order = request.args.get('order', 'asc')
    alunos = Formando.query.filter_by(turma=turma)
    alunos = alunos.order_by(
        Formando.aluno.desc() if order=='desc' else Formando.aluno.asc()
    ).all()

    return render_template(
        'turmas/editar_turma.html',
        turma_atual=turma,
        alunos=alunos,
        order=order,
        active_page='turmas'
    )


@turmas_bp.route('/excluir_aluno/<int:id>')
@login_required
def excluir_aluno(id):
    db.session.expire_all()
    f = Formando.query.get_or_404(id)
    old = f.turma
    db.session.delete(f)
    db.session.commit()
    logger_crud.info(
        f"Aluno excluído: '{f.aluno}' da turma '{old}' por {current_user.email}"
    )
    flash('Aluno excluído da Turma!', 'success')
    return redirect(
        url_for('turmas.editar_turma', turma=old, active_page='turmas')
    )


@turmas_bp.route('/adicionar_aluno/<string:turma>', methods=['POST'])
@login_required
def adicionar_aluno(turma):
    db.session.expire_all()
    novo = request.form.get('aluno')
    if not novo:
        flash('Nome do Aluno é obrigatório.', 'danger')
        return redirect(
            url_for('turmas.editar_turma', turma=turma, active_page='turmas')
        )
    db.session.add(Formando(turma=turma, aluno=novo))
    db.session.commit()
    logger_crud.info(
        f"Aluno adicionado: '{novo}' na turma '{turma}' por {current_user.email}"
    )
    flash('Aluno adicionado!', 'success')
    return redirect(
        url_for('turmas.editar_turma', turma=turma, active_page='turmas')
    )


@turmas_bp.route('/excluir_turma/<string:turma>')
@login_required
def excluir_turma(turma):
    db.session.expire_all()
    Formando.query.filter_by(turma=turma).delete()
    db.session.commit()
    logger_crud.warning(
        f"Turma excluída: '{turma}' por {current_user.email}"
    )
    flash('Turma excluída!', 'success')
    return redirect(url_for('turmas.index', active_page='turmas'))


# --- Endpoints para gerenciamento de Parentes ---

@turmas_bp.route('/listar_parents/<int:formando_id>')
@login_required
def listar_parents(formando_id):
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
    logger_crud.info(f"Parente criado: '{p.nome}' (grau: {p.grau}) para formando ID {fid} por {current_user.email}")

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
    logger_crud.info(f"Parente editado: '{p.nome}' (ID: {parente_id}) por {current_user.email}")

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
    logger_crud.warning(f"Parente excluído: '{p.nome}' (ID: {parente_id}) por {current_user.email}")

    return listar_parents(fid)
