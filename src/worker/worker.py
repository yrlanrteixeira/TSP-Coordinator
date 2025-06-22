import threading
import time
import uuid
from typing import Any, Dict, Optional

from algorithms.tsp_solver import TSPSolver
from common.communication import TCPClient
from common.message_types import Message, MessageType
from common.utils import create_heartbeat_data, setup_logging


class Worker(TCPClient):
    def __init__(
        self, coordinator_host: str = "localhost", coordinator_port: int = 8888
    ):
        # Gera ID único para o worker
        worker_id = f"WORKER_{uuid.uuid4().hex[:8].upper()}"
        super().__init__(worker_id, coordinator_host, coordinator_port)

        self.logger = setup_logging(worker_id)
        self.tsp_solver = TSPSolver()

        # Estado do worker
        self.is_registered = False
        self.current_task: Optional[Dict[str, Any]] = None
        self.heartbeat_interval = 5  # segundos

        # Threads de controle
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.task_thread: Optional[threading.Thread] = None

        # Registra handlers de mensagens
        self._register_message_handlers()

    def _register_message_handlers(self):
        """Registra handlers para diferentes tipos de mensagens"""
        self.register_handler(MessageType.REGISTER_ACK, self._handle_register_ack)
        self.register_handler(MessageType.TASK_ASSIGNMENT, self._handle_task_assignment)
        self.register_handler(MessageType.HEARTBEAT_ACK, self._handle_heartbeat_ack)
        self.register_handler(MessageType.SHUTDOWN, self._handle_shutdown)

    def start_worker(self) -> bool:
        """Inicia o worker e conecta ao coordenador"""
        self.logger.info(f"Starting worker {self.node_id}")

        # Conecta ao coordenador
        if not self.connect():
            self.logger.error("Failed to connect to coordinator")
            return False

        # Registra no coordenador
        if not self._register_with_coordinator():
            self.logger.error("Failed to register with coordinator")
            self.disconnect()
            return False

        # Inicia heartbeat thread
        self._start_heartbeat()

        self.logger.info("Worker started successfully")
        return True

    def stop_worker(self):
        """Para o worker e desconecta"""
        self.logger.info("Stopping worker...")

        # Para threads
        self.running = False

        # Desregistra do coordenador
        if self.is_registered:
            self._unregister_from_coordinator()

        # Desconecta
        self.disconnect()

        self.logger.info("Worker stopped")

    def _register_with_coordinator(self) -> bool:
        """Registra worker no coordenador"""
        register_message = self.create_message(
            MessageType.REGISTER,
            {
                "worker_capabilities": {
                    "tsp_solver": True,
                    "max_cities": 20,  # Limita complexidade
                },
                "worker_info": {"version": "1.0", "started_at": time.time()},
            },
        )

        if self.send(register_message):
            self.logger.info("Registration message sent to coordinator")
            # Aguarda confirmação (será processada via handler)
            return True
        else:
            self.logger.error("Failed to send registration message")
            return False

    def _unregister_from_coordinator(self):
        """Remove registro do worker no coordenador"""
        unregister_message = self.create_message(MessageType.UNREGISTER)
        self.send(unregister_message)
        self.is_registered = False
        self.logger.info("Unregistered from coordinator")

    def _handle_register_ack(self, message: Message, sender_socket=None):
        """Processa confirmação de registro"""
        data = message.data
        if data.get("status") == "registered":
            self.is_registered = True
            coordinator_id = data.get("coordinator_id", "unknown")
            self.logger.info(
                f"Successfully registered with coordinator {coordinator_id}"
            )
        else:
            self.logger.error("Registration failed")

    def _start_heartbeat(self):
        """Inicia thread de heartbeat"""
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão viva"""
        while self.running and self.connected and self.is_registered:
            heartbeat_message = self.create_message(
                MessageType.HEARTBEAT, create_heartbeat_data()
            )

            if not self.send(heartbeat_message):
                self.logger.error("Failed to send heartbeat")
                break

            time.sleep(self.heartbeat_interval)

        self.logger.debug("Heartbeat loop ended")

    def _handle_heartbeat_ack(self, message: Message, sender_socket=None):
        """Processa ACK de heartbeat"""
        # Heartbeat confirmado - conexão está ativa
        pass

    def _handle_task_assignment(self, message: Message, sender_socket=None):
        """Processa atribuição de tarefa"""
        task_data = message.data
        task_id = task_data["task_id"]

        self.logger.info(f"Received task assignment: {task_id}")

        # Verifica se já está processando uma tarefa
        if self.current_task is not None:
            self.logger.warning(
                f"Already processing task {self.current_task['task_id']}"
            )
            return

        # Armazena tarefa atual
        self.current_task = task_data

        # Inicia processamento em thread separada
        self.task_thread = threading.Thread(
            target=self._process_task, args=(task_data,)
        )
        self.task_thread.daemon = True
        self.task_thread.start()

    def _process_task(self, task_data: Dict[str, Any]):
        """Processa tarefa TSP em thread separada"""
        task_id = task_data["task_id"]
        tsp_data = task_data["task_data"]

        try:
            self.logger.info(f"Starting processing of task {task_id}")
            start_time = time.time()

            # Extrai dados da tarefa
            distance_matrix = tsp_data["distance_matrix"]
            cities = tsp_data["cities"]
            start_permutations = tsp_data.get("start_permutations", [])
            end_permutations = tsp_data.get("end_permutations", [])

            # Resolve subtarefa TSP
            result = self._solve_tsp_subtask(
                distance_matrix, cities, start_permutations, end_permutations
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Prepara resultado
            task_result = {
                "task_id": task_id,
                "worker_id": self.node_id,
                "best_path": result["best_path"],
                "best_cost": result["best_cost"],
                "permutations_checked": result["permutations_checked"],
                "processing_time": processing_time,
                "status": "completed",
            }

            # Envia resultado para coordenador
            result_message = self.create_message(MessageType.TASK_RESULT, task_result)

            if self.send(result_message):
                self.logger.info(f"Task {task_id} completed in {processing_time:.2f}s")
                self.logger.info(f"Best cost found: {result['best_cost']}")
            else:
                self.logger.error(f"Failed to send result for task {task_id}")

        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {e}")

            # Envia erro para coordenador
            error_result = {
                "task_id": task_id,
                "worker_id": self.node_id,
                "status": "error",
                "error_message": str(e),
            }

            error_message = self.create_message(MessageType.TASK_RESULT, error_result)
            self.send(error_message)

        finally:
            # Limpa tarefa atual
            self.current_task = None

    def _solve_tsp_subtask(self, distance_matrix, cities, start_perms, end_perms):
        """Resolve subtarefa do TSP"""
        self.logger.debug(f"Solving TSP for {len(cities)} cities")

        # Usa TSPSolver para resolver a subtarefa
        result = self.tsp_solver.solve_partial_permutations(
            distance_matrix=distance_matrix,
            cities=cities,
            start_permutations=start_perms,
            end_permutations=end_perms,
        )

        return result

    def _handle_shutdown(self, message: Message, sender_socket=None):
        """Processa comando de shutdown do coordenador"""
        self.logger.info("Received shutdown command from coordinator")

        # Se está processando tarefa, espera terminar (com timeout)
        if self.current_task and self.task_thread:
            self.logger.info("Waiting for current task to complete...")
            self.task_thread.join(timeout=30)  # Espera até 30s

            if self.task_thread.is_alive():
                self.logger.warning("Task did not complete in time, forcing shutdown")

        self.stop_worker()

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do worker"""
        return {
            "worker_id": self.node_id,
            "connected": self.connected,
            "registered": self.is_registered,
            "current_task": self.current_task["task_id"] if self.current_task else None,
            "processing": self.current_task is not None,
            "coordinator_host": self.server_host,
            "coordinator_port": self.server_port,
        }

    def is_idle(self) -> bool:
        """Verifica se worker está disponível"""
        return self.current_task is None

    def is_processing(self) -> bool:
        """Verifica se worker está processando tarefa"""
        return self.current_task is not None
