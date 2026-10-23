#!/usr/bin/env bash
cd "$(dirname "$0")"
export ROBOT_LLM_PROVIDER=ollama
export ROBOT_OLLAMA_MODEL=qwen2.5:1.5b
python3 main.py
