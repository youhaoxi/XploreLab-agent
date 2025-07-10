## changed files
- add folder `data` to define unifined structures for dataset samples and evaluaon results, along with the DataManager class to for the management of the dataset.
- add folder `processer` to define classes for pre-processing input dataset and post-processing output results(including judgement and stat.)
- add folder `benchmark` to define classes for the overall evaluation process, including laoding dataset, running inference, and evaluating the results.
- add file `common.py` to define some common functions for evaluation.
- add file `run_eval.py` and script `run_eval.sh` to run evaluation.
- add class `EvalConfig` in `utu/config/eval_config.py` to load evaluation config, and add new folder `configs/eval` to define evaluation configs.
- add some built-in benchmarks.

## run evaluation
**1. configure your evaluation config in `configs/eval`.**
```
dataset: [the dataset to be evaluated, maybe bulit-in benchmark name or file path for your own dataset.]
type: ["mixed"|"single", "mixed" means the dataset contains samples from mixed benckmarks.]
question_field: [the field name of question in the dataset.]
gt_field: [the field name of ground truth in the dataset.]

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

bash utu/eval/run_eval.sh --config_name [your_config_name]
```
