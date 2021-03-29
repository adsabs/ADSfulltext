import argparse
import json
import os
from glob import glob
from datetime import datetime
from sqlalchemy.orm import sessionmaker, load_only
from sqlalchemy import create_engine, text

# ============================= INITIALIZATION ==================================== #
from adsputils import setup_logging, load_config
proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))
config = load_config(proj_home=proj_home)
logger = setup_logging(__name__, proj_home=proj_home,
                        level=config.get('LOGGING_LEVEL', 'INFO'),
                        attach_stdout=config.get('LOG_STDOUT', False))


def build_input_list():

    xml_bibstems = [os.path.basename(os.path.normpath(x)) for x in glob(os.path.join(config.get('SOURCES_DIR'), '[A-Z]*', ''))]
    pdf_bibstems = [os.path.basename(os.path.normpath(x)) for x in glob(os.path.join(config.get('PDF_SOURCES_DIR'), '[A-Z]*', ''))]

    sources = list(set(xml_bibstems + pdf_bibstems))

    return sources


def bibcode_monitoring(year, bibstems=None):
    if not bibstems:
        # get the list of input bibstems
        bibstems = build_input_list()

    for bibstem in bibstems:
        bibstem_year = str(year) + bibstem

        # for each bibstem, check if any have the fulltext field but are missing the body
        no_body_query = "select bibcode from records where bibcode like '{0}%' and NOT (fulltext::jsonb ? 'body');"
        no_body = _execute_sql(no_body_query, bibstem_year)
        if no_body:
            for n in no_body:
                logger.info('Bibcode %s has extracted fulltext but no body was extracted.', n[0])
        else:
            logger.debug('All bibcodes for bibstem %s for year %s with extracted fulltext data have body text', bibstem, year)

        # for each bibstem, check the length of the extracted body against the average
        stats_query = "select avg(length(fulltext)), stddev_samp(length(fulltext)) from records where bibcode like '{0}%' and (fulltext::jsonb ? 'body');"
        stats = _execute_sql(stats_query, bibstem_year)
        s = stats.first()
        # these are returned as type decimal
        avg = float(s[0])
        stddev = float(s[1])

        body_query = "select bibcode, fulltext from records where bibcode like '{0}%' and (fulltext::jsonb ? 'body');"
        bib_full = _execute_sql(body_query, bibstem_year)

        for bf in bib_full:
            fulltext_json = json.loads(bf[1])
            body = fulltext_json.get('body', None)
            if not body:
                continue
            if len(body) < avg - (config.get('STDDEV_CUTOFF', 1.5) * stddev):
                logger.info('Bibcode %s has extracted fulltext but body is short compared to similar bibcodes', bf[0])


def bibstem_monitoring(bibstems=None):
    if not bibstems:
        # get the list of input bibstems
        bibstems = build_input_list()

    for bibstem in bibstems:
        # for each bibstem, get the average stats on fulltext by year, from 2000 onwards, to compare year-by-year
        # _ is the single character wildcard for postgres
        bibstem_year = '20__' + bibstem
        stats_query = "select avg(length(fulltext)), stddev_samp(length(fulltext)), left(bibcode,4) as year, count(*) as num from records where bibcode like '{0}%' and (fulltext::jsonb ? 'body') group by left(bibcode,4);"
        stats = _execute_sql(stats_query, bibstem_year)
        avg = []
        stddev = []
        years = []
        num = []
        for s in stats:
            avg.append(float(s[0]))
            stddev.append(float(s[1]))
            years.append(s[2])
            num.append(s[3])

        noise = [i**0.5 for i in num]
        for idx, n in enumerate(noise[:-1]):
            # check if too few records have an extracted body, compared to prior year
            if (num[idx] - (config.get('COUNT_ERR', 5) * n)) > num[idx+1]:
                logger.info('For bibstem %s, year %s has an anomalously low fulltext body count. Count: %s (prior year count: %s)', bibstem, years[idx+1], num[idx+1], num[idx])
            # check if the average length of the extracted body is too short, compared to prior year
            if (avg[idx] - (config.get('STDDEV_CUTOFF', 1.5) * stddev[idx])) > avg[idx+1]:
                logger.info('For bibstem %s, year %s has an anomalously low average body length. Avg: %s (prior year average: %s)', bibstem, years[idx+1], avg[idx+1], avg[idx])


def _execute_sql(sql_template, *args):
    """Build sql from template and execute"""
    sql_command = text(sql_template.format(*args))
    logger.debug("Executing SQL: %s", sql_command)
    return connection.execute(sql_command)


if __name__ == '__main__':
    # Runs reporting scripts, outputs results to logs

    engine = create_engine(config.get('SQLALCHEMY_URL'), echo=config.get('SQLALCHEMY_ECHO'))
    connection = engine.connect()
    session = sessionmaker(bind=engine)()

    parser = argparse.ArgumentParser(description='Process user input.')

    parser.add_argument('-y',
                        '--year',
                        dest='year',
                        action='store',
                        default=None,
                        help='For monitoring script, year to run script for, if not current year')

    parser.add_argument('-b',
                        '--bibstem',
                        dest='bibstem',
                        action='store',
                        default=None,
                        help='For monitoring script, comma-separated list bibstem(s) to run script for, if not all bibstems')

    parser.add_argument('-hi',
                        '--historical',
                        dest='historical',
                        action='store_true',
                        default=False,
                        help='For monitoring script, flag to run script for year-by-year historical comparisons')

    args = parser.parse_args()

    if args.bibstem:
        args.bibstem = [x.strip() for x in args.bibstem.split(',')]

    if args.historical:
        logger.info(f"Running historical monitoring for {', '.join(args.bibstem) if args.bibstem else 'all'} bibstems.")
        bibstem_monitoring(args.bibstem)

    else:
        if args.year:
            logger.info(f"Running monitoring for {', '.join(args.bibstem) if args.bibstem else 'all'} bibstems for year {args.year}.")
            bibcode_monitoring(args.year, args.bibstem)
        else:
            today = datetime.today()
            logger.info(f"Running monitoring for {', '.join(args.bibstem) if args.bibstem else 'all'} bibstems for current year.")
            bibcode_monitoring(today.year, args.bibstem)
