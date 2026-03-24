"""Generate model permutations for ablation studies."""

import yaml
from pathlib import Path

# Parameters for Non-Reasoning models
DECODING_LEVELS = {
    "deterministic": {"temperature": 0.0, "top_p": 1.0},
    "conservative": {"temperature": 0.3, "top_p": 0.8},
    "balanced": {"temperature": 0.7, "top_p": 0.95},
    "creative": {"temperature": 1.0, "top_p": 1.0},
    "chaotic": {"temperature": 1.2, "top_p": 1.0},
}

# The model families
CHAT_MODELS = [
    {
        "prefix": "ds_chat",
        "provider": "openai_compatible",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": "deepseek-chat",
    },
    {
        "prefix": "qwen_plus",
        "provider": "openai_compatible",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "QWEN_API_KEY",
        "model_name": "qwen-plus",
    },
    {
        "prefix": "qwen_turbo",
        "provider": "openai_compatible",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "QWEN_API_KEY",
        "model_name": "qwen-turbo",
    }
]

def main():
    config_dir = Path("configs")
    config_dir.mkdir(exist_ok=True)
    
    # Generate 3 chat models x 5 decoding levels = 15 configs
    for model in CHAT_MODELS:
        for level_name, params in DECODING_LEVELS.items():
            config = {
                "provider": model["provider"],
                "base_url": model["base_url"],
                "api_key_env": model["api_key_env"],
                "models": {
                    "solver_primary": model["model_name"],
                    "perturbation_generator": model["model_name"],
                    "optional_secondary": "",
                },
                "request_defaults": {
                    "temperature": params["temperature"],
                    "top_p": params["top_p"],
                    "max_tokens": 1536,
                    "timeout_seconds": 60,
                },
                "perturbation_defaults": {
                    "temperature": params["temperature"],
                    "top_p": params["top_p"],
                    "max_tokens": 1024,
                    "timeout_seconds": 60,
                }
            }
            file_path = config_dir / f"models_{model['prefix']}_{level_name}.yaml"
            with file_path.open("w", encoding="utf-8") as f:
                yaml.dump(config, f, sort_keys=False)
                
    # Generate exactly ONE reasoner config (ignoring decoding levels)
    reasoner_config = {
        "provider": "openai_compatible",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "models": {
            "solver_primary": "deepseek-reasoner",
            "perturbation_generator": "deepseek-chat", # Perturbation generation usually shouldn't be reasoned
            "optional_secondary": "",
        },
        "request_defaults": {
            "temperature": 1.0,  # DeepSeek reasoner ignores this
            "top_p": 1.0,
            "max_tokens": 4096,
            "timeout_seconds": 120, # Reasoners take a long time
        },
        "perturbation_defaults": {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
            "timeout_seconds": 60,
        }
    }
    with (config_dir / "models_ds_reason_baseline.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(reasoner_config, f, sort_keys=False)

    print("Generated 16 configuration files in configs/.")

if __name__ == "__main__":
    main()
