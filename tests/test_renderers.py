import logging
from unittest.mock import ANY


import renderers


class TestRenderers:
    title = "Newsletter"
    id = 1
    issue = 5

    def test_question_form_renderer(self, mocker, caplog):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)
        mock_print = mocker.patch("builtins.print")
        mocker.patch("renderers.os.path.join")

        mock_format = mocker.patch("renderers.format_html")
        mock_navbar = mocker.patch("renderers.make_navbar")
        mock_questions = mocker.patch("renderers.get_questions")
        mock_questions.return_value = (
            None,
            [(1, "User", "Question 1"), (2, "User 2", "Question 2")],
        )

        caplog.set_level(logging.INFO)

        # ACT
        renderers.render_question_form(self.title, self.id, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call(
            ANY, {"NAME": "User", "TEXT": "Question 1"}, sanitize=True
        )
        mock_format.assert_any_call(
            ANY, {"NAME": "User 2", "TEXT": "Question 2"}, sanitize=True
        )
        mock_navbar.assert_called()

        assert "Rendering question form" in caplog.text

    def test_answer_form_renderer(self, mocker, caplog):
        # ARRANGE
        mock_file = mocker.mock_open()
        mock_text = mocker.mock_open(read_data="text_question")
        mock_img = mocker.mock_open(read_data="img_question")

        def conditional_open(path, mode="r", *args, **kwargs):
            if "text_question" in path:
                return mock_text(path, mode, *args, **kwargs)
            elif "image_question" in path:
                return mock_img(path, mode, *args, **kwargs)
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)

        mock_print = mocker.patch("builtins.print")
        mock_join = mocker.patch("renderers.os.path.join")
        mock_join.side_effect = lambda *args: "/".join(args)

        mock_format = mocker.patch("renderers.format_html")
        mock_navbar = mocker.patch("renderers.make_navbar")
        mock_questions = mocker.patch("renderers.get_questions")
        mock_questions.return_value = (
            [(3, "Text Question", "text"), (4, "Image Question", "image")],
            [(1, "User", "Question 1"), (2, "User 2", "Question 2")],
        )

        caplog.set_level(logging.INFO)

        # ACT
        renderers.render_answer_form(self.title, self.id, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call(
            ANY,
            {"ID": "question_1", "NAME": "User", "QUESTION": "Question 1"},
            sanitize=True,
        )
        mock_format.assert_any_call(
            ANY,
            {"ID": "question_2", "NAME": "User 2", "QUESTION": "Question 2"},
            sanitize=True,
        )
        mock_format.assert_any_call(
            "text_question", {"ID": "question_3", "QUESTION": "Text Question"}
        )
        mock_format.assert_any_call(
            "img_question",
            {"ID": "question_4", "QUESTION": "Image Question", "IMG_ID": "image_4"},
        )
        mock_navbar.assert_called()

        assert "Rendering answer form" in caplog.text

    def test_newsletter_renderer(self, mocker, caplog):
        # ARRANGE
        mock_file = mocker.mock_open()
        mock_text = mocker.mock_open(read_data="text_question")
        mock_img = mocker.mock_open(read_data="img_question")

        def conditional_open(path, mode="r", *args, **kwargs):
            if "templates/image_response" in path:
                return mock_img(path, mode, *args, **kwargs)
            elif "templates/response" in path:
                return mock_text(path, mode, *args, **kwargs)
            else:
                return mock_file(path, mode, *args, **kwargs)

        mocker.patch("builtins.open", conditional_open)
        mock_shutil = mocker.patch("renderers.shutil.copy")

        mock_print = mocker.patch("builtins.print")
        mock_join = mocker.patch("renderers.os.path.join")
        mock_join.side_effect = lambda *args: "/".join(args)

        mock_format = mocker.patch("renderers.format_html")
        mock_navbar = mocker.patch("renderers.make_navbar")
        mock_responses = mocker.patch("renderers.get_responses")
        mock_responses.return_value = [
            ("User", "Question 1", [("User 2", "Answer 1", None)]),
            (
                "User 2",
                "Question 2",
                [("User 1", "Answer 1", None), ("User 2", "Answer 2", "path")],
            ),
        ]

        caplog.set_level(logging.INFO)

        # ACT
        renderers.render_newsletter(self.title, self.id, self.issue, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call(
            "text_question", {"NAME": "User 2", "TEXT": "Answer 1"}, sanitize=True
        )
        mock_format.assert_any_call(
            "text_question", {"NAME": "User 1", "TEXT": "Answer 1"}, sanitize=True
        )
        mock_format.assert_any_call(
            "img_question",
            {"NAME": "User 2", "SRC": "/images/path", "CAPTION": "Answer 2"},
            sanitize=True,
        )

        mock_format.assert_any_call(
            ANY, {"CREATOR": "User", "QUESTION": "Question 1", "RESPONSES": ANY}
        )
        mock_format.assert_any_call(
            ANY, {"CREATOR": "User 2", "QUESTION": "Question 2", "RESPONSES": ANY}
        )

        mock_navbar.assert_called()
        mock_shutil.assert_called_once()

        assert "Rendering published newsletter" in caplog.text
