import logging
import copy
import pytest
import mailer

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
        with pytest.raises(SystemExit) as info_e:
            mailer.main(config)

        # ASSERT
        assert "Illegal config file submitted" in caplog.text
        assert info_e.value.code == 2

    def test_invalid_folder_fails(self, mocker, caplog):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.folder = "missing"

        mock_file = mocker.mock_open()

        def conditional_open(path, mode="r", *args, **kwargs):
            if path == "missing/emails.txt":
                raise FileNotFoundError
            else:
                mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        caplog.set_level(logging.CRITICAL)

        # ACT
        with pytest.raises(SystemExit) as info_e:
            mailer.main(config)

        # ASSERT
        assert "Failed to load target addresses" in caplog.text
        assert info_e.value.code == 1

    def test_addresses_loaded(self, mocker):
        # ARRANGE
        config = copy.deepcopy(self.basic_config)
        config.folder = "folder"

        mocker.patch("mailer.generate_email_request")
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

        mocker.patch("mailer.generate_email_request")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        mock_generate = mocker.patch("mailer.generate_email_request")
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

        mocker.patch("mailer.generate_email_request")
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

        mocker.patch("mailer.generate_email_request")
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

        mocker.patch("mailer.generate_email_request")
        mocker.patch("mailer.send_email")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)

        caplog.set_level(logging.INFO)

        # ACT
        mailer.main(config)

        # ASSERT
        assert config.text == "Hope you have all had a wonderful month!"
        assert "Publishing" in caplog.text
