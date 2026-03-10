from collections import defaultdict
import logging
import copy
from unittest.mock import ANY


import endpoints
from utils.constants import State
from utils.type_hints import (
    EmptyConfig,
    NewsletterConfig,
    NewsletterToken,
)


class TestRender:
    config = NewsletterConfig(
        name="Title",
        email="mail@mail.com",
        folder="exists",
        link="https://www.site.net",
        issue=5,
        defaults=[],
    )

    token = NewsletterToken(title="Title", folder="exists", id=1)

    def test_render_question_form(self, mocker):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")
        mock_state.return_value = State.Question

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch("endpoints.get_questions")
        mock_questions.return_value = ([None], None)

        mock_question_renderer = mocker.patch("endpoints.render_question_form")

        # ACT
        endpoints.render(self.token, None)

        # ASSERT
        mock_load.assert_called_once_with("exists", ANY)
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_question_default_insert(self, mocker, caplog):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")
        mock_state.return_value = State.Question

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch("endpoints.get_questions")
        mock_questions.return_value = ([], None)

        mock_insert = mocker.patch("endpoints.insert_default_questions")
        mock_insert.return_value = (True, None)

        mock_question_renderer = mocker.patch("endpoints.render_question_form")

        caplog.set_level(logging.INFO)

        # ACT
        endpoints.render(self.token, None)

        # ASSERT
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

        assert "Inserting default questions" in caplog.text
        assert "Failed to add default questions" not in caplog.text

    def test_render_question_default_insert_fail(self, mocker, caplog):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")
        mock_state.return_value = State.Question

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_questions = mocker.patch("endpoints.get_questions")
        mock_questions.return_value = ([], None)

        mock_insert = mocker.patch("endpoints.insert_default_questions")
        mock_insert.return_value = (False, "error message")

        mock_question_renderer = mocker.patch("endpoints.render_question_form")

        caplog.set_level(logging.WARN)

        # ACT
        endpoints.render(self.token, None)

        # ASSERT
        mock_question_renderer.assert_called_once_with("Title", 1, 5)

        assert "Failed to add default questions\nerror message" not in caplog.text

    def test_render_answer_form(self, mocker):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")
        mock_state.return_value = State.Answer

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_answer_renderer = mocker.patch("endpoints.render_answer_form")

        # ACT
        endpoints.render(self.token, None)

        # ASSERT
        mock_answer_renderer.assert_called_once_with("Title", 1, 5)

    def test_render_newsletter(self, mocker):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")
        mock_state.return_value = State.Publish

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_newsletter_renderer = mocker.patch("endpoints.render_newsletter")

        # ACT
        endpoints.render(self.token, None)

        # ASSERT
        mock_newsletter_renderer.assert_called_once_with("Title", 1, 5, 5)

    def test_render_historic_issue(self, mocker, caplog):
        # ARRANGE
        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_newsletter = mocker.patch("endpoints.render_newsletter")

        caplog.set_level(logging.DEBUG)

        # ACT
        endpoints.render(self.token, 4)

        # ASSERT
        mock_newsletter.assert_called_once_with("Title", 1, 4, 5)

        assert "Rendering historical issue no. 4" in caplog.text

    def test_render_future_issue_fails(self, mocker, caplog):
        # ARRANGE
        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_newsletter = mocker.patch("endpoints.render_newsletter")

        caplog.set_level(logging.DEBUG)

        # ACT
        response = endpoints.render(self.token, 6)

        # ASSERT
        assert response.status == 404
        assert response.content == "Issue 6 does not exist for Title"
        assert response.content_type == "text/plain"

        mock_newsletter.assert_not_called()

    def test_render_current_issue_same_as_none(self, mocker):
        # ARRANGE
        mock_state = mocker.patch("endpoints.get_state")

        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_getter = mocker.patch("endpoints.get_questions")
        mock_getter.return_value = ([None], None)

        mock_question_renderer = mocker.patch("endpoints.render_question_form")
        mock_answer_renderer = mocker.patch("endpoints.render_answer_form")
        mock_newsletter = mocker.patch("endpoints.render_newsletter")

        for state, mock_renderer in zip(
            State,
            [
                mock_question_renderer,
                mock_answer_renderer,
                mock_newsletter,
            ],
        ):
            mock_state.return_value = state

            # ACT
            endpoints.render(self.token, self.config.issue)

            # ASSERT
            mock_renderer.assert_called_once()

    def test_config_issues_fail(self, mocker):
        # ARRANGE
        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = False, EmptyConfig

        # ACT
        response = endpoints.render(self.token, None)

        # ASSERT
        assert response.status == 500
        assert response.content == "Failed to load config"
        assert response.content_type == "text/plain"


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
        # ARRANGE
        mock_insert = mocker.patch("endpoints.insert_answer")
        mock_insert.return_value = (True, "")

        caplog.set_level(logging.INFO)

        responses = {
            "2": {"img": None, "text": "Answer 2"},
            "3": {"img": "some/path", "text": "Caption"},
        }

        # ACT
        response = endpoints.answer(self.params)

        # ASSERT
        assert response.status == 201
        assert response.content == "Thank you for submitting your answers :)."
        assert response.content_type == "text/plain"

        assert "Processing images upload" in caplog.text

        mock_insert.assert_called_once_with("Jo Blogs", ANY)
        assert isinstance(mock_insert.call_args[0][1], defaultdict)
        assert dict(mock_insert.call_args[0][1]) == responses

    def test_answer_submission_database_error(self, mocker):
        # ARRANGE
        mock_insert = mocker.patch("endpoints.insert_answer")
        mock_insert.return_value = (False, "database error")

        # ACT
        response = endpoints.answer(self.params)

        # ASSERT
        assert response.status == 500
        assert response.content == "database error"
        assert response.content_type == "text/plain"

    def test_answer_submission_fake_type(self):
        # ASSERT
        params = copy.deepcopy(self.params)
        params["caption_1"] = "injection"

        # ACT
        response = endpoints.answer(params)

        # ASSERT
        assert response.status == 400
        assert (
            response.content
            == "Form keys are not in expected format. Do not mess with the post request!"
        )
        assert response.content_type == "text/plain"

    def test_answer_submission_meddled(self):
        # ARRANGE
        params = copy.deepcopy(self.params)
        params["image_caption_1"] = "injection"

        # ACT
        response = endpoints.answer(params)

        # ASSERT
        assert response.status == 400
        assert (
            response.content
            == "Form keys not in two parts. Do not mess with the post request!"
        )
        assert response.content_type == "text/plain"

    def test_answer_submission_no_name(self):
        # ARRANGE
        params = copy.deepcopy(self.params)
        params["name"] = ""

        # ACT
        response = endpoints.answer(params)

        # ASSERT
        assert response.status == 422
        assert response.content == "No name provided"
        assert response.content_type == "text/plain"


