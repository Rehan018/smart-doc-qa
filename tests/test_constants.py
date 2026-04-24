from app.core.constants import NO_ANSWER_MESSAGE


def test_no_answer_message_is_stable():
    assert (
        NO_ANSWER_MESSAGE
        == "I couldn't find a reliable answer in the uploaded documents."
    )
