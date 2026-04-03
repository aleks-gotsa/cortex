# Local GPU Setup Guide (NVIDIA 3060 Ti / WSL2)

Step-by-step guide for running Dynamo workers on a Windows machine with an NVIDIA 3060 Ti (8GB VRAM) using WSL2.

## 1. WSL2 Setup

```powershell
# In Windows PowerShell (Admin)
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
```

Reboot, then open Ubuntu from the Start menu and create your user.

## 2. CUDA Drivers in WSL2

Install the NVIDIA GPU driver **on Windows** (not inside WSL2). WSL2 uses the Windows driver automatically.

Download from: https://www.nvidia.com/Download/index.aspx

Verify inside WSL2:

```bash
nvidia-smi
```

You should see your 3060 Ti with CUDA 12.x.

## 3. Install nvidia-container-toolkit

Inside WSL2 (Ubuntu):

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## 4. Docker Desktop GPU Passthrough

1. Open Docker Desktop on Windows
2. Settings > Resources > WSL Integration > Enable for Ubuntu-22.04
3. Settings > Docker Engine > Ensure `"runtimes"` includes `"nvidia"`
4. Apply & Restart

Verify inside WSL2:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```

## 5. HuggingFace Token + Model Access

1. Create account at https://huggingface.co
2. Generate token at https://huggingface.co/settings/tokens
3. Request access to `meta-llama/Llama-3.1-8B-Instruct` at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

```bash
export HUGGING_FACE_HUB_TOKEN=hf_your_token_here
```

## 6. First Run

```bash
# Start the Dynamo worker
cd /path/to/cortex
HUGGING_FACE_HUB_TOKEN=hf_xxx docker compose -f docker/docker-compose.dynamo-local.yml up

# In another terminal, start Cortex with Dynamo routing
DYNAMO_ENABLED=true DYNAMO_MODE=real uvicorn backend.main:app --reload --port 8000
```

First run will download the model (~5GB). Subsequent starts are fast thanks to the cached volume.

## 7. Health Check

```bash
# Check if the worker is ready
curl http://localhost:8001/health

# Test a completion
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `nvidia-smi` not found in WSL2 | Install GPU driver on Windows, not WSL2 |
| Docker can't see GPU | Restart Docker Desktop, ensure WSL integration is on |
| Out of memory (OOM) | Reduce `GPU_MEMORY_UTILIZATION` to `0.80` in compose file |
| Model download fails | Check `HUGGING_FACE_HUB_TOKEN` and model access approval |
| Port 8001 in use | Change port mapping in compose file |
