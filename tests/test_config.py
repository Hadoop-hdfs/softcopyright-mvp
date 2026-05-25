"""配置读取模块测试。"""

import importlib
import os
import tempfile
import unittest
from pathlib import Path

import config


class ConfigTestCase(unittest.TestCase):
    """验证环境变量文件加载和类型转换行为。"""

    def setUp(self) -> None:
        """清理测试环境变量，避免测试之间互相影响。"""
        self.keys = [
            "SOFTCOPYRIGHT_TEST_NAME",
            "SOFTCOPYRIGHT_TEST_COUNT",
            "SOFTCOPYRIGHT_TEST_RATIO",
            "SOFTCOPYRIGHT_TEST_ENABLED",
            "SOFTCOPYRIGHT_TEST_EXISTING",
            "SOFTCOPYRIGHT_AI_API_KEY",
            "SOFTCOPYRIGHT_AUTH_PATH",
        ]
        for key in self.keys:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        """测试结束后恢复干净环境。"""
        for key in self.keys:
            os.environ.pop(key, None)

    def test_load_env_file_reads_values_and_keeps_existing_environment(self) -> None:
        """读取 .env 文件时应解析值，但不覆盖已经存在的环境变量。"""
        os.environ["SOFTCOPYRIGHT_TEST_EXISTING"] = "from_environment"

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as env_file:
            env_file.write("# 用于测试字符串读取\n")
            env_file.write("SOFTCOPYRIGHT_TEST_NAME=软著工厂\n")
            env_file.write("SOFTCOPYRIGHT_TEST_EXISTING=from_file\n")
            env_file_path = env_file.name

        try:
            loaded_count = config.load_env_file(Path(env_file_path))
        finally:
            Path(env_file_path).unlink(missing_ok=True)

        self.assertEqual(loaded_count, 1)
        self.assertEqual(config.get_env_str("SOFTCOPYRIGHT_TEST_NAME", "默认值"), "软著工厂")
        self.assertEqual(
            config.get_env_str("SOFTCOPYRIGHT_TEST_EXISTING", "默认值"),
            "from_environment",
        )

    def test_get_env_converts_common_value_types(self) -> None:
        """配置读取函数应支持 int、float 和 bool 类型转换。"""
        os.environ["SOFTCOPYRIGHT_TEST_COUNT"] = "12"
        os.environ["SOFTCOPYRIGHT_TEST_RATIO"] = "0.75"
        os.environ["SOFTCOPYRIGHT_TEST_ENABLED"] = "true"

        self.assertEqual(config.get_env_int("SOFTCOPYRIGHT_TEST_COUNT", 1), 12)
        self.assertEqual(config.get_env_float("SOFTCOPYRIGHT_TEST_RATIO", 1.0), 0.75)
        self.assertTrue(config.get_env_bool("SOFTCOPYRIGHT_TEST_ENABLED", False))

    def test_resolve_path_returns_absolute_path_for_relative_value(self) -> None:
        """相对路径配置应基于项目根目录解析为绝对路径。"""
        resolved_path = config.resolve_path("render_outputs")

        self.assertTrue(resolved_path.is_absolute())
        self.assertEqual(resolved_path.name, "render_outputs")

    def test_ai_api_key_environment_value_skips_auth_file(self) -> None:
        """配置 API key 时，应直接使用环境变量而不读取本地认证文件。"""
        os.environ["SOFTCOPYRIGHT_AI_API_KEY"] = "env_api_key_for_test"
        os.environ["SOFTCOPYRIGHT_AUTH_PATH"] = "/private/tmp/missing_auth_for_test.json"

        import ai_client

        importlib.reload(config)
        importlib.reload(ai_client)

        self.assertEqual(ai_client._load_api_key(), "env_api_key_for_test")


if __name__ == "__main__":
    unittest.main()
