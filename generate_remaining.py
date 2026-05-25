"""批量生成指定项目中尚未生成的代码文件。"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

import config
from ai_client import call_ai_json


def load_json_file(path: Path) -> dict:
    """
    读取 JSON 文件。

    Args:
        path: JSON 文件路径。

    Returns:
        JSON 解析后的字典。

    Raises:
        FileNotFoundError: 文件不存在时抛出。
        json.JSONDecodeError: JSON 格式错误时抛出。
    """
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def load_prompt_file(name: str) -> str:
    """
    读取指定 prompt 文件。

    Args:
        name: prompt 文件名，不包含 .txt 后缀。

    Returns:
        prompt 文本。

    Raises:
        FileNotFoundError: prompt 文件不存在时抛出。
    """
    prompt_path = config.PROMPTS_DIR / f"{name}.txt"
    with prompt_path.open("r", encoding="utf-8") as prompt_file:
        return prompt_file.read()


def load_existing_code_files(code_dir: Path) -> tuple[list[dict], set[str]]:
    """
    加载已经生成的 Python 文件。

    Args:
        code_dir: 项目代码目录。

    Returns:
        已生成文件摘要列表和相对路径集合。
    """
    generated_files = []
    existing_paths = set()

    if not code_dir.exists():
        return generated_files, existing_paths

    for root, _, file_names in os.walk(code_dir):
        for file_name in sorted(file_names):
            if not file_name.endswith(".py"):
                continue

            file_path = Path(root) / file_name
            content = file_path.read_text(encoding="utf-8")
            relative_path = str(file_path.relative_to(code_dir))
            line_count = len([line for line in content.split("\n") if line.strip()])
            generated_files.append({
                "file_path": relative_path,
                "content": content,
                "line_count": line_count,
            })
            existing_paths.add(relative_path)

    return generated_files, existing_paths


def build_related_summary(file_info: dict, generated_files: list[dict]) -> str:
    """
    根据当前文件依赖构造已生成文件摘要。

    Args:
        file_info: 架构阶段定义的当前文件信息。
        generated_files: 已生成文件摘要列表。

    Returns:
        相关文件摘要文本。
    """
    related_summary = ""
    summary_chars = config.GENERATE_REMAINING_RELATED_CHARS

    for dependency in file_info.get("depends_on", []):
        dependency_name = dependency.split("/")[-1]
        for generated_file in generated_files:
            if generated_file["file_path"].endswith(dependency_name):
                content = generated_file["content"][:summary_chars]
                related_summary += f"\n--- {dependency} ---\n{content}...\n"

    return related_summary


def build_generation_prompt(
    file_info: dict,
    p1_data: dict,
    generated_files: list[dict],
) -> str:
    """
    构造单个代码文件的生成 prompt。

    Args:
        file_info: 当前待生成文件信息。
        p1_data: P1 阶段企业画像与数据 schema。
        generated_files: 已生成文件摘要列表。

    Returns:
        用于 AI 代码生成的 prompt。
    """
    style_seed = json.dumps(p1_data.get("style_seed", {}), ensure_ascii=False)
    terminology = json.dumps(p1_data.get("terminology_map", {}), ensure_ascii=False)
    mock_schema = json.dumps(p1_data.get("mock_data_schema", {}), ensure_ascii=False)
    related_summary = build_related_summary(file_info, generated_files)

    return (
        f"## 风格配置\n{style_seed}\n\n"
        f"## 术语映射\n{terminology}\n\n"
        f"## 数据 Schema\n{mock_schema}\n\n"
        f"## 当前文件\n{json.dumps(file_info, ensure_ascii=False)}\n\n"
        f"## 已生成的相关文件摘要\n{related_summary if related_summary else '（无）'}\n\n"
        f"请生成这个文件的完整源代码。"
    )


def resolve_target_project_dir(argv: list[str]) -> Path:
    """
    解析目标项目目录。

    Args:
        argv: 命令行参数列表。

    Returns:
        目标项目绝对路径。

    Raises:
        ValueError: 未配置目标项目目录时抛出。
    """
    target_project_dir = argv[1] if len(argv) > 1 else config.TARGET_PROJECT_DIR
    if not target_project_dir:
        raise ValueError("请设置 SOFTCOPYRIGHT_TARGET_PROJECT_DIR 或传入项目目录参数")
    return config.resolve_path(target_project_dir)


def generate_remaining_files(project_dir: Path) -> None:
    """
    生成项目中架构已定义但尚不存在的代码文件。

    Args:
        project_dir: 项目实例目录。

    Raises:
        FileNotFoundError: P1、P2 或 prompt 文件不存在时抛出。
    """
    p1_data = load_json_file(project_dir / "p1_insight.json")
    p2_data = load_json_file(project_dir / "p2_architecture.json")
    p3_system = load_prompt_file("coder")
    code_dir = project_dir / "code"
    code_dir.mkdir(parents=True, exist_ok=True)

    generated_files, existing_paths = load_existing_code_files(code_dir)
    all_files = p2_data.get("file_tree", [])
    remaining_files = [file_info for file_info in all_files if file_info.get("path") not in existing_paths]

    print(f"已有: {len(generated_files)} 个文件, {sum(g['line_count'] for g in generated_files)} 行")
    print(f"待生成: {len(remaining_files)} 个文件")
    print()

    total_tokens = 0
    for index, file_info in enumerate(remaining_files):
        file_path = file_info.get("path", f"unknown_{index}.py")
        print(f"[{index + 1}/{len(remaining_files)}] {file_path} ...", end="", flush=True)

        prompt = build_generation_prompt(file_info, p1_data, generated_files)

        for attempt in range(config.P3_MAX_RETRIES):
            try:
                result = call_ai_json(prompt, system_prompt=p3_system)
                total_tokens += result["tokens"]
                code_content = result["parsed"].get("content", "")

                if file_path.endswith(".py"):
                    ast.parse(code_content)

                output_path = code_dir / file_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(code_content, encoding="utf-8")

                actual_lines = len([line for line in code_content.split("\n") if line.strip()])
                generated_files.append({
                    "file_path": file_path,
                    "content": code_content,
                    "line_count": actual_lines,
                })
                print(f" ✅ {actual_lines}行 ({result['elapsed']}s, {result['tokens']}t)")
                break
            except SyntaxError as exc:
                if attempt < config.P3_MAX_RETRIES - 1:
                    print(" 语法错误重试...", end="", flush=True)
                else:
                    print(f" ❌ 语法错误: {exc}")
            except Exception as exc:
                if attempt < config.P3_MAX_RETRIES - 1:
                    print(" 重试...", end="", flush=True)
                else:
                    print(f" ❌ {exc}")

    total_lines = sum(generated_file["line_count"] for generated_file in generated_files)
    print(f"\n{'=' * 50}")
    print("✅ P3 全部完成")
    print(f"  文件数: {len(generated_files)} / {len(all_files)}")
    print(f"  总行数: {total_lines}")
    print(f"  本轮Token: {total_tokens}")


def main() -> None:
    """
    执行补生成脚本入口。

    Raises:
        SystemExit: 参数错误或运行失败时以非零状态退出。
    """
    try:
        project_dir = resolve_target_project_dir(sys.argv)
        generate_remaining_files(project_dir)
    except Exception as exc:
        print(f"❌ 补生成失败: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
