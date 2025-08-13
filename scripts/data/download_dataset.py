import argparse
import json
import os
import sys

from sqlmodel import Session, create_engine, select

from utu.db.eval_datapoint import DatasetSample


def download_dataset(dataset_name: str, output_path: str):
    """
    Connects to the database, fetches all datapoints for a specific dataset,
    and saves them to a local JSONL file.
    """
    db_url = os.environ.get("DB_URL")
    if not db_url:
        print("Error: DB_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(db_url)

    print(f"Connecting to the database...")
    with Session(engine) as session:
        print(f"Fetching datapoints for dataset: '{dataset_name}'...")

        statement = select(DatasetSample).where(DatasetSample.dataset == dataset_name).order_by(DatasetSample.index)
        datapoints = session.exec(statement).all()

        if not datapoints:
            print(f"No datapoints found for dataset '{dataset_name}'.")
            return

        print(f"Found {len(datapoints)} datapoints. Saving to {output_path}...")

        with open(output_path, "w", encoding="utf-8") as f:
            for dp in datapoints:
                # Convert the SQLModel object to a dictionary
                dp_dict = dp.model_dump(exclude_none=True)
                f.write(json.dumps(dp_dict, ensure_ascii=False) + "\n")

    print("Download complete.")


def main():
    parser = argparse.ArgumentParser(description="Download a dataset from the database to a JSONL file.")
    parser.add_argument("--dataset_name", type=str, help="The name of the dataset to download.")
    parser.add_argument("--output_path", type=str, default=None, help="The path to the output JSONL file.")

    args = parser.parse_args()

    if not args.output_path:
        args.output_path = f"data/{args.dataset_name}.jsonl"

    download_dataset(args.dataset_name, args.output_path)


if __name__ == "__main__":
    main()
