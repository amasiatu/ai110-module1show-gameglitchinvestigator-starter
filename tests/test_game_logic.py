from streamlit.testing.v1 import AppTest

from logic_utils import check_guess


def test_enter_key_submits_guess_via_form():
    # Regression test for the bug where pressing Enter in the guess input
    # did nothing. The fix moves the input + submit into an st.form, so the
    # submit becomes a form_submit_button (which Enter triggers natively).
    #
    # This test asserts the structural guarantee that makes Enter work:
    #   1. the guess input and a submit button live inside a form, and
    #   2. submitting that form actually processes the guess.
    at = AppTest.from_file("app.py").run()

    # Structural guarantee that makes Enter work: the guess input and its
    # submit button must live inside a single st.form. Enter only submits
    # when the control is a form_submit_button; a plain st.button (the old
    # code) ignores Enter entirely. AppTest can't press a physical Enter key,
    # so we assert the structure that wires Enter to submission instead.
    forms = at.get("form")
    assert forms, "guess input must be inside an st.form so Enter submits it"

    form = forms[0]
    child_types = {type(c).__name__ for c in form.children.values()}
    assert "TextInput" in child_types, "the guess input must be inside the form"

    submit_btn = next(
        b for b in form.children.values() if type(b).__name__ == "Button"
    )
    assert submit_btn.form_id, "submit must be a form_submit_button, not st.button"

    # Drive the form the same way pressing Enter does: set the input, submit.
    at.text_input[0].set_value("50").run()
    submit_btn.click().run()

    # The guess must have been registered: history records it and the
    # attempt counter advanced past its initial value.
    assert 50 in at.session_state["history"]
    assert at.session_state["attempts"] > 1
    assert not at.exception


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win.
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert message == "🎉 Correct!"


def test_guess_too_high_hints_lower():
    # Guess is above the secret -> outcome "Too High", hint must say GO LOWER.
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"


def test_guess_too_low_hints_higher():
    # Guess is below the secret -> outcome "Too Low", hint must say GO HIGHER.
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


def test_hint_direction_is_not_reversed():
    # Regression test for the original glitch where the high/low hints
    # were swapped. A high guess must never tell the player to go higher,
    # and a low guess must never tell them to go lower.
    _, high_message = check_guess(99, 50)
    assert "HIGHER" not in high_message

    _, low_message = check_guess(1, 50)
    assert "LOWER" not in low_message


def test_string_secret_still_gives_correct_hint():
    # The app passes the secret as a string on even attempts; the hint
    # must still be correct.
    outcome, message = check_guess(60, "50")
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"
