from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def _load_request(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"inputPath", "outputDirectory", "styleId", "prompt"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Missing required request fields: {', '.join(missing)}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="ARTIFEX Qwen Image Edit style runner")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument(
        "--model",
        default=os.getenv("ARTIFEX_QWEN_IMAGE_EDIT_MODEL", "Qwen/Qwen-Image-Edit-2509"),
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=int(os.getenv("ARTIFEX_QWEN_IMAGE_EDIT_STEPS", "30")),
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=float(os.getenv("ARTIFEX_QWEN_IMAGE_EDIT_GUIDANCE_SCALE", "4.0")),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.getenv("ARTIFEX_QWEN_IMAGE_EDIT_SEED", "42")),
    )
    parser.add_argument(
        "--cpu-offload",
        action="store_true",
        default=os.getenv("ARTIFEX_QWEN_IMAGE_EDIT_CPU_OFFLOAD", "0") == "1",
    )
    args = parser.parse_args()

    request = _load_request(args.request)
    input_path = Path(str(request["inputPath"])).resolve()
    output_dir = Path(str(request["outputDirectory"])).resolve()
    prompt = str(request["prompt"])
    negative_prompt = str(request.get("negativePrompt", ""))
    style_id = str(request["styleId"])

    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from diffusers import QwenImageEditPipeline
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Qwen style runner dependencies are missing. Install torch, diffusers, transformers, "
            "accelerate, safetensors and Pillow in the style-runner environment."
        ) from exc

    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    pipeline = QwenImageEditPipeline.from_pretrained(args.model, torch_dtype=dtype)

    if torch.cuda.is_available():
        if args.cpu_offload:
            pipeline.enable_model_cpu_offload()
        else:
            pipeline.to("cuda")
    else:
        pipeline.to("cpu")

    source = Image.open(input_path).convert("RGB")
    generator_device = "cuda" if torch.cuda.is_available() and not args.cpu_offload else "cpu"
    generator = torch.Generator(device=generator_device).manual_seed(args.seed)

    result = pipeline(
        image=source,
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance_scale,
        generator=generator,
    )
    if not result.images:
        raise RuntimeError("Qwen Image Edit returned no images")

    image_path = output_dir / "styled.png"
    result.images[0].save(image_path, format="PNG")
    manifest = {
        "image": {"path": image_path.name, "mediaType": "image/png"},
        "style": {
            "id": style_id,
            "model": args.model,
            "seed": args.seed,
            "steps": args.steps,
            "guidanceScale": args.guidance_scale,
            "preserveIdentity": bool(request.get("preserveIdentity", True)),
        },
    }
    (output_dir / "result.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
