import os, pytest
import random, string

from utils.html import format_html, hash_passcode, verify, make_navbar


class TestMakeNavbar:
    def test_curr_and_next_disabled_on_curr(self):
        # ARRANGE
        target = open('tests/templates/navbar_curr_issue_5.html', 'r').read()

        # ACT
        navbar = make_navbar(5, 5)

        # ASSERT
        assert target == navbar

    def test_all_enabled_on_prev(self):
        # ARRANGE
        target = open('tests/templates/navbar_prev_issue_5.html', 'r').read()

        # ACT
        navbar = make_navbar(4, 5)

        # ASSERT
        assert target == navbar

    def test_prev_disabled_on_first(self):
        # ARRANGE
        target = open('tests/templates/navbar_first_issue_5.html', 'r').read()

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
        values = {
            "MISSING": "This will fail"
        }

        with pytest.raises(KeyError):
            format_html(self.html, values)

    def test_text_replaced(self):
        values = {
            "REPLACE": "Replaced text"
        }
        formatted = format_html(self.html, values)

        assert "Replaced text" == formatted

    def test_empty_replacement_passes(self):
        values = {
            "REPLACE": ""
        }

        formatted = format_html(self.html, values)

        assert "" == formatted

    def test_links_valid(self):
        values = {
            "REPLACE": "<script></script>https://skye.purchasethe.uk"
        }

        formatted = format_html(self.html, values, sanitize=True)

        assert '&lt;script&gt;&lt;/script&gt;<a href="https://skye.purchasethe.uk" rel="nofollow">https://skye.purchasethe.uk</a>' == formatted


class TestVerify:
    def test_verify_hashed_passcode_passes(self):
        for _ in range(10):
            # ARRANGE
            length = random.randint(8,32)
            passcode = ''.join(random.sample(string.ascii_letters, length))
            hash = hash_passcode(passcode)

            # ACT
            success = verify(passcode, hash)

            # ASSERT
            assert success == True
