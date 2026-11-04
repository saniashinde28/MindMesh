# 🧠 MindMesh — Multi-Agent AI Research System

**Research smarter. Think deeper. Get structured insights with AI agents.**

MindMesh is a multi-agent AI research platform that automates the research process using specialized AI agents. Instead of relying on a single LLM response, MindMesh coordinates multiple agents to search the web, extract relevant information, generate structured research reports, and critically evaluate the results.

Built with **React, FastAPI, LangChain, Groq, and Tavily**, MindMesh transforms a research topic into a comprehensive report through a coordinated AI workflow.

---

## Features

### 🤖 Multi-Agent Research Pipeline

MindMesh uses two specialized agents and chains, each responsible for a different stage of research.

| Agent | Responsibility |
| --- | --- |
| 🔍 Search Agent | Uses Tavily to discover relevant and recent web sources for the research topic. |
| 📖 Reader Agent | Selects relevant URLs and extracts webpage content using BeautifulSoup. |
| ✍️ Writer Chain | Combines search results and extracted content to generate a structured research report. |
| 🧐 Critic Chain | Reviews the generated report and provides feedback on its quality, clarity, and completeness. |

### 🔄 Automated Research Workflow

-   Enter a research topic and initiate a research job.

-   Agents execute their respective tasks in sequence.

-   Track agent progress and status through live updates.

-   Generate a structured research report.

-   Receive a separate critic evaluation of the generated report.

### 📄 Research Report Generation

-   Structured research reports.

-   Markdown report export.

-   PDF report export.

-   Preserves report formatting, including headings, lists, tables, and links where supported.

### ⚡ Live Research Tracking

-   Real-time progress updates using Server-Sent Events (SSE).

-   Individual research job IDs.

-   Automatic SSE reconnection and event resumption.

-   Reload a research job using its URL without losing the job reference.

### 🔐 Authentication and Request Protection

-   Optional HTTP Basic authentication for protected API endpoints.

-   Configurable username and password.

-   Configurable research request rate limit.

-   Research queue with limited concurrent execution.

### 🧩 Bring Your Own API Keys (BYOK)

MindMesh is designed so developers can run their own instance.

-   No API keys are bundled with the repository.

-   Users provide their own Groq and Tavily API keys.

-   API usage is associated with the user's own provider accounts.

-   Users can configure their preferred supported Groq models.

---

## 🏗️ Architecture

MindMesh follows a sequential multi-agent architecture.

```
flowchart TD
    A["User enters research topic"] --> B["FastAPI Backend"]
    B --> C["Search Agent"]
    C --> D["Tavily Web Search"]
    D --> E["Reader Agent"]
    E --> F["BeautifulSoup Web Scraping"]
    F --> G["Writer Agent"]
    G --> H["Groq LLM"]
    H --> I["Structured Research Report"]
    I --> J["Critic Agent"]
    J --> K["Research Feedback"]
    I --> L["Markdown / PDF Export"]
    B --> M["SSE Live Progress"]
    M --> N["React Frontend"]
```

### Agent Execution Flow

**1\. Search Agent**

-   Accepts the research topic.

-   Searches the web using Tavily.

-   Collects relevant search results and source URLs.

**2\. Reader Agent**

-   Selects a relevant webpage.

-   Scrapes and extracts its content using BeautifulSoup.

-   Passes the extracted information to the next stage.

**3\. Writer Chain**

-   Uses the search results and scraped content.

-   Generates a comprehensive, structured research report using a Groq-hosted LLM.

**4\. Critic Chain**

-   Evaluates the generated report.

-   Provides feedback on the report's quality and completeness.

The agents execute sequentially, with intermediate outputs maintained throughout the pipeline. The critic currently provides an evaluation; it does not automatically rewrite the report.

---

## 🛠️ Tech Stack

| Category | Technologies |
| --- | --- |
| Frontend | React.js, Vite, JavaScript |
| Backend | Python, FastAPI |
| Agent Framework | LangChain |
| LLM Provider | Groq |
| Web Search | Tavily API |
| Web Scraping | BeautifulSoup |
| Real-time Updates | Server-Sent Events (SSE) |
| Report Generation | Markdown, PDF |
| Deployment | Docker, Render |
| Version Control | Git, GitHub |

---

## 📁 Project Structure

```
MindMesh/
│
├── backend/
│   ├── app.py              # FastAPI application and API endpoints
│   ├── agents.py           # Search, Reader, Writer and Critic agents
│   ├── pipeline.py         # Multi-agent research pipeline
│   ├── tools.py            # Search and webpage extraction tools
│   ├── jobs.py             # Research job and queue management
│   ├── export.py           # PDF report generation
│   ├── requirements.txt    # Python dependencies
│   └── .env                # Local environment variables (not committed)
│
├── frontend/
│   ├── src/                # React application source
│   ├── public/             # Static assets
│   ├── package.json
│   ├── package-lock.json
│   └── ...
│
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

There are two ways to use MindMesh:

1.  Run it locally using Docker.

2.  Deploy your own instance using a hosting platform that supports Docker.

You do not need to train or host an LLM locally. Groq and Tavily provide hosted APIs.

### Prerequisites

Install the following:

-   [Git](https://git-scm.com/)

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)

-   A [Groq API key](https://console.groq.com/keys)

-   A [Tavily API key](https://app.tavily.com/)

### Step 1: Clone the repository

```
git clone https://github.com/saniashinde28/MindMesh.git

