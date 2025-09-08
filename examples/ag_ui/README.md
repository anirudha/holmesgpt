# AG-UI Test Example

This directory contains a minimal server and browser client for exercising the AG-UI streaming protocol.

## Running

1. Start the server:

   ```bash
   pip install sse-starlette  # one-time dependency for EventSourceResponse
   poetry run python examples/ag_ui/test_server.py
   ```

   The server listens on <http://localhost:8000> and exposes `/agui/chat`.

2. Open `examples/ag_ui/test_client.html` in a web browser. The browser console will show the streamed events.
