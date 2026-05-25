# 软著工厂 MVP

自动化软件著作权申报材料生成系统。

## 快速开始

```bash
# 安装依赖
pip install jinja2 playwright python-docx
playwright install chromium

# 确认中文字体（Linux）
fc-list :lang=zh
# 如果没有：apt-get install fonts-noto-cjk
# macOS 通常自带中文字体

# 运行截图验证
python screenshot_mvp.py
```

## 目录结构

```
softcopyright-mvp/
├── template.html        # Jinja2 模板（数据看板风格）
├── data.json            # Mock 数据（注入模板）
├── screenshot_mvp.py    # Playwright 截图脚本
├── orchestrator.py      # P1-P5 中控状态机
├── ai_client.py         # OpenAI-compatible AI API 调用封装
├── renderer.py          # 根据 P1 数据和模板渲染截图
├── packer.py            # 生成软著申报 Word 文档
├── checker.py           # AST 与相似度校验
├── prompts/             # P1/P2/P3 AI 角色提示词
├── projects/            # 项目实例输出目录（运行后生成）
├── render_outputs/      # 截图输出目录（运行后生成）
└── README.md
```

## 五阶段流水线（规划）

| 阶段 | 角色 | 输入 | 输出 |
|------|------|------|------|
| P1 Insight | 分析师 AI | 公司全称 + 软件名 | p1_insight.json |
| P2 Design | 架构师 AI | p1_insight.json | p2_architecture.json |
| P3 Coding | 程序员 AI | p1 + p2 JSON | 15-25 个源文件 |
| P4 Rendering | Python 脚本 | 模板 + 数据 JSON | 15-20 张截图 |
| P5 Packaging | Python 脚本 | 截图 + 代码 | Word 文档 / 申报包 |

## 核心设计

- **Style_Seed**: 每个项目一个风格配置对象，确保代码差异化
- **Mock_Data_Schema**: 架构师定义数据契约，程序员和渲染脚本共享字段名
- **自愈逻辑**: ast.parse() 失败时，最多重试 2 次，仅传错误上下文
- **门控审批**: 每个阶段结束后 input("y/n") 等待人工确认

## 依赖

- Python 3.10+
- jinja2
- playwright
- python-docx（用于生成软著申报 Word 文档）

## 环境变量配置

项目启动时会自动读取根目录下的 `.env` 文件，不需要额外安装 `python-dotenv`。

- `.env`：本地真实配置文件，已加入 `.gitignore`，不要提交密钥或私有路径。
- `.env.example`：可提交的配置模板，完整列出所有环境变量，并在每个变量上方说明用途。
- `SOFTCOPYRIGHT_ENV_FILE` 只能在启动脚本前通过系统环境变量指定；写在 `.env`
  文件内部不会改变本次加载路径。
- `SOFTCOPYRIGHT_AI_API_KEY` 留空时，会按 `SOFTCOPYRIGHT_AUTH_PATH` 和
  `SOFTCOPYRIGHT_AUTH_PROVIDER` 从本地认证文件读取 API key。

常用配置项：

```bash
# AI 服务地址、模型和调用参数
SOFTCOPYRIGHT_AI_API_URL=https://inference-api.nousresearch.com/v1/chat/completions
SOFTCOPYRIGHT_AI_MODEL=xiaomi/mimo-v2-pro
SOFTCOPYRIGHT_AI_TIMEOUT_SECONDS=300

# 项目输出、prompt 和模板路径
SOFTCOPYRIGHT_PROJECTS_DIR=projects
SOFTCOPYRIGHT_PROMPTS_DIR=prompts
SOFTCOPYRIGHT_DEFAULT_TEMPLATE_PATH=template.html
SOFTCOPYRIGHT_DEFAULT_DATA_PATH=data.json

# 截图渲染参数
SOFTCOPYRIGHT_RENDER_OUTPUT_DIR=render_outputs
SOFTCOPYRIGHT_TAILWIND_CDN_URL=https://cdn.tailwindcss.com
SOFTCOPYRIGHT_VIEWPORT_WIDTH=1280
SOFTCOPYRIGHT_VIEWPORT_HEIGHT=800
SOFTCOPYRIGHT_THEME_COLOR=#1E40AF

# Word 文档和代码截取参数
SOFTCOPYRIGHT_DOC_BODY_FONT=仿宋_GB2312
SOFTCOPYRIGHT_SOURCE_FRONT_PAGES=30
SOFTCOPYRIGHT_SOURCE_BACK_PAGES=30
SOFTCOPYRIGHT_SOURCE_LINES_PER_PAGE=50
```

## 常用入口

```bash
# 最小截图链路验证
python screenshot_mvp.py

# 根据 P1 数据渲染截图
python renderer.py --template template.html --data projects/<项目名>/p1_insight.json --output projects/<项目名>/screenshots

# 检查生成代码
python checker.py projects/<项目名>

# 生成申报文档
python packer.py --project-dir projects/<项目名> --output projects/<项目名>/package

# 补生成缺失代码文件，也可通过 SOFTCOPYRIGHT_TARGET_PROJECT_DIR 配置目标项目目录
python generate_remaining.py projects/<项目名>
```
