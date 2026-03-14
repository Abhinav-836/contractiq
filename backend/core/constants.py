from enum import Enum

# File upload constants
ALLOWED_FILE_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


class ContractStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ObligationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    UPCOMING = "upcoming"


class AlertType(str, Enum):
    EXPIRY = "expiry"
    RISK = "risk"
    OBLIGATION = "obligation"
    RENEWAL = "renewal"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    MOCK = "mock"


CLAUSE_TYPES = [
    "Termination",
    "Liability Cap",
    "Indemnification",
    "Confidentiality",
    "Intellectual Property",
    "Payment Terms",
    "Auto-Renewal",
    "Governing Law",
    "Force Majeure",
    "Data Protection",
    "Non-Compete",
    "Dispute Resolution",
]