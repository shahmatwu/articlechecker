""" Read list of app_id's as generated by any of the scraper (e.g. applistscraper.py) modules and perform
    Apple Lookup API query to report on status/quality of each app.
    
    The scraper reports are expected to have columns article_id, article_url, published_at, app_id, itunes_link. """
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json
import time
from datetime import datetime
import urllib3.request
from urllib3 import PoolManager, Retry
import sys

LookupURL = 'https://itunes.apple.com/lookup?id='
#Http = urllib3.PoolManager(cert_reqs='CERT_NONE')
Http = PoolManager(cert_reqs='CERT_NONE', retries=3)
urllib3.disable_warnings()

def callapple(appid):
    """ call Apple Search API """
    url = LookupURL+str(appid)
    try:
        r = Http.request('GET', url)
    except:
        print('Unexpected error calling iTunes API: {}. app_id: {}'.format(sys.exc_info()[0], appid))
        return json.dumps('{"resultCount":0}')

    try:
        appjson=json.loads(r.data.decode('utf-8'))
    except:
        print('Unexpected error loading response into JSON: {}. app_id: {}'.format(sys.exc_info()[0], appid))
        return json.dumps('{"resultCount":0}')

    return appjson

def extractappfields(appjson:json):
    """ parse Apple Lookup API result and return dictionary of fields """
    result = {}
    if 'results' in appjson and len(appjson['results']) >= 1:
        appjson = appjson['results'][0]

    # get type of 'adam' (PHG terminology for iTunes product)
    if 'kind' not in appjson:
        if 'wrapperType' not in appjson:
            adamtype = 'NO APPLE RESULT'
        else:
            adamtype = appjson['wrapperType']
    else:
        adamtype = appjson['kind']

    result['adamtype'] = adamtype
    result['title'] = appjson.get('trackName', 'NULL')
    result['description'] = appjson.get('description', 'NULL')
    result['price'] = appjson.get('price', 'NULL')
    result['primarygenre'] = appjson.get('primaryGenreName', 'NULL')
    result['version'] = appjson.get('version', 'NULL')
    try:
        result['releasedate'] = datetime.strptime(appjson['releaseDate'],'%Y-%m-%dT%H:%M:%SZ')
    except:
        result['releasedate'] = 'NULL'
    result['rating'] = appjson.get('averageUserRating', 'NULL')
    result['ratings'] = appjson.get('userRatingCount', 'NULL')
    result['currrating'] = appjson.get('averageUserRatingForCurrentVersion', 'NULL')
    result['currratings'] = appjson.get('userRatingCountForCurrentVersion', 'NULL')
    result['currentVersionReleaseDate'] = appjson.get('currentVersionReleaseDate', 'NULL')

    return result

def main(inputcsv='D:\\projects\\AppPicker\\reports\\best of lists performance\\applist_scraper_report.csv',
         inputcsvhasheaders=True,
         outputcsv = 'D:\\projects\\AppPicker\\reports\\best of lists performance\\applelookup_report.csv'):
    # open output file
    with open(outputcsv, 'w', newline='', encoding='utf-8', errors='replace') as outfileh:
        writer = csv.writer(outfileh, delimiter=',', quotechar='"', escapechar='~', doublequote=False, quoting=csv.QUOTE_NONNUMERIC)

        # write out headings
        # remember to match values to writer.writerow at end of this loop
        writer.writerow(['app_id', 'adam_type', 'app_name', 'desc_extract', 'article_url', 'article_id', 'published_at', 'position',
                         'price', 'primary_genre', 'version', 'release_date', 'rating', 'ratings', 'curr_rating', 'curr_ratings', 'curr_ver_release_date'])

        # open input file
        with open(inputcsv, mode='rU', newline='\n', encoding='utf-8', errors='replace') as inputfileh:
            reader = csv.DictReader(inputfileh, 
                                    fieldnames=('article_id', 'article_url', 'published_at', 'app_id', 'itunes_link'),
                                    delimiter=',', 
                                    quotechar='"')
            input_rec_no = 1
            position_in_art = 0 # position an app occupies in an article (more relevant to lists; in a review, it will just be position 1)
            curr_article_id = 0

            if inputcsvhasheaders: next(reader) # skip header row
            for row in reader:
                #if input_rec_no % 10 == 0: print('Record: {}'.format(input_rec_no))

                # get input fields
                article_id = row['article_id']
                article_url = row['article_url']
                published_at = row['published_at']
                app_id = row['app_id']
                
                # get other values for output
                # 1. position number of app inside article
                if curr_article_id == article_id:
                    position_in_art += 1
                else:
                    position_in_art = 1
                    curr_article_id = article_id
                    print(('{}'.format(article_url)).encode('ascii', 'ignore').decode('utf-8')) # avoid errors in console if user's CSV does not contain actual URL here but string with unusual characters

                # 2. values from Apples Search/Lookup API

                if app_id and app_id.isdigit():
                    appjson = callapple(app_id)
                    flds = extractappfields(appjson)

                    print(('   {}...'.format(flds['title'][:50])).encode('ascii', 'ignore').decode('utf-8')) # avoids errors when unusual characters are printed to the console

                    # strip new lines and commas from description and shorten to 200 chars
                    desc_extract = flds['description'].replace('\n',' ').replace('\r', ' ').replace(',', ' ')[:200]

                    writer.writerow([app_id, flds['adamtype'], flds['title'], desc_extract,  article_url, article_id, published_at, position_in_art,
                                     flds['price'], flds['primarygenre'], flds['version'], flds['releasedate'], flds['rating'], flds['ratings'], flds['currrating'], flds['currratings'],
                                     flds['currentVersionReleaseDate']])
                else:
                    writer.writerow([app_id, 'Suspect ID. Did not query Apple API', 'NA', 'NA', article_url, article_id, published_at, position_in_art,
                                     'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA'])
                input_rec_no += 1
                #if input_rec_no == 300: break
            inputfileh.close()
        outfileh.close()

        return None

