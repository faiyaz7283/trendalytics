# Solution explained

![Running-Solution](https://raw.githubusercontent.com/faiyaz7283/gifs/master/take-home.gif)

## Given
- Date_of_month = data collection day, happens end of each month.
- Column weeks['times'] contains 36 monthly dates from 3 previous years from date_of_month.
- Column weeks['volumes'] contains volumes for each of those 36 months.
- Column period represents number of months.
- Each search and date_of_month row has one of these three periods: 1, 3, 6

## Formula breakdown
Based on my understanding from the information above, here is my breakdown of the formula used to solve the take home challenge.

### Periods converted to weeks
First I gather all the distinct periods (number represents month) - Found three 1, 3 and 6.
Then I convert these months into weeks (since we are interested in weekly avg) and asscociate
them with the period. Based on a google search a month equals about 4.345 weeks, so I went with it.
So to calculate weeks for each period, I take the period value and multiple with 4.345. Below are
the actual numbers.

| period | weeks |
| :---: | :---: |
| 1 | 4.345 |
| 2 | 13.05 |
| 3 | 26.07 |

#### Base weekly average per row
Now that I have the periods sorted out. Next challenge was to get a base weekly average from the weeks['volumes']. Each 'weeks' column represents 36 prior months data from 'date_of_month' date. So to get the weekly average from those 36 monthly volumes, I had to first figure out iroughly how many weeks are in between those weeks timefrmae. So I subtracted the first date from the last date, and used that timedelta to calculate approximate weeks. That number was generally ~150 to 152ish. I used this varying number of weeks and divided the sum of volumes found for each row. This was my base weekly average value.

> weekly_avg = sum_of_volumes / total_weeks_from_dates

#### Calculating the search volume
So for each applicable row, I used the weekly average and multiplied it with the number of weeks
representing the row's period. And this is the value I stored for that row's 'search_volume' column.

> search_volume = weekly_avg * period_in_weeks


## Running the services

To run the services with docker-compose, there is a helper build.sh script. I have used this script as a switch to invoke the underlying docker-compose setup. There are 1 optional flag `--limit <int>` available, and 2 choices of arguments `start | kill`. The flag and its value must be given before an argument, otherwise the script will ignore all. Running the script without `start` will directly invoke the worker container and it's task.

### Start service 

Start the service. Bring up docker-compose, worker waits for 30 second before task execution to allow postgres container to be ready for incoming requests.

```./build.sh start```

Similar with above, but just adds a limit flag. Basically, this tells the worker to only update search_volume column to only the limit number of rows. **Important** to note, regardless of limit set, the csv data extraction, transforming and storing the data will be done in full scale. 

```./build.sh --limit 10000 start```

### Kill services

Kill the docker-compose services. Basically it performs a docker-compose down, destroying the containers and networkks.

```./build.sh kill```

### Continue service

If the docker-compose has been started and containers are up and available, then you should avoid the `start` argument.
**Important** to note, running without any argument will fail if docker-compose is not already running.

```./build.sh```

You can also pass the `--limit <int>` flag.

```./build.sh --limit 10000```

## Walk through the process

For the first time when I run the docker-compose services, it will build two service containers, one for the postgres db and the other is a python worker. Then it will wait 30 seconds before kicking off the python scripts. There are two scripts db_loader.py and fix_tp_tsa_search_volume.py. After an initial check of the database, if the given table is empty, the db_loader script gets called to populate the table. db_loader extracts the data from the given trendpulse_summary_tsa_v2.csv file and then atomically stores the values in batches of 100,000 rows. 

```
# ./build.sh start
Creating network "hr-take-home-data_db" with the default driver
Building worker
...
..
Creating hr-take-home-data_db_1 ... done
Creating hr-take-home-data_worker_1 ... done
Waiting 30 seconds for db to finish loading...
Extract start...
Extracting: 502204it [00:14, 34779.81it/s]
Extract completed
Load start...
Inserting rows into trendpulse_summary_tsa_v2
Loading: 6it [02:50, 28.35s/it, batch 6/6]
Load completed
Transform start...
Transforming: 100%|████████████████████████████████████████| 499282/499282 [36:12<00:00, 229.80it/s]
Transform completed
Update start...
Updating: 5it [03:42, 44.47s/it, batch 5/5]
Update completed
Goodbye!
```
## Results

Below are some queries made to the postgres db, after the worker service finished its task. Here is a breakdown of the query reults.

| query | result | desc |
| :--- | :---: | :--- |
| SELECT COUNT(*) FROM trendpulse_summary_tsa_v2 | 502204 | Total available rows. |
| SELECT COUNT(*) FROM trendpulse_summary_tsa_v2 WHERE search_volume <> 0 | 497491 | Total rows where search_volume has been updated. |
| SELECT COUNT(*) FROM trendpulse_summary_tsa_v2 WHERE search_volume = 0 | 4713 | Total rows where search_volume is still 0. Some rows have weeks data, some are empty. |
| SELECT COUNT(*) FROM trendpulse_summary_tsa_v2 WHERE search_volume = 0 AND (weeks != '') IS TRUE | 1791 | Total rows where search volume is still 0, despite having weeks data. Basically, the sum of volumes found for these rows are 0, therefore the average is also 0. |

## Technology

| type | choices | reason |
| :--- | :--- | :--- |
| scripting | python, bash, docker-compose | Part of the challenge. |
| database | postgres | Part of the challenge. |
| sql | Peewee ORM | Ease of use. Allows to simplify the complexities of sql. |

