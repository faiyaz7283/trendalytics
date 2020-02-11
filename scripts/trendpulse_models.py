from peewee import *

database = PostgresqlDatabase(
    'trendpulse',
    **{'host': 'db',
       'port': 5432,
       'user': 'postgres',
       'password': 'postgres'}
)


class BaseModel(Model):
    class Meta:
        database = database

class TrendpulseSummaryTsaV2(BaseModel):
    date_of_month = DateField(null=True)
    period = IntegerField(null=True)
    search = TextField()
    search_volume = DecimalField(null=True)
    weeks = TextField(null=True)

    class Meta:
        table_name = 'trendpulse_summary_tsa_v2'
        indexes = (
            (('search', 'date_of_month', 'period'), True),
        )
        primary_key = False

