import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ecupl_course_sniper import (  # noqa: E402
    AttemptStatus,
    Course,
    CourseSniper,
    InMemoryGateway,
)


class CourseSniperTests(unittest.TestCase):
    def test_dry_run_does_not_take_a_seat(self) -> None:
        gateway = InMemoryGateway([Course("LAW101", "Law", capacity=1, enrolled=0)])

        result = CourseSniper(gateway).run_once("LAW101", "student-1")

        self.assertEqual(result.status, AttemptStatus.WOULD_ENROLL)
        self.assertEqual(gateway.get_course("LAW101").seats_available, 1)

    def test_simulated_submit_takes_one_seat(self) -> None:
        gateway = InMemoryGateway([Course("LAW101", "Law", capacity=1, enrolled=0)])

        result = CourseSniper(gateway, dry_run=False).run_once("LAW101", "student-1")

        self.assertEqual(result.status, AttemptStatus.ENROLLED)
        self.assertEqual(gateway.get_course("LAW101").seats_available, 0)

    def test_gateway_submit_is_idempotent(self) -> None:
        gateway = InMemoryGateway([Course("LAW101", "Law", capacity=2, enrolled=0)])
        sniper = CourseSniper(gateway, dry_run=False)

        first = sniper.run_once("LAW101", "student-1")
        second = sniper.run_once("LAW101", "student-1")

        self.assertEqual(first.status, AttemptStatus.ENROLLED)
        self.assertEqual(second.status, AttemptStatus.ALREADY_ENROLLED)
        self.assertEqual(gateway.get_course("LAW101").enrolled, 1)

    def test_no_submit_when_course_is_full(self) -> None:
        gateway = InMemoryGateway([Course("LAW101", "Law", capacity=1, enrolled=1)])

        result = CourseSniper(gateway, dry_run=False).run_once("LAW101", "student-1")

        self.assertEqual(result.status, AttemptStatus.UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()

