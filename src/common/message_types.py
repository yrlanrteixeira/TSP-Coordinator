import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class MessageType(Enum):
    # Registro e controle
    REGISTER = "REGISTER"
    REGISTER_ACK = "REGISTER_ACK"
    UNREGISTER = "UNREGISTER"

    # Tarefas TSP
    TASK_REQUEST = "TASK_REQUEST"
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_RESULT = "TASK_RESULT"
    TASK_COMPLETE = "TASK_COMPLETE"

    # Monitoramento
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    STATUS_REQUEST = "STATUS_REQUEST"
    STATUS_RESPONSE = "STATUS_RESPONSE"

    # Eleição de líder
    ELECTION = "ELECTION"
    COORDINATOR_ANNOUNCE = "COORDINATOR_ANNOUNCE"

    # Controle
    SHUTDOWN = "SHUTDOWN"
    ERROR = "ERROR"


@dataclass
class Message:
    msg_type: MessageType
    sender_id: str
    timestamp: float
    data: Optional[Any] = None
    sequence_number: int = 0

    def to_json(self) -> str:
        return json.dumps(
            {
                "msg_type": self.msg_type.value,
                "sender_id": self.sender_id,
                "timestamp": self.timestamp,
                "data": self.data,
                "sequence_number": self.sequence_number,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        data = json.loads(json_str)
        return cls(
            msg_type=MessageType(data["msg_type"]),
            sender_id=data["sender_id"],
            timestamp=data["timestamp"],
            data=data.get("data"),
            sequence_number=data.get("sequence_number", 0),
        )
