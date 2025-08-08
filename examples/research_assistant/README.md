# Multi-Modal Research Assistant

A comprehensive research agent that can analyze various data sources and produce detailed reports. This example showcases the Entity framework's ability to handle complex, multi-stage research workflows with persistent memory and tool orchestration.

## Features

- **Multi-modal input**: Accepts research queries, URLs, PDFs, and images
- **Smart parsing**: Extracts entities, dates, and key concepts
- **Strategic planning**: Plans research approach based on query complexity
- **Tool orchestration**: Coordinates multiple research tools and APIs
- **Quality control**: Fact-checks findings and validates citations
- **Rich output**: Generates formatted reports with citations and visualizations

## Architecture

The research assistant uses the Entity framework's 6-stage workflow:

1. **INPUT**: Accepts research queries in various formats
2. **PARSE**: Extracts key information and research parameters
3. **THINK**: Plans research strategy and identifies required sources
4. **DO**: Executes searches, fetches papers, analyzes data
5. **REVIEW**: Validates findings and checks citations
6. **OUTPUT**: Generates comprehensive research reports

## Usage

### Basic Research Query
```bash
python research_agent.py "What are the latest advances in quantum computing?"
```

### Research with PDF Analysis
```bash
python research_agent.py --pdf paper.pdf "Summarize and find related work"
```

### Multi-source Research
```bash
python research_agent.py --sources "arxiv,pubmed,web" "COVID-19 vaccine efficacy studies"
```

## Configuration

The agent can be configured via `research_config.yaml`:

```yaml
plugins:
  resources:
    llm:
      type: ollama
      model: "llama3.2:3b"
    memory:
      persistence: true
      vector_search: true

  workflow:
    input:
      - research_assistant.plugins.MultiModalInputPlugin
    parse:
      - research_assistant.plugins.QueryParserPlugin
      - research_assistant.plugins.EntityExtractorPlugin
    think:
      - research_assistant.plugins.ResearchPlannerPlugin
    do:
      - research_assistant.plugins.ArxivSearchPlugin
      - research_assistant.plugins.WebSearchPlugin
      - research_assistant.plugins.PDFAnalyzerPlugin
      - research_assistant.plugins.DataVisualizerPlugin
    review:
      - research_assistant.plugins.FactCheckerPlugin
      - research_assistant.plugins.CitationValidatorPlugin
    output:
      - research_assistant.plugins.ReportGeneratorPlugin
```

## Plugin Details

### MultiModalInputPlugin
Handles various input formats including text queries, URLs, file paths, and structured research requests.

### QueryParserPlugin
Extracts research intent, time ranges, source preferences, and output format requirements.

### ResearchPlannerPlugin
Creates a research strategy based on query complexity, available sources, and time constraints.

### Tool Plugins
- **ArxivSearchPlugin**: Searches and fetches papers from arXiv
- **WebSearchPlugin**: Performs web searches with academic focus
- **PDFAnalyzerPlugin**: Extracts and analyzes content from PDFs
- **DataVisualizerPlugin**: Creates charts and visualizations

### Quality Plugins
- **FactCheckerPlugin**: Validates claims against trusted sources
- **CitationValidatorPlugin**: Ensures proper citation formatting

### ReportGeneratorPlugin
Produces formatted reports in various styles (academic, executive summary, blog post).

## Example Output

```markdown
# Research Report: Advances in Quantum Computing

## Executive Summary
Recent advances in quantum computing have focused on three key areas...

## Key Findings
1. **Error Correction**: New topological approaches show 99.9% fidelity...
2. **Qubit Scaling**: IBM's latest processor achieves 433 qubits...
3. **Applications**: Drug discovery simulations show 1000x speedup...

## Detailed Analysis
[Comprehensive analysis with citations]

## References
1. Zhang et al. (2024). "Topological quantum error correction." Nature Physics.
2. Smith, J. (2024). "Scaling quantum processors beyond 400 qubits." Science.
...
```

## Deployment

### Local Development
```bash
# Install dependencies
poetry install

# Run with default configuration
poetry run python research_agent.py "your query"
```

### Docker Deployment
```bash
# Build image
docker build -t research-assistant .

# Run container
docker run -v $(pwd)/data:/data research-assistant "your query"
```

### Production Deployment
See `terraform/` directory for AWS deployment configuration.

## Testing

Run the test suite:
```bash
poetry run pytest tests/
```

## Extending

To add new research sources:
1. Create a new plugin inheriting from `ToolPlugin`
2. Implement the `_execute_impl` method
3. Add to the `do` stage in configuration
4. Register any required API keys in environment

## Performance

- Handles research sessions up to 10 hours
- Processes up to 1000 papers per query
- Maintains conversation context across multiple queries
- Supports concurrent research tasks for different users
