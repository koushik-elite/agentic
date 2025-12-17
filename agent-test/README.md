# agent-test

A base ReAct agent implemented using LangGraph with Agent2Agent (A2A) Protocol support
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.28.3`

## Project Structure

This project is organized as follows:

```
agent-test/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── agent_engine_app.py # Agent Engine application logic
│   └── app_utils/       # App utilities and helpers
│       ├── executor/    # A2A protocol executor implementation
│       └── converters/  # Message converters for A2A protocol
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
├── GEMINI.md            # AI-assisted development guide
└── pyproject.toml       # Project dependencies and configuration
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## Quick Start (Local Testing)

Install required packages and launch the local development environment:

```bash
make install && make playground
```
> **📊 Observability Note:** Agent telemetry (Cloud Trace) is always enabled. Prompt-response logging is not available for LangGraph agents due to SDK limitations with streaming.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch local development environment for testing agent |
| `make deploy`        | Deploy agent to Agent Engine |
| `make register-gemini-enterprise` | Register deployed agent to Gemini Enterprise ([docs](https://googlecloudplatform.github.io/agent-starter-pack/cli/register_gemini_enterprise.html)) |
| `make inspector`     | Launch A2A Protocol Inspector to test your agent implementation                             |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |

For full command options and usage, refer to the [Makefile](Makefile).

## Using the A2A Inspector

This agent implements the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/), enabling interoperability with agents across different frameworks and languages.

The [A2A Inspector](https://github.com/a2aproject/a2a-inspector) provides the following core features:
- 🔍 View agent card and capabilities
- ✅ Validate A2A specification compliance
- 💬 Test communication with live chat interface
- 🐛 Debug with the raw message console

### Local Testing

> **Note:** For Agent Engine deployments, local testing with A2A endpoints requires deployment first, as `make playground` uses the ADK web interface. For local development, use `make playground`. To test A2A protocol compliance, follow the Remote Testing instructions below.

### Remote Testing

1. Deploy your agent:
   ```bash
   make deploy
   ```

2. Launch the inspector:
   ```bash
   make inspector
   ```

3. Get an authentication token:
   ```bash
   gcloud auth print-access-token
   ```

4. In the inspector UI at http://localhost:5001:
   - Add an HTTP header with name: `Authorization`
   - Set the value to: `Bearer <your-token-from-step-3>`
   - Connect to your Agent Engine URL using this format:
     ```
     https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{REGION}/reasoningEngines/{ENGINE_ID}/a2a/v1/card
     ```
     Find your `PROJECT_ID`, `REGION`, and `ENGINE_ID` in the `latest_deployment_metadata.json` file created after deployment.


## Usage

This template follows a "bring your own agent" approach - you focus on your business logic, and the template handles everything else (UI, infrastructure, deployment, monitoring).
1. **Develop:** Edit your agent logic in `app/agent.py`.
2. **Test:** Explore your agent functionality using the local playground with `make playground`. The playground automatically reloads your agent on code changes.
3. **Enhance:** When ready for production, run `uvx agent-starter-pack enhance` to add CI/CD pipelines, Terraform infrastructure, and evaluation notebooks.

The project includes a `GEMINI.md` file that provides context for AI tools like Gemini CLI when asking questions about your template.


## Deployment

You can deploy your agent to a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make deploy
```


When ready for production deployment with CI/CD pipelines and Terraform infrastructure, run `uvx agent-starter-pack enhance` to add these capabilities.

## Monitoring and Observability

The application provides two levels of observability:

**1. Agent Telemetry Events (Always Enabled)**
- OpenTelemetry traces and spans exported to **Cloud Trace**
- Tracks agent execution, latency, and system metrics

**Note:** Prompt-response logging is not available for LangGraph agents due to SDK limitations with streaming responses.

See the [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability.html) for detailed instructions, example queries, and visualization options.
