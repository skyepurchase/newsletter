import os
import cron
import copy
import pytest
from utils.constants import State
from utils.type_hints import EmptyConfig, MailerConfig, NewsletterConfig


class TestCron:
    newsletter_cfg = NewsletterConfig(
        name="Title",
        email="mail@mail.com",
        folder="exists",
        link="https://www.site.net",
        issue=5,
        defaults=[],
    )

    mail_cfg = MailerConfig(
        isQuestion=True,
        isAnswer=False,
        isSend=False,
        isManual=False,
        name="Title",
        email="mail@mail.com",
        issue=5,
        addresses=["mail@mail.com"],
        folder="exists",
        text="",
        link="https://www.site.net",
        password="secret",
    )

    password = "secret"
    home = "/home/user"

    def test_cron_mails_users(self, mocker):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Question

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = True

        mock_config_dir = mocker.patch("cron.os.listdir")
        mock_config_dir.return_value = ["newsletter_1"]

        mock_inc = mocker.patch("cron.check_and_increment_issue")
        mock_inc.return_value = (True, "")

        mock_load = mocker.patch("cron.load_config")
        mock_load.return_value = (True, self.newsletter_cfg)

        mock_mailer = mocker.patch("cron.mailer.main")

        # ACT
        cron.main(self.home, self.password)

        # ASSERT
        mock_state.assert_called_once()
        mock_dir.assert_called_once_with(self.home + "/newsletters")
        mock_inc.assert_called_with(self.home + "/newsletters/newsletter_1")
        mock_mailer.assert_called_once_with(self.mail_cfg)

    def test_cron_mails_answer_request(self, mocker):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Answer

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = True

        mock_config_dir = mocker.patch("cron.os.listdir")
        mock_config_dir.return_value = ["newsletter_1"]

        mock_inc = mocker.patch("cron.check_and_increment_issue")
        mock_inc.return_value = (True, "")

        mock_load = mocker.patch("cron.load_config")
        mock_load.return_value = (True, self.newsletter_cfg)

        mock_mailer = mocker.patch("cron.mailer.main")

        target_cfg = copy.deepcopy(self.mail_cfg)
        target_cfg.isQuestion = False
        target_cfg.isAnswer = True

        # ACT
        cron.main(self.home, self.password)

        # ASSERT
        mock_mailer.assert_called_once_with(target_cfg)

    def test_cron_mails_publish(self, mocker):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Publish

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = True

        mock_config_dir = mocker.patch("cron.os.listdir")
        mock_config_dir.return_value = ["newsletter_1"]

        mock_inc = mocker.patch("cron.check_and_increment_issue")
        mock_inc.return_value = (True, "")

        mock_load = mocker.patch("cron.load_config")
        mock_load.return_value = (True, self.newsletter_cfg)

        mock_mailer = mocker.patch("cron.mailer.main")

        target_cfg = copy.deepcopy(self.mail_cfg)
        target_cfg.isQuestion = False
        target_cfg.isSend = True

        # ACT
        cron.main(self.home, self.password)

        # ASSERT
        mock_mailer.assert_called_once_with(target_cfg)

    def test_cron_skips_bad_config(self, mocker, capsys):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Question

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = True

        mock_config_dir = mocker.patch("cron.os.listdir")
        mock_config_dir.return_value = ["bad", "good", "bad"]

        mock_inc = mocker.patch("cron.check_and_increment_issue")
        mock_inc.return_value = (True, "")

        def conditional_load(path, *args):
            if path == os.path.join(self.home, "newsletters", "bad"):
                return (False, EmptyConfig)
            else:
                return (True, self.newsletter_cfg)

        mocker.patch("cron.load_config", conditional_load)

        mock_mailer = mocker.patch("cron.mailer.main")

        # ACT
        cron.main(self.home, self.password)

        captured = capsys.readouterr()

        # ASSERT
        mock_mailer.assert_called_once_with(self.mail_cfg)

        assert mock_inc.call_count == 3
        assert (
            captured.out
            == "Unable to load config for bad\ngood question request successful\nUnable to load config for bad\n"
        )

    def test_cron_fails_on_increment_fail(self, mocker, capsys):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Question

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = True

        mock_config_dir = mocker.patch("cron.os.listdir")
        mock_config_dir.return_value = ["newsletter_1"]

        mock_inc = mocker.patch("cron.check_and_increment_issue")
        mock_inc.return_value = (False, "test message")

        # ACT
        with pytest.raises(SystemExit) as e_info:
            cron.main(self.home, self.password)

        captured = capsys.readouterr()

        # ASSERT
        assert e_info.value.code == 3
        assert (
            captured.out
            == "Failed to increment the issue for newsletter_1: test message\n"
        )

    def test_cron_fails_if_newsletter_dir_nonexistant(self, mocker, capsys):
        # ARRANGE
        mock_state = mocker.patch("cron.get_state")
        mock_state.return_value = State.Question

        mock_dir = mocker.patch("cron.os.path.isdir")
        mock_dir.return_value = False

        # ACT
        with pytest.raises(SystemExit) as e_info:
            cron.main(self.home, self.password)

        captured = capsys.readouterr()

        # ASSERT
        assert e_info.value.code == 2
        assert captured.out == "Newsletter folder does not exist\n"
