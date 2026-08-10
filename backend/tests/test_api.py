from __future__ import annotations

import json

CONTENT = """AtlasAI is a knowledge assistant.

It answers questions using only the content of uploaded documents.

Every answer cites the chunks it was grounded on, shown as [1], [2] and so on.
"""


def _events(text: str) -> list[dict]:
    return [json.loads(line[len("data: ") :]) for line in text.splitlines() if line.strip()]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "documents" in body


def test_upload_list_and_delete_document(client):
    # upload
    r = client.post(
        "/api/documents/upload",
        files={"file": ("guide.txt", CONTENT.encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 201
    doc = r.json()
    assert doc["status"] == "ready"
    assert doc["chunk_count"] >= 1
    doc_id = doc["id"]

    # list
    listing = client.get("/api/documents").json()
    assert listing["total"] == 1
    assert listing["documents"][0]["id"] == doc_id

    # delete
    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.get("/api/documents").json()["total"] == 0


def test_upload_unsupported_type(client):
    r = client.post(
        "/api/documents/upload",
        files={"file": ("bad.exe", b"MZ...", "application/octet-stream")},
    )
    assert r.status_code == 422


def test_chat_streams_answer_and_citations(client):
    client.post(
        "/api/documents/upload",
        files={"file": ("guide.txt", CONTENT.encode("utf-8"), "text/plain")},
    )

    with client.stream(
        "POST",
        "/api/chat",
        json={"question": "What is AtlasAI?"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    events = _events(body)
    types = [e["type"] for e in events]
    assert "meta" in types and "token" in types and "done" in types

    meta = next(e for e in events if e["type"] == "meta")
    assert meta["session_id"]
    assert len(meta["citations"]) > 0

    tokens = "".join(e["content"] for e in events if e["type"] == "token")
    assert "grounded answer" in tokens

    # session + messages persisted
    sessions = client.get("/api/sessions").json()
    assert any(s["id"] == meta["session_id"] for s in sessions)

    messages = client.get(f"/api/sessions/{meta['session_id']}/messages").json()
    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant"]
    assert messages[-1]["sources"], "assistant message should carry citations"
