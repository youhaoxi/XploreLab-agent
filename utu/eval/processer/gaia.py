import os

from ..data import EvaluationSample as Datapoint
from .base import BaseMatchProcesser


class GAIAProcesser(BaseMatchProcesser):
    """ Processer for GAIA evaluation. """
    name: str = "GAIA"

    # TODO(siqi): fix the "file_name" to the correct path in the project
    def calculate_metrics(self, samples: list[Datapoint]) -> dict:
        # 1. calculate level metrics
        level_bin = {}
        invalid_count = 0
        for item in samples:
            level = item.level
            if level not in level_bin:
                level_bin[level] = {"correct": 0, "wrong": 0, "unknown": 0}
            if item.judged_response == "invalid":
                level_bin[level]["unknown"] += 1
                invalid_count += 1
                continue
            if item.correct:
                level_bin[level]["correct"] += 1
            else:
                level_bin[level]["wrong"] += 1
        # calculate overall metrics
        for level, counts in level_bin.items():
            total = counts["correct"] + counts["wrong"]
            if total > 0:
                counts["accuracy"] = round(counts["correct"] / total * 100, 4)
            else:
                counts["accuracy"] = 0.0
        # 2. calculate overall accuracy
        total = len(samples)
        correct_count = sum(item.correct for item in samples)
        incorrect_count = total - correct_count - invalid_count

        return {
            "Accuracy (%)": round(correct_count / total * 100, 4),
            "Details": {
                "correct": correct_count,
                "wrong": incorrect_count,
                "unknown": invalid_count,
                "total": total,
                "level_metrics": level_bin
            } 
        }

    def _get_file_prompt(self, file_name: str) -> str:
        """
        Get the file prompt if applicable.
        """
        prompt_use_files = ""
        if file_name:
            if ".MOV" in file_name:
                return ""
            prompt_use_files += f"\n\nTo answer the question above, you will have to use these attached files:"
            if file_name.split('.')[-1] in ['pdf', 'xlsx']:
                image_path = file_name.split('.')[0] + '.png'
                if os.path.exists(image_path):
                    prompt_use_files += f"\nAttached image: {image_path}"
                else:
                    prompt_use_files += f"\nAttached file: {file_name}"
            elif file_name.split('.')[-1] == "zip":
                import shutil
                folder_name = file_name.replace(".zip", "")
                os.makedirs(folder_name, exist_ok=True)
                shutil.unpack_archive(file_name, folder_name)

                # Convert the extracted files
                prompt_use_files = "\n\nYou have been given a zip archive of supporting files. We extracted it into a directory: find the extracted files at the following paths:\n"
                for root, dirs, files in os.walk(folder_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        prompt_use_files += f"- {file_path}\n"
            elif file_name.split('.')[-1] in ['png', 'jpg', 'jpeg']:
                prompt_use_files += f"\nAttached image: {file_name}"
            elif file_name.split('.')[-1] in ['mp3', 'm4a', 'wav']:
                prompt_use_files += f"\nAttached audio: {file_name}"
            else:
                prompt_use_files += f"\nAttached file: {file_name}"
        else:
            prompt_use_files += "\n\nYou have been given no local files to access."

        return prompt_use_files
