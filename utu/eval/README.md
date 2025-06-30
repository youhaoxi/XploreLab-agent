## changed files
- add folder `data_processer` to define classes for pre-processing input dataset.
- add folder `evaluation` to define classes for post-processing output prediction. (e.g. call LLM to judge correctness, calculate metrics, etc.)
- add file `common.py` to define samples' structure for pre-processing and post-processing, along with some common functions for evaluation.
- add file `run_eval.py` and script `run_eval.sh` to run evaluation.
- add class `EvalConfig` in `utu/config/loader.py` to load evaluation config, and add new file `configs/eval/eval.yaml` to define evaluation config.
- add some built-in benchmarks dataset in the folder `data`.

## run evaluation
**1. configure your evaluation config in `configs/eval/eval.yaml`.**
```
dataset: [the dataset to be evaluated, maybe bulit-in benchmark name or file path for your own dataset.]
eval_method: [you can speicify the evaluation method as benchmark name, or ignore this field to use default evaluation method.]
type: ["mixed"|"single", "mixed" means the dataset contains samples from mixed benckmarks.]
question_field: [the field name of question in the dataset.]
gt_field: [the field name of ground truth in the dataset.]

output_file: [output file name for prediction results.]
metrics_file : [output file name for metrics results.]
judge_output_file: [output file name for judgement results.]

thread_pool_size: [size of thread pool for inference and evaluation.]
concurrency: [concurrency for calling LLM service at inference time.]
max_turns: [the maximum number of turns for agent's acitons.]

judge_model: ${oc.env:JUDGE_MODEL}
judge_api_key: ${oc.env:JUDGE_API_KEY}
judge_model_base_url: ${oc.env:JUDGE_MODEL_BASE_URL}
judge_concurrency: [concurrency for calling LLM service at judgement time.]
```

**2. run evaluation scipt**

in the main folder, run
```
cp .env.example .env
# ... setup env, invluding env for LLM-based judgement.

bash utu/eval/run_eval.sh
```
