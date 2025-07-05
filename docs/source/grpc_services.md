# gRPC Service Stubs

Entity uses gRPC for all backend model communication. The `src/grpc_services`
package contains protocol definitions and stub implementations. Below is a
minimal example for text generation services.

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

Generate the Python bindings with `grpcio-tools` and implement the server using
`grpc.aio`:

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

``src/grpc_services/llm.proto`` and ``llm_service.py`` act as references for
future model services.

### Demo Script

Run the example server implemented with ``LLMGRPCAdapter`` and stream a short
response:

```bash
python examples/servers/grpc_server.py
```

The adapter launches ``LLMService`` locally and prints each token generated for
the sample prompt.
