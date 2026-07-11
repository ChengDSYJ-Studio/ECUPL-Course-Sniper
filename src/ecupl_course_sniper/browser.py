"""Browser-driven course selection for pages opened by the student."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path


ACTION_WORDS = ("选课", "选择", "报名", "加入")
SUCCESS_WORDS = ("选课成功", "操作成功", "已选", "报名成功", "选择成功")
FULL_WORDS = ("已满", "无余量", "人数已满", "容量已满", "不可选")


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_choices(raw: str, size: int) -> list[int]:
    values = []
    for part in raw.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit() or not 1 <= int(part) <= size:
            raise ValueError(f"无效编号: {part}")
        index = int(part) - 1
        if index not in values:
            values.append(index)
    if not values:
        raise ValueError("至少选择一门课程")
    return values


@dataclass(frozen=True, slots=True)
class PageCourse:
    text: str
    key: str


class BrowserCourseSniper:
    def __init__(
        self,
        *,
        url: str,
        profile: Path,
        interval: float = 8.0,
        submit: bool = False,
    ) -> None:
        if not 0.001 <= interval <= 10:
            raise ValueError("轮询间隔必须在 0.001 到 10 秒之间")
        self.url = url
        self.profile = profile
        self.interval = interval
        self.submit = submit

    @staticmethod
    def _discover(page) -> list[PageCourse]:
        records = page.locator("tr, [role=row], .course-item, .course-card, .el-card")
        found: list[PageCourse] = []
        seen: set[str] = set()
        for i in range(min(records.count(), 500)):
            row = records.nth(i)
            text = compact(row.inner_text())
            if len(text) < 4 or not any(word in text for word in ACTION_WORDS + FULL_WORDS):
                continue
            # Remove volatile button/status labels while retaining course/class identity.
            key = text
            for word in ACTION_WORDS + SUCCESS_WORDS + FULL_WORDS:
                key = key.replace(word, " ")
            key = compact(key)[:180]
            if len(key) < 2 or key in seen:
                continue
            seen.add(key)
            found.append(PageCourse(text=text[:240], key=key))
        return found

    @staticmethod
    def _find_row(page, course: PageCourse):
        candidates = page.locator("tr, [role=row], .course-item, .course-card, .el-card")
        best = None
        best_score = 0
        tokens = [token for token in re.split(r"[ |/]", course.key) if len(token) >= 2]
        for i in range(min(candidates.count(), 500)):
            row = candidates.nth(i)
            text = compact(row.inner_text())
            score = sum(token in text for token in tokens)
            if score > best_score:
                best, best_score = row, score
        threshold = 1 if len(tokens) < 3 else min(3, len(tokens))
        return best if best_score >= threshold else None

    @staticmethod
    def _action_button(row):
        controls = row.locator("button, a, [role=button]")
        for i in range(controls.count()):
            control = controls.nth(i)
            label = compact(control.inner_text())
            if any(word in label for word in ACTION_WORDS) and control.is_visible():
                return control
        return None

    @staticmethod
    def _page_message(page) -> str:
        notices = page.locator(
            "[role=alert], .el-message, .ant-message, .toast, .notification, .modal"
        )
        messages = []
        for i in range(min(notices.count(), 20)):
            item = notices.nth(i)
            if item.is_visible():
                messages.append(compact(item.inner_text()))
        return " | ".join(messages)

    def run(self) -> int:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise RuntimeError(
                "缺少 Playwright，请运行: pip install -e . && playwright install chromium"
            ) from error

        self.profile.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(self.profile), headless=False, viewport=None
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.on("dialog", lambda dialog: dialog.accept())
            if not page.url.startswith(self.url):
                page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)

            print("请在浏览器中完成登录，进入选课列表并设置好筛选条件。")
            input("页面准备好后按回车扫描课程: ")
            courses = self._discover(page)
            if not courses:
                print("没有发现课程行。请展开课程列表后重试，或运行 inspect 保存页面信息。")
                return 2

            for number, course in enumerate(courses, 1):
                print(f"[{number}] {course.text}")
            while True:
                try:
                    selected = parse_choices(input("输入目标课程编号（逗号分隔）: "), len(courses))
                    break
                except ValueError as error:
                    print(error)
            targets = [courses[index] for index in selected]
            mode = "自动提交" if self.submit else "只监测（dry-run）"
            print(f"已选择 {len(targets)} 门，模式={mode}，间隔={self.interval:.1f}s")

            while True:
                for target in list(targets):
                    row = self._find_row(page, target)
                    if row is None:
                        print(f"[{time.strftime('%H:%M:%S')}] 未找到: {target.key[:60]}")
                        continue
                    row_text = compact(row.inner_text())
                    if any(word in row_text for word in SUCCESS_WORDS):
                        print(f"已选: {target.key[:80]}")
                        targets.remove(target)
                        continue
                    button = self._action_button(row)
                    available = button is not None and button.is_enabled() and not any(
                        word in row_text for word in FULL_WORDS
                    )
                    print(
                        f"[{time.strftime('%H:%M:%S')}] "
                        f"{'可选' if available else '暂无名额'}: {target.key[:80]}"
                    )
                    if not available:
                        continue
                    if not self.submit:
                        continue
                    button.click()
                    page.wait_for_timeout(800)
                    confirm = page.locator(
                        "button:has-text('确定'), button:has-text('确认'), "
                        "button:has-text('提交')"
                    )
                    visible = [confirm.nth(i) for i in range(confirm.count()) if confirm.nth(i).is_visible()]
                    if len(visible) == 1:
                        visible[0].click()
                        page.wait_for_timeout(1200)
                    message = self._page_message(page)
                    if any(word in message for word in SUCCESS_WORDS):
                        print(f"成功: {target.key[:80]} ({message})")
                        targets.remove(target)
                    else:
                        print(f"已提交，页面消息: {message or '无'}")
                if not targets:
                    print("所有目标课程均已完成。")
                    return 0
                page.wait_for_timeout(int(self.interval * 1000))
                page.reload(wait_until="domcontentloaded", timeout=60_000)


def inspect_page(*, url: str, profile: Path, output: Path) -> int:
    from playwright.sync_api import sync_playwright

    profile.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), headless=False, viewport=None
        )
        page = context.pages[0] if context.pages else context.new_page()
        if not page.url.startswith(url):
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        input("登录并进入课程列表后按回车保存页面结构: ")
        output.write_text(page.locator("body").inner_text(), encoding="utf-8")
        print(f"页面文本已保存到 {output}")
    return 0
