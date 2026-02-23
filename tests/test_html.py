import pytest
import random
import string

from utils.html import authenticate, format_html, hash_passcode, verify, make_navbar


class TestMakeNavbar:
    def test_curr_and_next_disabled_on_curr(self):
        # ARRANGE
        target = open("tests/templates/navbar_curr_issue_5.html", "r").read()

        # ACT
        navbar = make_navbar(5, 5)

        # ASSERT
        assert target == navbar

    def test_all_enabled_on_prev(self):
        # ARRANGE
        target = open("tests/templates/navbar_prev_issue_5.html", "r").read()

        # ACT
        navbar = make_navbar(4, 5)

        # ASSERT
        assert target == navbar

    def test_prev_disabled_on_first(self):
        # ARRANGE
        target = open("tests/templates/navbar_first_issue_5.html", "r").read()

        # ACT
        navbar = make_navbar(0, 5)

        # ASSERT
        assert target == navbar

    def test_throw_error_out_of_bounds(self):
        with pytest.raises(ValueError):
            make_navbar(6, 5)

        with pytest.raises(ValueError):
            make_navbar(-1, 5)


class TestFormatHTML:
    html = "[REPLACE]"

    def test_missing_key_fails(self):
        values = {"MISSING": "This will fail"}

        with pytest.raises(KeyError):
            format_html(self.html, values)

    def test_text_replaced(self):
        values = {"REPLACE": "Replaced text"}
        formatted = format_html(self.html, values)

        assert "Replaced text" == formatted

    def test_empty_replacement_passes(self):
        values = {"REPLACE": ""}

        formatted = format_html(self.html, values)

        assert "" == formatted

    def test_links_valid(self):
        values = {"REPLACE": "<script></script>https://skye.purchasethe.uk"}

        formatted = format_html(self.html, values, sanitize=True)

        assert (
            '&lt;script&gt;&lt;/script&gt;<a href="https://skye.purchasethe.uk" rel="nofollow">https://skye.purchasethe.uk</a>'
            == formatted
        )


class TestVerify:
    def test_verify_hashed_passcode_passes(self):
        for _ in range(10):
            # ARRANGE
            length = random.randint(8, 32)
            passcode = "".join(
                [random.choice(string.ascii_letters) for _ in range(length)]
            )
            hash = hash_passcode(passcode)

            # ACT
            success = verify(passcode, hash)

            # ASSERT
            assert success

    def test_random_password_fails(self):
        for _ in range(10):
            # ARRANGE
            length = random.randint(8, 32)
            passcode = "".join(
                [random.choice(string.ascii_letters) for _ in range(length)]
            )
            attempt = "".join(
                [random.choice(string.ascii_letters) for _ in range(length)]
            )
            hash = hash_passcode(passcode)

            # ACT
            success = verify(attempt, hash)

            # ASSERT
            assert not success


class TestAuthenticate:
    passcode = "secret"

    def test_authenticate_authenticates_user(self, mocker):
        # ARRANGE
        hash = hash_passcode(self.passcode)

        # ACT
        mock_newsletters = mocker.patch("utils.html.get_newsletters")
        mock_newsletters.return_value = [
            (5, "Not a Title", b"huh", "fake path"),
            (1, "Title", hash, "path"),
        ]

        success, id, title, folder = authenticate(self.passcode)

        # ASSERT
        mock_newsletters.assert_called_once()

        assert success
        assert id == 1
        assert title == "Title"
        assert folder == "path"

    def test_authenticate_fails_on_invalid_passcode(self, mocker):
        # ARRANGE
        hash = hash_passcode(self.passcode)

        mock_newsletters = mocker.patch("utils.html.get_newsletters")
        mock_newsletters.return_value = [
            (5, "Not a Title", b"huh", "fake path"),
            (1, "Title", hash, "path"),
        ]

        # ACT
        success, id, title, folder = authenticate("attempt")

        # ASSERT
        assert not success
        assert id == -1
        assert title == ""
        assert folder == ""

    @pytest.mark.parametrize("value", ["one", "1", 1, [1]])
    def test_authenticate_fails_on_non_byte_hash(self, mocker, value):
        # ARRANGE
        mock_newsletters = mocker.patch("utils.html.get_newsletters")
        mock_newsletters.return_value = [(5, "Not a Title", value, "fake path")]

        # ACT
        with pytest.raises(AssertionError) as e_info:
            authenticate("attempt")

        # ASSERT
        assert e_info.value.args[0] == "SQL returned a hash that was not in bytes."
