#!/bin/bash

curl -X POST http://localhost:8001/system/execute \
-H "Content-Type: application/json" \
-d '{
  "command": "disk",
  "params": []
}'
