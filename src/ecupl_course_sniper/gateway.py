from typing import Protocol

from .models import AttemptResult, Course


class CourseGateway(Protocol):
    """Boundary between the orchestration code and a course system."""

    def get_course(self, course_id: str) -> Course:
        """Return the latest course state."""

    def enroll(self, course_id: str, student_id: str) -> AttemptResult:
        """Attempt one idempotent enrollment in an authorized environment."""

