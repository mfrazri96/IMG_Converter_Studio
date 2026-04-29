import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = PROJECT_ROOT / "web_app" / "app" / "static" / "index.html"


class WebStaticUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_convert_and_enhance_fields_are_preserved(self):
        for required in (
            'id="btnConvert"',
            'id="btnEnhance"',
            'id="targetFormat"',
            'id="quality"',
            'id="modelName"',
            'id="outscale"',
            'id="tile"',
            "RealESRGAN_x4plus",
        ):
            self.assertIn(required, self.html)

    def test_upload_progress_error_and_download_regions_are_preserved(self):
        for required in (
            'id="dropzone"',
            'id="files" type="file" multiple',
            'role="progressbar"',
            'id="formError" role="alert"',
            'id="downloadAllBtn"',
            'id="outputs"',
            "job.outputs",
            "job.errors",
        ):
            self.assertIn(required, self.html)

    def test_output_download_links_are_normalized_before_rendering(self):
        self.assertIn("function normalizeDownloadUrl(url)", self.html)
        self.assertIn("function downloadNameFromUrl(url)", self.html)
        self.assertIn("encodeURIComponent(filename)", self.html)
        self.assertIn("const href = normalizeDownloadUrl(url);", self.html)
        self.assertIn("link.href = href;", self.html)
        self.assertIn("link.download = displayName;", self.html)
        self.assertNotIn("link.href = url;", self.html)
        self.assertNotIn("url.split('/').pop()", self.html)

    def test_responsive_media_rules_are_preserved(self):
        self.assertIn("@media (max-width: 940px)", self.html)
        self.assertIn("@media (max-width: 640px)", self.html)
        self.assertIn("grid-template-columns: 1fr;", self.html)
        self.assertIn(".file-row", self.html)


if __name__ == "__main__":
    unittest.main()
