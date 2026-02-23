from datetime import datetime
import tempfile
import logging
import pytest
import os
from dotenv import load_dotenv
from utils.constants import State
from utils.helpers import check_and_increment_issue, load_config, get_state
from utils.type_hints import EmptyConfig, NewsletterConfig


load_dotenv()


HOME = os.getenv("HOME", "")


class TestLoadConfig:
    valid_data = "name: jo\nemail: jo@blogs.com\nfolder: jos\nlink: https://jo.blogs.com\ndefaults:\n- [text,text]"

    def test_missing_config_file_fails(self, mocker, caplog):
        # ARRANGE
        folder = "missing"

        mock_file = mocker.mock_open()

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "missing/config.yaml"):
                raise FileNotFoundError
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
        assert not success
        assert config == EmptyConfig
        assert f"Failed to load {folder}" in caplog.text

    def test_invalid_config_file_fails(self, mocker, caplog):
        # ARRANGE
        folder = "exists"

        mock_file = mocker.mock_open(read_data="name: jo\nbut=invalid")
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.WARNING)

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
        assert not success
        assert config == EmptyConfig
        assert f"Failed to parse {folder}" in caplog.text

    def test_missing_issue_file_fails(self, mocker, caplog):
        # ARRANGE
        folder = "exists"

        mock_file = mocker.mock_open(read_data=self.valid_data)

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                raise FileNotFoundError
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.WARNING)

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
        assert not success
        assert config == EmptyConfig
        assert f"Failed to load {folder} issue file" in caplog.text

    def test_invalid_issue_file_fails(self, mocker, caplog):
        # ARRANGE
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

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
        assert not success
        assert config == EmptyConfig
        assert f"Failed to parse {folder} issue file" in caplog.text

    def test_correct_config_returned(self, mocker):
        # ARRANGE
        folder = "exists"

        mock_issue = mocker.mock_open(read_data="1")
        mock_config = mocker.mock_open(read_data=self.valid_data)

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == os.path.join(HOME, "exists/issue"):
                return mock_issue(path, mode, *args, **kwargs)
            else:
                return mock_config(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
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
        # ARRANGE
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

        # ACT
        success, config = load_config(folder, logging.getLogger())

        # ASSERT
        assert not success
        assert config == EmptyConfig
        assert f"Failed to validate {folder}" in caplog.text


class TestGetState:
    def test_first_week_is_question(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 5)

        # ACT
        state = get_state()

        # ASSERT
        assert State.Question == state

    def test_second_week_is_question(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 11)

        # ACT
        state = get_state()

        # ASSERT
        assert State.Question == state

    def test_third_week_is_answer(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 21)

        # ACT
        state = get_state()

        # ASSERT
        assert State.Answer == state

    def test_fourth_week_is_publish(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 27)

        # ACT
        state = get_state()

        # ASSERT
        assert State.Publish == state


class TestIssueIncrement:
    directory = "folder"
    issue = 5

    @pytest.mark.parametrize("issue", [5, 42, 9001])
    def test_first_week_increments(self, mocker, issue):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 5)

        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "issue"), "w") as f:
                f.write(str(issue))

            # ACT
            success, err_msg = check_and_increment_issue(temp_dir)

            # ASSERT
            with open(os.path.join(temp_dir, "issue"), "r") as f:
                assert issue + 1 == int(f.read())

        assert success
        assert "" == err_msg

    @pytest.mark.parametrize(
        "date, issue",
        [
            (datetime(2025, 2, 10), 5),
            (datetime(2025, 2, 20), 42),
            (datetime(2025, 2, 28), 9001),
        ],
    )
    def test_other_weeks_remain(self, mocker, date, issue):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = date

        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "issue"), "w") as f:
                f.write(str(issue))

            # ACT
            success, err_msg = check_and_increment_issue(temp_dir)

            # ASSERT
            with open(os.path.join(temp_dir, "issue"), "r") as f:
                assert issue == int(f.read())

        assert success
        assert "" == err_msg

    def test_missing_issue_file_fails(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 5)

        mock_open = mocker.patch("builtins.open")
        mock_open.side_effect = OSError

        success, err_msg = check_and_increment_issue("missing")

        assert not success
        assert "Failed to open issue file" == err_msg

    def test_invalid_issue_file_fails(self, mocker):
        # ARRANGE
        mock_datetime = mocker.patch("utils.helpers.datetime")
        mock_datetime.now.return_value = datetime(2025, 2, 5)

        mock_file = mocker.mock_open(read_data="one")
        mocker.patch("builtins.open", mock_file)

        success, err_msg = check_and_increment_issue("missing")

        assert not success
        assert "Failed to parse issue file" == err_msg
