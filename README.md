<<<<<<< HEAD
# Capstone Protect Starter Repo

This is a starter repository for the Capstone Project.
Organize your code as per this starter repo structure.

Follow `run_instructions.md` to start the example service.

Add and run your own Red Team tests and gather evidence.
- Review and extend default tests in demo.py 
- Review and extend Red-Team tests in main.py
=======
# Cloud Run Expense Back
```
pip freeze > requirements.txt
```

```
gcloud builds submit --tag gcr.io/expensense-8110a/expense-back
```

```
gcloud run deploy expense-back \
  --image gcr.io/expensense-8110a/expense-back \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --service-account expense-back-sa@expensense-8110a.iam.gserviceaccount.com \
  --set-env-vars GCLOUD_PROJECT=expensense-8110a,STORAGE_BUCKET=expensense-8110a.firebasestorage.app \
  --set-secrets FIREBASE_API_KEY=FIREBASE_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest
```
>>>>>>> frontend
