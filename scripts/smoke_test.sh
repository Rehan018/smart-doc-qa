#!/usr/bin/env bash
set -e

echo "Checking health..."
if command -v jq >/dev/null 2>&1; then
  curl -s http://localhost:8000/api/v1/health/ | jq
else
  curl -s http://localhost:8000/api/v1/health/
  echo
fi

echo "Upload sample document manually with:"
echo 'curl -X POST "http://localhost:8000/api/v1/documents/upload" -F "file=@sample_docs/employee_policy.docx"'
