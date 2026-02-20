from pathlib import Path
import sys

# Ensure Spaces runtime can import project code without self-installing package.
sys.path.insert(0, str((Path(__file__).resolve().parent / "src").resolve()))

from llm_eval.ui.gradio_app import build_app

app = build_app()

if __name__ == "__main__":
    app.launch()
