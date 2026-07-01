from pathlib import Path


def test_dockerfile_exists_and_sets_sandbox():
    content = Path("deploy/Dockerfile").read_text()
    assert "PAPER_TO_DECK_SANDBOX" in content
    assert "google-adk" in content or "uv pip" in content


def test_cloudrun_doc_has_deploy_command():
    content = Path("deploy/cloudrun.md").read_text()
    assert "gcloud run deploy" in content
    assert "--project" in content and "--region" in content
