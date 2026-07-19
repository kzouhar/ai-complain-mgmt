#!/bin/bash
set -e

WEBHOOK_ZIP="lambda_function.zip"
TRANSCRIBE_ZIP="transcribe.zip"

log(){ echo; echo "==== $1 ===="; }

log "Building webhook Lambda"
rm -f "$WEBHOOK_ZIP"
zip -j "$WEBHOOK_ZIP" ../lambda/lambda_function.py

log "Building transcribe Lambda"
rm -rf package
mkdir package
cp ../lambda/transcribe.py package
(cd package && zip -r ../"$TRANSCRIBE_ZIP" .)

echo "Build complete."
