import pandas as pd

from utu.utils import DIR_ROOT

FN = DIR_ROOT / "data" / "web_walker" / "test.jsonl"


def main():
    df = pd.read_json(FN, lines=True)
    print(df.columns)
    print(df.shape)
    df["difficulty_level"] = df["info"].apply(lambda x: x["difficulty_level"])
    difficulty_dist = df["difficulty_level"].value_counts()
    print(difficulty_dist)

    # sample 50 from each difficulty level
    # easy, medium, hard
    df_sampled = df.groupby("difficulty_level").apply(lambda x: x.sample(n=50, random_state=42)).reset_index(drop=True)
    print(df_sampled.shape)
    print(df_sampled["difficulty_level"].value_counts())

    # save to jsonl
    df_sampled.to_json(FN.parent / "test_sampled_150.jsonl", lines=True, orient="records", force_ascii=False)

if __name__ == "__main__":
    main()
