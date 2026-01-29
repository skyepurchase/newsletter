import os
from unittest.mock import ANY
from dotenv import load_dotenv

import create_newsletter


load_dotenv()


HOME = os.getenv("HOME", "")


class TestCreateNewsletter:
    title = "Newsletter"
    email = "example@mail.com"
    passcode = "password"
    config = {
        "name": title,
        "email": email,
        "folder": "newsletters/newsletter",
        "link": "https://skye.purchasethe.uk/projects/newsletter/",
        "issue": 1,
        "passphrase": passcode,
        "defaults": [
            ["⛅ One Good Thing", "text"],
            ["👀 Check It Out", "text"],
            ["📸 Photo Wall", "image"],
        ],
    }

    def test_create_new_folder_and_files(self, mocker):
        # ARRANGE
        mock_isdir = mocker.patch("create_newsletter.os.path.isdir")
        mock_isdir.return_value = False
        mock_path_join = mocker.patch("create_newsletter.os.path.join")
        mock_path_join.side_effect = lambda *args: "/".join(args)

        mock_makedirs = mocker.patch("create_newsletter.os.makedirs")
        mock_chmod = mocker.patch("create_newsletter.os.chmod")
        mock_file = mocker.mock_open()
        mock_open = mocker.patch("builtins.open", mock_file)
        mock_yaml_dump = mocker.patch("create_newsletter.yaml.dump")
        mock_create_newsletter = mocker.patch("create_newsletter.create_newsletter")

        # ACT
        create_newsletter.create(self.title, self.email, self.passcode)

        # ASSERT
        mock_makedirs.assert_called_once_with("newsletters/newsletter")
        mock_chmod.assert_called_once_with("newsletters/newsletter", 0o0710)
        mock_open.assert_any_call("newsletters/newsletter/config.yaml", "w")
        mock_yaml_dump.assert_called_once_with(self.config, mock_open())
        mock_open.assert_any_call("newsletters/newsletter/emails.txt", "w")
        mock_open.assert_any_call("newsletters/newsletter/log", "w")
        mock_create_newsletter.assert_called_once()

    def test_folder_already_exists(self, mocker):
        # ARRANGE
        mock_isdir = mocker.patch("create_newsletter.os.path.isdir")
        mock_isdir.return_value = True

        mock_makedirs = mocker.patch("create_newsletter.os.makedirs")
        mock_create_newsletter = mocker.patch("create_newsletter.create_newsletter")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)
        mocker.patch("create_newsletter.yaml.dump")

        # ACT
        create_newsletter.create(self.title, self.email, self.passcode)

        # ASSERT
        mock_makedirs.assert_not_called()
        mock_create_newsletter.assert_called_once()

    def test_passcode_is_hashed(self, mocker):
        # ARRANGE
        mock_isdir = mocker.patch("create_newsletter.os.path.isdir")
        mock_isdir.return_value = False
        mock_path_join = mocker.patch("create_newsletter.os.path.join")
        mock_path_join.side_effect = lambda *args: "/".join(args)
        mock_hash_passcode = mocker.patch("create_newsletter.hash_passcode")
        mock_hash_passcode.return_value = "hashed_passcode"

        mock_create_newsletter = mocker.patch("create_newsletter.create_newsletter")

        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)
        mocker.patch("create_newsletter.yaml.dump")
        mocker.patch("create_newsletter.os.path.join")

        # ACT
        create_newsletter.create(self.title, self.email, self.passcode)

        # ASSERT
        mock_hash_passcode.assert_called_once_with(self.passcode)
        mock_create_newsletter.assert_called_once_with(
            self.title, "hashed_passcode", ANY
        )
