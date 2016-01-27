""" Scrape list of applists and create report CSV listing all apps found on the site for each applist.
    This can then be used to check the associated apps stored in our DB.
    
    The input CSV is expected to have columns 'article_id', 'article_type', 'published_at', 'slug'.
    The scraper reports are expected to have columns 'article_id', 'article_url', 'published_at', 'app_id', 'itunes_link'.
   
    In the future, we can create additional scrapers for the other article types, in which case common
    logic will be factored out of this to be shared by all scraper modules (or this module generalised
    to handle other article types). """
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.request
from articleUrls import articleUrls
import csv
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

class ApplistLoadError(Exception):
    def __init__(self, customMessage = 'Could not open specified applist URL'):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

class ApplistDomError(Exception):
    def __init__(self, customMessage = 'Unable to parse unexpected HTML document structure'):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

def getappIDfromiTunesLink(itunes_url):
    #pattern = re.compile(r'^.*/id(?P<id>[0-9]*)\?')
    #pattern = re.compile(r'^.*(?:itunes.apple.com).*/id(?P<id>[0-9]*)')
    pattern = re.compile(r'^.*(?:itunes.apple.com).*(?P<app>/app/)(.*/)*id(?P<id>[0-9]*)')
    matches = pattern.match(itunes_url)
       
    try:
        app_id = matches.group('id')
    except Exception as e:
        app_id = 'Suspect link'

    return app_id

def getappsfromlist(applist_url):
    """ Parse given applist and extract the app IDs thereon
        Returns list of tuples each containing app_id and iTunes link """
    soup = None
    appIds = []

    try:
        c = urllib.request.urlopen(applist_url)
    except http.client.IncompleteRead as e:
        c = e.partial
    except urllib.error.HTTPError as e:
        time.sleep(5)
        raise e
    except:
        raise ApplistLoadError('Could not open ' + applist_url)
    
    soup = BeautifulSoup(c.read(), 'html.parser')

    # build up list of itunes links in the article
    # check new style of applist
    newlist = soup.findAll('div', class_='app-block-landscape ')
    if newlist:
        try:
            itunes_links = [app.find('div', class_='button-application-wrapper').a['href'] for app in newlist]
        except Exception as e:
            raise ApplistDomError('Finding class \'button-application-wrapper\' in ' + applist_url) from e

        if not itunes_links:
            raise ApplistDomError('{} parse error. No <a href> tags found in new style \'button-application-wrapper\''.format(applist_url))
    else:
        # check old style of applist
        try:
            oldlist = soup.find('div', class_='best-of-lists-page__description')
        except Exception as e:
            raise ApplistDomError('Finding class \'best-of-lists-page__description\' in ' + applist_url) from e

        if oldlist:
            itunes_links = [app['href'] for app in oldlist.findAll('a', href=True)]
            if not itunes_links:
                raise ApplistDomError('{} parse error. No <a href> tags found in old style \'best-of-lists-page__description\''.format(applist_url))
        else:
            raise ApplistDomError('{} parse error. Could not find new style list div with class \'app-block-landscape\'" \
            " or old style list div with class \'best-of-lists-page__description\''.format(applist_url))

    for ituneslink in itunes_links:
        appIds.append((getappIDfromiTunesLink(ituneslink),ituneslink))
    return appIds

def main(inputcsv='D:\\projects\\AppPicker\\reports\\best of lists performance\\ap_article.csv', hasheader=True,
         outputcsv = 'D:\\projects\\AppPicker\\reports\\best of lists performance\\applist_scraper_report.csv'):

    APP_LIST_IDX_app_id = 0
    APP_LIST_IDX_itunes_link = 1

    # open output file
    with open(outputcsv, 'w', newline='', encoding='utf-8') as outfileh:
        writer = csv.writer(outfileh, delimiter=',', quotechar='"', escapechar='~', doublequote=False, quoting=csv.QUOTE_NONNUMERIC)

        # write out headings
        # these headings depend on the metrics requested in call to broker.get_results, and match values to writer.writerow at end of this loop
        writer.writerow(['article_id', 'article_url', 'published_at', 'app_id', 'itunes_link'])

        # open input file
        with open(inputcsv, newline='\n', encoding='utf-8') as inputfileh:
            reader = csv.DictReader(inputfileh, 
                                    fieldnames=('article_id', 'article_type', 'published_at', 'slug'),
                                    delimiter=',', 
                                    quotechar='"')
            i = 1
            if hasheader: next(reader) # skip header row

            for row in reader:
                if i % 10 == 0: print('Record: {}'.format(i))
                article_id = row['article_id']
                article_type = row['article_type']
                slug = row['slug']
                article_url = articleUrls(article_type, article_id, slug)
                print(str(article_url))
                published_at = row['published_at']

                # scrape the apps on this article
                #writer.writerow([article_id, article_url, 'APPS'])
                try:
                    apps = getappsfromlist(str(article_url))
                except urllib.error.HTTPError:
                    apps = getappsfromlist(str(article_url)) # try again
                for app in apps:
                    writer.writerow([article_id, article_url, published_at, app[APP_LIST_IDX_app_id], app[APP_LIST_IDX_itunes_link]])
                i += 1
                #if i==50:break
        inputfileh.close()
    outfileh.close()

    return None