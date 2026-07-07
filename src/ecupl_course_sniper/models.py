from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class Course:
    course_id: str
    name: str
    capacity: int
    enrolled: int

    @property
    def seats_available(self) -> int:
        return max(0, self.capacity - self.enrolled)


class AttemptStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    WOULD_ENROLL = "would_enroll"
    ENROLLED = "enrolled"
    ALREADY_ENROLLED = "already_enrolled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AttemptResult:
    course_id: str
    student_id: str
    status: AttemptStatus
    message: str

