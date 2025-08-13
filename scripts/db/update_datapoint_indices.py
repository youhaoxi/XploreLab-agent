"""
EvaluationSample: add index column
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
from collections import defaultdict

from utu.db import EvaluationSample


def update_indices():
    """
    Connects to the database, adds the 'index' column if it doesn't exist,
    and then updates the index for each datapoint within a dataset.
    The index is based on the primary key `id`.
    """
    db_url = os.environ.get("DB_URL")
    if not db_url:
        print("Error: DB_URL environment variable not set.")
        return

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Step 1: Add the 'index' column if it doesn't exist
    try:
        with session.begin_nested():
            print("Attempting to add 'index' column to 'data' table...")
            session.execute(text('ALTER TABLE data ADD COLUMN "index" INTEGER'))
            print("'index' column added successfully.")
        session.commit()
    except ProgrammingError as e:
        # This error is often raised if the column already exists (e.g., in PostgreSQL).
        session.rollback()
        print(f"Could not add column, it might already exist. Error: {e}. Proceeding...")
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred during ALTER TABLE: {e}. Aborting.")
        session.close()
        return

    # Step 2: Populate the 'index' column
    try:
        print("Fetching all evaluation datapoints to update indices...")
        datapoints = session.query(EvaluationSample).order_by(EvaluationSample.id).all()

        # Group datapoints by dataset
        dataset_map = defaultdict(list)
        for dp in datapoints:
            dataset_map[dp.dataset].append(dp)

        print(f"Found {len(datapoints)} datapoints across {len(dataset_map)} datasets.")

        # Update indices within each dataset
        for dataset_name, dps in dataset_map.items():
            print(f"Updating indices for dataset: {dataset_name}")
            for i, dp in enumerate(dps):
                # Check if index needs updating to avoid unnecessary writes
                if dp.index != i + 1:
                    dp.index = i + 1

        print("Committing index updates to the database...")
        session.commit()
        print("Successfully updated all datapoint indices.")

    except Exception as e:
        print(f"An error occurred during the update process: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    update_indices()
