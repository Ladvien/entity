# Entity Framework Examples

This directory contains comprehensive examples demonstrating the versatility and power of the Entity Framework for building AI agents. Each example showcases different aspects of the framework's capabilities and includes complete implementations with configurations, plugins, and deployment guides.

## 🚀 Featured Examples

### 1. [Multi-Modal Research Assistant](./research_assistant/)
**A comprehensive research agent that analyzes various data sources and produces detailed reports.**

- 📊 Multi-modal input (text, PDFs, URLs, images)
- 🔍 Intelligent source aggregation (arXiv, web, Semantic Scholar)
- 📈 Data visualization and citation networks
- ✅ Fact-checking and quality assurance
- 📝 Multiple output formats (academic, executive, blog)

**Use Cases**: Academic research, market analysis, competitive intelligence, literature reviews

### 2. [Code Review & Refactoring Agent](./code_reviewer/)
**An intelligent code assistant that reviews, analyzes, and suggests improvements.**

- 🔧 Multi-language support (Python, JS, Go, Rust, etc.)
- 🛡️ Security vulnerability detection
- ⚡ Performance analysis and optimization
- 🔄 Automated refactoring suggestions
- 🔌 Git/GitHub/GitLab integration

**Use Cases**: PR reviews, code quality gates, legacy code modernization, security audits

### 3. [Customer Support Agent](./customer_support/) *(Coming Soon)*
**A smart support agent with context awareness and escalation capabilities.**

- 💬 Multi-channel support (email, chat, voice)
- 🎯 Intent recognition and sentiment analysis
- 📊 Knowledge base integration
- 🔀 Intelligent routing and escalation
- 📈 Analytics and insights

**Use Cases**: Help desk automation, FAQ handling, ticket triage, customer satisfaction

### 4. [Data Pipeline & ETL Agent](./data_pipeline/) *(Coming Soon)*
**An intelligent data processing agent for ETL workflows.**

- 🔄 Auto-detection of data formats and schemas
- 🔧 Smart transformation and validation
- 🚨 Error handling and recovery
- 📊 Data quality monitoring
- 🔌 Multi-source/target support

**Use Cases**: Data migration, real-time processing, data warehouse loading, API integration

### 5. [Interactive Learning Tutor](./learning_tutor/) *(Coming Soon)*
**An adaptive educational agent that personalizes learning experiences.**

- 📚 Subject-specific expertise
- 🧠 Learning style adaptation
- 📝 Practice problem generation
- 📊 Progress tracking
- 🎯 Personalized feedback

**Use Cases**: Online education, corporate training, skill assessment, homework help

### 6. [DevOps Automation Agent](./devops_agent/) *(Coming Soon)*
**Infrastructure management and deployment automation.**

- 🚀 CI/CD pipeline orchestration
- 🛠️ Infrastructure as Code management
- 📊 Monitoring and alerting
- 🔧 Auto-remediation
- 📈 Performance optimization

**Use Cases**: Deployment automation, incident response, capacity planning, cost optimization

### 7. [Content Creation Pipeline](./content_creator/) *(Coming Soon)*
**Creative content generation with multiple personalities.**

- ✍️ Multi-format content (articles, stories, scripts)
- 🎨 Style and tone adaptation
- 🖼️ Multimedia integration
- 📝 SEO optimization
- 🔄 Content variations

**Use Cases**: Blog writing, marketing content, social media, creative writing

### 8. [Financial Analysis Agent](./financial_analyst/) *(Coming Soon)*
**Market analysis and financial insights generation.**

- 📈 Real-time market data analysis
- 📊 Technical indicator calculation
- 🔍 Fundamental analysis
- 📝 Report generation
- ⚠️ Risk assessment

**Use Cases**: Investment research, portfolio analysis, risk management, financial reporting

### 9. [Workflow Orchestration Agent](./workflow_orchestrator/) *(Coming Soon)*
**Meta-agent for creating and managing other agents.**

- 🔧 Dynamic agent creation
- 🔄 Workflow design and execution
- 📊 Performance monitoring
- 🚦 Resource management
- 🔌 Integration orchestration

