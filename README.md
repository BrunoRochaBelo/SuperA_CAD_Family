# Formaturas App

Este é um sistema simples para gerenciamento de parentes de formandos, criado em **Flask** com uma **arquitetura monolítica modular**. A aplicação foi projetada usando **Blueprints** para cada domínio (auth, home, parentes, relatórios, dashboard), mantendo assim o código organizado e fácil de manter.

---

## 📂 Estrutura do Projeto

```text
meu_projeto/
├── .env                        # Configurações de ambiente (ex.: SECRET_KEY, DATABASE_URL)
├── .gitignore
├── Procfile                    # Para deployment (opcional)
├── README.md                   # Documentação do projeto
├── requirements.txt            # Lista de dependências Python
├── run.py                      # Ponto de entrada da aplicação
├── SuperA_CAD_Family.py        # Arquivo principal gerado pelo Visual Studio
├── SuperA_CAD_Family.pyproj    # Projeto do Visual Studio
├── SuperA_CAD_Family.sln       # Solução do Visual Studio
├── __pycache__/
├── .vs/
├── .vscode/
├── env/                        # Ambiente virtual (venv)
├── formaturas_app/             # Aplicação Flask principal
│   ├── __init__.py             # Configuração do app, DB, login_manager, etc.
│   ├── decorators.py           # Decorators customizados
│   ├── models.py               # Definição dos models (Usuario, Formando, Parente, etc.)
│   ├── seed.py                # Script para popular o banco de dados
│   ├── auth/                  # Módulo de autenticação (login, logout, editar perfil, etc.)
│   ├── empresa/               # Módulo de gerenciamento de empresas
│   ├── equipe/                # Módulo de gerenciamento da equipe
│   ├── home/                  # Módulo "Home": turmas, importação de planilhas, etc.
│   ├── relatorios/            # Módulo de relatórios (filtros, pré-visualização, exportação CSV/Excel/PDF)
│   ├── static/                # Arquivos estáticos específicos do app
│   │   └── css/
│   │       └── style.css      # Estilos CSS da aplicação
│   └── templates/             # Templates Jinja2 da aplicação
│       ├── base.html          # Layout principal (header fixo, container flutuante, etc.)
│       ├── auth/              # Templates do módulo de autenticação
│       ├── home/              # Templates relacionados às turmas e importação
│       ├── relatorios/        # Templates de relatórios (filtros, preview, etc.)
│       └── equipe/            # Templates para gerenciamento da equipe
├── instance/                  # Arquivos de configuração sensíveis (instância)
├── logs/                      # Logs da aplicação
├── migrations/                # Scripts de migração do banco de dados (Alembic)
└── static/                    # Arquivos estáticos globais (se houver)
```

---

## 🏗️ Arquitetura e Design

- **Monolito Modular com Blueprints**: O projeto é estruturado como um monolito modular, onde cada funcionalidade (auth, home, parentes, relatórios, dashboard, empresa e equipe) é desenvolvida em módulos independentes utilizando **Blueprints**, o que garante a organização e facilita a escalabilidade.
- **Models Centralizados**: Toda a lógica de negócios e definição de entidades (como `Usuario`, `Formando`, `Parente`, etc.) está concentrada em `models.py`, promovendo um padrão unificado para o acesso aos dados.
- **Padrões de Projeto**:
  - **Blueprint Pattern**: Cada módulo possui seu próprio `routes.py`, permitindo a definição de rotas específicas e mantendo o código modularizado.
  - **MVC Simplificado**: O “model” reside em `models.py`, os “controllers” e rotas estão distribuídos nos Blueprints, e as “views” são implementadas nos templates Jinja2.
  - **Autenticação com Flask-Login**: Gerencia sessão e controle de acesso de forma segura.
  - **Renderização com Jinja2**: Facilita a criação de templates dinâmicos e reutilizáveis.
- **UI/UX Avançado**:
  - **Header fixo e Container flutuante**: Garante uma navegação consistente e uma visualização clara do conteúdo.
  - **Design Responsivo**: O uso de CSS com media queries, classes como `.table-responsive`, `.container-floating` e `.btn` adapta a interface para diversos dispositivos.
  - **Feedback Interativo**: Mensagens flash (`alert-success`, `alert-danger`, etc.) são utilizadas para comunicar o status das ações do usuário.
  - **Pré-visualização de Relatórios**: Apresenta as primeiras 5 linhas dos dados filtrados antes da geração dos arquivos finais (CSV, Excel, PDF).

---

## 📦 Módulos Principais

1. **auth**

   - Gerencia login e logout (rotas `auth/login` e `auth/logout`).
   - Usa `Flask-Login` para manter a sessão do usuário.
   - Define perfis de usuário (ADM, EDITOR, VISUALIZADOR).

2. **home**

   - “Tela principal” da aplicação.
   - Lista turmas (`Formando.turma`) e gerencia:
     - **Importação de planilhas** (CSV/XLS/XLSX) com colunas “Turma” e “Aluno”.
     - **Edição de turmas** (renomear, adicionar/excluir alunos).
     - **Exclusão de turmas** (remove todos os registros relacionados à turma).

