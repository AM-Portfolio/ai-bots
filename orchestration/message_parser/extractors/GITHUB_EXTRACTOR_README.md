# GitHub Data Extractor

## Overview

The GitHub Data Extractor is a comprehensive module designed to intelligently extract GitHub-related references from user messages. It can identify and parse various forms of GitHub mentions, including URLs, repository references, issue numbers, pull requests, and more.

## Features

### 1. **URL Pattern Extraction**
- **Full GitHub URLs**: `https://github.com/owner/repo/...`
- **SSH URLs**: `git@github.com:owner/repo.git`
- **Clone URLs**: `https://github.com/owner/repo.git`

### 2. **Repository Recognition**
- **Owner/Repository format**: `microsoft/vscode`, `facebook/react`
- **Repository mentions**: "repo named ai-bots", "repository called myproject"
- **Contextual references**: "on github: microsoft/typescript"

### 3. **Issue and Pull Request Detection**
- **Explicit issues**: "issue #123", "see issue #456"
- **Explicit PRs**: "PR #789", "pull request #101"
- **General numbers**: "#42" (with GitHub context)

### 4. **Commit Hash Recognition**
- **Long hashes**: `abc123def456789` (7+ characters)
- **Short hashes**: `abc123d` (when in GitHub context)

### 5. **Keyword-based Context Analysis**
- **Repository indicators**: repo, repository, reponame, github, git, clone, fork, branch, commit, push, pull, merge, checkout, remote, origin
- **Issue indicators**: issue, bug, ticket, problem, feature, enhancement, milestone, label
- **PR indicators**: pr, pull request, merge request, code review, draft, review, approval

## Usage Examples

### Basic Usage
```python
from orchestration.message_parser.extractors import GitHubExtractor

extractor = GitHubExtractor()

# Extract GitHub references
message = "Check the microsoft/vscode repo for issue #123"
references = extractor.extract_github_references(message)

# Analyze GitHub context
context = extractor.analyze_github_context(message)
```

### Integration with Message Parser
```python
from orchestration.message_parser.implementations.parser import MessageParser

parser = MessageParser()
parsed_message = await parser.parse("Clone git@github.com:owner/repo.git and fix issue #42")
```

## Extraction Methods

### 1. **URL-based Extraction** (Confidence: 1.0)
- Direct GitHub URLs (HTTPS/SSH)
- Parsed into components (owner, repo, path, etc.)

### 2. **Pattern-based Extraction** (Confidence: 0.8-0.9)
- `owner/repo` format recognition
- Issue/PR number patterns
- Repository name mentions

### 3. **Context-aware Extraction** (Confidence: 0.6-0.7)
- References detected with GitHub keywords
- Commit hashes in GitHub context
- General number patterns as issues/PRs

## Reference Types

### GitHubURL
```python
Reference(
    type=ReferenceType.GITHUB_URL,
    raw_text="https://github.com/microsoft/vscode",
    normalized_value="microsoft/vscode",
    metadata={
        'owner': 'microsoft',
        'repo': 'vscode',
        'url_type': 'https'
    }
)
```

### GitHub Issue
```python
Reference(
    type=ReferenceType.GITHUB_ISSUE,
    raw_text="issue #123",
    normalized_value="#123",
    metadata={
        'issue_number': '123',
        'extraction_method': 'issue_pattern'
    }
)
```

### GitHub Pull Request
```python
Reference(
    type=ReferenceType.GITHUB_PR,
    raw_text="PR #456",
    normalized_value="PR#456",
    metadata={
        'pr_number': '456',
        'extraction_method': 'pr_pattern'
    }
)
```

## Context Analysis

The extractor provides context analysis to understand the GitHub-related intent of messages:

```python
{
    'has_github_keywords': True,
    'github_keywords_found': ['repo', 'git', 'issue'],
    'likely_github_context': True,
    'context_strength': 0.6
}
```

### Context Strength Levels
- **0.0-0.3**: Low GitHub context (isolated keywords)
- **0.3-0.6**: Moderate GitHub context (multiple keywords)
- **0.6-1.0**: High GitHub context (strong GitHub indicators)

## Advanced Features

### 1. **Deduplication**
- Removes duplicate references
- Preserves highest confidence instances
- Handles overlapping patterns

### 2. **False Positive Reduction**
- Filters out very short names
- Excludes common words
- Validates repository name patterns

### 3. **Comprehensive Metadata**
- Extraction method tracking
- Confidence scoring
- Rich contextual information

## Message Examples and Extractions

| Message | Detected References | Context Strength |
|---------|-------------------|------------------|
| "Check https://github.com/microsoft/vscode" | github_url: microsoft/vscode | 0.6 |
| "Clone git@github.com:owner/repo.git" | github_url: owner/repo | 0.6 |
| "Look at the microsoft/vscode repo" | github_url: microsoft/vscode | 0.2 |
| "See issue #123 for details" | github_issue: #123 | 0.2 |
| "Check PR #456 and issue #789" | github_pr: PR#456, github_issue: #789 | 0.4 |
| "In the ai-bots repository, fix bug in PR #45" | github_url: ai-bots, github_pr: PR#45 | 1.0 |

## Integration Notes

### With Message Parser
The GitHub extractor is automatically integrated into the main `MessageParser` class, providing seamless GitHub reference detection alongside other reference types (Jira, Confluence, etc.).

### With Orchestration Layer
Extracted GitHub references are automatically passed to the context enrichment stage, where they can be used to fetch repository information, issue details, or file contents.

### Error Handling
The extractor gracefully handles:
- Malformed URLs
- Invalid repository names
- Network timeouts (when used with GitHub API)
- Pattern matching edge cases

## Performance Considerations

- **Regex Compilation**: Patterns are compiled once during initialization
- **Memory Usage**: Minimal memory footprint with efficient pattern matching
- **Processing Speed**: Linear time complexity with message length
- **Confidence Scoring**: Dynamic scoring based on extraction method and context

## Future Enhancements

1. **Machine Learning Integration**: Train models on actual GitHub usage patterns
2. **Domain-specific Patterns**: Support for GitHub Enterprise domains
3. **Advanced Context**: Integration with project configuration files
4. **Real-time Validation**: Optional API validation of extracted references