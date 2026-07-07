from .gateway import CourseGateway
from .models import AttemptResult, AttemptStatus


class CourseSniper:
    """Coordinates one safe check-and-attempt cycle."""

    def __init__(self, gateway: CourseGateway, *, dry_run: bool = True) -> None:
        self._gateway = gateway
        self._dry_run = dry_run

    def run_once(self, course_id: str, student_id: str) -> AttemptResult:
        course = self._gateway.get_course(course_id)
        if course.seats_available == 0:
            return AttemptResult(
                course_id=course_id,
                student_id=student_id,
                status=AttemptStatus.UNAVAILABLE,
                message="no simulated seat is currently available",
            )
        if self._dry_run:
            return AttemptResult(
                course_id=course_id,
                student_id=student_id,
                status=AttemptStatus.WOULD_ENROLL,
                message="seat available; dry-run only",
            )
        return self._gateway.enroll(course_id, student_id)

