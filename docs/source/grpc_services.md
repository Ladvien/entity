# gRPC Services

Entity uses gRPC for all backend model communication. The `src/grpc_services`
package contains both the protocol definitions and a working implementation of
``LLMService`` for text generation. The excerpt below shows the protocol used by
this service.

```proto
syntax = "proto3";
package entity.grpc;

service LLMService {
    rpc Generate (GenerateRequest) returns (stream GenerateResponse);
}

message GenerateRequest {
    string prompt = 1;
}

message GenerateResponse {
    string token = 1;
}
```

Generate the Python bindings with `grpcio-tools` and use them with the
``LLMService`` implementation found in ``src/grpc_services/llm_service.py``.
The server leverages ``grpc.aio`` for async handling:

```python
import asyncio
import grpc

from grpc_services import llm_pb2, llm_pb2_grpc
from grpc_services.llm_service import LLMService

async def serve() -> None:
    server = grpc.aio.server()
    llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
```

``src/grpc_services/llm_service.py`` implements a full ``LLMService`` using
``UnifiedLLMResource``. The service streams tokens from any configured model and
can serve as a template for additional gRPC endpoints. It requires the
generated ``llm_pb2`` and ``llm_pb2_grpc`` modules; regenerate them if imports
fail.

### Demo Script

Run the example server implemented with ``LLMGRPCAdapter`` and stream a short
response:

```bash
python examples/servers/grpc_server.py
```

The adapter launches ``LLMService`` locally and prints each token generated for
the sample prompt.

### Regenerating gRPC Code

Regenerate ``llm_pb2.py`` and ``llm_pb2_grpc.py`` whenever ``llm.proto``
changes. Execute the following command from the project root:

```bash
python -m grpc_tools.protoc \
    -I src/grpc_services \
    --python_out=src/grpc_services \
    --grpc_python_out=src/grpc_services \
    src/grpc_services/llm.proto
```
