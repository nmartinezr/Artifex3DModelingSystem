import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PACKAGE_ROOT / "v1" / "project.schema.json"
EXAMPLES_PATH = PACKAGE_ROOT / "v1" / "examples"


class ProjectSchemaV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def assert_valid_fixture(self, filename: str):
        payload = json.loads((EXAMPLES_PATH / filename).read_text(encoding="utf-8"))
        errors = sorted(self.validator.iter_errors(payload), key=lambda error: list(error.path))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def test_single_object_fixture_is_valid(self):
        self.assert_valid_fixture("single-object.json")

    def test_multi_object_fixture_is_valid(self):
        self.assert_valid_fixture("multi-object.json")

    def test_schema_rejects_unsupported_version(self):
        payload = json.loads((EXAMPLES_PATH / "single-object.json").read_text(encoding="utf-8"))
        payload["schemaVersion"] = "2.0.0"
        errors = list(self.validator.iter_errors(payload))
        self.assertTrue(errors)

    def test_schema_requires_scene(self):
        payload = json.loads((EXAMPLES_PATH / "single-object.json").read_text(encoding="utf-8"))
        del payload["scene"]
        errors = list(self.validator.iter_errors(payload))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
