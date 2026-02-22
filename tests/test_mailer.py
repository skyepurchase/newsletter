import logging
import copy
import random
import string
import pytest
import smtplib
from unittest.mock import ANY

import mailer
from utils import email
from utils.type_hints import MailerConfig


class TestMailer:
    basic_config = MailerConfig(
        isQuestion=True,
        isAnswer=False,
        isSend=False,
        isManual=False,
        name="",
        email="",
        issue=0,
        addresses=[""],
        folder="",
        text="",
        link="",
        password="",
    )

    def test_invalid_config_fails(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.isQuestion = False

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.CRITICAL)

        # ACT
        with pytest.raises(SystemExit) as e_info:
            mailer.main(config)

        # ASSERT
        assert "Illegal config file submitted" in caplog.text
        assert e_info.value.code == 2

    def test_invalid_folder_fails(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.folder = "missing"

        mock_file = mocker.mock_open()

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == "missing/emails.txt":
                raise FileNotFoundError
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.CRITICAL)

        # ACT
        with pytest.raises(SystemExit) as e_info:
            mailer.main(config)

        # ASSERT
        assert "Failed to load target addresses" in caplog.text
        assert e_info.value.code == 1

    def test_addresses_loaded(self, mocker):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.folder = "folder"

        mocker.patch("mailer.generate_email")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open(read_data="test@mail.com\nexample@mail.com")
        mocker.patch("builtins.open", mock_file)

        # ACT
        mailer.main(config)

        # ASSERT
        mock_file.assert_called_with("folder/emails.txt", "r")
        assert config.addresses == ["test@mail.com", "example@mail.com"]

    def test_email_generated_and_sent(self, mocker):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)

        mocker.patch("mailer.generate_email")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_generate = mocker.patch("mailer.generate_email")
        mock_generate.return_value = "email_body"
        mock_send = mocker.patch("mailer.send_email")

        # ACT
        mailer.main(config)

        # ASSERT
        mock_generate.assert_called_with(config)
        mock_send.assert_called_with("email_body", config)

    def test_question_config(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)

        mocker.patch("mailer.generate_email")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.INFO)

        # ACT
        mailer.main(config)

        # ASSERT
        assert config.text == "Time to submit your questions!"
        assert "Question request" in caplog.text

    def test_answer_config(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.isQuestion = False
        config.isAnswer = True

        mocker.patch("mailer.generate_email")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.INFO)

        # ACT
        mailer.main(config)

        # ASSERT
        assert config.text == "Time to submit your responses!"
        assert "Answer request" in caplog.text

    def test_publish_config(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.isQuestion = False
        config.isSend = True

        mocker.patch("mailer.generate_email")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.INFO)

        # ACT
        mailer.main(config)

        # ASSERT
        assert config.text == "Hope you have all had a wonderful month!"
        assert "Publishing" in caplog.text


class TestGenerateEmail:
    basic_config = MailerConfig(
        isQuestion=True,
        isAnswer=False,
        isSend=False,
        isManual=False,
        name="test",
        email="test@mail.com",
        issue=1,
        addresses=["another@mail.com"],
        folder="exists",
        text="text",
        link="https://jo.blogs.com",
        password="secret",
    )

    def test_question_correct(self, mocker):
        # ARRANGE
        mock_formatter = mocker.patch("utils.email.format_html")

        config = copy.deepcopy(self.basic_config)
        values = {
            "NAME": config.name.title(),
            "ISSUE": config.issue,
            "LINK": config.link,
            "TYPE": "submit questions",
        }

        # ACT
        email.generate_email(config)

        # ASSERT
        mock_formatter.assert_called_once_with(ANY, values)

    def test_answer_correct(self, mocker):
        # ARRANGE
        mock_formatter = mocker.patch("utils.email.format_html")

        config = copy.deepcopy(self.basic_config)
        config.isQuestion = False
        config.isAnswer = True

        values = {
            "NAME": config.name.title(),
            "ISSUE": config.issue,
            "LINK": config.link,
            "TYPE": "submit answers",
        }

        # ACT
        email.generate_email(config)

        # ASSERT
        mock_formatter.assert_called_once_with(ANY, values)

    def test_publish_correct(self, mocker):
        # ARRANGE
        mock_formatter = mocker.patch("utils.email.format_html")

        config = copy.deepcopy(self.basic_config)
        config.isQuestion = False
        config.isSend = True

        values = {
            "NAME": config.name.title(),
            "ISSUE": config.issue,
            "LINK": config.link,
            "TYPE": "view",
        }

        # ACT
        email.generate_email(config)

        # ASSERT
        mock_formatter.assert_called_once_with(ANY, values)


class TestSendEmail:
    basic_config = MailerConfig(
        isQuestion=True,
        isAnswer=False,
        isSend=False,
        isManual=False,
        name="",
        email="test@mail.com",
        issue=0,
        addresses=["target1@mail.com", "target2@mail.com"],
        folder="",
        text="",
        link="",
        password="",
    )

    def test_incorrect_password_fails_gracefully(self, mocker):
        # ARRANGE
        mock_server = mocker.Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(-1, "")

        mock_smtp = mocker.patch("utils.email.smtplib.SMTP_SSL")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # ACT
        success = email.send_email("", self.basic_config)

        # ASSERT
        assert success is not None
        assert not success

        mock_server.sendmail.assert_not_called()

    def test_correct_password_passes(self, mocker):
        # ARRANGE
        mock_server = mocker.Mock()
        mock_smtp = mocker.patch("utils.email.smtplib.SMTP_SSL")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # ACT
        random_text = "".join([random.choice(string.ascii_letters) for _ in range(100)])
        success = email.send_email(random_text, self.basic_config)
        call_args = mock_server.sendmail.call_args

        # ASSERT
        assert success

        mock_server.sendmail.assert_called_once_with(
            "test@mail.com", ["target1@mail.com", "target2@mail.com"], ANY
        )

        assert "From: test@mail.com" in call_args[0][2]
        assert "To: target1@mail.com, target2@mail.com" in call_args[0][2]
        assert random_text in call_args[0][2]

    def test_debug_sends_to_self(self, mocker):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.debug = True

        mock_server = mocker.Mock()
        mock_smtp = mocker.patch("utils.email.smtplib.SMTP_SSL")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # ACT
        success = email.send_email("", config)
        call_args = mock_server.sendmail.call_args

        # ASSERT
        assert success

        mock_server.sendmail.assert_called_once_with(
            "test@mail.com", "test@mail.com", ANY
        )

        assert "To: test@mail.com" in call_args[0][2]
        assert "target1@mail.com" not in call_args[0][2]
