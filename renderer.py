"""
软著工厂 - 渲染器
从 p1_insight.json 的 mock_data_schema 自动生成假数据并截图
"""

import argparse
import asyncio
import json
import os
import random
import string
from datetime import datetime, timedelta

from jinja2 import Template
from playwright.async_api import async_playwright

import config


def build_template_settings() -> dict:
    """
    构造模板展示配置。

    Returns:
        模板需要的版本、管理员、刷新和数据源文案。
    """
    return {
        "tailwind_cdn_url": config.TAILWIND_CDN_URL,
        "version_text": config.TEMPLATE_VERSION_TEXT,
        "admin_name": config.TEMPLATE_ADMIN_NAME,
        "refresh_text": config.TEMPLATE_REFRESH_TEXT,
        "data_source_text": config.TEMPLATE_DATA_SOURCE_TEXT,
    }


def apply_template_settings(data: dict) -> dict:
    """
    将环境变量中的模板展示配置合并到渲染数据。

    Args:
        data: 原始渲染数据。

    Returns:
        合并模板展示配置后的新字典。
    """
    return {**data, **build_template_settings()}


def build_cjk_font_style() -> str:
    """
    构造中文字体回退 CSS。

    Returns:
        可注入页面的 CSS 字符串。
    """
    local_fonts = ", ".join(f"local('{font_name}')" for font_name in config.CJK_FONT_FAMILY)
    return f"""
        @font-face {{
            font-family: 'CJKFallback';
            src: {local_fonts};
        }}
        * {{ font-family: 'CJKFallback', sans-serif !important; }}
    """


def generate_mock_value(field: dict) -> str:
    """根据字段规则生成假数据"""
    ftype = field.get("type", "string")
    mock_rule = field.get("mock_rule", "")

    if ftype == "int":
        return str(random.randint(100, 9999))
    elif ftype == "float":
        return f"{random.uniform(10, 999):.1f}"
    elif ftype == "bool":
        return random.choice(["是", "否"])
    elif ftype == "datetime":
        dt = datetime.now() - timedelta(hours=random.randint(0, 72))
        return dt.strftime("%Y-%m-%d %H:%M")
    elif ftype == "enum":
        # 从 mock_rule 中提取选项
        options = [o.strip() for o in mock_rule.replace("、", ",").split(",") if o.strip()]
        return random.choice(options) if options else "正常"
    else:
        # string 类型
        if "编号" in field.get("display", "") or "id" in field.get("name", "").lower():
            return f"{''.join(random.choices(string.ascii_uppercase, k=2))}-{random.randint(1000, 9999)}"
        elif "率" in field.get("display", "") or "度" in field.get("display", ""):
            return f"{random.uniform(85, 99):.1f}%"
        elif "负载" in field.get("display", "") or "电流" in field.get("display", "") or "电压" in field.get("display", ""):
            return f"{random.uniform(100, 2000):.1f}"
        else:
            # 使用 mock_rule 中的提示生成
            return mock_rule if mock_rule else f"数据_{random.randint(1, 100)}"


def build_dashboard_data(p1_data: dict, app_name: str, theme_color: str | None = None) -> dict:
    """从 p1_insight.json 构造仪表盘渲染数据"""
    selected_theme_color = theme_color or config.THEME_COLOR
    mock_schema = p1_data.get("mock_data_schema", {})
    entities = mock_schema.get("entities", [])
    features = p1_data.get("feature_outline", [])

    # 菜单
    menu_items = features[:5] if len(features) >= 5 else features + ["系统设置"]

    # 统计卡片（取第一个实体的数值型字段）
    dashboard_cards = []
    if entities:
        primary = entities[0]
        for f in primary.get("fields", []):
            if f.get("type") in ("int", "float") or "率" in f.get("display", "") or "负载" in f.get("display", ""):
                dashboard_cards.append({
                    "label": f.get("display", f.get("name", "")),
                    "value": generate_mock_value(f),
                })
                if len(dashboard_cards) >= 3:
                    break

    if not dashboard_cards:
        dashboard_cards = [
            {"label": "总数量", "value": str(random.randint(100, 9999))},
            {"label": "今日处理", "value": str(random.randint(50, 500))},
            {"label": "系统健康度", "value": f"{random.randint(90, 99)}%"},
        ]

    # 表格数据（取第一个实体的字段作为列，生成 5 行）
    table_data = []
    primary_entity = entities[0] if entities else {"fields": [], "display_name": "记录"}
    fields = primary_entity.get("fields", [])

    for i in range(5):
        row = {}
        for f in fields[:4]:  # 最多 4 列
            row[f.get("name", "col")] = generate_mock_value(f)
        table_data.append(row)

    return {
        "app_name": app_name,
        "theme_color_hex": selected_theme_color,
        "menu": menu_items,
        "dashboard_cards": dashboard_cards,
        "table_data": table_data,
        "entities": entities,
        "features": features,
        **build_template_settings(),
    }


