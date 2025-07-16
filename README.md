# Agentflow: Multi-Agent Virtual Office

A sophisticated multi-agent system for business automation and decision support, powered by LangGraph and advanced AI agents.

## Key Features

- **Specialized AI Agents**: Cofounder, Manager, Sales, Marketing, Finance, Legal, and more
- **Structured Communication**: LangGraph-based state management for reliable agent coordination
- **Advanced Memory Systems**: Neo4j for private memory, Qdrant for vector/global memory
- **Tool Integration**: Built-in tools for web search, financial modeling, and legal compliance
- **Self-Healing**: Automatic error detection and recovery mechanisms
- **Personality Profiles**: Customizable agent behaviors and expertise areas

## Architecture

![AgentFlow Architecture](docs/architecture.png)

### Core Components

1. **LangGraph Orchestrator**
   - Manages agent workflows and state transitions
   - Implements error handling and quality control
   - Ensures structured communication between agents

2. **Agent Types**
   - **Cofounder**: Vision and strategy
   - **Manager**: Project coordination and task delegation
   - **Sales**: Customer acquisition and forecasting
   - **Marketing**: Content strategy and brand amplification
   - **Finance**: Financial modeling and ROI analysis
   - **Legal**: Compliance and document generation

3. **Memory Systems**
   - **Neo4j**: Private agent memory and knowledge graphs
   - **Qdrant**: Vector embeddings and semantic search
   - **Redis**: Caching and queue management

4. **Tool Integration**
   - Web search and content analysis
   - Financial modeling and forecasting
   - Legal document generation
   - SEO and marketing analytics

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for local development)
- API keys for required services (OpenRouter, Qdrant, Neo4j, Redis)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/aparnap2/agentflow.git
   cd agentflow
   ```

2. Set up the environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```bash
   python -m scripts.initialize_db
   ```

## Agent Personalities

Each agent has a distinct personality and expertise area:

| Agent | Personality | Key Focus | Temperature | Confidence Threshold |
|-------|-------------|-----------|-------------|----------------------|
| Cofounder | Visionary | Strategy | 0.7 | 0.75 |
| Manager | Organized | Coordination | 0.5 | 0.8 |
| Sales | Persuasive | Revenue | 0.6 | 0.7 |
| Marketing | Creative | Branding | 0.7 | 0.6 |
| Finance | Analytical | ROI | 0.3 | 0.8 |
| Legal | Precise | Compliance | 0.3 | 0.85 |

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
agentflow/
├── backend/
│   ├── agents/           # Agent implementations
│   ├── tools/            # Custom tools
│   ├── workflows/        # LangGraph workflows
│   ├── memory/           # Memory management
│   └── main.py           # FastAPI application
├── frontend/             # Web interface
└── docker-compose.yml    # Development environment
```

## Documentation

For detailed documentation, see:

- [Agent Development Guide](docs/agent_development.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please open an issue or contact [your-email@example.com](mailto:your-email@example.com)