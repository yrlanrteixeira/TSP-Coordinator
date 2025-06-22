import logging
import socket
import threading
import time
from typing import Callable, Dict, List, Optional

from .message_types import Message, MessageType


class NetworkNode:
    def __init__(self, node_id: str, host: str = "localhost"):
        self.node_id = node_id
        self.host = host
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.sequence_counter = 0
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.logger = logging.getLogger(f"{node_id}")

    def create_message(self, msg_type: MessageType, data: any = None) -> Message:
        """Cria uma mensagem com timestamp e número de sequência"""
        self.sequence_counter += 1
        return Message(
            msg_type=msg_type,
            sender_id=self.node_id,
            timestamp=time.time(),
            data=data,
            sequence_number=self.sequence_counter,
        )

    def send_message(self, sock: socket.socket, message: Message) -> bool:
        """Envia mensagem através do socket"""
        try:
            msg_json = message.to_json()
            msg_bytes = msg_json.encode("utf-8")
            msg_length = len(msg_bytes)

            # Envia tamanho da mensagem primeiro (4 bytes)
            sock.send(msg_length.to_bytes(4, byteorder="big"))
            # Envia a mensagem
            sock.send(msg_bytes)

            self.logger.debug(f"Sent {message.msg_type.value} to {sock.getpeername()}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def receive_message(self, sock: socket.socket) -> Optional[Message]:
        """Recebe mensagem do socket"""
        try:
            # Recebe tamanho da mensagem (4 bytes)
            msg_length_bytes = sock.recv(4)
            if not msg_length_bytes:
                return None

            msg_length = int.from_bytes(msg_length_bytes, byteorder="big")

            # Recebe a mensagem completa
            msg_bytes = b""
            while len(msg_bytes) < msg_length:
                chunk = sock.recv(msg_length - len(msg_bytes))
                if not chunk:
                    break
                msg_bytes += chunk

            if len(msg_bytes) != msg_length:
                raise Exception("Incomplete message received")

            msg_json = msg_bytes.decode("utf-8")
            message = Message.from_json(msg_json)

            self.logger.debug(
                f"Received {message.msg_type.value} from {message.sender_id}"
            )
            return message

        except Exception as e:
            self.logger.error(f"Error receiving message: {e}")
            return None

    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Registra handler para tipo de mensagem"""
        self.message_handlers[msg_type] = handler

    def handle_message(self, message: Message, sender_socket: socket.socket = None):
        """Processa mensagem recebida"""
        if message.msg_type in self.message_handlers:
            try:
                self.message_handlers[message.msg_type](message, sender_socket)
            except Exception as e:
                self.logger.error(f"Error handling {message.msg_type.value}: {e}")
        else:
            self.logger.warning(
                f"No handler for message type: {message.msg_type.value}"
            )


class TCPClient(NetworkNode):
    def __init__(self, node_id: str, server_host: str, server_port: int):
        super().__init__(node_id)
        self.server_host = server_host
        self.server_port = server_port
        self.connected = False

    def connect(self) -> bool:
        """Conecta ao servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            self.logger.info(f"Connected to {self.server_host}:{self.server_port}")

            # Inicia thread para receber mensagens
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Desconecta do servidor"""
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.logger.info("Disconnected from server")

    def send(self, message: Message) -> bool:
        """Envia mensagem para o servidor"""
        if not self.connected or not self.socket:
            return False
        return self.send_message(self.socket, message)

    def _receive_loop(self):
        """Loop para receber mensagens do servidor"""
        while self.running and self.connected:
            try:
                message = self.receive_message(self.socket)
                if message:
                    self.handle_message(message, self.socket)
                else:
                    break
            except Exception as e:
                self.logger.error(f"Receive loop error: {e}")
                break

        self.connected = False


class TCPServer(NetworkNode):
    def __init__(self, node_id: str, host: str, port: int, max_connections: int = 10):
        super().__init__(node_id, host)
        self.port = port
        self.max_connections = max_connections
        self.client_sockets: Dict[str, socket.socket] = {}
        self.client_threads: List[threading.Thread] = []

    def start(self) -> bool:
        """Inicia o servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.max_connections)

            self.running = True
            self.logger.info(f"Server started on {self.host}:{self.port}")

            # Thread para aceitar conexões
            self.accept_thread = threading.Thread(target=self._accept_loop)
            self.accept_thread.daemon = True
            self.accept_thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Server start failed: {e}")
            return False

    def stop(self):
        """Para o servidor"""
        self.running = False

        # Fecha conexões de clientes
        for client_id, sock in self.client_sockets.items():
            try:
                sock.close()
            except:
                pass

        # Fecha socket do servidor
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.logger.info("Server stopped")

    def send_to_client(self, client_id: str, message: Message) -> bool:
        """Envia mensagem para cliente específico"""
        if client_id in self.client_sockets:
            return self.send_message(self.client_sockets[client_id], message)
        return False

    def broadcast(self, message: Message, exclude_client: str = None):
        """Envia mensagem para todos os clientes conectados"""
        for client_id, sock in self.client_sockets.items():
            if client_id != exclude_client:
                self.send_message(sock, message)

    def _accept_loop(self):
        """Loop para aceitar novas conexões"""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                self.logger.info(f"New connection from {address}")

                # Thread para lidar com este cliente
                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                self.client_threads.append(client_thread)

            except Exception as e:
                if self.running:
                    self.logger.error(f"Accept loop error: {e}")
                break

    def _handle_client(self, client_socket: socket.socket, address):
        """Lida com mensagens de um cliente"""
        client_id = None

        try:
            while self.running:
                message = self.receive_message(client_socket)
                if message:
                    # Se é primeira mensagem, registra o cliente
                    if client_id is None:
                        client_id = message.sender_id
                        self.client_sockets[client_id] = client_socket
                        self.logger.info(f"Client {client_id} registered")

                    self.handle_message(message, client_socket)
                else:
                    break

        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            # Remove cliente ao desconectar
            if client_id and client_id in self.client_sockets:
                del self.client_sockets[client_id]
                self.logger.info(f"Client {client_id} disconnected")

            try:
                client_socket.close()
            except:
                pass
