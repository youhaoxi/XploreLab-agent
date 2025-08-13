import pandas as pd

from utu.utils import DIR_ROOT

FN = DIR_ROOT / "data" / "WebWalker.jsonl"


def main(n: int = 50):
    # set random seed
    import random

    random.seed(42)

    df = pd.read_json(FN, lines=True)
    print(df.columns)
    print(df.shape)

    # if has `id` column, remove it
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # df["difficulty_level"] = df["info"].apply(lambda x: x["difficulty_level"])
    # difficulty_dist = df["difficulty_level"].value_counts()
    difficulty_dist = df["level"].value_counts()
    print(difficulty_dist)

    # sample 50 from each level - easy, medium, hard
    df_sampled = df.groupby("level").apply(lambda x: x.sample(n=n, random_state=42)).reset_index(drop=True)
    print(df_sampled.shape)
    print(df_sampled["level"].value_counts())

    # move `index` to `source_index`
    df_sampled["source_index"] = df_sampled["index"]
    # reset index, from 1
    df_sampled["index"] = range(1, len(df_sampled) + 1)

    # save to jsonl
    df_sampled.to_json(FN.parent / f"WebWalker_{3 * n}.jsonl", lines=True, orient="records", force_ascii=False)


if __name__ == "__main__":
    main()
