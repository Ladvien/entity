FROM ollama/ollama:latest

ENV OLLAMA_MODEL=llama3:8b-instruct-q6_K \
    OLLAMA_HOST=0.0.0.0

EXPOSE 11434

ENTRYPOINT ["bash", "-c", "ollama serve & sleep 3 && ollama pull ${OLLAMA_MODEL} || true && wait"]
