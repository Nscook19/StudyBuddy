FROM ghcr.io/ggml-org/llama.cpp:server

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Download the Qwen3-1.7B Q4_K_M GGUF model at build time, not each startup.
RUN mkdir -p /models && curl -fL -o /models/model.gguf \
    https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B.Q4_K_M.gguf

RUN useradd --create-home llm && chmod 644 /models/model.gguf
USER llm

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=10 --start-period=100s \
    CMD curl -f http://localhost:8000/health || exit 1

# Base image already uses llama-server as its entrypoint.
CMD ["-m", "/models/model.gguf", "--host", "0.0.0.0", "--port", "8000", "--reasoning", "off"]
