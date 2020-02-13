import argparse
import logging
from math import ceil

from peewee import *
from playhouse.shortcuts import model_to_dict
from tqdm import tqdm
import yaml

from db_loader import DbLoader
from trendpulse_models import database, TrendpulseSummaryTsaV2 as tp

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("--limit", default=None)
args = parser.parse_args()


class Trendpulse:
    """
    Class Trendpulse

        Given:
        - Date_of_month = data collection day, happens end of each month.
        - Column weeks['times'] contain 36 monthly dates from 3 previous years from date_of_month.
        - Column weeks['volumes'] contain volumes for each of those 36 months.
        - Column period represents number of months.
        - Each date_of_month has 3 periods: 1,3,6
        - Period 1 would equal to the 1 month.

        Formula used:

            period 1 month is 4.345 weeks
            period 3 months is 13.035 weeks
            period 6 months is 26.07 weeks

            The weeks['times'] field holds dates of 36 months. I take the oldest date and the
            latest date and calculate the total amount of weeks. Then I get the sum of the
            weeks['volumes'] field and divide that with the total weeks to get the weekly average
            value.

                weekly_avg = sum_of_volumes / total_weeks_from_dates

            Now I multiple each periods (converted to weeks) with the weekly_avg to get the
            final search_volume for each corresponding row.

                search_volume = weekly_avg * period_in_weeks

    """

    def __init__(self, limit):
        self.last_weekly_avg = None
        self.limit = limit
        self.periods = self._get_distinct_periods()
        self.total_upsert_count = 0

    def _get_distinct_periods(self):
        """
        Get distinct periods with its corresponding weeks
        """
        periods = {}
        # weeks in a month = ((days / year) / week ) rounded upto three decimal points.
        weeks_in_a_month = round((365 / 12) / 7, 3)

        query = (tp
                .select(tp.period)
                .distinct()
                .order_by(tp.period.asc()))

        for model in query:
            periods[model.period] = model.period * weeks_in_a_month

        return periods

    def _get_upsert_query(self):
        """
        Query to find rows that needs search_volume update.
        """
        query = (tp
                .select()
                .where((tp.search_volume == 0) & (tp.weeks != ""))
                .order_by(tp.search.asc(), tp.date_of_month.asc(), tp.period.asc())
                .limit(self.limit))

        # total result.
        self.total_upsert_count = query.count()
        return query

    def transform_data(self, query):
        """
        Transform data.
        """
        for model in query:
            yield self._calculate_avg(model)

    def _calculate_avg(self, model):
        """
        Calculate weekly average based on a model's weeks timeframe.
        """
        # do calculation only once and store/use/replace value.
        if not self.last_weekly_avg or model.period == list(self.periods)[0]:
            # weeks column consist of invalid JSON (missing double quotes),
            # so using the yaml module to normalize it.
            weeks = yaml.load(model.weeks, Loader=yaml.FullLoader)
            # Sorted dates list found in "times" key. We will need to extract the 
            # earliest date and the latest date from it.
            dates = weeks["times"]
            first_date_found = dates[0]
            last_date_found = dates[-1]
            date_delta = last_date_found - first_date_found
            # Calculate the total weeks within this time frame and get the weekly
            # average time.
            total_weeks_from_dates = (date_delta.days // 7)
            volumes_total = sum(weeks["volumes"])
            weekly_avg = volumes_total / total_weeks_from_dates
            self.last_weekly_avg = weekly_avg

        if self.last_weekly_avg:
            # Set the search_volume for the period based on its weeks count
            model.search_volume = self.last_weekly_avg * self.periods[model.period]

        return model_to_dict(model)

    def upsert_search_volume(self):
        """
        Upsert search volume from transformed models.
        """
        query = self._get_upsert_query()

        logger.info(f"Upsert start...")
        if not self.total_upsert_count:
            logger.info("Nothing to upsert")
        else:
            chunk_size = 10000
            total_batches = ceil(self.total_upsert_count / chunk_size)

            with database.atomic(), \
                     tqdm(total=self.total_upsert_count,
                          desc="Upserting",
                          postfix=f"batch 0/{total_batches}",
                          ncols=100) as pbar:
                for idx, batch in enumerate(chunked(self.transform_data(query), chunk_size)):
                    (tp
                     .insert_many(batch)
                     .on_conflict(
                            conflict_target=[tp.search, tp.date_of_month, tp.period],
                            update={tp.search_volume: EXCLUDED.search_volume}
                         )
                     .execute())
                    pbar.set_postfix_str(f"batch {idx + 1}/{total_batches}")
                    pbar.update(chunk_size)
            logger.info(f"Upsert completed")

if __name__ == "__main__":
    if (not tp.table_exists()) or (not len(tp)):
        DbLoader().load_data()

    limit = int(args.limit) if args.limit else None
    trendpulse = Trendpulse(limit)
    trendpulse.upsert_search_volume()
    logger.info("Goodbye!")

