#!/usr/bin/env python3
import sys
import signal
import argparse
import time
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from worker.worker import Worker
from common.utils import setup_logging

worker = None

def signal_handler(signum, frame):
    """Handler para sinais de parada"""
    print(f"\nReceived shutdown signal...")
    if worker:
        worker.stop_worker()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='TSP Distributed Worker')
    parser.add_argument('--host', default='localhost', help='Coordinator host address')
    parser.add_argument('--port', type=int, default=8888, help='Coordinator port number')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Registra handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Cria e inicia worker
    global worker
    worker = Worker(args.host, args.port)

    if worker.start_worker():
        print(f"Worker {worker.node_id} connected to {args.host}:{args.port}")
        print("Press Ctrl+C to stop")

        # Mantém rodando
        try:
            while worker.running and worker.connected:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            worker.stop_worker()
    else:
        print("Failed to start worker")
        sys.exit(1)

if __name__ == "__main__":
    main() 