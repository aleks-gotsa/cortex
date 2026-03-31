# Cortex — README Fix Prompt

Three targeted changes to README.md only. Do not touch any other file.

## 1. Add badges after the # Cortex heading

Insert these three lines immediately after the `# Cortex` heading:

```markdown
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Model](https://img.shields.io/badge/model-Claude%20Sonnet-orange)
```

## 2. Replace the comparison table

Replace the existing "What Makes It Different" comparison table with this:

| Feature | Standard AI Search | Cortex |
|---------|-------------------|--------|
| Search depth | Single pass | Up to 3 iterative passes |
| Gap detection | No | Automatic coverage scoring + targeted follow-up |
| Claim verification | No | Every citation checked against its source |
| Memory | No | Qdrant vector DB recalls prior research |
| Cost control | Opaque | Model routing: Haiku for planning, Sonnet for synthesis |
| Source transparency | Partial | Full inline citations with verification verdicts |
| Self-hosted | No | Yes, fully open-source |

## 3. Fix component names in Project Structure

In the Project Structure section, update the frontend/components/ file list:
- ResearchInput.tsx → SearchInput.tsx
- ProgressStream.tsx → PipelineProgress.tsx
- DocumentView.tsx → ResearchDocument.tsx

Also add cli/ to the top-level structure after backend/:
```
├── cli/
│   ├── cortex_cli.py        # CLI entrypoint, REPL, commands
│   ├── connection.py        # SSE stream client
│   ├── progress.py          # Live stage progress display
│   ├── output.py            # File saving and stats footer
│   └── renderer.py          # Terminal markdown renderer
```
