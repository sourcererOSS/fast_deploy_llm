"""Bedrock model aliases → inference profile / model IDs (config only)."""

MODELS: dict[str, str] = {
    "qwen3-coder-480b": "qwen.qwen3-coder-480b-a35b-v1:0",
    "claude-haiku": "apac.anthropic.claude-3-haiku-20240307-v1:0",
    "claude-sonnet": "apac.anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-5-sonnet": "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-3-7-sonnet": "apac.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "claude-sonnet-4": "apac.anthropic.claude-sonnet-4-20250514-v1:0",
    "nova-micro": "apac.amazon.nova-micro-v1:0",
    "nova-lite": "apac.amazon.nova-lite-v1:0",
    "nova-pro": "apac.amazon.nova-pro-v1:0",
    "claude-sonnet-4-5": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-sonnet-4-6": "global.anthropic.claude-sonnet-4-6",
    "nova-2-lite": "global.amazon.nova-2-lite-v1:0",
}

DEFAULT_MODEL = "nova-micro"
