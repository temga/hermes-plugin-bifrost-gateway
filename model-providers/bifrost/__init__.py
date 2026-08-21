"""Bifrost AI Gateway — model-provider profile.

Routes all LLM requests through a single Bifrost gateway endpoint.
One virtual key (sk-bf-*) gives access to all upstream providers
(neuraldeep, tropass, turbocloud, routerai) with centralized rate
limits, budgets, and logging.

Environment variables:
    BIFROST_API_KEY   — virtual key (sk-bf-*), required
    BIFROST_BASE_URL  — gateway URL (default: https://router.rove-ai.ru/v1)

The Bifrost API is fully OpenAI Chat-Completions compatible, so a
basic ProviderProfile without hook overrides is sufficient.
"""

from __future__ import annotations

import os

from providers import register_provider
from providers.base import ProviderProfile

# Default gateway URL (local Bifrost instance)
_DEFAULT_BASE_URL = "https://router.rove-ai.ru/v1"

# Curated fallback model list — the full catalog is dynamic (24+ models
# across 4 upstream providers). Users can set any model id in config.yaml
# and it will be passed through to the gateway.
_FALLBACK_MODELS = (
    # neuraldeep — reasoning + noreason variants
    "neuraldeep/gpt-oss-120b",
    "neuraldeep/qwen3.6-35b-a3b",
    "neuraldeep/qwen3.6-35b-a3b-noreason",
    "neuraldeep/qwen3.8-27b",
    "neuraldeep/qwen3.8-27b-noreason",
    "neuraldeep/kimi-k2.6",
    "neuraldeep/gemma-4-31b",
    "neuraldeep/gemma-4-31b-noreason",
    "neuraldeep/frida",
    # tropass
    "tropass/GLM-5.2",
    "tropass/Qwen3.5-397B-A17B-FP8",
    # turbocloud
    "turbocloud/GLM-5.2",
)

bifrost = ProviderProfile(
    name="bifrost",
    aliases=("bf", "gateway"),
    env_vars=("BIFROST_API_KEY",),
    display_name="Bifrost Gateway",
    description=(
        "Bifrost AI Gateway — единый шлюз: LLM, image gen, search. "
        "Один ключ sk-bf-* для всех провайдеров."
    ),
    signup_url="https://router.rove-ai.ru",
    # Resolve base URL at import time from env (or fall back to default).
    # The profile dataclass stores a static string; if the user sets
    # BIFROST_BASE_URL in .env, it takes effect on next session start.
    base_url=os.environ.get("BIFROST_BASE_URL", _DEFAULT_BASE_URL),
    fallback_models=_FALLBACK_MODELS,
    # Non-reasoning model for background/aux text tasks (compression, session
    # search, title generation, etc.). NOT used for vision — see below.
    default_aux_model="neuraldeep/qwen3.6-35b-a3b-noreason",
    supports_vision=True,
)


def _bifrost_default_vision_model() -> str | None:
    """Return a vision-capable model for the Bifrost gateway.

    The main chat model (e.g. neuraldeep/gpt-oss-120b) is text-only —
    sending image input to it produces a cryptic upstream error. This
    override routes vision auto-detect to a known multimodal model so
    ``auxiliary.vision.provider: auto`` works out of the box.
    """
    return "neuraldeep/qwen3.8-27b"


# Patch the hook onto the profile instance. ProviderProfile.default_vision_model
# is an overridable method; we set it per-instance so the auto-detect chain in
# auxiliary_client._resolve_provider_vision_default() picks up our choice.
bifrost.default_vision_model = _bifrost_default_vision_model

register_provider(bifrost)
