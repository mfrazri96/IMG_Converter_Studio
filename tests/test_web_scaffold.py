import builtins
import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from web_app import cli
from web_app.cli import PROJECT_ROOT


class WebScaffoldTests(unittest.TestCase):
    def test_local_web_entrypoint_files_exist(self):
        self.assertTrue((PROJECT_ROOT / "run_web.py").is_file())
        self.assertTrue((PROJECT_ROOT / "web_app" / "cli.py").is_file())
        self.assertTrue((PROJECT_ROOT / "web_app" / "app" / "main.py").is_file())
        self.assertTrue((PROJECT_ROOT / "web_app" / "app" / "static" / "index.html").is_file())

    def test_root_requirements_include_web_runtime(self):
        requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("-r web_app/requirements-web.txt", requirements)

    def test_console_script_points_to_local_web_cli(self):
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('easy-img-web = "web_app.cli:main"', pyproject)

    def test_local_web_cli_supports_host_port_and_reload(self):
        cli = (PROJECT_ROOT / "web_app" / "cli.py").read_text(encoding="utf-8")
        self.assertIn("EASY_IMG_HOST", cli)
        self.assertIn("EASY_IMG_PORT", cli)
        self.assertIn("--reload", cli)
        self.assertIn('"web_app.app.main:app"', cli)
        self.assertIn("python -m pip install -r requirements.txt", cli)

    def test_local_web_cli_reports_missing_runtime_dependency(self):
        original_import = builtins.__import__

        def import_without_uvicorn(name, *args, **kwargs):
            if name == "uvicorn":
                raise ModuleNotFoundError("No module named 'uvicorn'", name="uvicorn")
            return original_import(name, *args, **kwargs)

        stderr = io.StringIO()
        with patch("builtins.__import__", side_effect=import_without_uvicorn):
            with patch("sys.argv", ["run_web.py"]):
                with redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as raised:
                        cli.main()

        self.assertEqual(raised.exception.code, 1)
        message = stderr.getvalue()
        self.assertIn("Missing local web runtime dependency: uvicorn", message)
        self.assertIn("python -m pip install -r requirements.txt", message)

    def test_backend_enhance_dependencies_fail_per_job_not_on_import(self):
        main = (PROJECT_ROOT / "web_app" / "app" / "main.py").read_text(encoding="utf-8")
        self.assertIn("cv2 = None", main)
        self.assertIn("OpenCV dependency is missing. Install with: python -m pip install -r requirements.txt", main)
        self.assertIn("Real-ESRGAN dependencies are missing. Install with: python -m pip install -r requirements.txt", main)

    def test_docker_support_files_are_preserved(self):
        dockerfile = (PROJECT_ROOT / "web_app" / "Dockerfile").read_text(encoding="utf-8")
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("web_app/requirements-web.txt", dockerfile)
        self.assertIn("uvicorn", dockerfile)
        self.assertIn("app.main:app", dockerfile)
        self.assertIn("web_app/Dockerfile", compose)
        self.assertIn("8000:8000", compose)

    def test_operator_docs_include_local_and_docker_web_steps(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        helix = (PROJECT_ROOT / "HELIX.md").read_text(encoding="utf-8")

        for docs in (readme, helix):
            self.assertIn("python run_web.py", docs)
            self.assertIn("http://127.0.0.1:8000", docs)
            self.assertIn("docker compose up --build", docs)
            self.assertIn("docker compose down", docs)


if __name__ == "__main__":
    unittest.main()
