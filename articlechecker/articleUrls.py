#!/usr/bin/env python
# -*- coding: utf-8 -*-

class ArticleTypeException(Exception):
    def __init__(self, customMessage = 'Unknown article type was specified'):
        self.customMessage = customMessage
    def __str__(self):
        return repr(self.customMessage)

class articleUrls():
    """ construct appPicker URL for an article given its ID and slug """
    def __init__(self, article_type:int, article_id:int, slug:str):
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


