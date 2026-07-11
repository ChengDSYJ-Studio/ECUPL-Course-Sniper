# ECUPL Course Sniper

## 没有人比我更懂抢课
抢课脚本，理论上适用于全部高校。大数据课作业的一部分，顺便上传过来。

## 浏览器模式

安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

启动可视化界面：

```bash
course-sniper gui
```

依次点击“打开并登录”、“扫描课程”，在列表中多选目标课程，然后设置检查间隔并启动。
界面允许 `0.001–10` 秒的调度间隔；真实页面网络刷新最多每秒一次，防止教务系统限流，
其余快速周期用于检查当前页面状态。

先以只监测模式运行：

```bash
course-sniper browser
```

浏览器打开后手动登录，进入课程列表并设置筛选条件；回到终端按回车，程序会列出
检测到的课程，输入编号即可自行选择目标课程。确认页面适配正确后启用自动提交：

```bash
course-sniper browser --submit --interval 8
```

登录状态保存在被 `.gitignore` 排除的 `data/browser-profile/` 中。若页面无法识别，运行：

```bash
course-sniper inspect
```

该命令会把当前页面可见文本保存至 `data/page-text.txt`，用于调整页面选择器。

## 已实现

- 课程及提交结果的数据模型
- 可替换的 `CourseGateway` 接口
- 本地 `InMemoryGateway` 课程与席位模拟器
- 浏览器内交互选择目标课程
- 课程余量轮询和显式启用的自动提交
- 发现余量后执行一次提交的核心引擎
- 默认开启的 dry-run（只报告、不占位）
- 同一学生与课程的幂等保护
- 无余量、提交成功、重复提交等自动化测试
- GitHub Actions 持续集成

## 快速开始

项目核心只依赖 Python 3.11 标准库：

```bash
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m ecupl_course_sniper demo
```

默认演示为 dry-run：

```text
course=LAW101 status=would_enroll message=seat available; dry-run only
```

显式启用模拟提交：

```bash
PYTHONPATH=src python3 -m ecupl_course_sniper demo --allow-submit
```

该参数只作用于内存模拟器。

## 项目结构

```text
.
├── src/ecupl_course_sniper/
│   ├── models.py       # 数据模型与结果状态
│   ├── gateway.py      # 外部系统抽象接口
│   ├── simulator.py    # 本地课程与席位模拟器
│   ├── engine.py       # 监测、判断、幂等与提交编排
│   └── cli.py          # 命令行演示
├── tests/              # 核心行为测试
├── docs/
│   ├── architecture.md # 架构与数据流
│   └── roadmap.md      # 后续迭代路线
└── .github/workflows/  # CI
```

## 设计边界

- 默认且持续支持模拟环境与 dry-run。
- 不提交账号、Cookie、Token 或个人信息。
- 不绕过验证码、多因素认证、访问控制或频率限制。
- 不对真实教务系统做压力测试或并发抢占。
- 若后续连接任何真实系统，必须取得明确授权，并将适配器放在独立私有配置中。

## 后续方向

详见 [`docs/roadmap.md`](docs/roadmap.md)。第一优先级是完善模拟服务、并发测试、
可观测性和演示界面，而不是连接真实教务系统。

## License

[MIT](LICENSE)
