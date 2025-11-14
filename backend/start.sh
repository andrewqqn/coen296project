#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="./firebase-key.json"
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
