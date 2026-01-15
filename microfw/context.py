from dataclasses import dataclass, field
from typing import List, Optional
import time

@dataclass
class RequestContext:
    trace_id: str
    span_id: str
    start_time: float = field(default_factory=time.time)
    deadline: float = field(default_factory=lambda: time.time() + 30.0) # Default 30s deadline
    service_name: str = "unknown-service"
    spans: List[dict] = field(default_factory=list)

    def remaining_time(self) -> float:
        return max(0.0, self.deadline - time.time())