**Use Cases**: Business process automation, complex workflow management, agent coordination

### 10. [Security Analysis Agent](./security_analyzer/) *(Coming Soon)*
**Defensive security assessment and vulnerability detection.**

- 🛡️ Vulnerability scanning
- 🔍 Configuration analysis
- 📊 Compliance checking
- 📝 Security reporting
- 🔧 Remediation guidance

**Use Cases**: Security audits, compliance verification, penetration testing, risk assessment

## 🏗️ Framework Architecture

Each example demonstrates key Entity Framework concepts:

### 6-Stage Workflow
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```

### 4-Layer Resource System
```
Infrastructure → Resources → Canonical Resources → Plugins
```

### Core Resources
- **LLM**: Language model for reasoning
- **Memory**: Persistent state management
- **FileStorage**: File and object storage
- **Logging**: Rich-based structured logging

## 🚀 Getting Started

### Prerequisites
```bash
# Install Entity Framework
pip install entity-framework

# Or use Poetry
poetry add entity-framework
```

### Running Examples

1. **Choose an example**:
```bash
cd examples/research_assistant
```

2. **Install dependencies**:
```bash
poetry install
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Run the agent**:
```bash
python research_agent.py "Your query here"
```

## 📚 Learning Path

### For Beginners
1. Start with **[default_agent.py](./default_agent.py)** - Simplest example
2. Try **Customer Support Agent** - Clear workflow stages
3. Explore **Learning Tutor** - User interaction patterns

### For Developers  
1. Study **Code Review Agent** - Tool integration
2. Examine **Data Pipeline** - Error handling
3. Build with **DevOps Agent** - Infrastructure patterns

### For Advanced Users
1. Master **Research Assistant** - Complex orchestration
2. Analyze **Financial Agent** - Real-time processing
3. Create with **Workflow Orchestrator** - Meta-programming

## 🛠️ Common Patterns

### Plugin Development
```python
class MyPlugin(PromptPlugin):
    supported_stages = [WorkflowExecutor.THINK]
    
    async def _execute_impl(self, context):
        # Your logic here
        llm = context.get_resource("llm")
        result = await llm.generate("Your prompt")
        await context.remember("key", result)
```

### Workflow Configuration
```yaml
workflow:
  input:
    - my_agent.plugins.InputPlugin
  think:
    - my_agent.plugins.AnalysisPlugin
  output:
    - my_agent.plugins.ResponsePlugin
```

### Resource Customization
```python
from entity import Agent
from entity.resources import Memory, LLM

# Custom configuration
agent = Agent(
    resources={
        "memory": Memory(...),
        "llm": LLM(...),
    },
    workflow=my_workflow
)
```

## 📊 Performance Tips

1. **Use appropriate LLM models**: Smaller for speed, larger for quality
2. **Enable caching**: Reduce redundant API calls
3. **Parallelize tools**: Execute independent operations concurrently
4. **Optimize prompts**: Concise, specific instructions
5. **Monitor resources**: Track memory and API usage

## 🤝 Contributing

We welcome contributions! To add a new example:

1. Create a directory: `examples/your_agent/`
2. Include:
   - `README.md` - Comprehensive documentation
   - `your_agent.py` - Main implementation
   - `config.yaml` - Configuration file
   - `your_agent/plugins/` - Custom plugins
   - `tests/` - Test cases
3. Follow the existing examples' structure
4. Submit a pull request

## 📄 License

All examples are provided under the same license as the Entity Framework. See the main project LICENSE file for details.

## 🔗 Resources

- [Entity Framework Documentation](https://docs.entity-framework.ai)
- [Plugin Development Guide](https://docs.entity-framework.ai/plugins)
- [Deployment Guide](https://docs.entity-framework.ai/deployment)
- [API Reference](https://docs.entity-framework.ai/api)

## 💡 Need Help?

- 📧 Email: support@entity-framework.ai
- 💬 Discord: [Join our community](https://discord.gg/entity-framework)
- 🐛 Issues: [GitHub Issues](https://github.com/entity-framework/entity/issues)

---

**Start building powerful AI agents today with the Entity Framework!** 🚀