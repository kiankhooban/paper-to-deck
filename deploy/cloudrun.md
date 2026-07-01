# Deploying Paper-to-Deck Architect to Cloud Run

## Prerequisites
- `gcloud` CLI installed and authenticated:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```
- A Google Cloud project with the **Cloud Run**, **Cloud Build**, and **Vertex AI** APIs enabled.
- Authentication is strictly **Vertex AI + Application Default Credentials (ADC)**. There are NO API keys and NO Secret Manager secrets used.

## Deploying the Service
Execute the following command from the root of the repository to build and deploy the container. 
The `--no-allow-unauthenticated` flag is strictly required to prevent runaway billing from public internet access.

```bash
gcloud run deploy paper-to-deck \
  --source . \
  --region us-central1 \
  --project your-project-id \
  --no-allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```

## Least Privilege
Ensure that the runtime service account assigned to this Cloud Run service is granted **only** the `roles/aiplatform.user` IAM role. Do not use API keys and do not grant Owner/Editor roles.

## Verify Deployment
- **Security Check:** Try visiting the service URL in an incognito window. An unauthenticated request must return a `403 Forbidden` error.
- **Accessing the Service:** To reach the service securely, append an identity token to your request, or use the Google Cloud Console's Cloud Run testing proxy.

## Post-Demo Teardown
To immediately stop any potential billing after your presentation or testing, delete the service:

```bash
gcloud run services delete paper-to-deck --region us-central1 --project your-project-id
```
