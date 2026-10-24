# Data and Model Sources

## Benchmark Dataset

| Source | URL | Licence | Notes |
|--------|-----|---------|-------|
| BIRD (BIg Bench for Large-scale Database Grounded Text-to-SQL Evaluation) | https://bird-bench.github.io/ | CC BY 4.0 (benchmark questions); individual database licences vary — see per-database README files inside the archive | Download dev split (~1.5 GB) and test split separately. Do not redistribute databases. |

### Download instructions

1. Register at https://bird-bench.github.io/ and download `dev.zip` and `test.zip`.
2. Extract to `data/bird/`:
   ```
   data/bird/dev.json
   data/bird/dev_databases/<db_id>/<db_id>.sqlite
   data/bird/test.json
   data/bird/test_databases/<db_id>/<db_id>.sqlite
   ```
3. The `data/bird/` tree is gitignored and must not be committed.

## Model

| Model | Parameters | Licence | Inference |
|-------|-----------|---------|-----------|
| Qwen2.5-Coder-7B-Instruct | 7.6 B | Apache 2.0 | Ollama: `ollama pull qwen2.5-coder:7b` |
| Llama-3.1-8B-Instruct (alternative) | 8 B | Meta Llama 3.1 Community Licence | Ollama: `ollama pull llama3.1:8b` |

Both models are well within the 8 B parameter cap. Qwen2.5-Coder is the default because it scores higher on SQL generation benchmarks at this parameter count.

## Inference Backend

| Tool | URL | Licence | Notes |
|------|-----|---------|-------|
| Ollama | https://ollama.com/ | MIT | Default backend; exposes OpenAI-compatible REST |
| vLLM (optional) | https://github.com/vllm-project/vllm | Apache 2.0 | Set `provider: vllm` in config |

## Compliance notes

- No personally identifiable data is collected, stored, or processed.
- Databases from BIRD must be used only for research/benchmark purposes per their original licences.
- This project uses only SELECT queries; no data is written to any database.
