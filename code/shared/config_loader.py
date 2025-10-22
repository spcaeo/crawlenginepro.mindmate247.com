#!/usr/bin/env python3
"""
Shared Configuration Loader for PipeLineServices
Single source of truth for environment configuration

Usage in service config.py:
    from pathlib import Path
    import sys

    # Add shared to path
    SHARED_DIR = Path(__file__).resolve().parents[4] / "shared"
    sys.path.insert(0, str(SHARED_DIR))

    from config_loader import load_shared_env, get_env

    # Load environment
    load_shared_env()

    # Access variables
    API_KEY = get_env("SAMBANOVA_API_KEY")
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Determine shared directory
SHARED_DIR = Path(__file__).resolve().parent

# Environment selection (dev, prod, staging)
PIPELINE_ENV = os.getenv("PIPELINE_ENV", "dev")

# Supported environments
SUPPORTED_ENVS = ["dev", "prod", "staging"]


def load_shared_env(env: Optional[str] = None, verbose: bool = True) -> Path:
    """
    Load environment variables from shared config directory

    Args:
        env: Environment to load (dev, prod, staging). If None, uses PIPELINE_ENV or defaults to 'dev'
        verbose: Print loading information

    Returns:
        Path to loaded .env file

    Raises:
        FileNotFoundError: If .env file doesn't exist
        ValueError: If invalid environment specified
    """
    # Determine which environment to load
    target_env = env or PIPELINE_ENV

    if target_env not in SUPPORTED_ENVS:
        raise ValueError(f"Invalid environment '{target_env}'. Must be one of: {SUPPORTED_ENVS}")

    # Construct path to .env file
    env_file = SHARED_DIR / f".env.{target_env}"

    if not env_file.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")

    # Load the environment file
    load_dotenv(env_file, override=True)

    if verbose:
        print(f"[CONFIG] Loaded environment: {target_env}")
        print(f"[CONFIG] Config file: {env_file}")
        print(f"[CONFIG] Shared directory: {SHARED_DIR}")

    return env_file


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and validation

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Raise error if not found and no default

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required=True and variable not found
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' not found")

    return value


def get_shared_dir() -> Path:
    """Get path to shared directory"""
    return SHARED_DIR


def get_current_env() -> str:
    """Get current environment name (dev, prod, staging)"""
    return PIPELINE_ENV


def print_config_summary():
    """Print summary of loaded configuration (for debugging)"""
    print("=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"Environment: {PIPELINE_ENV}")
    print(f"Config file: {SHARED_DIR / f'.env.{PIPELINE_ENV}'}")
    print(f"Shared directory: {SHARED_DIR}")
    print()
    print("Key environment variables:")

    # Check critical variables
    critical_vars = [
        "SAMBANOVA_API_KEY",
        "NEBIUS_API_KEY",
        "MILVUS_HOST_DEVELOPMENT",
        "MILVUS_HOST_PRODUCTION",
        "LLM_GATEWAY_URL_DEVELOPMENT",
        "LLM_GATEWAY_URL_PRODUCTION"
    ]

    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Mask API keys
            if "KEY" in var or "PASSWORD" in var:
                display = f"{value[:20]}..." if len(value) > 20 else value
            else:
                display = value
            print(f"  ✅ {var}: {display}")
        else:
            print(f"  ❌ {var}: NOT SET")

    print("=" * 80)


if __name__ == "__main__":
    # Test the loader
    print("Testing config_loader.py\n")
    load_shared_env(verbose=True)
    print()
    print_config_summary()
