#!/bin/bash

./build.sh
export VERIFY_TOKEN="khalil"
export WHATSAPP_ACCESS_TOKEN=XXXX"
export OPENAI_API_KEY="XXXX"
./deploy.sh
./test.sh