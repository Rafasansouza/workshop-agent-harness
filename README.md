<div align="center">

<img src="./assets/agent-harness.jpg" alt="Workshop Agent Harness — Jornada de Dados" width="100%" />

# Workshop Agent Harness · Jornada de Dados

**Projeto desenvolvido por [Rafael Souza](https://github.com/Rafasansouza)** durante o Workshop de **Agent Harness** da **Jornada de Dados**.

Como organizar o repositório e os arquivos que o Claude Code usa — **rules, hooks, MCP, subagents e skills** — **antes** de escrever a primeira linha de código, conduzindo um projeto real do PRD às issues e à implementação medida.

[**🎓 Workshop**](https://lp.suajornadadedados.com.br/agent-harness) • [**📖 Documentação**](https://github.com/caio-moliveira/workshop-agent-harness) • [**🌐 Site Oficial**](https://suajornadadedados.com.br/)

</div>

---

## Autor

**Rafael Souza** — [@Rafasansouza](https://github.com/Rafasansouza)

Este projeto foi desenvolvido como parte do Workshop Agent Harness da Jornada de Dados, aplicando os conceitos de **agent harness** para construir um assistente analítico de vendas completo.

---

## O projeto · Agente Analítico de Vendas

Assistente agêntico que costura **text-to-SQL** (Postgres, somente leitura) com **recuperação
qualitativa** (Qdrant) para gerar **relatórios de melhoria de vendas fundamentados** — cruzando o
*o quê* (números) com o *porquê* (voz do cliente) e o *o que fazer* (playbooks que já funcionaram).

É um **produto de mundo real construído ao vivo**. O foco não é só o app: é o **método** — sair de
uma ideia solta e chegar em issues prontas para um agente implementar, governado por um **agent
harness** que codifica os padrões, as validações e as métricas de um time de verdade.

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|------------|
| **Backend** | FastAPI (Python 3.13) + LangGraph |
| **Frontend** | React + TypeScript + Vite |
| **Banco de Dados** | PostgreSQL (vendas + metas) |
| **Vector Store** | Qdrant (busca semântica) |
| **Object Storage** | MinIO (documentos) |
| **Proxy** | nginx (SSE streaming) |
| **Embeddings** | OpenAI text-embedding-3-large |

---

## Do PRD ao código — Status

| # | Passo | Origem | Entra | Sai | Estado |
|---|---|---|---|---|---|
| 0 | `ideia.md` | — | — | a ideia inicial | ✅ |
| 1 | `/grill-me` | Matt Pocock | `ideia.md` | entendimento afiado | ✅ |
| 2 | `/to-prd` | Matt Pocock | sessão do grill | **`PRD.md`** | ✅ |
| 3 | **harness à mão** | nós (ao vivo) | `PRD.md` | `.claude/` (rules · hooks · MCP · subagente · comandos · métricas) | ✅ |
| 4 | `/to-issues` | Matt Pocock | `PRD.md` | issues *ready-for-agent* | ✅ |
| 5 | implementar | — | issues | código (gate + revisor + scorecard) | ✅ |

### Issues Implementadas

| Issue | Descrição | Status |
|-------|-----------|--------|
| #1 | Esqueleto FastAPI + nginx | ✅ |
| #2 | Tool run_sql com guardrails | ✅ |
| #3 | Tool search (Qdrant) | ✅ |
| #4 | Nó planejar | ✅ |
| #5 | Nó perna_quantitativa | ✅ |
| #6 | Nó enriquecer | ✅ |
| #7 | Nó relatorio | ✅ |
| #8 | Endpoint /chat SSE | ✅ |
| #9 | Frontend React chat | ✅ |
| #10 | Fontes inspecionáveis | ✅ |
| #11 | Persistência harness | ✅ |

**Validação:** 80 testes passando (ruff + mypy + pytest)

---

## Estrutura do Repositório

```
├── backend/                    # FastAPI + LangGraph
│   ├── app/                    #   routers + services
│   ├── agent/                  #   grafo, nós e tools
│   │   ├── nodes/              #     planejar, perna_quantitativa, enriquecer, relatorio
│   │   └── tools/              #     run_sql, search
│   ├── harness/                #   persistência de runs (SQLAlchemy)
│   └── tests/                  #   80 testes
├── frontend/                   # React + TypeScript + Vite
│   └── src/
│       ├── api/                #   tipos e cliente SSE
│       └── components/         #   Chat, Report, Estados, Inspection panels
├── infra/
│   └── nginx/                  # proxy com suporte SSE
├── alembic/                    # migrations
├── seed/                       # ingestão (dados + corpus)
├── .claude/                    # agent harness
│   ├── rules/                  #   padrões por área
│   ├── agents/                 #   revisor-codigo
│   ├── commands/               #   /validar, /scorecard
│   └── skills/                 #   skills baixadas
├── CLAUDE.md                   # índice durável do projeto
├── PRD.md                      # PRD consolidado
└── docker-compose.yml          # stack completa
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- **Docker** e **Docker Compose**
- **Python 3.13** com [**uv**](https://docs.astral.sh/uv/)
- **Node.js 18+** e **npm**
- **Chave da API OpenAI** (para embeddings)

### Passo 1: Clone o repositório

```bash
git clone https://github.com/Rafasansouza/workshop-agent-harness.git
cd workshop-agent-harness
```

### Passo 2: Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e adicione sua chave da OpenAI:

```env
OPENAI_API_KEY=sk-...
```

### Passo 3: Suba a infraestrutura

```bash
docker compose up -d postgres qdrant minio
```

Aguarde os containers iniciarem (~10s).

### Passo 4: Instale as dependências Python

```bash
uv sync
```

### Passo 5: Execute a ingestão de dados

```bash
# Gera os CSVs de vendas (dataset sintético)
uv run python seed/generate.py

# Carrega no PostgreSQL
uv run python seed/load.py

# Ingere o corpus qualitativo no Qdrant
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minio-2024-secure uv run python seed/ingest.py
```

### Passo 6: Execute as migrations do Alembic

```bash
uv run alembic upgrade head
```

### Passo 7: Inicie o backend

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

### Passo 8: Inicie o frontend (em outro terminal)

```bash
cd frontend
npm install
npm run dev
```

### Passo 9: Acesse a aplicação

- **Frontend:** http://localhost:5173
- **API (health):** http://localhost:8000/health
- **MinIO Console:** http://localhost:9001
- **Qdrant Dashboard:** http://localhost:6333/dashboard

---

## 🧪 Rodando os Testes

```bash
# Validação completa (lint + types + tests)
uv run ruff check --fix backend && uv run mypy backend && uv run pytest -q

# Ou use o comando do harness
/validar
```

---

## 📚 Consoles e Dashboards

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| MinIO | http://localhost:9001 | `minioadmin` / `minio-2024-secure` |
| Qdrant | http://localhost:6333/dashboard | — |
| API Docs | http://localhost:8000/docs | — |

---

## 🎁 Bônus Workshop Jornada de Dados

### O que você aprendeu neste workshop:

1. **Agent Harness** — Como estruturar o `.claude/` com rules, hooks, MCP, subagents e skills
2. **Do PRD às Issues** — Processo `/grill-me` → `/to-prd` → harness → `/to-issues`
3. **Grafo Determinístico** — LangGraph com topologia fixa (planejar → quantitativo → enriquecer → relatório)
4. **Guardrails** — SQL read-only com allowlist e LIMIT injetado
5. **Grounding** — Toda recomendação amarrada a uma fonte rastreável
6. **SSE Streaming** — Relatório renderizado incrementalmente no frontend
7. **Observabilidade** — Persistência de runs no schema `harness`

### Próximos passos para você:

1. **Adicione Langfuse** — Observabilidade completa do LLM
2. **Implemente mais nós** — Análise de concorrência, previsão de demanda
3. **Conecte ao seu banco** — Substitua o dataset sintético por dados reais
4. **Deploy** — Use o `docker-compose.yml` completo para produção

### Recursos adicionais:

- [Documentação Claude Code](https://docs.anthropic.com/claude-code)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Skills do Matt Pocock](https://github.com/mattpocock/skills)
- [Skills LangChain](https://github.com/langchain-ai/langchain-skills)

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais como parte do Workshop Agent Harness da [Jornada de Dados](https://suajornadadedados.com.br/).

---

<div align="center">

**Desenvolvido com 🤖 por [Rafael Souza](https://github.com/Rafasansouza)**

*Workshop Agent Harness · Jornada de Dados · 2025*

</div>
