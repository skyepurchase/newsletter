import logging
import os
from dotenv import load_dotenv
from utils.helpers import load_config
from utils.type_hints import EmptyConfig, NewsletterConfig


load_dotenv()


HOME = os.getenv("HOME", "")


class TestLoadConfig:
    valid_data = "name: jo\nemail: jo@blogs.com\nfolder: jos\nlink: https://jo.blogs.com\ndefaults:\n- [text,text]"

    def test_missing_config_file_fails(self, mocker, caplog):
        folder = "missing"

        mock_file = mocker.mock_open()

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "missing/config.yaml"):
                raise FileNotFoundError
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        success, config = load_config(folder, logging.getLogger())

        assert not success
        assert config == EmptyConfig
        assert f"Failed to load {folder}" in caplog.text

    def test_invalid_config_file_fails(self, mocker, caplog):
        folder = "exists"

        mock_file = mocker.mock_open(read_data="name: jo\nbut=invalid")
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.WARNING)

        success, config = load_config(folder, logging.getLogger())

        assert not success
        assert config == EmptyConfig
        assert f"Failed to parse {folder}" in caplog.text

    def test_missing_issue_file_fails(self, mocker, caplog):
        folder = "exists"

        mock_file = mocker.mock_open(read_data=self.valid_data)

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                raise FileNotFoundError
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        success, config = load_config(folder, logging.getLogger())

        assert not success
        assert config == EmptyConfig
        assert f"Failed to load {folder} issue file" in caplog.text

    def test_invalid_issue_file_fails(self, mocker, caplog):
        folder = "exists"

        mock_issue = mocker.mock_open(read_data="one")
        mock_config = mocker.mock_open(read_data=self.valid_data)

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                return mock_issue(path, mode, *args, **kwargs)
            else:
                return mock_config(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        success, config = load_config(folder, logging.getLogger())

        assert not success
        assert config == EmptyConfig
        assert f"Failed to parse {folder} issue file" in caplog.text

    def test_correct_config_returned(self, mocker):
        folder = "exists"

        mock_issue = mocker.mock_open(read_data="1")
        mock_config = mocker.mock_open(read_data=self.valid_data)

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                return mock_issue(path, mode, *args, **kwargs)
            else:
                return mock_config(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        success, config = load_config(folder, logging.getLogger())

        assert success
        assert config == NewsletterConfig(
            name="jo",
            email="jo@blogs.com",
            folder="jos",
            link="https://jo.blogs.com",
            defaults=[("text", "text")],
            issue=1,
        )

    def test_incorrect_config_fails(self, mocker, caplog):
        folder = "exists"

        mock_issue = mocker.mock_open(read_data="1")
        mock_config = mocker.mock_open(read_data=self.valid_data[:-11] + "text")

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                return mock_issue(path, mode, *args, **kwargs)
            else:
                return mock_config(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        success, config = load_config(folder, logging.getLogger())

        assert not success
        assert config == EmptyConfig
        assert f"Failed to validate {folder}" in caplog.text
