#!/usr/bin/env bash
# Copy-paste these curl requests for http://localhost:8000
# If BEDROCK_ENDPOINT_API_KEY is set, pass: -H "Authorization: Bearer <your-key>" or -H "X-API-Key: <your-key>"

# ─── List models ─────────────────────────────────────────────────────────────
curl -s http://localhost:8000/v1/models -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" | python3 -m json.tool

# ─── Basic chat (non-streaming) ──────────────────────────────────────────────
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-micro","messages":[{"role":"user","content":"What is 2 + 2?"}]}' | python3 -m json.tool

# ─── Streaming ───────────────────────────────────────────────────────────────
curl -N -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-micro","stream":true,"messages":[{"role":"user","content":"Count to 5."}]}'

# ─── Multi-turn ──────────────────────────────────────────────────────────────
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-lite","messages":[{"role":"user","content":"My name is Alice."},{"role":"assistant","content":"Nice to meet you!"},{"role":"user","content":"What is my name?"}]}' | python3 -m json.tool

# ─── System prompt ───────────────────────────────────────────────────────────
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-pro","messages":[{"role":"system","content":"You are a pirate."},{"role":"user","content":"What is the weather?"}]}' | python3 -m json.tool

# ─── Different model (nova-lite) ──────────────────────────────────────────────
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-lite","messages":[{"role":"user","content":"Say hi."}]}' | python3 -m json.tool

# ─── Invalid model (expect 400) ────────────────────────────────────────────────
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-99","messages":[{"role":"user","content":"hi"}]}' | python3 -m json.tool

# Copy-paste these curl requests for https://models.neurofx.co/api
# If BEDROCK_ENDPOINT_API_KEY is set, pass: -H "Authorization: Bearer <your-key>" or -H "X-API-Key: <your-key>"

# ─── List models ─────────────────────────────────────────────────────────────
curl -s https://models.neurofx.co/api/v1/models -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" | python3 -m json.tool

# ─── Basic chat (non-streaming) ──────────────────────────────────────────────
curl -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-micro","messages":[{"role":"user","content":"What is 2 + 2?"}]}' | python3 -m json.tool

# ─── Streaming ───────────────────────────────────────────────────────────────
curl -N -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-micro","stream":true,"messages":[{"role":"user","content":"Count to 5."}]}'

# ─── Multi-turn ──────────────────────────────────────────────────────────────
curl -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-lite","messages":[{"role":"user","content":"My name is Alice."},{"role":"assistant","content":"Nice to meet you!"},{"role":"user","content":"What is my name?"}]}' | python3 -m json.tool

# ─── System prompt ───────────────────────────────────────────────────────────
curl -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-pro","messages":[{"role":"system","content":"You are a pirate."},{"role":"user","content":"What is the weather?"}]}' | python3 -m json.tool

# ─── Different model (nova-lite) ──────────────────────────────────────────────
curl -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"nova-lite","messages":[{"role":"user","content":"Say hi."}]}' | python3 -m json.tool

# ─── Invalid model (expect 400) ────────────────────────────────────────────────
curl -s -X POST https://models.neurofx.co/api/v1/chat/completions \
  -H "Authorization: Bearer sk-bedrock-1234-ABSKQmVkcm9ja0FQSUtleS01M2dsLWF0L" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-99","messages":[{"role":"user","content":"hi"}]}' | python3 -m json.tool