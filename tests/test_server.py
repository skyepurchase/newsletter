from collections import defaultdict
import logging
import copy
from typing import DefaultDict
import pytest
from unittest.mock import ANY


import server
from utils.type_hints import EmptyConfig, NewsletterConfig, NewsletterException, NewsletterToken


class TestRenderers:
    title = "Newsletter"
    id = 1
    issue = 5
    def test_question_form_renderer(self, mocker, caplog):
        # ARRANGE
        mock_file = mocker.mock_open()
        mocker.patch("builtins.open", mock_file)
        mock_print = mocker.patch("builtins.print")
        mocker.patch("server.os.path.join")

        mock_format = mocker.patch("server.format_html")
        mock_navbar = mocker.patch("server.make_navbar")
        mock_questions = mocker.patch("server.get_questions")
        mock_questions.return_value = (None, [(1, "User", "Question 1"), (2, "User 2", "Question 2")])

        caplog.set_level(logging.INFO)

        # ACT
        server.render_question_form(self.title, self.id, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call(ANY, {"NAME": "User", "TEXT": "Question 1"}, sanitize=True)
        mock_format.assert_any_call(ANY, {"NAME": "User 2", "TEXT": "Question 2"}, sanitize=True)
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
        mock_join = mocker.patch("server.os.path.join")
        mock_join.side_effect = lambda *args: "/".join(args)

        mock_format = mocker.patch("server.format_html")
        mock_navbar = mocker.patch("server.make_navbar")
        mock_questions = mocker.patch("server.get_questions")
        mock_questions.return_value = ([(3, "Text Question", "text"), (4, "Image Question", "image")], [(1, "User", "Question 1"), (2, "User 2", "Question 2")])

        caplog.set_level(logging.INFO)

        # ACT
        server.render_answer_form(self.title, self.id, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call(ANY, {"ID": "question_1", "NAME": "User", "QUESTION": "Question 1"}, sanitize=True)
        mock_format.assert_any_call(ANY, {"ID": "question_2", "NAME": "User 2", "QUESTION": "Question 2"}, sanitize=True)
        mock_format.assert_any_call("text_question", {"ID": "question_3", "QUESTION": "Text Question"})
        mock_format.assert_any_call("img_question", {"ID": "question_4", "QUESTION": "Image Question", "IMG_ID": "image_4"})
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
        mock_shutil = mocker.patch("server.shutil.copy")

        mock_print = mocker.patch("builtins.print")
        mock_join = mocker.patch("server.os.path.join")
        mock_join.side_effect = lambda *args: "/".join(args)

        mock_format = mocker.patch("server.format_html")
        mock_navbar = mocker.patch("server.make_navbar")
        mock_responses = mocker.patch("server.get_responses")
        mock_responses.return_value = [
            ("User", "Question 1", [("User 2", "Answer 1", None)]),
            ("User 2", "Question 2", [("User 1", "Answer 1", None), ("User 2", "Answer 2", "path")])
        ]

        caplog.set_level(logging.INFO)

        # ACT
        server.render_newsletter(self.title, self.id, self.issue, self.issue)

        # ASSERT
        mock_print.assert_any_call("Content-Type: text/html")
        mock_print.assert_any_call("Status: 200\n")

        mock_format.assert_any_call("text_question", {"NAME": "User 2", "TEXT": "Answer 1"}, sanitize=True)
        mock_format.assert_any_call("text_question", {"NAME": "User 1", "TEXT": "Answer 1"}, sanitize=True)
        mock_format.assert_any_call("img_question", {"NAME": "User 2", "SRC": "/images/path", "CAPTION": "Answer 2"}, sanitize=True)

        mock_format.assert_any_call(ANY, {"CREATOR": "User", "QUESTION": "Question 1", "RESPONSES": ANY})
        mock_format.assert_any_call(ANY, {"CREATOR": "User 2", "QUESTION": "Question 2", "RESPONSES": ANY})

        mock_navbar.assert_called()
        mock_shutil.assert_called_once()

        assert "Rendering published newsletter" in caplog.text


class TestRender:
    config = NewsletterConfig(
        name="Title",
        email="mail@mail.com",
        folder="exists",
        link="https://www.site.net",
        issue=5,
        defaults=[]
    )

    token = NewsletterToken(
        title="Title",
        folder="exists",
        id=1
    )
    def test_render_question_form(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_now.strftime.return_value = "1"

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch('server.get_questions')
        mock_questions.return_value = ([None], None)

        mock_question_renderer = mocker.patch('server.render_question_form')

        # ACT
        server.render(self.token, None)

        # ASSERT
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_question_form_fuzz(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch('server.get_questions')
        mock_questions.return_value = ([None], None)

        for week_num in ["2", "5", "42"]:
            mock_now.strftime.return_value = week_num
            mock_question_renderer = mocker.patch('server.render_question_form')

            # ACT
            server.render(self.token, None)

            # ASSERT
            mock_question_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_question_default_insert(self, mocker, caplog):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_now.strftime.return_value = "1"

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch('server.get_questions')
        mock_questions.return_value = ([], None)

        mock_insert = mocker.patch('server.insert_default_questions')
        mock_insert.return_value = (True, None)

        mock_question_renderer = mocker.patch('server.render_question_form')

        caplog.set_level(logging.INFO)

        # ACT
        server.render(self.token, None)

        # ASSERT
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

        assert "Inserting default questions" in caplog.text
        assert "Failed to add default questions" not in caplog.text

    def test_render_question_default_insert_fail(self, mocker, caplog):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_now.strftime.return_value = "1"

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch('server.get_questions')
        mock_questions.return_value = ([], None)

        mock_insert = mocker.patch('server.insert_default_questions')
        mock_insert.return_value = (False, "error message")

        mock_question_renderer = mocker.patch('server.render_question_form')

        caplog.set_level(logging.WARN)

        # ACT
        server.render(self.token, None)

        # ASSERT
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

        assert "Failed to add default questions\nerror message" not in caplog.text

    def test_render_answer_form(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_now.strftime.return_value = "3"

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_answer_renderer = mocker.patch('server.render_answer_form')

        # ACT
        server.render(self.token, None)

        # ASSERT
        mock_answer_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_answer_form_fuzz(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        for week_num in ["7", "35"]:
            mock_now.strftime.return_value = week_num
            mock_answer_renderer = mocker.patch('server.render_answer_form')

            # ACT
            server.render(self.token, None)

            # ASSERT
            mock_answer_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_newsletter(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')
        mock_now.strftime.return_value = "4"

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_newsletter_renderer = mocker.patch('server.render_newsletter')

        # ACT
        server.render(self.token, None)

        # ASSERT
        mock_newsletter_renderer.assert_called_once_with("Title", 1, 5, 5)

    def test_render_newsletter_fuzz(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        for week_num in ["4", "28"]:
            mock_now.strftime.return_value = week_num
            mock_newsletter_renderer = mocker.patch('server.render_newsletter')

            # ACT
            server.render(self.token, None)

            # ASSERT
            mock_newsletter_renderer.assert_called_once_with("Title", 1, 5, 5)

    def test_render_historic_issue(self, mocker, caplog):
        # ARRANGE
        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_newsletter = mocker.patch('server.render_newsletter')

        caplog.set_level(logging.DEBUG)

        # ACT
        server.render(self.token, 4)

        # ASSERT
        mock_newsletter.assert_called_once_with("Title", 1, 4, 5)

        assert "Rendering historical issue no. 4" in caplog.text

    def test_render_future_issue_fails(self, mocker, caplog):
        # ARRANGE
        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_newsletter = mocker.patch('server.render_newsletter')

        caplog.set_level(logging.DEBUG)

        with pytest.raises(NewsletterException) as e_info:
            # ACT
            server.render(self.token, 6)

        # ASSERT
        assert e_info.value.status == 404
        assert e_info.value.msg == "Issue 6 does not exist for Title"

        mock_newsletter.assert_not_called()

    def test_render_current_issue_same_as_none(self, mocker):
        # ARRANGE
        mock_now = mocker.patch('server.NOW')

        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = (True, self.config)

        mock_getter = mocker.patch('server.get_questions')
        mock_getter.return_value = ([None], None)

        mock_question_renderer = mocker.patch('server.render_question_form')
        mock_answer_renderer = mocker.patch('server.render_answer_form')
        mock_newsletter = mocker.patch('server.render_newsletter')

        for week_num, mock_renderer in zip(["1", "3", "4"], [mock_question_renderer, mock_question_renderer, mock_answer_renderer, mock_newsletter]):
            mock_now.strftime.return_value = week_num

            # ACT
            server.render(self.token, self.config.issue)

            # ASSERT
            mock_renderer.assert_called_once()

    def test_config_issues_fail(self, mocker):
        # ARRANGE
        mock_load = mocker.patch('server.load_config')
        mock_load.return_value = False, EmptyConfig

        # ACT
        with pytest.raises(NewsletterException) as e_info:
            server.render(self.token, None)

        # ASSERT
        assert e_info.value.status == 500
        assert e_info.value.msg == "Failed to load config"


class TestAnswer:
    params = {
        "unlock": "password",
        "name": "Jo Blogs",
        "question_1": "",
        "question_2": "Answer 2",
        "question_3": "Caption",
        "image_3": {"path": "some/path"},
    }
    def test_answer_submission(self, mocker, caplog):
        mock_insert = mocker.patch('server.insert_answer')
        mock_insert.return_value = (True, "")

        caplog.set_level(logging.INFO)

        responses = {
            "2": {"img": None, "text": "Answer 2"},
            "3": {"img": "some/path", "text": "Caption"}
        }

        with pytest.raises(NewsletterException) as e_info:
            server.answer(self.params)

        assert e_info.value.status == 201
        assert e_info.value.msg == "Thank you for submitting your answers :)."

        assert "Processing images upload" in caplog.text

        mock_insert.assert_called_once_with("Jo Blogs", ANY)
        assert isinstance(mock_insert.call_args[0][1], defaultdict)
        assert dict(mock_insert.call_args[0][1]) == responses

    def test_answer_submission_database_error(self, mocker):
        mock_insert = mocker.patch('server.insert_answer')
        mock_insert.return_value = (False, "database error")

        with pytest.raises(NewsletterException) as e_info:
            server.answer(self.params)

        assert e_info.value.status == 500
        assert e_info.value.msg == "database error"

    def test_answer_submission_fake_type(self):
        params = copy.deepcopy(self.params)
        params["caption_1"] = "injection"

        with pytest.raises(NewsletterException) as e_info:
            server.answer(params)

        assert e_info.value.status == 400
        assert e_info.value.msg == "Form keys are not in expected format. Do not mess with the post request!"

    def test_answer_submission_meddled(self):
        params = copy.deepcopy(self.params)
        params["image_caption_1"] = "injection"

        with pytest.raises(NewsletterException) as e_info:
            server.answer(params)

        assert e_info.value.status == 400
        assert e_info.value.msg == "Form keys not in two parts. Do not mess with the post request!"

    def test_answer_submission_no_name(self):
        params = copy.deepcopy(self.params)
        params["name"] = ""

        with pytest.raises(NewsletterException) as e_info:
            server.answer(params)

        assert e_info.value.status == 422
        assert e_info.value.msg == "No name provided"


class TestQuestion:
    pass
