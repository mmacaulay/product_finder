#!/bin/bash
set -e

gcloud run jobs execute createsuperuser-job \
  --region="northamerica-northeast2" \
  --update-env-vars="DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME},DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL},DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}"