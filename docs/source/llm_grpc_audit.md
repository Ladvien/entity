# LLM gRPC Audit

The architecture requires backend models to expose gRPC streaming endpoints. The `LLMService` in `src/grpc_services/llm_service.py` wraps `UnifiedLLMResource` and is served by `LLMGRPCAdapter`.

The providers found in `src/plugins/builtin/resources/llm/providers/` rely on HTTP or SDK calls:

- `OpenAIProvider`, `GeminiProvider`, `ClaudeProvider`, and `OllamaProvider` use `HttpLLMResource` for REST requests.
- `BedrockProvider` uses `aioboto3` to invoke AWS Bedrock.
- `EchoProvider` simply echoes the prompt.

None of these providers expose gRPC directly. They are wrapped by `LLMService` when gRPC access is required.

## Recommendations

- Implement gRPC wrappers for each provider to allow direct gRPC consumption.
- Alternatively, extend the provider interface with optional gRPC client methods so `LLMService` can delegate to them when available.
