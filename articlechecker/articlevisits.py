#!/usr/bin/env python
# -*- coding: utf-8 -*-

from articleUrls import articleUrls
from articleUrls import ArticleLoadError
import pageanalytics
import csv
import json
from datetime import datetime
import time

def datetime_str_to_object(dt_string:str):
    return datetime.strptime(dt_string, '%d/%m/%Y %H:%M')

def roundtonearestdate(dt:datetime):
    newdt = datetime.date(dt + timedelta(hours=12))
    return newdt

class google():
    def extract_metrics(garesults):
        metrics = {}
        #print('{}'.format(json.dumps(garesults)))
        if garesults.get('rows') != None:
            for i in garesults['rows']:
                for idx, j in enumerate(garesults['columnHeaders']):
                    metrics[j['name']] = i[idx]
        return metrics

    def main(inputcsv = 'D:\\projects\\AppPicker\\reports\\best of lists performance\\ap_article.csv',
             outputcsv = 'D:\\projects\\AppPicker\\reports\\best of lists performance\\article_visits_up.csv',
             start_date_str = '2016-01-01',
             end_date_str = '2016-01-31',
             trustslugs = True):
        """ Generate Google Analytics report for articles listed in the input CSV. If trustslugs = False, then do
            http queries of appPicker for the real URLs instead of constructing URLs from the slugs in the input CSV """
        broker = pageanalytics.Broker()

        # open output file
        with open(outputcsv, 'w', newline='', encoding='utf-8') as outfileh:
            writer = csv.writer(outfileh, delimiter=',', quotechar='"', escapechar='~', doublequote=False, quoting=csv.QUOTE_NONNUMERIC)

            # write out headings
            # these headings depend on the metrics requested in call to broker.get_results, and match values to writer.writerow at end of this loop
            writer.writerow(['article_id', 'published_at', 'page_url', 'users', 'new_users', 'sessions', 'bounces', 'bounce_rate',
                             'avg_session', 'page_views', 'avg_time_on_page', 'avg_page_load_secs', 'sessions_per_user'])

            # open input file
            with open(inputcsv, newline='\n', encoding='utf-8') as inputfileh:
                reader = csv.DictReader(inputfileh, 
                                        fieldnames=('article_id', 'article_type', 'published_at', 'slug'),
                                        delimiter=',', 
                                        quotechar='"')
                i = 1
                for i in range(1):
                    next(reader) # skip header row
                for row in reader:
                    article_id = row['article_id']
                    article_type = row['article_type']
                    published_at = row.get('published_at', 'not provided')
                    slug = row.get('slug', 'blah')
                    if trustslugs:
                        article_url = articleUrls(article_type, article_id, slug)
                    else:
                        try:
                            article_url = articleUrls(article_type, article_id, 'blah').realurl()
                        except ArticleLoadError as e:
                            writer.writerow([article_id, published_at, 'Error: {0}'.format(e.customMessage), 'NULL', 'NULL', 'NULL', 'NULL', 'NULL',
                                             'NULL', 'NULL', 'NULL', 'NULL', 'NULL'])
                            print('Could not open URL: {0}'.format(e.customMessage))
                            continue

                    print(str(article_url).replace('http://www.apppicker.com',''))

                    # get Google Analytics results for period between start and end dates
                    try:
                        garesults = broker.get_results(pagePath=str(article_url).replace('http://www.apppicker.com',''), 
                                                       start_date=start_date_str, end_date=end_date_str,
                                                       metrics='ga:sessions,ga:pageviews,ga:users,ga:newUsers,ga:bounces,ga:avgTimeOnPage,ga:sessionsPerUser,ga:avgPageLoadTime,ga:avgSessionDuration,ga:bounceRate')
                    except googleapiclient.errors.HttpError as e:
                        time.sleep(5)
                        garesults = broker.get_results(pagePath=str(article_url).replace('http://www.apppicker.com',''), 
                                                       start_date=start_date_str, end_date=end_date_str,
                                                       metrics='ga:sessions,ga:pageviews,ga:users,ga:newUsers,ga:bounces,ga:avgTimeOnPage,ga:sessionsPerUser,ga:avgPageLoadTime,ga:avgSessionDuration,ga:bounceRate')
                    metrics = google.extract_metrics(garesults)
    #                print('{}'.format(json.dumps(row)))

                    writer.writerow([article_id, published_at, article_url, metrics.get('ga:users',0), metrics.get('ga:newUsers',0), 
                                     metrics.get('ga:sessions'), metrics.get('ga:bounces',0), metrics.get('ga:bounceRate',0), metrics.get('ga:avgSessionDuration',0), 
                                     metrics.get('ga:pageviews',0), metrics.get('ga:avgTimeOnPage',0), metrics.get('ga:avgPageLoadTime',0), metrics.get('ga:sessionsPerUser',0)])
                    i += 1
                    if i % 10 == 0: print('Record: {}'.format(i))
                    #if i==10:break
            inputfileh.close()
        outfileh.close()

        return None

