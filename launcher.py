import inspect
import os
from pathlib import Path

from streamlit.web import bootstrap


def main():
    project_dir = Path(__file__).resolve().parent
    app_path = project_dir / "app.py"

    os.chdir(project_dir)
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "localhost")

    signature = inspect.signature(bootstrap.run)
    param_count = len(signature.parameters)

    if param_count == 4:
        bootstrap.run(str(app_path), False, [], {})
    elif param_count == 3:
        bootstrap.run(str(app_path), [], {})
    else:
        bootstrap.run(str(app_path), False, [], {}, flag_options={})


if __name__ == "__main__":
    main()
