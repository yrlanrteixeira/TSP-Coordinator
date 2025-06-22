import logging
import time
from typing import Any, Dict


def setup_logging(node_id: str, level: int = logging.INFO):
    """Configura logging para um nó"""
    logger = logging.getLogger(node_id)
    logger.setLevel(level)

    # Remove handlers existentes para evitar duplicação
    if logger.handlers:
        logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f"[{node_id}] %(asctime)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def validate_message(message: dict) -> bool:
    """Valida estrutura básica da mensagem"""
    required_fields = ["msg_type", "sender_id", "timestamp"]
    return all(field in message for field in required_fields)


def create_heartbeat_data() -> Dict[str, Any]:
    """Cria dados para mensagem de heartbeat"""
    return {"timestamp": time.time(), "status": "alive"}