async def render_and_screenshot(data: dict, template_path: str, output_dir: str) -> list:
    """渲染 HTML 并截图"""
    os.makedirs(output_dir, exist_ok=True)

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    template = Template(html_template)
    rendered_html = template.render(**data)

    # 保存渲染后 HTML
    html_path = os.path.join(output_dir, "rendered.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    screenshots = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.PLAYWRIGHT_HEADLESS)
        page = await browser.new_page(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
        )

        try:
            await page.set_content(rendered_html, wait_until="networkidle")
            await page.add_style_tag(content=build_cjk_font_style())
            await page.wait_for_timeout(config.RENDER_WAIT_MS)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 截图 1：控制面板
            p1 = os.path.join(output_dir, f"01_dashboard_{ts}.png")
            await page.screenshot(path=p1, full_page=False)
            screenshots.append(p1)

            # 截图 2：点击第二个菜单项
            try:
                menu_items = await page.query_selector_all("nav a")
                if len(menu_items) > 1:
                    await menu_items[1].click()
                    await page.wait_for_timeout(config.SUBMENU_WAIT_MS)
                    p2 = os.path.join(output_dir, f"02_submenu_{ts}.png")
                    await page.screenshot(path=p2, full_page=False)
                    screenshots.append(p2)
            except Exception:
                pass

            # 截图 3：全屏
            p3 = os.path.join(output_dir, f"03_fullscreen_{ts}.png")
            await page.screenshot(path=p3, full_page=True)
            screenshots.append(p3)

        finally:
            await browser.close()

    return screenshots


def main():
    parser = argparse.ArgumentParser(description="软著工厂 - 渲染器")
    parser.add_argument("--template", default=str(config.DEFAULT_TEMPLATE_PATH), help="Jinja2 模板路径")
    parser.add_argument("--data", default="", help="p1_insight.json 路径")
    parser.add_argument("--output", default=str(config.RENDER_OUTPUT_DIR), help="截图输出目录")
    parser.add_argument("--app-name", default="", help="应用名称（覆盖 data 中的）")
    parser.add_argument("--theme", default=config.THEME_COLOR, help="主题色")
    args = parser.parse_args()

    # 加载数据
    if args.data and os.path.exists(args.data):
        with open(args.data, "r", encoding="utf-8") as f:
            p1_data = json.load(f)
        app_name = args.app_name or p1_data.get("company_profile", {}).get("name", "管理系统")
        render_data = build_dashboard_data(p1_data, app_name, args.theme)
    else:
        # 使用默认 MVP 数据
        with open(config.DEFAULT_DATA_PATH, "r", encoding="utf-8") as f:
            render_data = json.load(f)
        if args.app_name:
            render_data["app_name"] = args.app_name
        render_data.setdefault("theme_color_hex", args.theme)
        render_data = apply_template_settings(render_data)

    screenshots = asyncio.run(render_and_screenshot(render_data, args.template, args.output))

    print(f"✅ 渲染完成: {len(screenshots)} 张截图")
    for s in screenshots:
        print(f"   - {s}")


if __name__ == "__main__":
    main()
