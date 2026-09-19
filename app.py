# ── Model selection ───────────────────────────
TEXT_MODEL = "openai/gpt-oss-120b"          # change if you prefer another text model
VISION_MODELS = [
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]

if has_images:
    # Try vision models in order until one works
    model = None
    last_error = None
    for candidate in VISION_MODELS:
        try:
            # quick dry-run style check is not possible, so we just pick the first
            # and let the real call catch the error
            model = candidate
            break
        except Exception:
            continue
    if model is None:
        model = TEXT_MODEL
else:
    model = TEXT_MODEL
