"""Per-visitor scoping helpers (no credentials needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from text_utils import display_name, scoped_name, visible_to  # noqa: E402


def test_shared_documents_are_visible_to_everyone():
    assert visible_to("aquapilot_x3_manual.pdf", "a1b2c3d4")
    assert visible_to("aquapilot_x3_manual.pdf", None)


def test_uploads_are_visible_only_to_their_session():
    stored = scoped_name("a1b2c3d4", "contract.pdf")
    assert visible_to(stored, "a1b2c3d4")
    assert not visible_to(stored, "ffff0000")
    assert not visible_to(stored, None)


def test_display_name_strips_the_session_prefix():
    assert display_name(scoped_name("a1b2c3d4", "my__notes.pdf")) == "my__notes.pdf"
    assert display_name("aquapilot_x3_manual.pdf") == "aquapilot_x3_manual.pdf"
    # A double underscore alone is not a session prefix
    assert display_name("annual__report.pdf") == "annual__report.pdf"
