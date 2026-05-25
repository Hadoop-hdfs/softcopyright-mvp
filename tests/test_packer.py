"""Word 打包模块配置行为测试。"""

import importlib
import sys
import types
import unittest


def import_packer_with_docx_stub():
    """
    使用最小 docx stub 导入 packer。

    Returns:
        已导入的 packer 模块。
    """
    docx_module = types.ModuleType("docx")
    docx_module.Document = object

    enum_module = types.ModuleType("docx.enum")
    enum_text_module = types.ModuleType("docx.enum.text")
    enum_text_module.WD_ALIGN_PARAGRAPH = types.SimpleNamespace(CENTER="CENTER")

    shared_module = types.ModuleType("docx.shared")
    shared_module.Pt = lambda value: value
    shared_module.Cm = lambda value: value
    shared_module.RGBColor = object

    oxml_module = types.ModuleType("docx.oxml")
    oxml_ns_module = types.ModuleType("docx.oxml.ns")
    oxml_ns_module.qn = lambda value: value

    stub_modules = {
        "docx": docx_module,
        "docx.enum": enum_module,
        "docx.enum.text": enum_text_module,
        "docx.shared": shared_module,
        "docx.oxml": oxml_module,
        "docx.oxml.ns": oxml_ns_module,
    }

    previous_modules = {name: sys.modules.get(name) for name in stub_modules}
    sys.modules.update(stub_modules)
    try:
        if "packer" in sys.modules:
            return importlib.reload(sys.modules["packer"])
        return importlib.import_module("packer")
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


class PackerConfigTestCase(unittest.TestCase):
    """验证打包模块中的可配置文案。"""

    def test_build_source_part_heading_uses_configured_page_count(self) -> None:
        """源代码文档分段标题应使用配置后的页数。"""
        packer = import_packer_with_docx_stub()

        self.assertEqual(packer.build_source_part_heading("第一部分", 12), "第一部分（前 12 页）")
        self.assertEqual(packer.build_source_part_heading("第二部分", 8), "第二部分（后 8 页）")


if __name__ == "__main__":
    unittest.main()
