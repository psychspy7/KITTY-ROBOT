# Open model recommendation — researched23October2026

## Starting choice

**Qwen3.5-2B through Ollama** is the starting recommendation for local conversation and occasional scene questions, not a claim of being universally best. Official model card: https://huggingface.co/Qwen/Qwen3.5-2B . Ollama package: https://ollama.com/library/qwen3.5:2b . Its displayed package size is about3.1GB at review time; download size is not runtime RAM/VRAM. Use the Acer RTX4050 laptop after measuring actual VRAM/systemRAM and available memory. This computer has not benchmarked that Acer.

Begin with short context (e.g.4096), concise output and non-thinking responses; verify runtime support via Ollama `/api/show`. Enable/disable thinking using the chat API's supported `think` values. No fine-tuning or training from scratch is needed for initial personality. The included Modelfile is a prompt profile, not trained weights. A4B variant may improve answers but must beat2B on actual response delay, useful response rate and memory while perception is running; https://ollama.com/library/qwen3.5:4b lists about4.0GB download, not a promise it fits all remaining resources.

## Fast perception is separate

Benchmark a small detector such as **YOLO26n**, with YOLO11n as a documented fallback. Official docs https://docs.ultralytics.com/models/yolo26/ and https://docs.ultralytics.com/models/yolo11/ provide pretrained supported-class models. Begin with one known class in a marked demo zone. This is an unbenchmarked integration recommendation; no detector is installed in this repository. Upstream Ultralytics models/software have AGPL-3.0/Enterprise terms; preserve terms and decide repository licensing before public redistribution. A visual-language response is not a calibrated distance/pose estimate or guaranteed obstacle map.

## Learned robot-action policies

LeRobot/SmolVLA is real open robotics work (https://huggingface.co/lerobot/smolvla_base), but its documented pipelines depend on compatible robot/state/action datasets and task-specific adaptation. It is not a ready-trained ESP32 rover navigation policy. Do not adopt an arm checkpoint as a wheel controller or train 'walking' for this wheeled robot under the deadline. First implement perception, bounded target steering, local stopping and measured floor tests. Navigation tuning means calibrating this drivetrain/controller, not teaching an LLM to issue unrestricted motor commands.

## Acceptance before naming a final model

Measure cold/warm startup, p50/p95 reply latency across20short prompts, peakRAM/VRAM, target detector throughput and frame age concurrently, command/status truthfulness, behavior during dropped frames and loss of model service. No target frame rate or reply latency has yet been demonstrated. Keep language-model work off the critical motor-stop path. Voice/STT/TTS are separate tasks to test; model text capability alone does not supply voice.

Sources are primary model cards/runtime documentation, not a YouTube performance claim. Qwen artifacts/Ollama listing show Apache2.0 terms; retain upstream licenses. No paid API requests or model downloads were performed during this preparation.
