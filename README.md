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
```
