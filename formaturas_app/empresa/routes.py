from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from formaturas_app.models import Empresa, Usuario, PapelEnum, StatusEnum
from formaturas_app import db
from formaturas_app.utils.loggers import log_access, log_crud, log_audit
import datetime

empresa_bp = Blueprint('empresa', __name__)

@empresa_bp.route('/')
@login_required
def index():
    # Só o master super-admin global
    if current_user.email.lower() != "adminbruno@diretiva.com":
        log_audit("Tentativa de acesso não autorizado à lista de empresas")
        flash("Acesso não autorizado!", "danger")
        return redirect(url_for("auth.login"))

    log_access("Acesso à lista de empresas")
    empresas = Empresa.query.order_by(Empresa.nome).all()
    companies_data = []
    for emp in empresas:
        admin = Usuario.query.filter_by(
            empresa_id=emp.id, papel=PapelEnum.ADM
        ).first()
        companies_data.append({
            'id':          emp.id,
            'nome':        emp.nome,
            'status':      emp.status.value,
            'admin_email': admin.email if admin else "N/A"
        })

    return render_template('empresa/index.html', empresas=companies_data)


@empresa_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_empresa():
    if current_user.email.lower() != "adminbruno@diretiva.com":
        log_audit("Tentativa de acesso não autorizado ao cadastro de empresas")
        flash("Acesso não autorizado!", "danger")
        return redirect(url_for("auth.login"))

    if request.method == 'POST':
        nome_empresa           = request.form.get('nome_empresa', '').strip()
        email_admin            = request.form.get('email_admin', '').lower().strip()
        senha_admin            = request.form.get('senha_admin', '').strip()
        max_usuarios_s         = request.form.get('max_usuarios', '').strip()
        assinatura_ativa_ate_s = request.form.get('assinatura_ativa_ate', '').strip()
        status_str             = request.form.get('status', '').strip()

        if not nome_empresa or not email_admin or not senha_admin:
            flash("Preencha os campos obrigatórios!", "danger")
            return redirect(url_for('empresa.cadastrar_empresa'))

        try:
            max_usuarios = int(max_usuarios_s) if max_usuarios_s else 5
        except ValueError:
            max_usuarios = 5

        try:
            if assinatura_ativa_ate_s:
                assinatura_ativa_ate = datetime.datetime.strptime(
                    assinatura_ativa_ate_s, '%Y-%m-%d'
                ).date()
            else:
                assinatura_ativa_ate = datetime.date.today() + datetime.timedelta(days=30)
        except ValueError:
            assinatura_ativa_ate = datetime.date.today() + datetime.timedelta(days=30)

        if Empresa.query.filter_by(nome=nome_empresa).first():
            flash("Já existe uma empresa com esse nome.", "danger")
            return redirect(url_for('empresa.cadastrar_empresa'))

        nova_empresa = Empresa(
            nome=nome_empresa,
            assinatura_ativa_ate=assinatura_ativa_ate,
            max_usuarios=max_usuarios,
            status=StatusEnum(status_str) if status_str else StatusEnum.ATIVA
        )
        db.session.add(nova_empresa)
        db.session.commit()
        log_crud("criou", f"empresa '{nome_empresa}'")

        # cria usuário ADM vinculado
        admin = Usuario(
            email=email_admin,
            nome="Administrador",
            papel=PapelEnum.ADM,
            empresa_id=nova_empresa.id
        )
        admin.set_password(senha_admin)
        db.session.add(admin)
        db.session.commit()
        log_crud(
            "criou",
            f"usuário ADM '{email_admin}' para empresa '{nome_empresa}'"
        )

        flash("Empresa e usuário administrador cadastrados com sucesso!", "success")
        return redirect(url_for('empresa.index'))

    return render_template('empresa/register.html')


@empresa_bp.route('/editar_empresa/<int:empresa_id>', methods=['POST'])
@login_required
def editar_empresa(empresa_id):
    if current_user.email.lower() != "adminbruno@diretiva.com":
        log_audit("Tentativa de edição não autorizada de empresa")
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403

    data = request.get_json() or {}
    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404

    if empresa.nome == "Administração do Sistema":
        return jsonify({
            'success': False,
            'message': 'Não é permitido alterar a administração do sistema.'
        }), 403

    old_nome = empresa.nome
    empresa.nome = data.get('nome', old_nome).strip() or old_nome
    status_str = data.get('status')
    if status_str:
        try:
            empresa.status = StatusEnum(status_str)
        except ValueError:
            pass

    db.session.commit()
    log_crud(
        "editou",
        f"empresa (ID:{empresa.id}) de '{old_nome}' para "
        f"'{empresa.nome}', status='{empresa.status.value}'"
    )
    return jsonify({'success': True})


@empresa_bp.route('/excluir_empresa/<int:empresa_id>', methods=['DELETE'])
@login_required
def excluir_empresa(empresa_id):
    # Só super-admin global
    if current_user.email.lower() != "adminbruno@diretiva.com":
        log_audit("Tentativa de exclusão não autorizada de empresa")
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403

    empresa = Empresa.query.get(empresa_id)
    if not empresa:
        return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404

    # 🚫 Não deixa excluir a própria empresa do super-admin
    if empresa.id == current_user.empresa_id:
        return jsonify({
            'success': False,
            'message': 'Não é permitido excluir sua própria empresa.'
        }), 403

    nome = empresa.nome
    db.session.delete(empresa)
    db.session.commit()
    log_crud("excluiu", f"empresa (ID:{empresa_id}) '{nome}'")
    return jsonify({'success': True})


@empresa_bp.route('/api/empresas', methods=['GET'])
@login_required
def api_empresas():
    if current_user.email.lower() != "adminbruno@diretiva.com":
        log_audit("Tentativa de acesso não autorizado ao endpoint /api/empresas")
        return jsonify({'success': False, 'message': 'Acesso não autorizado'}), 403

    log_access("Listagem de empresas via API")
    empresas = Empresa.query.order_by(Empresa.nome).all()
    empresas_data = []
    for emp in empresas:
        admin = Usuario.query.filter_by(
            empresa_id=emp.id, papel=PapelEnum.ADM
        ).first()
        empresas_data.append({
            'id':          emp.id,
            'nome':        emp.nome,
            'status':      emp.status.value,
            'admin_email': admin.email if admin else "N/A"
        })
    return jsonify({'empresas': empresas_data})
