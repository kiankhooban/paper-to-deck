# Deploying Paper-to-Deck Architect to Cloud Run

## Prerequisites
- `gcloud` authenticated: `gcloud auth login` and `gcloud auth application-default login`
- A GCP project with Cloud Run + Cloud Build + Vertex AI APIs enabled
- Auth is **Vertex AI + ADC**. There is NO api key and no Secret Manager secret for one.

## Deploy with the ADK CLI (authenticated only)
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
# When prompted "Allow unauthenticated invocations", answer N (no public access).
```

## Set the runtime env on the service (Vertex, no key)
```bash
gcloud run services update paper-to-deck \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --no-allow-unauthenticated \
  --update-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT",GOOGLE_CLOUD_LOCATION="$GOOGLE_CLOUD_LOCATION",GEMINI_MODEL=gemini-2.5-flash
```

## Least privilege
Grant the service's runtime service account only `roles/aiplatform.user`. Do not use a key, do not grant owner.

## Verify
- The service must require auth: an unauthenticated curl returns 403. Reach it as yourself with an identity token.
- Confirm assets land in the container `/tmp/paper_to_deck_sandbox/assets`.
- Cloud Run filesystem is ephemeral. For persistent decks, upload deck.html to a GCS bucket in a later iteration.

## Post-demo teardown
```bash
gcloud run services delete paper-to-deck --region "$GOOGLE_CLOUD_LOCATION"
```
