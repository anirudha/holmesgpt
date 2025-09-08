import importlib.util
import pathlib

from fastapi.testclient import TestClient


def load_app():
    module_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "examples"
        / "ag_ui"
        / "test_server.py"
    )
    spec = importlib.util.spec_from_file_location("agui_test_server", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module.app


def test_stream_emits_expected_events():
    app = load_app()
    client = TestClient(app)
    with client.stream("GET", "/agui/chat") as response:
        body = b"".join(response.iter_raw())
    payload = body.decode()
    assert "event: text" in payload
    assert "event: thinking" in payload
    assert "event: tool-call" in payload
    assert "event: state_snapshot" in payload
