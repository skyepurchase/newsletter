from unittest.mock import ANY

import mysql.connector
from mysql.connector import errorcode

from utils.database import (
    get_newsletters,
    get_questions,
    get_responses,
    insert_answer,
    insert_question,
    insert_default_questions,
    create_newsletter,
)


class TestDatabaseGetters:
    def test_get_newsletters(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.fetchall.return_value = [(1, "Newsletter 1", "pass_hash_1")]

        newsletters = get_newsletters()

        mock_cursor.execute.assert_called_once_with("SELECT * FROM newsletters;")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert newsletters == [(1, "Newsletter 1", "pass_hash_1")]

    def test_get_questions(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.fetchall.side_effect = [
            [(1, "User", "What is this?")],
            [(2, "What is the purpose?", "text")],
        ]

        default, submitted = get_questions(1, 1)

        mock_cursor.execute.assert_called_with(ANY, (1, 1))

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert submitted == [(1, "User", "What is this?")]
        assert default == [(2, "What is the purpose?", "text")]

    def test_get_responses(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.fetchall.side_effect = [
            [(21, "creator1", "User Question 1")],
            [(22, "Default Question 1")],
            [("creator1", "Answer 1", ["img1.png"])],
            [("", "Answer 2", ["img2.png"])],
        ]

        expected = [
            ("creator1", "User Question 1", [("creator1", "Answer 1", ["img1.png"])]),
            ("", "Default Question 1", [("", "Answer 2", ["img2.png"])]),
        ]

        results = get_responses(1, 1)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert mock_cursor.execute.call_count == 4
        for i, call in enumerate(
            [(ANY, (1, 1)), (ANY, (1, 1)), (ANY, (21,)), (ANY, (22,))]
        ):
            assert mock_cursor.execute.call_args_list[i][0] == call

        assert results == expected


class TestInsertAnswer:
    def test_insert_answer_success(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        responses = {1: {"img": "img1.png", "text": "Answer 1"}}
        success, error_text = insert_answer("User", responses)

        mock_cursor.execute.assert_called_with(ANY, (1, "User", "img1.png", "Answer 1"))
        mock_conn.commit.assert_called_once()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success
        assert error_text is None

    def test_insert_duplicate_answer(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_ENTRY
        )

        responses = {1: {"img": "img1.png", "text": "Answer 1"}}
        success, error_text = insert_answer("User", responses)

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success is not None
        assert not success
        assert error_text == "Attempted to insert entry that already exists."

    def test_insert_null_answer(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_BAD_NULL_ERROR
        )

        responses = {1: {"img": "img1.png", "text": "Answer 1"}}
        success, error_text = insert_answer("User", responses)

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success is not None
        assert not success
        assert error_text == "Expected value but received null."

    def test_insert_incorrectly_formatted_answer(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_FIELDNAME
        )

        responses = {1: {"img": "img1.png", "text": "Answer 1"}}
        success, error_text = insert_answer("User", responses)

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success is not None
        assert not success
        assert error_text == "Unexpected columns or duplicated columns."


class TestInsertQuestion:
    def test_insert_question_success(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        success, error_text = insert_question(1, 1, "User", "What is the purpose?")

        mock_cursor.execute.assert_called_with(
            ANY, (1, "User", "What is the purpose?", 1)
        )
        mock_conn.commit.assert_called_once()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success
        assert error_text is None

    def test_insert_duplicate_question(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_ENTRY
        )

        success, error_text = insert_question(1, 1, "User", "What is the purpose?")

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Attempted to insert entry that already exists."

    def test_insert_null_question(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_BAD_NULL_ERROR
        )

        success, error_text = insert_question(1, 1, "User", "What is the purpose?")

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Expected value but received null."

    def test_insert_incorrectly_formatted_question(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_FIELDNAME
        )

        success, error_text = insert_question(1, 1, "User", "What is the purpose?")

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Unexpected columns or duplicated columns."


class TestInsertDefaults:
    def test_insert_defaults_success(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        success, error_text = insert_default_questions(
            1, 1, [("What is the purpose?", "text")]
        )

        mock_cursor.execute.assert_called_with(
            ANY, (1, "SYS", "What is the purpose?", 1, True, "text")
        )
        mock_conn.commit.assert_called_once()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert success
        assert error_text is None

    def test_insert_duplicate_defaults(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_ENTRY
        )

        success, error_text = insert_default_questions(
            1, 1, [("User", "What is the purpose?")]
        )

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Attempted to insert entry that already exists."

    def test_insert_null_defaults(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_BAD_NULL_ERROR
        )

        success, error_text = insert_default_questions(
            1, 1, [("User", "What is the purpose?")]
        )

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Expected value but received null."

    def test_insert_incorrectly_formatted_defaults(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_FIELDNAME
        )

        success, error_text = insert_default_questions(
            1, 1, [("User", "What is the purpose?")]
        )

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Unexpected columns or duplicated columns."


class TestCreateNewsletter:
    def test_create_newsletter_success(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        success, error_text = create_newsletter("Title", b"hash", "config_folder")

        mock_cursor.execute.assert_called_once_with(
            ANY, ("Title", b"hash", "config_folder")
        )
        mock_conn.commit.assert_called_once()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success
        assert error_text is None

    def test_create_newsletter_duplicate(self, mocker):
        mock_conn = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_get_connection = mocker.patch("utils.database._get_connection")
        mock_get_connection.return_value = (mock_conn, mock_cursor)

        mock_cursor.execute.side_effect = mysql.connector.IntegrityError(
            errno=errorcode.ER_DUP_FIELDNAME
        )

        success, error_text = create_newsletter("Title", b"hash", "config_folder")

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
        assert success is not None
        assert not success
        assert error_text == "Failed to create newsletter due to integrity error."
