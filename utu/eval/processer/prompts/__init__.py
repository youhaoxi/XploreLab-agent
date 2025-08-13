import pathlib

import yaml


def load_yaml(file_path: pathlib.Path) -> dict[str, str]:
    with file_path.open() as f:
        return yaml.safe_load(f)


_prompt_path = pathlib.Path(__file__).parent
AUGMENTATION_PROMPTS = load_yaml(_prompt_path / "augmentation_templates.yaml")
JUDGE_PROMPTS = load_yaml(_prompt_path / "judge_templates.yaml")
