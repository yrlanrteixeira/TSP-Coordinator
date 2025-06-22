import time
from typing import Any, Dict, List, Optional

from common.communication import TCPClient
from common.message_types import Message, MessageType
from common.utils import setup_logging


class TSPClient(TCPClient):
    def __init__(
        self, coordinator_host: str = "localhost", coordinator_port: int = 8888
    ):
        super().__init__("CLIENT", coordinator_host, coordinator_port)
        self.logger = setup_logging("CLIENT")

        # Estado do cliente
        self.waiting_for_result = False
        self.current_problem: Optional[Dict[str, Any]] = None
        self.final_result: Optional[Dict[str, Any]] = None

        # Registra handlers de mensagens
        self._register_message_handlers()

    def _register_message_handlers(self):
        """Registra handlers para diferentes tipos de mensagens"""
        self.register_handler(MessageType.REGISTER_ACK, self._handle_problem_ack)
        self.register_handler(MessageType.TASK_COMPLETE, self._handle_final_result)
        self.register_handler(MessageType.ERROR, self._handle_error)

    def solve_tsp_problem(
        self, distance_matrix: List[List[float]], cities: List[str], timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        Envia problema TSP para o coordenador e aguarda resultado

        Args:
            distance_matrix: Matrix de distâncias entre cidades
            cities: Lista de nomes das cidades
            timeout: Timeout em segundos para aguardar resultado

        Returns:
            Dicionário com a solução ou None se falhou
        """
        self.logger.info(f"Solving TSP problem with {len(cities)} cities")

        # Conecta ao coordenador
        if not self.connect():
            self.logger.error("Failed to connect to coordinator")
            return None

        try:
            # Prepara dados do problema
            problem_data = {
                "distance_matrix": distance_matrix,
                "cities": cities,
                "client_id": self.node_id,
                "submitted_at": time.time(),
            }

            # Envia problema
            if not self._send_problem(problem_data):
                return None

            # Aguarda resultado
            result = self._wait_for_result(timeout)

            return result

        finally:
            self.disconnect()

    def _send_problem(self, problem_data: Dict[str, Any]) -> bool:
        """Envia problema TSP para o coordenador"""
        self.current_problem = problem_data
        self.waiting_for_result = True
        self.final_result = None

        # Cria mensagem de solicitação
        request_message = self.create_message(MessageType.TASK_REQUEST, problem_data)

        if self.send(request_message):
            self.logger.info("TSP problem sent to coordinator")
            return True
        else:
            self.logger.error("Failed to send problem to coordinator")
            return False

    def _wait_for_result(self, timeout: int) -> Optional[Dict[str, Any]]:
        """Aguarda resultado do coordenador"""
        start_time = time.time()

        self.logger.info(f"Waiting for result (timeout: {timeout}s)")

        while self.waiting_for_result and self.connected:
            if time.time() - start_time > timeout:
                self.logger.error("Timeout waiting for result")
                return None

            time.sleep(0.1)  # Pequena pausa para não sobrecarregar CPU

        if self.final_result:
            self.logger.info("Result received successfully")
            return self.final_result
        else:
            self.logger.error("No result received")
            return None

    def _handle_problem_ack(self, message: Message, sender_socket=None):
        """Processa confirmação de recebimento do problema"""
        data = message.data
        status = data.get("status")

        if status == "problem_received":
            total_tasks = data.get("total_tasks", 0)
            self.logger.info(
                f"Problem accepted by coordinator, divided into {total_tasks} tasks"
            )
        else:
            self.logger.error(f"Problem rejected: {data}")
            self.waiting_for_result = False

    def _handle_final_result(self, message: Message, sender_socket=None):
        """Processa resultado final do TSP"""
        self.final_result = message.data
        self.waiting_for_result = False

        # Log do resultado
        if "best_solution" in self.final_result:
            solution = self.final_result["best_solution"]
            self.logger.info(f"Solution received - Cost: {solution['best_cost']}")
            self.logger.info(f"Path: {' -> '.join(solution['best_path'])}")

    def _handle_error(self, message: Message, sender_socket=None):
        """Processa mensagem de erro"""
        error_data = message.data
        self.logger.error(f"Received error from coordinator: {error_data}")
        self.waiting_for_result = False
