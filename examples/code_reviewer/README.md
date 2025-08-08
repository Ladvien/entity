# Code Review & Refactoring Agent

An intelligent code review assistant that analyzes code quality, identifies issues, and suggests improvements. This example demonstrates the Entity framework's ability to integrate with development tools and provide actionable code insights.

## Features

- **Multi-language support**: Python, JavaScript, TypeScript, Go, Rust, Java
- **Comprehensive analysis**: Code quality, security, performance, best practices
- **Smart refactoring**: Automated suggestions with explanations
- **Tool integration**: Works with Git, GitHub/GitLab, linters, and static analyzers
- **Learning mode**: Adapts to your codebase's style and conventions
- **Actionable feedback**: Provides specific, implementable suggestions

## Architecture

The code reviewer uses the Entity framework's 6-stage workflow:

1. **INPUT**: Accept code files, PRs, or repository URLs
2. **PARSE**: Identify language, extract code structure, detect patterns
3. **THINK**: Analyze code quality, plan review strategy
4. **DO**: Run analysis tools, check security, assess performance
5. **REVIEW**: Validate findings, prioritize issues
6. **OUTPUT**: Generate detailed review with actionable suggestions

## Usage

### Review a Single File
```bash
python code_reviewer.py review file.py
```

### Review a Pull Request
```bash
python code_reviewer.py review --pr https://github.com/user/repo/pull/123
```

### Review Entire Repository
```bash
python code_reviewer.py review --repo https://github.com/user/repo --branch feature
```

### Interactive Refactoring
```bash
python code_reviewer.py refactor file.py --interactive
```

## Configuration

Configure via `reviewer_config.yaml`:

```yaml
plugins:
  resources:
    llm:
      type: vllm
      model: "Qwen/Qwen2.5-7B-Instruct"
      temperature: 0.3  # Lower for more consistent analysis
    
  workflow:
    input:
      - code_reviewer.plugins.CodeInputPlugin
    parse:
      - code_reviewer.plugins.LanguageDetectorPlugin
      - code_reviewer.plugins.ASTParserPlugin
      - code_reviewer.plugins.PatternExtractorPlugin
    think:
      - code_reviewer.plugins.ReviewStrategyPlugin
      - code_reviewer.plugins.IssueClassifierPlugin
    do:
      - code_reviewer.plugins.StaticAnalyzerPlugin
      - code_reviewer.plugins.SecurityScannerPlugin
      - code_reviewer.plugins.PerformanceAnalyzerPlugin
      - code_reviewer.plugins.DependencyCheckerPlugin
      - code_reviewer.plugins.TestCoveragePlugin
    review:
      - code_reviewer.plugins.IssuePrioritizerPlugin
      - code_reviewer.plugins.FalsePositiveFilterPlugin
      - code_reviewer.plugins.RefactoringSuggesterPlugin
    output:
      - code_reviewer.plugins.ReviewFormatterPlugin

# Language-specific configurations
languages:
  python:
    linters: ["pylint", "flake8", "mypy"]
    security_tools: ["bandit", "safety"]
    style_guide: "PEP 8"
  
  javascript:
    linters: ["eslint", "jshint"]
    security_tools: ["npm audit", "snyk"]
    style_guide: "airbnb"
  
  go:
    linters: ["golint", "go vet"]
    security_tools: ["gosec"]
    style_guide: "effective_go"

# Review preferences
review_settings:
  severity_threshold: "info"  # info, warning, error, critical
  max_issues_per_file: 50
  include_positive_feedback: true
  suggest_refactoring: true
  check_documentation: true
  enforce_testing: true
```

## Plugin Details

### CodeInputPlugin
Handles various input formats including local files, Git repositories, and pull requests.

### LanguageDetectorPlugin
Automatically detects programming language and framework from file extensions and content.

### ASTParserPlugin
Builds Abstract Syntax Trees for deep code analysis and pattern recognition.

### ReviewStrategyPlugin
Determines the optimal review approach based on code complexity and type.

### StaticAnalyzerPlugin
Integrates with language-specific static analysis tools for comprehensive checking.