class TestQuestion:
    config = NewsletterConfig(
        name="Title",
        email="mail@mail.com",
        folder="exists",
        link="https://www.site.net",
        issue=5,
        defaults=[],
    )

    params = {
        "unlock": "password",
        "name": "Jo Blogs",
        "question": "Question 1",
    }

    token = NewsletterToken(title="Title", folder="exists", id=1)

    def test_question_submission(self, mocker):
        # ARRANGE
        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_insert = mocker.patch("endpoints.insert_question")
        mock_insert.return_value = (True, "")

        # ACT
        response = endpoints.question_submit(self.token, self.params)

        # ASSERT
        assert response.status == 201
        assert response.content == "Thank you for submitting your question :)."
        assert response.content_type == "text/plain"

        mock_load.assert_called_once_with("exists", ANY)
        mock_insert.assert_called_once_with(1, 5, "Jo Blogs", "Question 1")

    def test_question_submission_database_error(self, mocker):
        # ARRANGE
        mock_load = mocker.patch("endpoints.load_config")
        mock_load.return_value = (True, self.config)

        mock_insert = mocker.patch("endpoints.insert_question")
        mock_insert.return_value = (False, "database error.")

        # ACT
        response = endpoints.question_submit(self.token, self.params)

        # ASSERT
        assert response.status == 500
        assert response.content == "database error."
        assert response.content_type == "text/plain"
