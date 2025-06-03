from flask import Blueprint, render_template, request
from flask_login import login_required, current_user  # <<< import do current_user
from sqlalchemy import func
from formaturas_app.models import Formando, Parente
from formaturas_app import db
from formaturas_app.decorators import exige_turma

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=["GET"])
@login_required
@exige_turma(
    active_page='home',
    title='Sem turmas cadastradas',
    message='Para acessar o dashboard, adicione ao menos uma turma.'
)
def index():
    # Garante dados fresquinhos
    db.session.expire_all()
    
    # Filtros opcionais
    turma_filter = request.args.get('turma')
    cidade_filter = request.args.get('cidade')

    # — Total de Alunos (só da empresa atual)
    alunos_query = Formando.query.filter(Formando.empresa_id == current_user.empresa_id)
    if turma_filter:
        alunos_query = alunos_query.filter(Formando.turma == turma_filter)
    total_alunos = alunos_query.count()

    # — Total de Turmas distintas
    turmas_query = (
        db.session.query(Formando.turma)
        .filter(Formando.empresa_id == current_user.empresa_id)
        .distinct()
    )
    if turma_filter:
        turmas_query = turmas_query.filter(Formando.turma == turma_filter)
    total_turmas = turmas_query.count()

    # — Parentes (filtra por turma, cidade e empresa)
    parentes_query = (
        Parente.query
        .join(Formando, Parente.formando_id == Formando.id)
        .filter(Formando.empresa_id == current_user.empresa_id)
    )
    if turma_filter:
        parentes_query = parentes_query.filter(Formando.turma == turma_filter)
    if cidade_filter:
        parentes_query = parentes_query.filter(Parente.cidade == cidade_filter)
    total_parentes = parentes_query.count()

    # — Fotos compradas
    fotos_compradas = parentes_query.filter(Parente.comprou_foto.is_(True)).count()
    nao_compraram = total_parentes - fotos_compradas

    # — Média de parentes por aluno
    media_parentes = (total_parentes / total_alunos) if total_alunos else 0

    # — % de alunos com pelo menos 1 foto
    alunos_com_foto = (
        db.session.query(Formando)
        .join(Parente)
        .filter(
            Formando.empresa_id == current_user.empresa_id,
            Parente.comprou_foto.is_(True)
        )
        .distinct()
        .count()
    )
    perc_alunos_foto = (alunos_com_foto / total_alunos * 100) if total_alunos else 0

    # — Gráfico: Alunos vs Alunos com Foto
    if turma_filter:
        alunos_por_turma = (
            db.session.query(Formando.turma, func.count(Formando.id))
            .filter(
                Formando.empresa_id == current_user.empresa_id,
                Formando.turma == turma_filter
            )
            .group_by(Formando.turma)
            .all()
        )
    else:
        alunos_por_turma = [(turma_filter or "Todas as Turmas", total_alunos)]

    turmas_labels = [t for t, _ in alunos_por_turma]
    total_alunos_per_turma = [cnt for _, cnt in alunos_por_turma]

    alunos_com_foto_por_turma = (
        db.session.query(Formando.turma, func.count(Formando.id))
        .join(Parente)
        .filter(
            Formando.empresa_id == current_user.empresa_id,
            Parente.comprou_foto.is_(True),
            Formando.turma == (turma_filter or Formando.turma)
        )
        .group_by(Formando.turma)
        .all()
    )
    foto_dict = {t: cnt for t, cnt in alunos_com_foto_por_turma}
    if turma_filter:
        alunos_com_foto_data = [foto_dict.get(t, 0) for t in turmas_labels]
    else:
        total_fotos = sum(foto_dict.values())
        alunos_com_foto_data = [total_fotos]

    # — Pizza: Parentes por cidade
    pais_por_cidade = (
        db.session.query(
            func.trim(func.lower(Parente.cidade)).label('cidade_norm'),
            func.count(Parente.id)
        )
        .join(Formando)
        .filter(Formando.empresa_id == current_user.empresa_id)
    )
    if turma_filter:
        pais_por_cidade = pais_por_cidade.filter(Formando.turma == turma_filter)
    pais_por_cidade = pais_por_cidade.group_by('cidade_norm').all()

    cidades_labels = [
        (cidade.capitalize() if cidade else "Desconhecido")
        for cidade, _ in pais_por_cidade
    ]
    pais_counts = [cnt for _, cnt in pais_por_cidade]

    # — Ranking de Turmas por Taxa de Conversão
    turmas = [
        t[0] for t in (
            db.session.query(Formando.turma)
            .filter(Formando.empresa_id == current_user.empresa_id)
            .distinct()
            .all()
        )
    ]
    ranking_data = []
    for t in turmas:
        total = (
            db.session.query(func.count(Formando.id))
            .filter(
                Formando.empresa_id == current_user.empresa_id,
                Formando.turma == t
            ).scalar() or 0
        )
        with_foto = (
            db.session.query(Formando.id)
            .join(Parente)
            .filter(
                Formando.empresa_id == current_user.empresa_id,
                Formando.turma == t,
                Parente.comprou_foto.is_(True)
            )
            .distinct()
            .count()
        )
        taxa = (with_foto / total * 100) if total else 0
        ranking_data.append({
            'turma': t,
            'total_alunos': total,
            'alunos_com_foto': with_foto,
            'conversion_rate': taxa
        })
    ranking_data.sort(key=lambda x: x['conversion_rate'], reverse=True)

    # — Opções de filtros (só da empresa)
    all_turmas = turmas
    all_cidades = [
        c[0] for c in (
            db.session.query(Parente.cidade)
            .join(Formando)
            .filter(Formando.empresa_id == current_user.empresa_id)
            .distinct()
            .all()
        )
    ]

    stats = {
        'turmas': total_turmas,
        'alunos': total_alunos,
        'parentes': total_parentes,
        'compraram_foto': fotos_compradas,
        'nao_compraram': nao_compraram,
        'media_parentes': media_parentes,
        'perc_alunos_foto': perc_alunos_foto
    }

    chart_data = {
        'alunos_turma': {
            'labels': turmas_labels,
            'total': total_alunos_per_turma,
            'com_foto': alunos_com_foto_data
        },
        'pais_cidade': {
            'labels': cidades_labels,
            'data': pais_counts
        }
    }

    return render_template(
        'home/dashboard.html',
        stats=stats,
        chart_data=chart_data,
        ranking=ranking_data,
        filtros={'turma': turma_filter, 'cidade': cidade_filter},
        all_turmas=all_turmas,
        all_cidades=all_cidades,
        active_page='home'
    )
