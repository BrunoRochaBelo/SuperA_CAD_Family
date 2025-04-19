from flask import Blueprint, render_template, request
from flask_login import login_required
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
    # Expira a sessão para garantir dados atualizados
    db.session.expire_all()
    
    # Captura de filtros opcionais via query string
    turma_filter = request.args.get('turma')
    cidade_filter = request.args.get('cidade')

    # Consulta para Alunos (filtrados se informado turma)
    alunos_query = Formando.query
    if turma_filter:
        alunos_query = alunos_query.filter(Formando.turma == turma_filter)
    total_alunos = alunos_query.count()

    # Consulta de Turmas distintas (filtradas se houver)
    turmas_query = db.session.query(Formando.turma).distinct()
    if turma_filter:
        turmas_query = turmas_query.filter(Formando.turma == turma_filter)
    total_turmas = turmas_query.count()

    # Consulta para Parentes (filtra por turma e cidade, se informado)
    parentes_query = Parente.query.join(Formando, Parente.formando_id == Formando.id)
    if turma_filter:
        parentes_query = parentes_query.filter(Formando.turma == turma_filter)
    if cidade_filter:
        parentes_query = parentes_query.filter(Parente.cidade == cidade_filter)
    total_parentes = parentes_query.count()

    # Fotos compradas (usando o mesmo parentes_query)
    fotos_compradas = parentes_query.filter(Parente.comprou_foto == True).count()
    nao_compraram = total_parentes - fotos_compradas

    # Indicador: Média de Parentes por Aluno
    media_parentes = (total_parentes / total_alunos) if total_alunos else 0

    # Indicador: Percentual de Alunos com pelo menos 1 parente que comprou a foto
    alunos_com_foto = db.session.query(Formando).join(Parente)\
                          .filter(Parente.comprou_foto == True)\
                          .distinct().count()
    perc_alunos_foto = (alunos_com_foto / total_alunos * 100) if total_alunos else 0

    # Gráfico Agrupado: Alunos vs. Alunos com Foto
    if turma_filter:
        alunos_por_turma_q = db.session.query(Formando.turma, func.count(Formando.id))\
                              .filter(Formando.turma == turma_filter)\
                              .group_by(Formando.turma)
        alunos_por_turma = alunos_por_turma_q.all()
        turmas_labels = [turma for turma, count in alunos_por_turma]
        total_alunos_per_turma = [count for turma, count in alunos_por_turma]

        alunos_com_foto_por_turma_q = db.session.query(Formando.turma, func.count(Formando.id))\
            .join(Parente).filter(Formando.turma == turma_filter, Parente.comprou_foto == True)\
            .group_by(Formando.turma)
        alunos_com_foto_por_turma = alunos_com_foto_por_turma_q.all()
        alunos_com_foto_dict = {turma: count for turma, count in alunos_com_foto_por_turma}
        alunos_com_foto_data = [alunos_com_foto_dict.get(turma, 0) for turma in turmas_labels]
    else:
        turmas_labels = ["Todas as Turmas"]
        total_alunos_per_turma = [total_alunos]
        alunos_com_foto_data = [alunos_com_foto]

    # Gráfico de Pizza: Distribuição de Parentes por Cidade
    pais_por_cidade_q = db.session.query(
        func.trim(func.lower(Parente.cidade)).label('cidade_norm'),
        func.count(Parente.id)
    ).join(Formando)
    if turma_filter:
        pais_por_cidade_q = pais_por_cidade_q.filter(Formando.turma == turma_filter)
    pais_por_cidade = pais_por_cidade_q.group_by('cidade_norm').all()
    cidades_labels = [
        (cidade.capitalize() if cidade else "Desconhecido")
        for cidade, _ in pais_por_cidade
    ]
    pais_counts = [count for _, count in pais_por_cidade]

    # Ranking de Turmas por Taxa de Conversão
    turmas = [t[0] for t in db.session.query(Formando.turma).distinct().all()]
    ranking_data = []
    for t in turmas:
        total = db.session.query(func.count(Formando.id))\
                   .filter(Formando.turma == t).scalar() or 0
        alunos_com_foto_t = db.session.query(Formando.id).join(Parente)\
                              .filter(Formando.turma == t, Parente.comprou_foto == True)\
                              .distinct().count()
        conversion_rate = (alunos_com_foto_t / total * 100) if total > 0 else 0
        ranking_data.append({
            'turma': t,
            'total_alunos': total,
            'alunos_com_foto': alunos_com_foto_t,
            'conversion_rate': conversion_rate
        })
    ranking_data = sorted(ranking_data, key=lambda x: x['conversion_rate'], reverse=True)

    # Opções para os filtros na dashboard
    all_turmas = [t[0] for t in db.session.query(Formando.turma).distinct().all()]
    all_cidades = [c[0] for c in db.session.query(Parente.cidade).distinct().all()]

    # Dicionário de Indicadores
    stats = {
        'turmas': total_turmas,
        'alunos': total_alunos,
        'parentes': total_parentes,
        'compraram_foto': fotos_compradas,
        'nao_compraram': nao_compraram,
        'media_parentes': media_parentes,
        'perc_alunos_foto': perc_alunos_foto
    }

    # Dados para os gráficos
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
