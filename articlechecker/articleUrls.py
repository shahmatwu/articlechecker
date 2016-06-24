#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request
import http
import time

class ArticleTypeException(Exception):
    def __init__(self, customMessage = 'Unknown article type was specified'):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

class ArticleSlugException(Exception):
    def __init__(self, customMessage = "Slug in bad format"):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

class ArticleLoadError(Exception):
    def __init__(self, customMessage = 'Could not open specified article URL'):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

class articleUrls():
    """ construct appPicker URL for an article given its ID and slug """
    def __init__(self, article_type:int, article_id:int, slug:str):
        if " " in slug:
            raise ArticleSlugException('Badly formatted slug: ' + str(slug))

        if article_type in (0, '0'):
            self.value = 'http://www.apppicker.com/news/{}/{}'.format(article_id, slug)
        elif article_type in (1, '1'):
            self.value = 'http://www.apppicker.com/reviews/{}/{}'.format(article_id, slug)
        elif article_type in (2, '2'):
            self.value = 'http://www.apppicker.com/applists/{}/{}'.format(article_id, slug)
        elif article_type in (3, '3'):
            self.value = 'http://www.apppicker.com/interviews/{}/{}'.format(article_id, slug)
        elif article_type in (4, '4'):
            self.value = 'http://www.apppicker.com/developernews/{}/{}'.format(article_id, slug)
        elif article_type in (5, '5'):
            self.value = 'http://www.apppicker.com/appsale/{}/{}'.format(article_id, slug)
        elif article_type in (6, '6'):
            self.value = 'http://www.apppicker.com/appmanscorner/{}/{}'.format(article_id, slug)
        else:
            raise ArticleTypeException('Unknown article type was specified: ' + str(article_type))

    def __str__(self):
        return self.value
    def __eq__(self, y):
        return self.value==y.value

    def realurl(self):
        """ Open a dummy url based on routing pattern and return 'real' url (e.g. after a redirection from the given url) """

        try:
            c = urllib.request.urlopen(str(self))
        except http.client.IncompleteRead as e:
            c = e.partial
        except urllib.error.HTTPError as e:
            time.sleep(5)
            raise ArticleLoadError('Could not open {0}: {1}'.format(str(self), e.reason))
        except:
            raise ArticleLoadError('Could not open ' + str(self))
    
        return c.url
