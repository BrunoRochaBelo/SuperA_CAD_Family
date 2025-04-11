# Formaturas App

Este é um sistema simples para gerenciamento de parentes de formandos, criado em **Flask** com uma **arquitetura monolítica modular**. A aplicação foi projetada usando **Blueprints** para cada domínio (auth, home, parentes, relatórios, dashboard), mantendo assim o código organizado e fácil de manter.

---

## 📂 Estrutura do Projeto

```text
meu_projeto/
├── formaturas_app/
│   ├── __init__.py        # Configuração principal da aplicação (create_app, DB, login_manager)
│   ├── models.py          # Definição das tabelas (Usuario, Formando, Parente)
│   ├── auth/              # Módulo de autenticação (login, logout)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── home/              # Módulo "Home": gerenciamento de turmas, importação de planilha
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── parentes/          # Módulo de cadastro de parentes
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── relatorios/        # Módulo de relatórios (filtros, geração CSV/Excel/PDF)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── dashboard/         # Módulo de dashboard (placeholder)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── static/            # Arquivos estáticos (CSS, JS, favicon, etc.)
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── chart.umd.js
│   │   └── favicon.ico
│   ├── templates/         # HTMLs usando Jinja2
│   │   ├── login_base.html  # Layout de login sem header
│   │   ├── base.html        # Layout principal com header fixo e container flutuante
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── home/
│   │   │   ├── index.html       # Lista turmas
│   │   │   ├── importar.html    # Importar planilha
│   │   │   └── editar_turma.html
│   │   ├── parentes/
│   │   │   └── cadastrar.html
│   │   ├── relatorios/
│   │   │   └── filtrar.html
│   │   └── dashboard/
│   │       └── index.html
│   ├── utils/            # Funções auxiliares (ex.: criar_usuarios_iniciais)
│   │   ├── __init__.py
│   │   └── criar_usuarios_iniciais.py
│   └── migrations/       # Para versionamento do banco (opcional, se usar Flask-Migrate)
├── run.py                # Ponto de entrada da aplicação
├── requirements.txt      # Lista de dependências
├── .env                  # Configurações de ambiente (SECRET_KEY, DB, etc.)
└── .gitignore
```

---

## 🏗️ Arquitetura e Design

- **Monolito Modular**: Embora seja um único projeto Flask, cada funcionalidade principal (auth, home, parentes, relatórios, dashboard) é separada em **Blueprints**, garantindo organização e separação de responsabilidades.
- **Models**: Centralizados em `models.py`, definindo as classes `Usuario`, `Formando` e `Parente`.
- **Padrões**:
  - **Blueprint Pattern**: cada módulo tem seu `routes.py`, registrando rotas específicas, mantendo o projeto escalável.
  - **MVC Simplificado**: o “model” fica em `models.py`, o “controller”/“routes” está nos Blueprints, e o “view” nos templates Jinja2.
  - **Flask-Login** para autenticação e controle de sessão.
  - **Jinja2** para renderização de templates.
- **UI/UX**:
  - **Header fixo** e **container flutuante** para o conteúdo principal, facilitando leitura e mantendo uma navegação coerente.
  - **Responsividade**: CSS com media queries, classes `.table-responsive`, `.container-floating` e `.btn` para melhor adaptação em telas menores.
  - **Feedbacks**: uso de mensagens flash (`alert-success`, `alert-danger`, etc.) para informar o usuário sobre ações bem-sucedidas ou erros.
  - **Pré-visualização** de relatórios (primeiras 5 linhas) antes de gerar o arquivo final.

---

## 📦 Módulos Principais

1. **auth**  
   - Gerencia login e logout (rotas `auth/login` e `auth/logout`).
   - Usa `Flask-Login` para manter sessão do usuário.
   - Define perfis de usuário (ADM, EDITOR, VISUALIZADOR).

