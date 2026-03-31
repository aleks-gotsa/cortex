# Cortex — CLI Fix Prompt

Five fixes and one README addition. Do not change anything else.

## 1. cli/cortex_cli.py — fix hardcoded strings in print_header()

- `"serper + brave"` → `"serper + tavily"`
- `"mistral-small (plan) · sonnet (synth/verify)"` → `"haiku (plan) · sonnet (synth/verify)"`
- `"localhost:8000"` in the status line → replace with the actual `BACKEND_URL` variable so it reflects the real backend address

## 2. cli/progress.py — remove dead import

Remove this unused import:
```python
from rich.spinner import Spinner
```

## 3. README.md — add CLI section after the existing curl section

```markdown
## CLI

Run research from your terminal:

```bash
pip install -e .
cortex "What is retrieval-augmented generation?"
cortex --depth deep "How do transformers work?"
cortex history
cortex view <research_id>
```

Or launch the interactive REPL:

```bash
cortex
```
```
