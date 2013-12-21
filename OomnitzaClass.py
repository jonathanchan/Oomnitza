#!/usr/bin/python

import json
import random
import requests
import string


class Oomnitza:
  """Oomnitza class that provides access to most of the Oomnitza user and
  asset apis.

  username, password, and company name are required to use Oomnitza's apis.
  """
  def __init__(self, username, password, company):
    self._username = username
    self._password = password
    self._url = 'https://' + company + '.oomnitza.com'
    self._headers = {'content-type':'application/x-www-form-urlencoded'}
    self._session = None
    self._token = None

  def connect(self):
    """Establishes a connection to Oomnitza"""

    self._session = requests.session()
    resp = self._session.post(self._url + '/api/request_token?login=' \
                                    + self._username + '&password=' + \
                                    self._password, headers=self._headers)

    if resp.status_code == 200:
      self._token = resp.json()['token']
      return True
    else:
      print 'Could not connect. Error code: ' + str(resp.status_code)
      return False


  def disconnect(self):
    if self._session:
      self._session = None
      self._token = None

  def __is_connected(self):
    return bool(self._token)

  def search_user(self, username):
    """Search user by username and returns a dict"""

    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    url = self._url + '/api/people/individuals/info?access_token=' + \
           self._token + "&id=" + username

    result = self._session.post(url, headers=self._headers)

    if result.status_code != 200:
      print 'Could not perform search. Error code: ' + str(resp.status_code)
      return False

    if result.json()['errors']:
      print 'Error searching ' + username + ': ' + \
            str(result.json()['errors'][0])
      return False

    user_data = result.json()['info']

    return(self.__get_user_info(user_data))

  def __get_user_info(self, user):
    # Return a dict of values of each attribute from Oomnitza's feed
    attr = ["USER", "FIRST_NAME", "LAST_NAME", "POSITION", "ADDRESS", "EMAIL", \
            "DESK_NUMBER", "IS_ACTIVE"]

    user_info = {}

    for id in attr:
      for field in user:
        if field['ID'] == id:
          user_info[id] = field['VALUE']
          break

    return user_info


  def update_user(self, user):
    """
    Updates Oomnitza user data with user data from AD.
    This assumes sAMAccountName is the Oomnitza username.

    User is a dict with at least the following keys:
      str('sAMAccountName')
      str('givenName')
      str('sn')
      str('l') - location
      bool('status')

    Returns bool.
    """

    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    passwd = self.__make_password()

    """
    TODO: Read status as a string or int instead of bool along with account
          expiration. Create a function that determines if the account is
          enabled or disabled.

          Don't hard code PERMISSIONS_ID and POSITION.
    """

    payload = {'output[USER]': user['sAMAccountName'], \
               'output[PASSWORD]': passwd, \
               'output[FIRST_NAME]': user['givenName'], \
               'output[LAST_NAME]': user['sn'], \
               'output[EMAIL]': user['mail'], \
               'output[HOURLY_WAGE]': '0', \
               'output[PERMISSIONS_ID]': '39', \
               'output[POSITION]': 'Employee', \
               'output[PHONE]': '', \
               'output[ADDRESS]': user['l'], \
               'output[DESK_NUMBER]': '', \
               'output[IS_ACTIVE]': str(int(user['status']))}

    url = self._url + '/api/people/individuals/edit?access_token=' \
          + self._token + '&id=' + user['sAMAccountName']

    result = self._session.post(url, headers=self._headers, data=payload)

    if result.status_code != 200:
      print 'Error updating ' + user['sAMAccountName'] + ' : status_code:' + \
            result.status_code
      return False

    if result.json()['errors']:
      print 'Error updating ' + user['sAMAccountName'] + ' : ' + \
            str(result.json()['errors'])
      return False

    return True

  def add_user(self, user):
    """Create an Oomnitza user account
    User is a dict with at least the following keys:
      str(sAMAccountName)
      str(givenName)
      str(sn)
      str(l) - location
      bool(status)

    Returns bool.
    """

    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    passwd = self._make_password()

    """
    TODO: Read status as a string or int instead of bool along with account
          expiration. Create a function that determines if the account is
          enabled or disabled.

          Don't hard code PERMISSIONS_ID and POSITION.
    """
    payload = {'output[USER]': user['sAMAccountName'], \
               'output[PASSWORD]': passwd, \
               'output[FIRST_NAME]': user['givenName'], \
               'output[LAST_NAME]': user['sn'], \
               'output[EMAIL]': user['mail'], \
               'output[HOURLY_WAGE]': '0', \
               'output[PERMISSIONS_ID]': '39', \
               'output[POSITION]': 'Employee', \
               'output[PHONE]': '', \
               'output[ADDRESS]': user['l'], \
               'output[DESK_NUMBER]': '', \
               'output[IS_ACTIVE]': str(int(user['status']))}

    url = self._url + '/api/people/individuals/add?access_token=' \
          + self._token

    result = self._session.post(url, headers=self._headers, data=payload)

    if result.status_code != 200:
      print 'Error adding ' + user['sAMAccountName'] + ' : status_code:' + \
            str(result.status_code)
      return False

    if result.json()['errors']:
      print 'Error adding ' + user['sAMAccountName'] + ' : ' + \
            str(result.json()['errors'])
      return False

    return True

  def __make_password():
    """random password... people should be using sso to login
    """
    return ''.join(random.choice(string.lowercase + string.digits + \
                               string.uppercase) for i in range(20))


  def assets_print_all_fields(self):
    """Prettified json of all asset fields are printed to the screen.
    Returns bool.
    """
    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    url = self._url + '/api/assets/assets/empty?access_token=' + \
          self._token

    result = self._session.post(url, headers=self._headers)

    if result.status_code != 200:
      print 'Error querying for asset fields. status_code: ' + \
            str(result.status_code)
      return False

    if result.json()['errors']:
      print 'Error getting asset fields. ' + str(result.json()['errors'])
      return False

    print json.dumps(result.json(), sort_keys=True, indent=2)
    return True


  def assets_search(self, search_fields, limit=0, begin=0):
    """Query the asset database and returns a list of dict.

    seach_fields is a list of lists as follows:\n
       [['field_id1', 'value1', 'EQ'],
        ['field_id2', 'value2', 'LT'],
        ['field_id3', 'value3', 'GT']
       ]

    limit is integer limit of max results. Oomnitza default is 10.

    begin is the integer of result number to start with (default = 0)

    >>>someList = [['field1', 'first_name', 'EQ'],
                   ['field2', 'last_name', 'EQ']]
    >>>assets_search(someList)
          <list of dictionary is returned>
    """

    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    search_url = ''

    for fields in search_fields:
      if len(fields) != 3:
        return "Search_field needs to have three values."

      field_id = fields[0]
      value = fields[1]
      cmp = fields[2].upper()

      if cmp not in ['EQ', 'GT', 'LT']:
        return "Third value needs to be 'eq', 'gt', or 'lt'"

      search_url += '&filter[' + field_id + '][type]=' + cmp + '&filter[' + \
                    field_id + '][value]=' + value

    if limit > 0:
      search_url += '&limit=' + str(limit)

    if begin > 0:
      search_url += '&begin=' + str(begin)

    url = self._url + '/api/assets/assets/blocks?access_token=' + \
          self._token + search_url

    result = self._session.post(url, headers=self._headers)

    if result.json()['errors']:
      return result.json()['errors']

    if result.json()['has_next']:
      output = result.json()['rows']
      return output + \
             self.assets_search(search_fields, limit, begin + len(output))
    else:
      return result.json()['rows']


  def asset_info(self, id):
    """Get info for a specific asset

    id is the asset id number
    """
    if not self.__is_connected():
      return 'Not connected to Oomnitza.'

    if not isinstance(int(id), int):
      return ["id is not an int."]

    url = self._url + '/api/assets/assets/info?access_token=' + \
          self._token + '&id=' + str(id)

    result = self._session.post(url, headers=self._headers)

    if result.json()['errors']:
      return result.json()['errors']

    return result.json()['info']