cd MindMesh
```

### Step 2: Get your API keys

Create your own accounts and generate API keys:

-   **Groq:** [https://console.groq.com/keys](https://console.groq.com/keys)

-   **Tavily:** [https://app.tavily.com/](https://app.tavily.com/)

These keys are required for the AI research pipeline.

### Step 3: Configure environment variables

Create a `.env` file inside the `backend` directory.

```
backend/.env
```

Add your own configuration:

```
# Groq API
GROQ_API_KEY=your_groq_api_key

# Tavily API
TAVILY_API_KEY=your_tavily_api_key

# LLM Configuration
WRITER_MODEL=groq:openai/gpt-oss-120b
TOOL_MODEL=your_supported_groq_tool_model

# Optional HTTP Basic Authentication
APP_USER=mindmesh
APP_PASSWORD=choose_a_secure_password

# Optional research rate limit
RATE_LIMIT_PER_HOUR=5
```

**Important:**

-   Replace the API key placeholders with your own keys.

-   Configure `TOOL_MODEL` with a Groq model supported by your agent/tool configuration.

-   You can change the writer model to another compatible model supported by your implementation.

-   Authentication is optional. If `APP_PASSWORD` is not configured, the authentication gate is inactive.


### Step 4: Build the Docker image

From the root of the project:

```
docker build -t mindmesh .
```

This builds the React frontend and prepares the Python backend in a single Docker image.

### Step 5: Run MindMesh

```
docker run --rm -p 8000:8000 --env-file backend/.env mindmesh
```

### Step 6: Open the application

Visit:

```
http://localhost:8000
```

Your MindMesh instance is now running locally!

---

## 🔑 Using Your Own API Keys

MindMesh follows a Bring Your Own API Keys model.

Every developer can:

1.  Clone the public GitHub repository.

2.  Create their own Groq and Tavily accounts.

3.  Generate their own API keys.

4.  Add those keys to `backend/.env`.

5.  Build and run the Docker image.

6.  Use their own independently running MindMesh instance.

**Your API keys remain yours.** They are supplied through local environment variables and are not included in the public repository or Docker image.

API usage, quotas, and applicable provider charges are associated with your own accounts and their respective plans.

---

## 🌐 API Endpoints

The FastAPI backend exposes the following endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | /api/research | Starts a new research job. |
| GET | /api/research/{job_id} | Retrieves research job information and status. |
| GET | /api/research/{job_id}/events | Streams live job events using SSE. |
| GET | /api/research/{job_id}/report.md | Downloads the report in Markdown format. |
| GET | /api/research/{job_id}/report.pdf | Downloads the report in PDF format. |
| GET | /api/health | Health check endpoint. |

### Example: Start a research job

**Request**

```
POST /api/research
Content-Type: application/json
```

```
{
  "topic": "The impact of artificial intelligence on healthcare"
}
```

**Response**

```
{
  "job_id": "your-generated-job-id"
}
```

Use the returned job ID to retrieve job status, subscribe to progress events, and download the generated report.

---

**Deployment note:** The current job manager uses in-memory storage. A server restart or redeployment can remove active and previously stored jobs. For the current implementation, use a single application instance rather than multiple independently running instances.

---

## ⚙️ Configuration

| Variable | Required | Description |
| --- | --- | --- |
| GROQ_API_KEY | Yes | API key for Groq-hosted LLMs. |
| TAVILY_API_KEY | Yes | API key for Tavily web search. |
| WRITER_MODEL | Yes | Model used by the Writer agent. |
| TOOL_MODEL | Configuration-dependent | Groq model used by the tool-enabled agent configuration. |
| APP_USER | Optional | HTTP Basic authentication username. Defaults to mindmesh. |
| APP_PASSWORD | Optional | Enables the HTTP Basic authentication gate when configured. |
| RATE_LIMIT_PER_HOUR | Optional | Maximum research requests per hour. Defaults to 5. |
| ALLOWED_ORIGINS | Optional | Allowed CORS origins for development or cross-origin setups. |

---

## ⚠️ Current Limitations

-   The research pipeline depends on external Groq and Tavily APIs.

-   Search results and webpage extraction depend on the availability and accessibility of external websites.

-   The Critic chain currently evaluates the report but does not automatically revise it.

-   Research jobs are stored in memory and are not persisted across server restarts.

-   Concurrent research execution is limited by the configured job manager.

-   Free hosting plans may spin down inactive services and interrupt running research jobs.

---

## 🔮 Future Improvements

Some potential improvements for future versions include:

-   Persistent research job storage using a database.

-   Automatic report refinement using critic feedback.

-   Source citations and reference validation.

-   Parallel agent execution.

-   More advanced multi-agent orchestration.

---

## 🤝 Contributing

Contributions, suggestions, bug reports, and feature requests are welcome!
---

## 👩‍💻 Author

**Sania Shinde**

-   GitHub: [@saniashinde28](https://github.com/saniashinde28)

-   LinkedIn: [Sania Shinde](https://www.linkedin.com/in/sania-shinde-4b79572b/)

---

## ⭐ Support

If you find MindMesh interesting or useful, consider giving the repository a ⭐ on GitHub.

Feel free to fork it, experiment with your own API keys, and build your own AI-powered research assistant!

**MindMesh — Turning research questions into structured knowledge, one agent at a time.**
