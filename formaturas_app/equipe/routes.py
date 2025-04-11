from flask import Blueprint, render_template
from flask_login import login_required
from formaturas_app.models import Usuario  # ou use o alias User, conforme sua preferência

equipe_bp = Blueprint('equipe', __name__, template_folder='templates', static_folder='static')

@equipe_bp.route('/')
@login_required
def index():
    # Busca todos os usuários cadastrados
    users = Usuario.query.all()
    # Passa o active_page para o template
    return render_template('equipe/index.html', users=users, active_page='equipe')
