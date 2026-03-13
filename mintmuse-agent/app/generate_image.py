# mintmuse-agent/app/generate_image.py

import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

# Hugging Face Inference API — free with a HF account
# Change HF_MODEL in .env to try different models
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "black-forest-labs/FLUX.1-schnell")
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"

# Max seconds to wait if model is loading (HF cold start)
HF_MAX_WAIT_SEC = int(os.getenv("HF_MAX_WAIT_SEC", "120"))


def generate_image_bytes(prompt: str) -> tuple[bytes, str]:
    """
    Generate an image via the Hugging Face Inference API (free with HF account).

    Parameters:
    - prompt: text prompt guiding the image generation

    Returns:
    - (image_bytes, mime_type)

    Requires HF_TOKEN to be set in .env.
    Raises an exception on failure — caller is responsible for fallback.
    """
    if not HF_TOKEN:
        raise ValueError(
            "HF_TOKEN is missing from .env — create a token at huggingface.co/settings/tokens"
        )

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"inputs": prompt}

    logger.info(f"HuggingFace: generating image with model '{HF_MODEL}'")
    logger.info(f"Prompt: '{prompt[:80]}'")

    waited = 0
    while True:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)

        # 503 = model is loading (cold start) — wait and retry
        if response.status_code == 503 and waited < HF_MAX_WAIT_SEC:
            try:
                wait_hint = response.json().get("estimated_time", 20)
            except Exception:
                wait_hint = 20
            wait_sec = min(float(wait_hint), 30)
            logger.info(f"HuggingFace: model loading, waiting {wait_sec:.0f}s...")
            time.sleep(wait_sec)
            waited += wait_sec
            continue

        response.raise_for_status()
        break

    mime_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    logger.info(f"HuggingFace: done — size={len(response.content)} bytes, mime={mime_type}")

    return response.content, mime_type
