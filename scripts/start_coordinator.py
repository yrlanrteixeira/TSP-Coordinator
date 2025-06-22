#!/usr/bin/env python3
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from common.utils import setup_logging
from coordinator.coordinator import Coordinator

coordinator = None


def signal_handler(signum, frame):
    """Handler para sinais de parada"""
    print("\nReceived shutdown signal...")
    if coordinator:
        coordinator.stop_coordinator()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="TSP Distributed Coordinator")
    parser.add_argument("--host", default="localhost", help="Host address")
    parser.add_argument("--port", type=int, default=8888, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configura logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging("COORDINATOR", log_level)

    # Registra handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Cria e inicia coordenador
    global coordinator
    coordinator = Coordinator(args.host, args.port)

    if coordinator.start_coordinator():
        logger.info(f"Coordinator running on {args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop")

        # Mantém rodando
        try:
            while coordinator.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        logger.error("Failed to start coordinator")
        sys.exit(1)


if __name__ == "__main__":
    main()
