import concurrent.futures
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from algorithms.task_distributor import TaskDistributor
from common.communication import TCPServer
from common.message_types import Message, MessageType
from common.utils import setup_logging


class WorkerStatus(Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    DISCONNECTED = "DISCONNECTED"


@dataclass
class WorkerInfo:
    worker_id: str
    status: WorkerStatus
    last_heartbeat: float
    current_task_id: Optional[str] = None
    tasks_completed: int = 0


class Coordinator(TCPServer):
    def __init__(self, host: str = "localhost", port: int = 8888):
        super().__init__("COORDINATOR", host, port)
        self.logger = setup_logging("COORDINATOR")

        # Gerenciamento de Workers
        self.workers: Dict[str, WorkerInfo] = {}
        self.worker_lock = threading.Lock()

        # Gerenciamento de Tarefas
        self.task_distributor = TaskDistributor()
        self.pending_tasks: Dict[str, dict] = {}  # task_id -> task_data
        self.assigned_tasks: Dict[str, str] = {}  # task_id -> worker_id
        self.completed_tasks: Dict[str, dict] = {}  # task_id -> result

        # Estado do problema TSP
        self.current_problem: Optional[dict] = None
        self.best_solution: Optional[dict] = None
        self.client_socket = None

        # Controle de execução
        self.heartbeat_thread = None
        self.monitoring_thread = None

        # Registra handlers de mensagens
        self._register_message_handlers()

    def _register_message_handlers(self):
        """Registra handlers para diferentes tipos de mensagens"""
        self.register_handler(MessageType.REGISTER, self._handle_worker_register)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.TASK_RESULT, self._handle_task_result)
        self.register_handler(MessageType.TASK_REQUEST, self._handle_task_request)
        self.register_handler(MessageType.STATUS_REQUEST, self._handle_status_request)
        self.register_handler(MessageType.UNREGISTER, self._handle_worker_unregister)

    def _handle_worker_register(self, message: Message, sender_socket):
        """Processa registro de novo worker"""
        worker_id = message.sender_id

        with self.worker_lock:
            if worker_id not in self.workers:
                self.workers[worker_id] = WorkerInfo(
                    worker_id=worker_id,
                    status=WorkerStatus.IDLE,
                    last_heartbeat=time.time(),
                )
                self.logger.info(f"Worker {worker_id} registered")

                # Envia confirmação
                ack_message = self.create_message(
                    MessageType.REGISTER_ACK,
                    {"status": "registered", "coordinator_id": self.node_id},
                )
                self.send_message(sender_socket, ack_message)

                # Se há tarefas pendentes, atribui uma
                self._assign_pending_tasks_locked()
            else:
                self.logger.warning(f"Worker {worker_id} already registered")

    def _handle_worker_unregister(self, message: Message, sender_socket):
        """Processa desregistro de worker"""
        worker_id = message.sender_id

        with self.worker_lock:
            if worker_id in self.workers:
                # Se worker tinha tarefa, move de volta para pendentes
                worker_info = self.workers[worker_id]
                if worker_info.current_task_id:
                    task_id = worker_info.current_task_id
                    if task_id in self.assigned_tasks:
                        del self.assigned_tasks[task_id]
                        # Tarefa volta para pendentes
                        self.logger.info(
                            f"Task {task_id} returned to pending due to worker disconnect"
                        )

                del self.workers[worker_id]
                self.logger.info(f"Worker {worker_id} unregistered")

    def _handle_heartbeat(self, message: Message, sender_socket):
        """Processa heartbeat de worker"""
        worker_id = message.sender_id

        with self.worker_lock:
            if worker_id in self.workers:
                self.workers[worker_id].last_heartbeat = time.time()

                # Envia ACK
                ack_message = self.create_message(
                    MessageType.HEARTBEAT_ACK, {"timestamp": time.time()}
                )
                self.send_message(sender_socket, ack_message)
            else:
                self.logger.warning(f"Heartbeat from unregistered worker: {worker_id}")

    def _monitor_workers(self):
        """Monitora workers e detecta desconexões"""
        while self.running:
            current_time = time.time()
            disconnected_workers = []

            with self.worker_lock:
                for worker_id, worker_info in self.workers.items():
                    if current_time - worker_info.last_heartbeat > 30:  # 30s timeout
                        disconnected_workers.append(worker_id)
                        worker_info.status = WorkerStatus.DISCONNECTED

            # Remove workers desconectados
            for worker_id in disconnected_workers:
                self.logger.warning(f"Worker {worker_id} disconnected (timeout)")
                self._handle_worker_disconnect(worker_id)

            time.sleep(10)  # Verifica a cada 10 segundos

    def _handle_worker_disconnect(self, worker_id: str):
        """Lida com desconexão de worker"""
        with self.worker_lock:
            if worker_id in self.workers:
                worker_info = self.workers[worker_id]

                # Recupera tarefa se estava em execução
                if worker_info.current_task_id:
                    task_id = worker_info.current_task_id
                    if task_id in self.assigned_tasks:
                        del self.assigned_tasks[task_id]
                        self.logger.info(
                            f"Task {task_id} reassigned due to worker disconnect"
                        )

                del self.workers[worker_id]

                # Tenta reatribuir tarefas pendentes
                self._assign_pending_tasks_locked()

    def _handle_task_request(self, message: Message, sender_socket):
        """Processa solicitação de problema TSP do cliente"""
        self.client_socket = sender_socket
        problem_data = message.data

        self.logger.info("Received TSP problem from client")
        self.logger.info(f"Problem has {len(problem_data.get('cities', []))} cities")
        self.current_problem = problem_data

        # Process task generation in a separate thread to avoid blocking
        def process_task_generation():
            try:
                # Gera subtarefas
                self.logger.info("Starting task generation...")
                self._generate_tasks(problem_data)
                self.logger.info("Task generation completed")

                # Inicia distribuição
                self.logger.info("Starting task assignment...")
                self._assign_pending_tasks()
                self.logger.info("Task assignment completed")

                # Envia confirmação ao cliente
                ack_message = self.create_message(
                    MessageType.REGISTER_ACK,
                    {
                        "status": "problem_received",
                        "total_tasks": len(self.pending_tasks),
                    },
                )
                self.send_message(sender_socket, ack_message)

            except Exception as e:
                self.logger.error(f"Error in task generation: {e}")
                # Send error message to client
                error_message = self.create_message(
                    MessageType.REGISTER_ACK,
                    {"status": "error", "error": str(e)},
                )
                self.send_message(sender_socket, error_message)

        # Start task generation in background thread
        task_thread = threading.Thread(target=process_task_generation, daemon=True)
        task_thread.start()

    def _generate_tasks(self, problem_data: dict):
        """Gera subtarefas a partir do problema TSP"""
        self.logger.info("_generate_tasks: entered")
        distance_matrix = problem_data["distance_matrix"]
        self.logger.info("_generate_tasks: got distance_matrix")
        cities = problem_data["cities"]
        self.logger.info("_generate_tasks: got cities")

        # Only lock to read worker statuses
        self.logger.info("_generate_tasks: about to acquire worker_lock")
        with self.worker_lock:
            self.logger.info("_generate_tasks: acquired worker_lock")
            available_workers = len(
                [w for w in self.workers.values() if w.status == WorkerStatus.IDLE]
            )
            self.logger.info(f"Total workers: {len(self.workers)}")
            for worker_id, worker_info in self.workers.items():
                self.logger.info(
                    f"Worker {worker_id}: status={worker_info.status.value}"
                )

        # Now OUTSIDE the lock, do the rest!
        self.logger.info(
            f"Generating tasks for {len(cities)} cities with {available_workers} available workers"
        )
        if available_workers == 0:
            self.logger.warning("No available workers found! Cannot generate tasks.")
            return

        self.logger.info("Calling TaskDistributor.distribute_tsp_tasks with timeout...")
        tasks = None
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.task_distributor.distribute_tsp_tasks,
                    distance_matrix,
                    cities,
                    max(1, available_workers),
                )
                tasks = future.result(timeout=10)  # 10 seconds timeout
            self.logger.info(f"TaskDistributor returned {len(tasks)} tasks")
        except concurrent.futures.TimeoutError:
            self.logger.error("Timeout in task distribution!")
            return
        except Exception as e:
            self.logger.error(f"Error in task distribution: {e}")
            return

        self.logger.info("_generate_tasks: got tasks, clearing old tasks")
        self.pending_tasks.clear()
        self.assigned_tasks.clear()
        self.completed_tasks.clear()

        self.logger.info("_generate_tasks: adding new tasks")
        for i, task in enumerate(tasks):
            task_id = f"task_{i}"
            self.pending_tasks[task_id] = task

        self.logger.info(
            f"Generated {len(tasks)} subtasks for {available_workers} workers"
        )
        for i, task in enumerate(tasks):
            work_size = task.get("estimated_work_size", 0)
            self.logger.debug(f"Task {i}: estimated work size = {work_size}")
        self.logger.info("_generate_tasks: completed")

    def _assign_pending_tasks_locked(self):
        """Atribui tarefas pendentes para workers disponíveis (deve ser chamado com worker_lock já adquirido)"""
        idle_workers = [
            worker_id
            for worker_id, worker_info in self.workers.items()
            if worker_info.status == WorkerStatus.IDLE
        ]

        self.logger.debug(
            f"Assigning tasks - {len(self.pending_tasks)} pending, {len(idle_workers)} idle workers"
        )

        # Atribui tarefas para workers disponíveis
        for worker_id in idle_workers:
            if not self.pending_tasks:
                break

            # Pega primeira tarefa pendente
            task_id = next(iter(self.pending_tasks))
            task_data = self.pending_tasks.pop(task_id)

            # Atribui para worker
            self.assigned_tasks[task_id] = worker_id
            self.workers[worker_id].status = WorkerStatus.BUSY
            self.workers[worker_id].current_task_id = task_id

            # Envia tarefa para worker
            task_message = self.create_message(
                MessageType.TASK_ASSIGNMENT,
                {"task_id": task_id, "task_data": task_data},
            )

            if self.send_to_client(worker_id, task_message):
                self.logger.info(f"Task {task_id} assigned to worker {worker_id}")
                work_size = task_data.get("estimated_work_size", 0)
                self.logger.debug(f"Task {task_id} work size: {work_size}")
            else:
                # Falha ao enviar, volta tarefa para pendentes
                self.logger.error(
                    f"Failed to send task {task_id} to worker {worker_id}"
                )
                self.pending_tasks[task_id] = task_data
                del self.assigned_tasks[task_id]
                self.workers[worker_id].status = WorkerStatus.IDLE
                self.workers[worker_id].current_task_id = None

    def _assign_pending_tasks(self):
        """Atribui tarefas pendentes para workers disponíveis"""
        with self.worker_lock:
            self._assign_pending_tasks_locked()

    def _handle_task_result(self, message: Message, sender_socket):
        """Processa resultado de tarefa de worker"""
        worker_id = message.sender_id
        result_data = message.data
        task_id = result_data["task_id"]

        self.logger.info(f"Received result for task {task_id} from worker {worker_id}")

        with self.worker_lock:
            # Atualiza status do worker
            if worker_id in self.workers:
                self.workers[worker_id].status = WorkerStatus.IDLE
                self.workers[worker_id].current_task_id = None
                self.workers[worker_id].tasks_completed += 1

            # Remove da lista de tarefas atribuídas
            if task_id in self.assigned_tasks:
                del self.assigned_tasks[task_id]

            # Armazena resultado
            self.completed_tasks[task_id] = result_data

            # Verifica se é melhor solução
            self._update_best_solution(result_data)

            # Atribui próxima tarefa se disponível
            self._assign_pending_tasks_locked()

            # Verifica se terminou
            self.logger.info(
                f"Checking completion: pending={len(self.pending_tasks)}, assigned={len(self.assigned_tasks)}, completed={len(self.completed_tasks)}"
            )
            if self._all_tasks_completed():
                self.logger.info("All tasks completed! Sending final result...")
                self._send_final_result()
            else:
                self.logger.info("Not all tasks completed yet")

    def _update_best_solution(self, result_data: dict):
        """Atualiza melhor solução encontrada"""
        if "best_path" in result_data and "best_cost" in result_data:
            if (
                self.best_solution is None
                or result_data["best_cost"] < self.best_solution["best_cost"]
            ):
                self.best_solution = {
                    "best_path": result_data["best_path"],
                    "best_cost": result_data["best_cost"],
                    "found_by": result_data.get("worker_id", "unknown"),
                }

                self.logger.info(
                    f"New best solution found: cost = {result_data['best_cost']}"
                )

    def _all_tasks_completed(self) -> bool:
        """Verifica se todas as tarefas foram completadas"""
        return (
            len(self.pending_tasks) == 0
            and len(self.assigned_tasks) == 0
            and len(self.completed_tasks) > 0
        )

    def _send_final_result(self):
        """Envia resultado final para o cliente"""
        self.logger.info(
            f"_send_final_result called: client_socket={self.client_socket is not None}, best_solution={self.best_solution is not None}"
        )

        if self.client_socket and self.best_solution:
            self.logger.info("Creating final result message...")
            result_message = self.create_message(
                MessageType.TASK_COMPLETE,
                {
                    "status": "completed",
                    "best_solution": self.best_solution,
                    "total_tasks": len(self.completed_tasks),
                    "execution_stats": self._get_execution_stats_locked(),
                },
            )

            self.logger.info("Sending final result message to client...")
            success = self.send_message(self.client_socket, result_message)
            if success:
                self.logger.info("Final result sent to client")
            else:
                self.logger.error("Failed to send final result to client")
        else:
            self.logger.error(
                f"Cannot send final result: client_socket={self.client_socket is not None}, best_solution={self.best_solution is not None}"
            )

    def _get_execution_stats_locked(self) -> dict:
        """Coleta estatísticas de execução (deve ser chamado com worker_lock já adquirido)"""
        return {
            "total_workers": len(self.workers),
            "tasks_per_worker": {
                worker_id: worker_info.tasks_completed
                for worker_id, worker_info in self.workers.items()
            },
            "active_workers": len(
                [
                    w
                    for w in self.workers.values()
                    if w.status != WorkerStatus.DISCONNECTED
                ]
            ),
        }

    def _get_execution_stats(self) -> dict:
        """Coleta estatísticas de execução"""
        with self.worker_lock:
            return self._get_execution_stats_locked()

    def start_coordinator(self):
        """Inicia o coordenador"""
        if not self.start():
            self.logger.error("Failed to start coordinator")
            return False

        # Inicia threads de monitoramento
        self.monitoring_thread = threading.Thread(target=self._monitor_workers)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        self.logger.info("Coordinator started successfully")
        return True

    def stop_coordinator(self):
        """Para o coordenador"""
        self.logger.info("Stopping coordinator...")

        # Notifica workers
        shutdown_message = self.create_message(MessageType.SHUTDOWN)
        self.broadcast(shutdown_message)

        # Para servidor
        self.stop()

        self.logger.info("Coordinator stopped")

    def _handle_status_request(self, message: Message, sender_socket):
        """Fornece status do coordenador"""
        with self.worker_lock:
            status_data = {
                "coordinator_id": self.node_id,
                "workers_count": len(self.workers),
                "active_workers": len(
                    [
                        w
                        for w in self.workers.values()
                        if w.status != WorkerStatus.DISCONNECTED
                    ]
                ),
                "pending_tasks": len(self.pending_tasks),
                "assigned_tasks": len(self.assigned_tasks),
                "completed_tasks": len(self.completed_tasks),
                "has_active_problem": self.current_problem is not None,
                "best_cost": self.best_solution["best_cost"]
                if self.best_solution
                else None,
            }

        response = self.create_message(MessageType.STATUS_RESPONSE, status_data)
        self.send_message(sender_socket, response)
