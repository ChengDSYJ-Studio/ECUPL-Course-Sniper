import argparse

from .engine import CourseSniper
from .models import Course
from .simulator import InMemoryGateway


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Course-seat simulation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser("demo", help="run one local simulated attempt")
    demo.add_argument("--course-id", default="LAW101")
    demo.add_argument("--student-id", default="demo-student")
    demo.add_argument(
        "--allow-submit",
        action="store_true",
        help="allow submission to the in-memory simulator only",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "demo":
        return 2

    gateway = InMemoryGateway(
        [Course(course_id="LAW101", name="Introduction to Law", capacity=2, enrolled=1)]
    )
    sniper = CourseSniper(gateway, dry_run=not args.allow_submit)
    result = sniper.run_once(args.course_id, args.student_id)
    print(f"course={result.course_id} status={result.status} message={result.message}")
    return 0

