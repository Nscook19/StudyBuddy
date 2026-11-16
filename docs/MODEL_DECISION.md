# Model selection

Selected: Qwen3-1.7B Q4_K_M, running locally in llama.cpp. This is an open-weight model; there are no per-request model API charges. CPU/RAM and AWS infrastructure can still incur charges.

The file comes from https://huggingface.co/QuantFactory/Qwen3-1.7B-GGUF and is downloaded during Docker image build. We selected Q4_K_M for modest memory use on a 16 GB development PC.

The API contract stays OpenAI-compatible, so switching models later will only require updating the image/model configuration and testing the new model's behavior.
