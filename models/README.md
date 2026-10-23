# Optional local personality profile

Prepared configuration only; no model installed or benchmarked here. Install Ollama from its official site on the chosen laptop and confirm its supported hardware/runtime. Downloading a model needs internet and disk space.

From this repository root, when ready:

```text
ollama pull qwen3.5:2b
ollama create kitty-robot -f models/Modelfile
ollama run kitty-robot
```

This creates a local prompt profile, not fine-tuned weights. The simulator's existing Ollama path supplies its own explicit simulation-system message; use it to preserve truthfulness. The profile is presently for separate conversation testing; a new integration must explicitly load `prompts/kitty-personality.txt` and appropriate current telemetry. Do not claim it is already controlling the physical robot or already integrated into the simulator's personality.

The model configuration is optional: simulator tests and offline commands need no Ollama. No GitHub workflow will download or run these weights. The moving robot must stop correctly even if model/voice services hang or are unavailable.
