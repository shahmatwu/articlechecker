#!/usr/bin/env python
# -*- coding: utf-8 -*-

from googleapiclient.discovery import build
import httplib2
from oauth2client.client import SignedJwtAssertionCredentials

class Broker(object):
    """ Broker object to Google Analytics API """
    #_service = None # class variable shared by ALL INSTANCES
    #_profile = None

    def __init__(self, **kwargs):
        # Define the auth scopes to request.
        scope = ['https://www.googleapis.com/auth/analytics.readonly']
        service_account_email = 'apppicker@coastal-sanctum-114912.iam.gserviceaccount.com'
        key_file_location = 'Stephen First Project-b3fef0b50ccf.p12'

        # Authenticate and construct service.

        self._service = self._get_service('analytics', 'v3', scope, key_file_location, service_account_email)
        self._profile = self._get_first_profile_id(self._service)
        #print('profile id: {}'.format(self._profile))
        return None

    def _get_service(self, api_name, api_version, scope, key_file_location, service_account_email):
        """Get a service that communicates to a Google API.

        Args:
            api_name: The name of the api to connect to.
            api_version: The api version to connect to.
            scope: A list auth scopes to authorize for the application.
            key_file_location: The path to a valid service account p12 key file.
            service_account_email: The service account email address.
    
        Returns:
            A service that is connected to the specified API.
        """
    
        f = open(key_file_location, 'rb')
        key = f.read()
        f.close()
    
        credentials = SignedJwtAssertionCredentials(service_account_email, key, scope=scope)
    
        http = credentials.authorize(httplib2.Http())

        # Build the service object.
        service = build(api_name, api_version, http=http)

        return service

    def _get_first_profile_id(self, service):
        # Use the Analytics service object to get the first profile id.

        # Get a list of all Google Analytics accounts for this user
        accounts = service.management().accounts().list().execute()

        if accounts.get('items'):
            # Get the first Google Analytics account.
            account = accounts.get('items')[0].get('id')

            # Get a list of all the properties for the first account.
            properties = service.management().webproperties().list(
                accountId=account).execute()

            if properties.get('items'):
                # Get the first property_ id.
                property_ = properties.get('items')[0].get('id')

                # Get a list of all views (profiles) for the first property_.
                profiles = service.management().profiles().list(
                    accountId=account,
                    webPropertyId=property_).execute()

                if profiles.get('items'):
                    # return the first view (profile) id.
                    return profiles.get('items')[0].get('id')
        return None

    def get_results(self, pagePath='/', start_date='30daysAgo', end_date='yesterday',
                    metrics='ga:sessions,ga:sessionDuration,ga:pageviews,ga:exits'):
        # Use the Analytics Service Object to query the Core Reporting API
        # for predefined metrics within given day range.
        pagePath = 'ga:pagePath==' + pagePath
        service = self._service
        profile_id = self._profile

        return service.data().ga().get(
            ids='ga:' + profile_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            #dimensions=dimensions,
            #sort='-ga:sessions',
            filters=pagePath).execute()

    def extract_pageviews(self, results):
        """ Simple helper to get pageviews data from total results """
        return results.get('totalsForAllResults').get('ga:pageviews')

def print_results(results):
    # Print data nicely for the user.
    if results:
        print('View (Profile): %s' % results.get('profileInfo').get('profileName'))
        print('Total Page Views: %s' % results.get('totalsForAllResults').get('ga:pageviews'))
    
    else:
        print('No results found')

def main():
    # Define the auth scopes to request.
    scope = ['https://www.googleapis.com/auth/analytics.readonly']
    
    # Use the developer console and replace the values with your
    # service account email and relative location of your key file.
    service_account_email = 'apppicker@coastal-sanctum-114912.iam.gserviceaccount.com'
    key_file_location = 'Stephen First Project-b3fef0b50ccf.p12'
    
    # Authenticate and construct service.
    service = get_service('analytics', 'v3', scope, key_file_location, service_account_email)
    profile = get_first_profile_id(service)
    for i in range(0,3): # check I can make multiple calls after having got the service object
        print_results(get_results(service, profile))
    return get_results(service, profile)

