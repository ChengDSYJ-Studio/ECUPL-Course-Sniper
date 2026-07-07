from dataclasses import replace
from threading import Lock

from .models import AttemptResult, AttemptStatus, Course


class InMemoryGateway:
    """Thread-safe local simulator used by demos and tests."""

    def __init__(self, courses: list[Course]) -> None:
        self._courses = {course.course_id: course for course in courses}
        self._enrollments: set[tuple[str, str]] = set()
        self._lock = Lock()

    def get_course(self, course_id: str) -> Course:
        try:
            return self._courses[course_id]
        except KeyError as error:
            raise LookupError(f"unknown course: {course_id}") from error

    def enroll(self, course_id: str, student_id: str) -> AttemptResult:
        key = (student_id, course_id)
        with self._lock:
            course = self.get_course(course_id)
            if key in self._enrollments:
                return AttemptResult(
                    course_id=course_id,
                    student_id=student_id,
                    status=AttemptStatus.ALREADY_ENROLLED,
                    message="the simulated enrollment already exists",
                )
            if course.seats_available == 0:
                return AttemptResult(
                    course_id=course_id,
                    student_id=student_id,
                    status=AttemptStatus.REJECTED,
                    message="the last simulated seat was taken",
                )

            self._courses[course_id] = replace(course, enrolled=course.enrolled + 1)
            self._enrollments.add(key)
            return AttemptResult(
                course_id=course_id,
                student_id=student_id,
                status=AttemptStatus.ENROLLED,
                message="simulated enrollment completed",
            )

