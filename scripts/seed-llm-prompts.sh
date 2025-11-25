#!/bin/bash
set -e

gcloud run jobs execute seed-llm-prompts --region="us-east1"