### SecurityScannerPlugin
Identifies security vulnerabilities, hardcoded secrets, and unsafe patterns.

### RefactoringSuggesterPlugin
Generates specific refactoring suggestions with before/after examples.

### ReviewFormatterPlugin
Produces formatted reviews in various styles (GitHub comments, markdown, JSON).

## Example Output

```markdown
# Code Review Report

**File**: `src/utils/auth.py`
**Language**: Python
**Overall Score**: 7.2/10

## Critical Issues (2)

### 1. SQL Injection Vulnerability
**Location**: Line 45
```python
# Current (UNSAFE)
query = f"SELECT * FROM users WHERE id = {user_id}"

# Suggested Fix
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```
**Explanation**: Direct string interpolation in SQL queries can lead to injection attacks.

### 2. Hardcoded Secret
**Location**: Line 12
```python
# Current (UNSAFE)
API_KEY = "sk-1234567890abcdef"

# Suggested Fix
API_KEY = os.environ.get("API_KEY")
```
**Explanation**: Secrets should never be hardcoded. Use environment variables.

## Code Quality Issues (5)

### 1. Function Complexity
**Location**: `authenticate_user()` (Lines 20-85)
**Cyclomatic Complexity**: 12 (threshold: 10)
**Suggestion**: Break down into smaller functions:
- `validate_credentials()`
- `check_permissions()`
- `generate_token()`

### 2. Missing Type Hints
**Location**: Throughout file
**Suggestion**: Add type hints for better code clarity:
```python
def get_user(user_id: int) -> Optional[User]:
    ...
```

## Performance Suggestions (3)

### 1. Inefficient Database Queries
**Location**: Lines 90-95
**Issue**: N+1 query problem
**Suggestion**: Use a single query with JOIN:
```python
# Instead of multiple queries in a loop
users = User.objects.select_related('profile').all()
```

## Positive Feedback
- Good error handling in `verify_token()`
- Comprehensive logging throughout
- Well-structured module organization

## Refactoring Opportunities

1. **Extract Method**: `authenticate_user()` → 3 smaller methods
2. **Replace Magic Numbers**: Define constants for token expiry times
3. **Introduce Parameter Object**: Group related parameters in `UserCredentials`

## Next Steps
1. Fix critical security issues immediately
2. Add comprehensive tests (current coverage: 45%)
3. Update documentation for public methods
4. Consider implementing rate limiting for auth endpoints
```

## Integration Examples

### GitHub Integration
```python
# Automatically review PRs
from entity import Agent

agent = Agent.from_config("reviewer_config.yaml")
agent.review_github_pr(
    owner="myorg",
    repo="myproject", 
    pr_number=123,
    post_comments=True
)
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python code_reviewer.py review --staged --fail-on-critical
```

### CI/CD Pipeline
```yaml
# .github/workflows/code-review.yml
name: Automated Code Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Entity Code Reviewer
        run: |
          python code_reviewer.py review \
            --pr ${{ github.event.pull_request.html_url }} \
            --post-comments
```

## Customization

### Adding Custom Rules
```python
class MyCustomRule(ReviewRule):
    """Check for company-specific patterns."""
    
    def check(self, ast_node):
        # Custom logic here
        if self.violates_rule(ast_node):
            return Issue(
                severity="warning",
                message="Violates company standard X",
                suggestion="Use pattern Y instead"
            )
```

### Training on Your Codebase
```bash
# Learn from existing good code
python code_reviewer.py learn --from ./src --style company-style.json

# Apply learned style to reviews
python code_reviewer.py review file.py --style company-style.json
```

## Performance

- Analyzes ~1000 lines/second
- Supports parallel file processing
- Caches analysis results for faster re-reviews
- Incremental analysis for large codebases

## Best Practices

1. **Start with low severity**: Begin with `info` level to understand all findings
2. **Customize rules**: Adapt rules to your team's coding standards
3. **Regular updates**: Keep analysis tools and security databases current
4. **Team review**: Have team review and agree on automated suggestions
5. **Gradual adoption**: Start with new code, gradually apply to legacy code