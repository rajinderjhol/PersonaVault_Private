#!/bin/bash
# PersonaVault Cloud Shell Environment Restore
# Run: chmod +x cloud_setup.sh && ./cloud_setup.sh

echo ">>> Installing zstd and Ollama..."
sudo apt-get update && sudo apt-get install -y zstd
curl -fsSL https://ollama.com/install.sh | sh

echo ">>> Starting Ollama in background (logging to ollama.log)..."
nohup ollama serve > ollama.log 2>&1 &

echo ">>> Pulling tinydolphin..."
sleep 5 # Wait for server to initialize
ollama pull tinydolphin
echo ">>> Environment Ready."