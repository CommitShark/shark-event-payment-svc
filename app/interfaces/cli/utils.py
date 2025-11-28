import json
import logging
from pydantic import ValidationError, BaseModel
from pathlib import Path
from typing import List, Optional, Type, TypeVar, Union


T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


def load_json_model(path: str, model: Type[T]) -> Optional[Union[T, List[T]]]:
    """
    Load and validate a JSON file into a given Pydantic model or list of models.

    Args:
        path (str): Path to the JSON file.
        model (Type[T]): A Pydantic model class to validate against.

    Returns:
        Optional[Union[T, List[T]]]: Instance(s) of the model if valid, else None.
    """
    file_path = Path(path).expanduser()
    logger.debug(f"Attempting to load JSON file: {file_path}")

    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None

    try:
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            logger.warning(f"File is empty: {file_path}")
            return None

        data = json.loads(content)
        validated: Union[T, List[T]]

        if isinstance(data, list):
            logger.debug(
                f"Detected JSON array; validating list of {model.__name__} models"
            )
            validated = [model.model_validate(item) for item in data]
        else:
            logger.debug(
                f"Detected JSON object; validating single {model.__name__} model"
            )
            validated = model.model_validate(data)

        logger.info(f"Successfully loaded {model.__name__} data from {file_path}")
        return validated

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
    except ValidationError as e:
        logger.error(f"Validation failed for {model.__name__}: {e.errors()}")
    except OSError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error while loading {file_path}: {e}")

    return None
