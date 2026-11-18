# Backoffice do Laboratório

Projeto Django para o backoffice de um laboratório de próteses dentárias. A interface desktop usa templates Bootstrap e JavaScript `fetch` para consumir a API REST. A área de administração inclui autenticação, um painel e uma página para consultar e filtrar trabalhos; em desenvolvimento, o projeto usa SQLite por omissão e pode ligar-se ao PostgreSQL do Neon através de `DATABASE_URL`.

## Requisitos

- Python 3.12
- Uma base de dados PostgreSQL no Neon (opcional para começar localmente)

## Preparar o ambiente

```bash
# Usa Python 3.12; se necessário, instala-o primeiro com uv.
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Se o comando `python3.12` não estiver no `PATH`, usa o caminho completo para o Python 3.12 instalado com uv: `$HOME/.local/bin/python3.12 -m venv .venv`.

Gera uma chave com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` e substitui `replace-with-a-random-secret` em `.env`. Para começar sem ligar ao Neon, deixa `DATABASE_URL` vazio: será usada uma base SQLite local.

## Executar

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Mantém `DATABASE_URL` vazio nestes passos para preparar a base SQLite local. Depois, abre <http://127.0.0.1:8000/> para iniciar sessão, <http://127.0.0.1:8000/dashboard/> para abrir o painel ou <http://127.0.0.1:8000/trabalhos/> para consultar trabalhos. A administração Django está em <http://127.0.0.1:8000/admin/>.

## Ligar ao Neon

Coloca a connection string PostgreSQL fornecida pelo Neon em `DATABASE_URL` no `.env`. Mantém as credenciais privadas e não partilhes o `.env`; o ficheiro está excluído do Git. A ligação exige SSL.

Como a base de dados já existe, primeiro inspeciona o esquema antes de criar migrações ou executar `migrate`. Para gerar uma primeira referência dos modelos a partir das tabelas existentes:

```bash
python manage.py inspectdb
```

Os modelos das 22 tabelas existentes foram gerados em `core/models.py` e estão marcados como `managed = False`: o Django não tentará criar ou alterar essas tabelas através de migrações. `inspectdb` apenas lê o esquema; não consulta os registos. Revê os modelos antes de os usar e não executes `migrate` com `DATABASE_URL` apontado ao Neon sem decidir primeiro como gerir as tabelas próprias do Django. Não se executam migrações automaticamente ao iniciar o servidor.

## API

A API REST está versionada em `/api/v1/` e usa JWT com a tabela `utilizador` existente:

- `POST /api/v1/auth/token/` recebe `email` e `password` e devolve tokens `access` e `refresh`.
- `POST /api/v1/auth/token/refresh/` recebe um `refresh` e devolve um novo `access`.
- `GET /api/v1/auth/me/` devolve a conta autenticada e o perfil detetado.
- `GET /api/v1/trabalhos/` e `GET /api/v1/trabalhos/{id}/` expõem trabalhos em modo de leitura, com resultados limitados pelo perfil.
- `GET /api/v1/encomendas/rececao/` lista pedidos em avaliação para administradores e colaboradores com a permissão de receção.
- `GET` e `POST /api/v1/permissoes/colaboradores/{id}/` consultam ou concedem permissões; `DELETE /api/v1/permissoes/colaboradores/{id}/{codigo}/` revoga uma permissão. Apenas administradores podem gerir delegações.

Envia o token de acesso no cabeçalho `Authorization: Bearer <access>`. O campo `password_hash` deve conter hashes compatíveis com os hashers do Django; nunca guardes palavras-passe em texto simples. Os restantes recursos da API devem ser acrescentados com permissões por perfil antes de expor operações de leitura ou escrita.

Administradores veem todos os trabalhos; colaboradores veem trabalhos operacionais, excluindo os estados `Em Avaliação`, `Concluído` e `Entregue`; clientes veem apenas trabalhos associados ao seu próprio perfil, incluindo o histórico. As operações de escrita nos trabalhos e a delegação de outras páginas ainda não estão implementadas.

A permissão atualmente disponível é `rececao_trabalhos`. O identificador `{id}` da rota de permissões é o `utilizador_id` do perfil de colaborador.
