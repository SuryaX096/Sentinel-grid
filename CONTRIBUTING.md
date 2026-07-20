# Contributing to SentinelMind AI

Thank you for your interest in contributing to the SentinelMind AI Agentic Cyber Resilience Platform! To ensure code quality, security, and maintainability, please adhere to the following guidelines.

## Code of Conduct
- Be respectful, professional, and collaborative.
- Maintain strict focus on cybersecurity engineering best practices.

## Coding Style
- **Formatting:** Adhere to PEP 8 standards for Python code formatting.
- **Imports:** Maintain clean absolute import paths starting with `src.`. Do not introduce circular dependencies.
- **Type Hints:** Use descriptive Python type hints for all function signatures and parameters.
- **Security:** Do not commit hardcoded API keys or credentials. Verify that all inputs to critical endpoints are sanitized.

## Development Workflow
1. Fork the repository and create a new branch (`feature/your-feature-name` or `bugfix/issue-description`).
2. Make targeted, incremental changes. Do not bundle unrelated changes in a single commit.
3. Ensure no deprecated features (e.g. `@app.on_event` or Pydantic `.dict()`) are introduced.
4. Run validation checks and automated tests:
   ```bash
   python -m unittest tests/test_pipeline.py
   ```

## Pull Request Guidelines
- Document your changes clearly in the PR description.
- Provide step-by-step verification commands used to validate your changes.
- Ensure all automated checks pass before requesting review.
