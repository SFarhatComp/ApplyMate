import os
import yaml
from loguru import logger

def load_config_with_env_vars():
    """Load configuration from YAML file and replace environment variables."""
    try:
        # Check if config file exists, if not copy from example
        if not os.path.exists("config/config.yaml"):
            if os.path.exists("config/config.yaml.example"):
                logger.info("Config file not found. Creating from example...")
                with open("config/config.yaml.example", "r") as example_file:
                    example_config = example_file.read()
                
                with open("config/config.yaml", "w") as config_file:
                    config_file.write(example_config)
            else:
                logger.error("No config file or example found!")
                return None
        
        # Load the config file
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        # Replace environment variables in the config
        _replace_env_vars_in_config(config)
        
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return None

def _replace_env_vars_in_config(config):
    """Recursively replace environment variables in config."""
    if isinstance(config, dict):
        for key, value in config.items():
            if isinstance(value, (dict, list)):
                _replace_env_vars_in_config(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.environ.get(env_var)
                if env_value:
                    config[key] = env_value
                else:
                    logger.warning(f"Environment variable {env_var} not found")
    elif isinstance(config, list):
        for i, item in enumerate(config):
            if isinstance(item, (dict, list)):
                _replace_env_vars_in_config(item)
            elif isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                env_var = item[2:-1]
                env_value = os.environ.get(env_var)
                if env_value:
                    config[i] = env_value
                else:
                    logger.warning(f"Environment variable {env_var} not found") 