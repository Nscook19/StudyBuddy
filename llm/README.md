# LLM service — Milestone 2

Runs **Qwen3-1.7B Q4_K_M** using llama.cpp in a private Compose service.
The GGUF model is approximately 1.28 GB and is downloaded at Docker build time.

- Model weights: https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF
- Upstream model: https://huggingface.co/Qwen/Qwen3-1.7B
- Internal server: `http://llm:8000`
- Endpoints: `GET /health`, `POST /v1/chat/completions`
- Port 8000 is not published to the host; requests go through the FastAPI backend.
- Thinking is disabled for faster, short responses during connectivity tests.

This milestone demonstrates a model connection; flashcard generation comes later.
