from pathlib import Path


def test_acceptance_checkpoints_are_recorded() -> None:
    docs = (Path(__file__).parents[2] / "docs" / "tasks.md").read_text()

    for checkpoint in (
        "- [x] 15. Foundation checkpoint",
        "- [x] 16. Data and research checkpoint",
        "- [x] 17. Final checkpoint",
    ):
        assert docs.count(checkpoint) == 1
