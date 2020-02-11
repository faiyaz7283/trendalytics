CREATE TABLE "public"."trendpulse_summary_tsa_v2"


(
    "search"                          text NOT NULL,
    "search_volume"                   numeric,
    "weeks"                           text,
    "date_of_month"                   date,
    "period"                          int4
)
    WITH (OIDS= FALSE)
;

create unique index on public.trendpulse_summary_tsa_v2
    USING btree
    (search, date_of_month, period);
