# mintmuse-agent/app/generate_image.py

from google import genai
from google.genai import types
from .config import get_env_var

# Load project- och region från .env
PROJECT_ID = get_env_var("GCP_PROJECT_ID")
LOCATION = get_env_var("GCP_LOCATION", default="us-central1")

def generate_image(prompt: str, model: str = "imagen-4.0-generate-001") -> str:
    """
    Generate an image using Vertex AI Imagen model.

    Parameters:
    - prompt: the text prompt to guide the image generation
    - model: Imagen model version; default is "imagen-4.0-generate-001"

    Returns:
    - A URL or base64 string of the generated image
    """

    client = genai.Client()

    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
        ),
    )
    # Take the first generated image
    generated = response.generated_images[0]

    # The SDK returns an object where .image.image_bytes is bytes
    img_bytes = generated.image.image_bytes

    # Convert bytes to base64 or upload to storage & return URL
    # For simplicity we convert to base64 URL
    import base64
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{generated.mime_type};base64,{b64}"
