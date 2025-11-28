#!/bin/bash
set -euo pipefail

alembic upgrade head

echo "seed charges"
shark-event seed:charges