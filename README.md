# ledDisplay

Requires Python 3.11 or later. Python 3.10 is no longer supported because the
Pillow 13 security update requires Python 3.11.

Install the locked dependencies and run the image-processing compatibility tests:

```sh
uv sync --locked
uv run --locked python -m unittest discover -s tests
```
