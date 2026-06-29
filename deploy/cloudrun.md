# Deploying Paper-to-Deck Architect to Cloud Run

## Prerequisites
- `gcloud` authenticated: `gcloud auth login`
- A GCP project with Cloud Run + Vertex AI APIs enabled
- `GOOGLE_API_KEY` (or Vertex auth) available to the service

## Deploy with the ADK CLI (preferred)
```bash
export GOOGLE_CLOUD_PROJECT=project-7e8ad372-6939-4d8e-be7
export GOOGLE_CLOUD_LOCATION=us-central1

uv run adk deploy cloud_run \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --service_name paper-to-deck \
  --app_name paper_to_deck \
  --with_ui \
  src/paper_to_deck/agents
```

## Deploy with the Dockerfile (fallback)
```bash
gcloud run deploy paper-to-deck \
  --source . \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --allow-unauthenticated \
  --set-env-vars GEMINI_MODEL=gemini-1.5-flash
```

## Verify
- Hit the returned service URL with `--with_ui` to interview the Concierge in-browser.
- Confirm assets land in the container `/tmp/paper_to_deck_sandbox/assets`.
- Note: Cloud Run filesystem is ephemeral. For persistent decks, mount GCS or upload deck.html to a bucket in a later iteration.
