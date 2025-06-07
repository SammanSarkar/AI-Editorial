"""Logging utilities for the editorial generator."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Set up logging directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Create a unique log file for each run
LOG_FILE = LOG_DIR / f"editorial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_problem_data(problem_data: Dict[str, Any]) -> None:
    """Log the problem data received from the API."""
    logger.info("=" * 80)
    logger.info("PROBLEM DATA")
    logger.info("=" * 80)
    logger.info(json.dumps(problem_data, indent=2, ensure_ascii=False))
    logger.info("\n")

def log_prompt(prompt: str) -> None:
    """Log the prompt sent to the AI."""
    logger.info("=" * 80)
    logger.info("AI PROMPT")
    logger.info("=" * 80)
    logger.info(prompt)
    logger.info("\n")

def log_response(response: str) -> None:
    """Log the response received from the AI."""
    logger.info("=" * 80)
    logger.info("AI RESPONSE")
    logger.info("=" * 80)
    logger.info(response)
    logger.info("\n")

def log_error(error: Exception) -> None:
    """Log any errors that occur during execution."""
    logger.error("An error occurred:", exc_info=error)