3. **parentes**

   - Cadastro de parentes por aluno.
   - Permite que o usuário escolha uma turma, filtre os alunos dessa turma e visualize a lista de parentes do aluno selecionado.
   - Suporta criação, edição e exclusão de parentes via modais (requisições AJAX).

4. **relatorios**

   - Filtra dados de parentes e alunos com a possibilidade de escolher **campos** (ex.: turma, aluno, cidade, etc.) e gerar:
     - **CSV**
     - **Excel** (usando `pandas` + `openpyxl`)
     - **PDF** (usando `pdfkit` + `wkhtmltopdf`)
   - **Pré-visualização**: mostra as primeiras 5 linhas do resultado antes de gerar o arquivo final.
   - Inclui filtros para Turma, Aluno, Cidade, “Comprou Foto?”, entre outros.

5. **empresa**

   - Responsável pelo gerenciamento das informações de empresas relacionadas.
   - Permite o cadastro, edição e consulta de dados empresariais integrados na aplicação.

6. **equipe**
   - Gerencia o cadastro e a organização dos membros da equipe.
   - Facilita a distribuição de tarefas e o acompanhamento das atividades internas.

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

Copie o arquivo `.env.example` para `.env` e ajuste as variáveis conforme o seu ambiente. Para executar em produção, defina `DATABASE_URL` apontando para o banco PostgreSQL desejado. Um exemplo é:

```
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/politika
```

O mesmo arquivo também permite customizar a `SECRET_KEY` e outras configurações que você queira manter fora do controle de versão.

### 4️⃣ Rode o script de criação do usuário master

Execute o comando abaixo para criar a empresa e o usuário master inicial (apenas no primeiro uso):

```bash
python -m formaturas_app.utils.criar_usuarios_iniciais
```

O usuário master criado será responsável por cadastrar os demais usuários pela interface do sistema.

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

- **Flask** + **Blueprints**: Base para a estrutura modular, permitindo a separação clara entre as funcionalidades (auth, home, parentes, relatórios, empresa e equipe).
- **Flask-Login**: Gerencia autenticação e controle de acesso, definindo perfis (ADM, EDITOR, VISUALIZADOR) conforme o sistema.
- **Flask-SQLAlchemy**: ORM que facilita o acesso e a manipulação dos dados.
- **Flask-Migrate**: Simplifica as migrações do banco de dados, garantindo a evolução controlada do modelo de dados.
- **Jinja2**: Motor de templates para construir views dinâmicas e reutilizáveis.
- **pdfkit** e **wkhtmltopdf**: Permitem a geração de PDFs a partir do HTML, suportando os relatórios do sistema.
- **pandas** + **openpyxl**: Auxiliam na manipulação e exportação de dados para Excel.
- **HTML5/CSS3** com **Bootstrap 5**: Base para interfaces modernas e responsivas, assegurando uma boa experiência em todos os dispositivos.
- **pytest**: Ferramenta utilizada para a criação de testes unitários e de integração, mantendo a qualidade do código.
- **AJAX**: Implementado nos modais das operações de gerenciamento de parentes, proporcionando interações mais dinâmicas e sem recarregamento da página.

---

## 📊 Funcionalidades

1. **Importar Turmas/Alunos** via planilha (CSV/XLS/XLSX).
2. **Gerenciar Parentes** de cada Aluno.
3. **Relatórios** filtrados e exportáveis (CSV, Excel, PDF).
4. **Pré-visualizar** dados antes de gerar relatório.
5. **Controle de Usuários** (ADM, EDITOR, VISUALIZADOR).
6. **Dashboard** com indicadores e gráficos dinâmicos para monitorar estatísticas e desempenho.

---

## 💡 Padrões e Boas Práticas

- **Blueprint Pattern**: cada domínio possui seu `routes.py` isolado, facilitando a manutenção e escalabilidade.
- **Uso de Flash Messages**: feedback rápido ao usuário (ex.: “Importação realizada com sucesso!”) e outras interações.
- **Responsividade**: utilização de classes como `.table-responsive`, `.container-floating` e media queries no CSS para uma ótima experiência em dispositivos móveis.
- **Código DRY**: evita duplicação com funções e módulos reutilizáveis (ex.: `_build_query` em relatórios) e componentes de interface.
- **Segurança**: rotas protegidas por `@login_required` e controle de papel (ADM, EDITOR), com validação tanto no frontend quanto no backend.
- **Validação e Feedback Imediato**: validação consistente dos formulários com mensagens de erro claras e imediatas.
- **Interatividade com AJAX**: uso de requisições assíncronas nos modais e em operações dinâmicas para evitar o recarregamento desnecessário da página.

---

## ✨ Contribuição

Sinta-se à vontade para abrir issues, sugerir melhorias ou enviar PRs. Toda ajuda é bem-vinda para tornar este sistema mais robusto e completo.

---

## 📬 Contato

Se tiver dúvidas ou precisar de suporte, entre em contato! Boas implementações!
