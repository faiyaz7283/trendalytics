import csv
import logging
from math import ceil
import os

from peewee import chunked
from tqdm import tqdm
import yaml

from trendpulse_models import database, TrendpulseSummaryTsaV2 as tp

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class DbLoader:
    """
    A simple class to extract and load data from a CSV file onto postgres DB.
    """

    def __init__(self):
        script_dir = os.path.dirname(__file__)
        rel_path = "../data/trendpulse_summary_tsa_v2.csv"
        self.csv_file = os.path.join(script_dir, rel_path)

    def _extract_data(self):
        """
        Extract all the data from CSV file.
        """
        with open(self.csv_file) as cf:
            csv_reader = csv.reader(cf, delimiter="\t")
            columns = ["search", "search_volume", "weeks", "date_of_month", "period"]
            for row in csv_reader:
                row = [r.replace("\\N", "") for r in row]
                extracted_row = {col:row[key] for key, col in enumerate(columns)}
                yield extracted_row

    def load_data(self):
        """
        Load data into table if empty.
        """
        if len(tp):
            logger.info("Data already exist")
        else:
            with open(self.csv_file) as cf:
                total = sum(1 for row in csv.reader(cf, delimiter="\t"))
            data = self._extract_data()
            chunk_size = 100000
            total_batches = ceil(total / chunk_size)
            logger.info("Load start...")
            with database.atomic(), \
                     tqdm(total=total,
                          desc="Loading",
                          postfix=f"batch 0/{total_batches}",
                          ncols=100) as pbar:
                for idx, batch in enumerate(chunked(data, chunk_size)):
                    tp.insert_many(batch).execute()
                    pbar.set_postfix_str(f"batch {idx + 1}/{total_batches}")
                    pbar.update(chunk_size)
            logger.info("Load completed")


if __name__ == "__main__":
    DbLoader().load_data()
