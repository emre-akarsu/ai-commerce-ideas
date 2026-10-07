#!/usr/bin/env bash
# Creates ONE Always Free e2-micro VM. Run it yourself from Cloud Shell or a machine with gcloud
# signed in to YOUR project; nothing here is run by the repo's agents. It does not store credentials.
# Free tier (check https://cloud.google.com/free/docs/free-cloud-features#compute before relying on it):
# one non-preemptible e2-micro per month in us-west1, us-central1 or us-east1, 30 GB-months of
# standard persistent disk, 1 GB/month egress from North America. Anything beyond that is billed:
# an external IPv4 address, a bigger disk, SSD disks, snapshots over the allowance, more egress.
set -euo pipefail
: "${PROJECT:?set PROJECT to your GCP project id}"
ZONE="${ZONE:-us-central1-a}"          # must be in us-west1, us-central1 or us-east1
NAME="${NAME:-rfq-free}"
case "$ZONE" in us-west1-*|us-central1-*|us-east1-*) ;; *) echo "zone $ZONE is not in a free-tier region" >&2; exit 1;; esac
gcloud compute instances create "$NAME" \
  --project "$PROJECT" --zone "$ZONE" \
  --machine-type e2-micro \
  --provisioning-model STANDARD \
  --image-family debian-12 --image-project debian-cloud \
  --boot-disk-size 30GB --boot-disk-type pd-standard \
  --tags http-server,https-server \
  --metadata-from-file startup-script="$(dirname "$0")/bootstrap.sh"
echo "Open ports 80/443 only if you will serve publicly (see README). Never open 8000 or 5432."
