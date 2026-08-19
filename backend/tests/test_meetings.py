import io

from app.schemas.llm_output import ActionItemOut, SummaryOut
from app.services import asr_service, llm_service


def _fake_audio_file() -> tuple[str, io.BytesIO, str]:
    return ("test.wav", io.BytesIO(b"not-real-audio-bytes"), "audio/wav")


def test_upload_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/meetings",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


def test_get_nonexistent_meeting_returns_404(client):
    response = client.get("/api/meetings/does-not-exist")
    assert response.status_code == 404


def test_upload_short_meeting_auto_completes(client, monkeypatch):
    monkeypatch.setattr(
        asr_service, "transcribe_file",
        lambda path, max_attempts=3: {"text": "Sam: I'll send the doc by Friday.", "language": "English"},
    )
    monkeypatch.setattr(
        llm_service, "summarize_transcript",
        lambda text, two_pass: (
            SummaryOut(
                overview="Test overview.",
                key_decisions=["Test decision."],
                action_items=[ActionItemOut(description="Send the doc", owner="Sam", priority="medium")],
            ),
            "v1-single",
        ),
    )

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()}, data={"title": "Standup"})
    assert upload.status_code == 201
    meeting = upload.json()
    assert meeting["requires_chunking"] is False

    # TestClient runs BackgroundTasks synchronously as part of the request,
    # so processing has already finished by the time we get here.
    detail = client.get(f"/api/meetings/{meeting['id']}").json()
    assert detail["status"] == "completed"

    transcript = client.get(f"/api/meetings/{meeting['id']}/transcript").json()
    assert "Sam" in transcript["full_text"]

    summary = client.get(f"/api/meetings/{meeting['id']}/summary").json()
    assert summary["overview"] == "Test overview."
    assert summary["key_decisions"] == ["Test decision."]
    assert len(summary["action_items"]) == 1
    assert summary["action_items"][0]["owner"] == "Sam"


def test_upload_failure_marks_meeting_failed(client, monkeypatch):
    def boom(path, max_attempts=3):
        raise RuntimeError("simulated ASR outage")

    monkeypatch.setattr(asr_service, "transcribe_file", boom)

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()})
    meeting_id = upload.json()["id"]

    detail = client.get(f"/api/meetings/{meeting_id}").json()
    assert detail["status"] == "failed"
    assert "simulated ASR outage" in detail["error_message"]


def test_summary_404_before_processing_completes(client, monkeypatch):
    # Patch transcribe to hang forever is impractical in a sync test; instead
    # just check the 404 contract directly against a meeting with no summary.
    monkeypatch.setattr(
        asr_service, "transcribe_file",
        lambda path, max_attempts=3: {"text": "hello", "language": "English"},
    )

    def boom(text, two_pass):
        raise RuntimeError("simulated LLM outage")

    monkeypatch.setattr(llm_service, "summarize_transcript", boom)

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()})
    meeting_id = upload.json()["id"]

    assert client.get(f"/api/meetings/{meeting_id}/summary").status_code == 404
    detail = client.get(f"/api/meetings/{meeting_id}").json()
    assert detail["status"] == "failed"
    assert "Summarization failed" in detail["error_message"]


def test_confirm_processing_conflict_when_not_pending(client, monkeypatch):
    monkeypatch.setattr(
        asr_service, "transcribe_file",
        lambda path, max_attempts=3: {"text": "hello", "language": "English"},
    )
    monkeypatch.setattr(
        llm_service, "summarize_transcript",
        lambda text, two_pass: (SummaryOut(overview="x", key_decisions=[], action_items=[]), "v1-single"),
    )

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()})
    meeting_id = upload.json()["id"]

    response = client.post(f"/api/meetings/{meeting_id}/confirm-processing")
    assert response.status_code == 409


def test_confirm_processing_404_for_missing_meeting(client):
    response = client.post("/api/meetings/does-not-exist/confirm-processing")
    assert response.status_code == 404


def test_action_item_patch_rejects_invalid_status(client, monkeypatch):
    monkeypatch.setattr(
        asr_service, "transcribe_file",
        lambda path, max_attempts=3: {"text": "hello", "language": "English"},
    )
    monkeypatch.setattr(
        llm_service, "summarize_transcript",
        lambda text, two_pass: (
            SummaryOut(overview="x", key_decisions=[], action_items=[ActionItemOut(description="Do thing")]),
            "v1-single",
        ),
    )

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()})
    meeting_id = upload.json()["id"]
    item_id = client.get(f"/api/meetings/{meeting_id}/summary").json()["action_items"][0]["id"]

    bad = client.patch(f"/api/action-items/{item_id}", json={"status": "bogus"})
    assert bad.status_code == 400

    good = client.patch(f"/api/action-items/{item_id}", json={"status": "done"})
    assert good.status_code == 200
    assert good.json()["status"] == "done"


def test_action_item_patch_404_for_missing_item(client):
    response = client.patch("/api/action-items/does-not-exist", json={"status": "done"})
    assert response.status_code == 404


def test_delete_meeting_removes_it(client, monkeypatch):
    monkeypatch.setattr(
        asr_service, "transcribe_file",
        lambda path, max_attempts=3: {"text": "hello", "language": "English"},
    )
    monkeypatch.setattr(
        llm_service, "summarize_transcript",
        lambda text, two_pass: (SummaryOut(overview="x", key_decisions=[], action_items=[]), "v1-single"),
    )

    upload = client.post("/api/meetings", files={"file": _fake_audio_file()})
    meeting_id = upload.json()["id"]

    delete_response = client.delete(f"/api/meetings/{meeting_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/meetings/{meeting_id}").status_code == 404


def test_delete_nonexistent_meeting_404(client):
    response = client.delete("/api/meetings/does-not-exist")
    assert response.status_code == 404
