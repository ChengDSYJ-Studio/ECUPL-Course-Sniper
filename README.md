# ECUPL Course Sniper

## 没有人比我更懂抢课
一个正在制作的华政抢课脚本

## 没有人比我更懂Vibe Coding
- 本脚本完全由20刀的Codex制作。
- 没有Gemini 3.5Pro ,我们吃什么?

## 已实现

- 课程及提交结果的数据模型
- 可替换的 `CourseGateway` 接口
- 本地 `InMemoryGateway` 课程与席位模拟器
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

