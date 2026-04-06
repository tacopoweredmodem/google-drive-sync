"""Tests for gdsync.core — pure functions and config logic."""

import yaml

from gdsync.core import (
    DEFAULT_CONFIG,
    html_to_markdown,
    load_config,
    safe_filename,
    save_default_config,
)

# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------


class TestSafeFilename:
    def test_passthrough(self):
        assert safe_filename("hello world") == "hello world"

    def test_slashes_replaced(self):
        assert safe_filename("a/b\\c") == "a_b_c"

    def test_special_chars_replaced(self):
        assert safe_filename('a:b*c?d"e<f>g|h') == "a_b_c_d_e_f_g_h"

    def test_dotdot_replaced(self):
        # ".." → "__", then leading dots/spaces stripped → "_sneaky"
        assert safe_filename("..sneaky") == "_sneaky"

    def test_null_byte_replaced(self):
        assert safe_filename("has\x00null") == "has_null"

    def test_stripped_dots_and_spaces(self):
        assert safe_filename("  .name. ") == "name"

    def test_empty_becomes_unnamed(self):
        assert safe_filename("") == "_unnamed"

    def test_all_dots_becomes_underscore(self):
        # "..." → "_._" (dotdot replaced) → stripped → "_"
        assert safe_filename("...") == "_"

    def test_truncated_at_200(self):
        long_name = "a" * 300
        result = safe_filename(long_name)
        assert len(result) == 200


# ---------------------------------------------------------------------------
# html_to_markdown
# ---------------------------------------------------------------------------


class TestHtmlToMarkdown:
    def test_basic_html(self):
        html = b"<h1>Title</h1><p>Hello world</p>"
        md = html_to_markdown(html)
        assert "# Title" in md
        assert "Hello world" in md

    def test_strips_images(self):
        html = b'<p>Text <img src="foo.png"/> more</p>'
        md = html_to_markdown(html)
        assert "foo.png" not in md
        assert "Text" in md

    def test_handles_encoding_errors(self):
        bad_bytes = b"Hello \xff\xfe world"
        md = html_to_markdown(bad_bytes)
        assert "Hello" in md
        assert "world" in md


# ---------------------------------------------------------------------------
# Config loading/saving
# ---------------------------------------------------------------------------


class TestConfig:
    def test_load_defaults_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gdsync.core.get_config_dir", lambda: tmp_path)
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_load_merges_user_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gdsync.core.get_config_dir", lambda: tmp_path)
        user_config = {"output_dir": "/custom/path", "max_retries": 10}
        (tmp_path / "config.yaml").write_text(yaml.dump(user_config))
        config = load_config()
        assert config["output_dir"] == "/custom/path"
        assert config["max_retries"] == 10
        assert config["rate_limit_delay"] == 0.2  # default preserved

    def test_load_handles_corrupt_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gdsync.core.get_config_dir", lambda: tmp_path)
        (tmp_path / "config.yaml").write_text(": : : bad yaml [[[")
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_save_default_creates_valid_yaml(self, tmp_path, monkeypatch):
        monkeypatch.setattr("gdsync.core.get_config_dir", lambda: tmp_path)
        path = save_default_config()
        assert path.exists()
        loaded = yaml.safe_load(path.read_text())
        assert loaded == DEFAULT_CONFIG
