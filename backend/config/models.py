"""
Rudraksh AI — Model Registry & Configuration.

Defines the supported LLM models, their capabilities, and recommended
parameter presets.  Optimised for CPU inference on a 16 GB RAM machine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique
from typing import Final


@unique
class ModelProvider(StrEnum):
    """Supported LLM inference providers."""

    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"


@unique
class ModelCapability(StrEnum):
    """Capabilities a model may advertise."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CODE = "code"
    VISION = "vision"


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Immutable configuration for a single model variant."""

    name: str
    provider: ModelProvider
    display_name: str
    context_window: int
    capabilities: tuple[ModelCapability, ...] = field(default_factory=tuple)
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    ram_estimate_gb: float = 2.0
    description: str = ""

    @property
    def supports_chat(self) -> bool:
        return ModelCapability.CHAT in self.capabilities

    @property
    def supports_embedding(self) -> bool:
        return ModelCapability.EMBEDDING in self.capabilities

    @property
    def supports_code(self) -> bool:
        return ModelCapability.CODE in self.capabilities


# ──────────────────────────────────────────────────────────────────────
#  Pre-configured model registry
# ──────────────────────────────────────────────────────────────────────

MODEL_REGISTRY: Final[dict[str, ModelConfig]] = {
    # ── Ollama models ────────────────────────────────────────────────
    "llama3.2:3b": ModelConfig(
        name="llama3.2:3b",
        provider=ModelProvider.OLLAMA,
        display_name="Llama 3.2 3B",
        context_window=8192,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.7,
        default_max_tokens=2048,
        ram_estimate_gb=2.5,
        description="Default general-purpose model. Fast on CPU, good for most tasks.",
    ),
    "llama3.2:1b": ModelConfig(
        name="llama3.2:1b",
        provider=ModelProvider.OLLAMA,
        display_name="Llama 3.2 1B",
        context_window=8192,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.7,
        default_max_tokens=1024,
        ram_estimate_gb=1.2,
        description="Ultra-light model for quick tasks when speed matters more than quality.",
    ),
    "deepseek-coder-v2:lite": ModelConfig(
        name="deepseek-coder-v2:lite",
        provider=ModelProvider.OLLAMA,
        display_name="DeepSeek Coder V2 Lite",
        context_window=16384,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.CODE,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.3,
        default_max_tokens=4096,
        ram_estimate_gb=5.0,
        description="Specialised coding model for code generation and refactoring.",
    ),
    "qwen2.5-coder:3b": ModelConfig(
        name="qwen2.5-coder:3b",
        provider=ModelProvider.OLLAMA,
        display_name="Qwen 2.5 Coder 3B",
        context_window=32768,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.CODE,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.3,
        default_max_tokens=4096,
        ram_estimate_gb=2.5,
        description="Compact coding assistant with a large context window.",
    ),
    "nomic-embed-text": ModelConfig(
        name="nomic-embed-text",
        provider=ModelProvider.OLLAMA,
        display_name="Nomic Embed Text",
        context_window=8192,
        capabilities=(ModelCapability.EMBEDDING,),
        default_temperature=0.0,
        default_max_tokens=0,
        ram_estimate_gb=0.5,
        description="High-quality text embedding model for RAG and semantic search.",
    ),
    "phi3:mini": ModelConfig(
        name="phi3:mini",
        provider=ModelProvider.OLLAMA,
        display_name="Phi-3 Mini",
        context_window=4096,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.7,
        default_max_tokens=2048,
        ram_estimate_gb=2.3,
        description="Microsoft's compact model — strong reasoning per parameter.",
    ),
    "gemma2:2b": ModelConfig(
        name="gemma2:2b",
        provider=ModelProvider.OLLAMA,
        display_name="Gemma 2 2B",
        context_window=8192,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
        ),
        default_temperature=0.7,
        default_max_tokens=2048,
        ram_estimate_gb=1.8,
        description="Google's efficient small model for everyday use.",
    ),

    # ── LM Studio (generic placeholder — real model set in LM Studio) ──
    "lmstudio-default": ModelConfig(
        name="lmstudio-default",
        provider=ModelProvider.LMSTUDIO,
        display_name="LM Studio Default",
        context_window=4096,
        capabilities=(
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.CODE,
        ),
        default_temperature=0.7,
        default_max_tokens=2048,
        ram_estimate_gb=0.0,  # managed externally
        description="Whatever model is currently loaded in LM Studio.",
    ),
}

# ── Default model key ────────────────────────────────────────────────
DEFAULT_MODEL: Final[str] = "llama3.2:3b"
DEFAULT_EMBED_MODEL: Final[str] = "nomic-embed-text"


def get_model_config(model_name: str) -> ModelConfig | None:
    """Look up a model configuration by name."""
    return MODEL_REGISTRY.get(model_name)


def list_models(provider: ModelProvider | None = None) -> list[ModelConfig]:
    """
    List all registered models, optionally filtered by provider.
    """
    models = list(MODEL_REGISTRY.values())
    if provider is not None:
        models = [m for m in models if m.provider == provider]
    return models


def get_recommended_model(capability: ModelCapability) -> ModelConfig | None:
    """
    Return the first registered model that supports the requested capability,
    preferring smaller RAM footprints.
    """
    candidates = [
        m for m in MODEL_REGISTRY.values() if capability in m.capabilities
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda m: m.ram_estimate_gb)