2. **home**  
   - “Tela principal” da aplicação.
   - Lista Turmas (`Formando.turma`) e gerencia:
     - **Importar planilha** CSV/XLS/XLSX com colunas “Turma” e “Aluno”.
     - **Editar Turma** (renomear, adicionar/excluir Alunos).
     - **Excluir Turma** (remove todos os registros ligados àquela turma).

3. **parentes**  
   - Cadastro de Parentes por Aluno.
   - O usuário escolhe a Turma, filtra os Alunos daquela Turma e, em seguida, vê a lista de Parentes do Aluno selecionado.
   - Pode criar, editar e excluir Parentes via modal (requisições AJAX).

4. **relatorios**  
   - Filtra dados de Parentes e Alunos, com possibilidade de escolher **campos** (ex.: turma, aluno, cidade, etc.) e gerar:
     - **CSV**
     - **Excel** (usando `pandas` + `openpyxl`)
     - **PDF** (usando `pdfkit` + `wkhtmltopdf`)
   - **Pré-visualização**: mostra as 5 primeiras linhas do resultado antes de gerar o arquivo final.
   - Filtros de Turma, Aluno, Cidade, “Comprou Foto?” etc.

5. **dashboard**  
   - Placeholder para gráficos e KPIs futuros.
   - Exemplo com `chart.umd.js`.

---

## 🔧 Como rodar o projeto

### 1️⃣ Crie e ative um ambiente virtual

**Windows**:
```bash
python -m venv venv
.\venv\Scripts\activate
```
**Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Instale as dependências
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure o `.env`
No arquivo `.env`, você pode definir:
```
SECRET_KEY=chave-secreta-super-segura
DATABASE_URL=sqlite:///formaturas.db
```

### 4️⃣ Crie usuários iniciais (admin, editor, visualizador)
```bash
python -m formaturas_app.utils.criar_usuarios_iniciais
```

### 5️⃣ Rode a aplicação
```bash
python run.py
```

### 6️⃣ Acesse no navegador
```
http://127.0.0.1:5000/auth/login
```
- **admin** / senha: `1234` (ADM)  
- **editor** / senha: `1234` (EDITOR)  
- **visualizador** / senha: `1234` (VISUALIZADOR)

---

## 🏗️ Tecnologias e Padrões

- **Flask** + **Blueprints**  
- **Flask-Login** (autenticação e controle de sessão)  
- **Flask-SQLAlchemy** (ORM)  
- **Flask-Migrate** (migração de banco, se desejado)  
- **Jinja2** (templates)  
- **pdfkit** e **wkhtmltopdf** (geração de PDF)  
- **pandas** + **openpyxl** (exportação Excel)  
- **HTML/CSS** responsivo (layout fixo no topo + container flutuante)

---

## 📊 Funcionalidades

1. **Importar Turmas/Alunos** via planilha (CSV/XLS/XLSX).
2. **Gerenciar Parentes** de cada Aluno.
3. **Relatórios** filtrados e exportáveis (CSV, Excel, PDF).
4. **Pré-visualizar** dados antes de gerar relatório.
5. **Controle de Usuários** (ADM, EDITOR, VISUALIZADOR).

---

## 💡 Padrões e Boas Práticas

- **Blueprint Pattern**: cada domínio possui seu `routes.py` isolado, facilitando manutenção e escalabilidade.
- **Uso de Flash Messages**: feedback rápido ao usuário (ex.: “Importação realizada com sucesso!”).
- **Responsividade**: classes `.table-responsive`, `.container-floating`, e media queries no CSS para telas menores.
- **Código DRY**: evita duplicação (ex.: `_build_query` em relatórios).
- **Segurança**: rotas protegidas por `@login_required` e controle de papel (ADM, EDITOR).

---

## ✨ Contribuição

Sinta-se à vontade para abrir issues, sugerir melhorias ou enviar PRs. Toda ajuda é bem-vinda para tornar este sistema mais robusto e completo.

---

## 📬 Contato

Se tiver dúvidas ou precisar de suporte, entre em contato! Boas implementações!