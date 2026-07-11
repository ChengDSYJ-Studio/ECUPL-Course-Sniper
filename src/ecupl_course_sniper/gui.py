"""Tkinter desktop interface for browser-based course selection."""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .browser import BrowserCourseSniper, PageCourse, compact


class BrowserWorker(threading.Thread):
    """Own Playwright in one thread and communicate with Tk through queues."""

    def __init__(self, commands: queue.Queue, events: queue.Queue) -> None:
        super().__init__(daemon=True)
        self.commands = commands
        self.events = events

    def emit(self, kind: str, payload=None) -> None:
        self.events.put((kind, payload))

    def run(self) -> None:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                context = None
                page = None
                targets: list[PageCourse] = []
                running = False
                submit = False
                interval = 8.0
                next_check = 0.0
                last_reload = 0.0
                while True:
                    timeout = max(0.001, next_check - time.monotonic()) if running else 0.1
                    try:
                        command, data = self.commands.get(timeout=min(timeout, 0.1))
                    except queue.Empty:
                        command = None

                    if command == "quit":
                        if context:
                            context.close()
                        return
                    if command == "open":
                        if context:
                            context.close()
                        profile = Path(data["profile"])
                        profile.mkdir(parents=True, exist_ok=True)
                        context = playwright.chromium.launch_persistent_context(
                            str(profile), headless=False, viewport=None
                        )
                        page = context.pages[0] if context.pages else context.new_page()
                        page.on("dialog", lambda dialog: dialog.accept())
                        page.goto(data["url"], wait_until="domcontentloaded", timeout=60_000)
                        self.emit("status", "浏览器已打开，请手动登录并进入课程列表")
                    elif command == "scan":
                        if page is None:
                            self.emit("error", "请先打开浏览器")
                        else:
                            courses = BrowserCourseSniper._discover(page)
                            self.emit("courses", courses)
                            self.emit("status", f"发现 {len(courses)} 门可识别课程")
                    elif command == "start":
                        if page is None:
                            self.emit("error", "请先打开浏览器")
                            continue
                        targets = data["targets"]
                        interval = data["interval"]
                        submit = data["submit"]
                        running = True
                        next_check = time.monotonic()
                        self.emit("status", "自动选课运行中" if submit else "余量监测运行中")
                    elif command == "stop":
                        running = False
                        self.emit("status", "已停止")

                    now = time.monotonic()
                    if not running or page is None or now < next_check:
                        continue
                    next_check = now + interval
                    # The UI scheduler supports 1 ms precision. Network reloads are capped at
                    # once per second to avoid flooding the teaching system.
                    if now - last_reload >= max(1.0, interval):
                        page.reload(wait_until="domcontentloaded", timeout=60_000)
                        last_reload = now
                    for target in list(targets):
                        row = BrowserCourseSniper._find_row(page, target)
                        if row is None:
                            self.emit("log", f"未找到 | {target.key[:100]}")
                            continue
                        text = compact(row.inner_text())
                        button = BrowserCourseSniper._action_button(row)
                        available = button is not None and button.is_enabled()
                        self.emit("log", f"{'可选' if available else '等待'} | {target.key[:100]}")
                        if not available or not submit:
                            continue
                        button.click()
                        page.wait_for_timeout(500)
                        confirms = page.locator(
                            "button:has-text('确定'), button:has-text('确认'), button:has-text('提交')"
                        )
                        visible = [
                            confirms.nth(i)
                            for i in range(confirms.count())
                            if confirms.nth(i).is_visible()
                        ]
                        if len(visible) == 1:
                            visible[0].click()
                            page.wait_for_timeout(800)
                        message = BrowserCourseSniper._page_message(page)
                        self.emit("log", f"已提交 | {target.key[:100]} | {message or '等待结果'}")
                        if any(word in message for word in ("成功", "已选")):
                            targets.remove(target)
                    if not targets:
                        running = False
                        self.emit("done", "所有目标课程均已完成")
        except Exception as error:  # Keep GUI failures visible instead of losing the thread.
            self.emit("error", str(error))


class CourseSniperApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ECUPL 课程监测与选课")
        self.root.geometry("940x680")
        self.commands: queue.Queue = queue.Queue()
        self.events: queue.Queue = queue.Queue()
        self.worker = BrowserWorker(self.commands, self.events)
        self.worker.start()
        self.courses: list[PageCourse] = []

        self.url = tk.StringVar(value="https://jwgl.ecupl.edu.cn/course-selection")
        self.profile = tk.StringVar(value="data/browser-profile")
        self.interval = tk.StringVar(value="8")
        self.submit = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="准备就绪")
        self._build()
        self.root.after(100, self._poll_events)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        settings = ttk.LabelFrame(outer, text="连接设置", padding=10)
        settings.pack(fill="x")
        ttk.Label(settings, text="选课网址").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings, textvariable=self.url).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Label(settings, text="浏览器数据").grid(row=1, column=0, sticky="w")
        ttk.Entry(settings, textvariable=self.profile).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(settings, text="1. 打开并登录", command=self._open).grid(row=0, column=2)
        ttk.Button(settings, text="2. 扫描课程", command=self._scan).grid(row=1, column=2)
        settings.columnconfigure(1, weight=1)

        course_box = ttk.LabelFrame(outer, text="课程列表（可多选）", padding=10)
        course_box.pack(fill="both", expand=True, pady=10)
        self.listbox = tk.Listbox(course_box, selectmode=tk.EXTENDED, exportselection=False)
        scroll = ttk.Scrollbar(course_box, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        controls = ttk.Frame(outer)
        controls.pack(fill="x")
        ttk.Label(controls, text="检查间隔（0.001–10 秒）").pack(side="left")
        ttk.Entry(controls, textvariable=self.interval, width=9).pack(side="left", padx=8)
        ttk.Checkbutton(controls, text="自动点击选课（关闭时仅监测）", variable=self.submit).pack(
            side="left", padx=10
        )
        ttk.Button(controls, text="开始", command=self._start).pack(side="right")
        ttk.Button(controls, text="停止", command=self._stop).pack(side="right", padx=8)

        logs = ttk.LabelFrame(outer, text="运行日志", padding=8)
        logs.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(logs, height=9, state="disabled")
        self.log.pack(fill="both", expand=True)
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

    def _open(self) -> None:
        self.commands.put(("open", {"url": self.url.get().strip(), "profile": self.profile.get()}))

    def _scan(self) -> None:
        self.commands.put(("scan", None))

    def _start(self) -> None:
        indexes = list(self.listbox.curselection())
        if not indexes:
            messagebox.showwarning("未选择课程", "请先扫描并选择至少一门课程")
            return
        try:
            interval = float(self.interval.get())
            if not 0.001 <= interval <= 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("间隔无效", "轮询间隔必须在 0.001 到 10 秒之间")
            return
        self.commands.put(
            (
                "start",
                {
                    "targets": [self.courses[i] for i in indexes],
                    "interval": interval,
                    "submit": self.submit.get(),
                },
            )
        )

    def _stop(self) -> None:
        self.commands.put(("stop", None))

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "courses":
                    self.courses = payload
                    self.listbox.delete(0, "end")
                    for course in self.courses:
                        self.listbox.insert("end", course.text)
                elif kind == "status":
                    self.status.set(payload)
                elif kind == "log":
                    self._append_log(payload)
                elif kind == "done":
                    self.status.set(payload)
                    messagebox.showinfo("完成", payload)
                elif kind == "error":
                    self.status.set("发生错误")
                    messagebox.showerror("错误", payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _close(self) -> None:
        self.commands.put(("quit", None))
        self.root.destroy()


def launch_gui() -> int:
    root = tk.Tk()
    CourseSniperApp(root)
    root.mainloop()
    return 0
