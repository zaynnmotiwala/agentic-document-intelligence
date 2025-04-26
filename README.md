# Agentic Document Intelligence: Citation-Grounded RAG on Databricks

A retrieval-augmented chat assistant that answers questions from a PDF document corpus and **shows its sources**. Each answer links to the original PDF, which opens in a built-in viewer with the relevant passage highlighted. Agentic Document Intelligence runs end to end on Databricks, using Mosaic AI Vector Search, Model Serving, and Databricks Apps.

## Features

- **Source-grounded answers.** Every response cites the documents it used.
- **In-app PDF viewer.** Click a source to open the PDF at the right page, with the matching text highlighted.
- **Tool-calling agent.** A LangGraph agent decides when to call the vector-search retriever.
- **Automated RAG pipeline.** A three-step Databricks job loads, indexes, and deploys everything.
- **Managed vector search.** A Delta Sync index with `databricks-gte-large-en` embeddings stays in sync with the source table.
- **Model serving.** The agent is logged with MLflow, registered in Unity Catalog, and deployed as a serving endpoint.
- **Custom chat UI.** A React chat component, wrapped as a Dash component and served alongside FastAPI.
- **One-command deployment** with Databricks Asset Bundles.

## Architecture

```text
                ┌──────────────── RAG pipeline (Databricks Job) ───────────────┐
                │                                                              │
  PDF docs ──► loader ──► Delta table (chunks) ──► indexer ──► Vector Search   │
                │          pypdf + text splitter        Delta Sync index        │
                │                                       (gte-large-en)         │
                │                                              │               │
                │                              driver ◄────────┘               │
                │           LangGraph agent → MLflow → Unity Catalog → Serving │
                └──────────────────────────────────────────────────────────────┘
                                                               │
                ┌──────────────── Databricks App ──────────────┼───────────────┐
                │                                              ▼               │
  User ──► Dash UI (React chat + PDF viewer) ──► FastAPI /api ──► Agent        │
                │          ▲                            │       endpoint       │
                │          └── PDF + highlighted page ◄─┘ (from UC Volume)     │
                └──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Platform | Databricks Apps, Asset Bundles, Unity Catalog, Volumes |
| LLM | `databricks-meta-llama-3-3-70b-instruct` (Model Serving) |
| Embeddings | `databricks-gte-large-en` |
| Vector store | Mosaic AI Vector Search (Delta Sync index) |
| Agent | LangGraph, `databricks-langchain`, MLflow, `databricks-agents` |
| Data processing | PySpark, pypdf, LangChain text splitters |
| Backend | FastAPI, Uvicorn |
| Frontend | Dash, React, TypeScript, Tailwind CSS, react-pdf, Fuse.js |
| Text matching | RapidFuzz |
| Tooling | uv, Ruff, Node.js |

## RAG Pipeline

The `chatten_rag` job runs three tasks in order:

| Task | What it does |
|---|---|
| **loader** | Downloads sample PDF documentation into a Unity Catalog Volume, extracts the text with pypdf, splits it into chunks, and writes them to a Delta table |
| **indexer** | Creates a Delta Sync Vector Search index on the chunks table and syncs it |
| **driver** | Builds the LangGraph agent with a retriever tool (top 3 results), logs it with MLflow, registers it in Unity Catalog, and deploys it to a serving endpoint |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Sends a message to the agent and returns the answer with its sources |
| `GET` | `/api/files` | Streams a source PDF from the Volume |
| `POST` | `/api/files/relevant_page` | Finds the page that best matches a cited passage |

## Prerequisites

- A Databricks workspace with **Unity Catalog**, **Model Serving**, **Vector Search**, and **Databricks Apps** enabled
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html)
- [uv](https://docs.astral.sh/uv/)
- [Node.js](https://nodejs.org/) (to build the UI)
- Python 3.10

## Setup

**1. Clone and install**

```bash
git clone https://github.com/zaynnmotiwala/agentic-document-intelligence.git
cd agentic-document-intelligence
uv sync --all-packages
```

**2. Configure the environment.** Create a `.env` file in the project root:

```env
CHATTEN_PROFILE=<your-databricks-profile>
CHATTEN_CATALOG=<your-catalog>

# Optional: override bundle variables (see databricks.yml for defaults)
BUNDLE_VAR_vsi_endpoint=<your-vector-search-endpoint>
```

**3. Authenticate with Databricks**

```bash
databricks auth login -p <profile-name>
```

## Deployment

```bash
# 1. Build and deploy the app and the RAG job
make deploy profile=<profile-name> catalog=<catalog-name>

# 2. Run the RAG pipeline (loader → indexer → driver)
make run-rag profile=<profile-name> catalog=<catalog-name>

# 3. Grant the app's service principal read access to the Volume

# 4. Start the app
make run-app profile=<profile-name> catalog=<catalog-name>
```

Then open the app from **Compute → Apps** in your Databricks workspace.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `catalog` | none (required) | Unity Catalog name |
| `db` | `chatten` | Schema name |
| `vsi_endpoint` | `dbdemos_vs_endpoint` | Vector Search endpoint |
| `agent_serving_endpoint` | `chatten_agent` | Agent serving endpoint name |

## Local Development

Run these in two terminals:

```bash
# Terminal 1: rebuild the UI component on change
cd packages/chatten_ui && npm run watch

# Terminal 2: run the server with hot reload
uvicorn chatten_app.app:app --reload
```

## Project Structure

```text
├── packages/
│   ├── chatten_app/     # FastAPI backend and Dash app (chat API, PDF serving)
│   ├── chatten_rag/     # RAG pipeline: loader, indexer, driver, and the agent
│   └── chatten_ui/      # React chat and PDF viewer, packaged as a Dash component
├── src/chatten/         # Shared configuration (pydantic-settings)
├── scripts/             # Cleanup utilities
├── databricks.yml       # Asset Bundle: app and job definitions
├── Makefile             # Build, deploy, and run commands
└── pyproject.toml       # uv workspace
```

## Customization

- **Use your own documents.** Upload PDFs to the Volume's `raw_docs` folder and run the pipeline again.
- **Change the model.** Set `chat_endpoint` in `src/chatten/config.py` to any Databricks serving endpoint.
- **Change the assistant's behavior.** Edit `PROMPT` in `src/chatten/config.py`.

## License

MIT. See [LICENSE](LICENSE).
