# utu-agent-ui

1. install npm packages

```
npm install
```

2. build

```
pip install build
bash ./build.sh
```

you will get a wheel file in the `build` directory.

3. usage

to use the static files, install the wheel file

```
pip install utu_agent_ui-0.1.0-py3-none-any.whl
```

usage example:

```python
import importlib

static_files = importlib.resources.files("utu_agent_ui").joinpath("static")

# hack for tornado (convert `static_files` to str path)
with importlib.resources.as_file(importlib.resources.files("utu_agent_ui.static").joinpath("index.html")) as static_dir:
  static_path = str(static_dir).replace("index.html", "")

# then you can use `static_path` as the static path for tornado
```