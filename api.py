import copy
import json
import os
import requests
import time
import urllib.parse

from collections.abc import Callable
from functools import wraps

API_URL = 'https://api.github.com'

# Note: GitHub returns "403 Forbidden" for rate limit responses,
# instead of the correct "429 Too Many Requests".
# As they publish what the limits are, I just wrap the request
# calls with the rate_limit decorator to pre-throttle the calls
# and prevent the 403.
def rate_limit(func):
    """Decorator to handle catching, and retrying, rate limit responses

    """
    @wraps(func)
    def wrapper(*pargs, **kwargs):
        while True:
            response = func(*pargs, **kwargs)

            # Catch rate limit and repeat request
            if response.status_code in (403, 429) and response.text:
                msg = response.json()


                if msg.get('message', '').lower().startswith('api rate limit'):
                    rate_limit_sleep(response.headers)
                    # sleep_time = 60 # default rate limit wait

                    
                    # sleep_time = int(response.headers['X-RateLimit-Reset']) - time.time()
                    # print(f'- ERROR: Rate Limit exceeded, sleeping {sleep_time}, then retrying')
                    # time.sleep(sleep_time)
                    continue

            # Not rate limited, break the loop and return
            break

        return response
    return wrapper

def rate_limit_sleep(headers):
    sleep_time = 60 # default rate limit wait

    sleep_time = int(headers.get('Retry-After', sleep_time))

    xrlr = headers.get('X-RateLimit-Reset', None)
    if xrlr is not None:
        sleep_time = int(xrlr) - int(time.time())

    print(f'- ERROR: Rate Limit exceeded, sleeping {sleep_time} seconds, then retrying')
    time.sleep(sleep_time)


class NoApiToken(Exception):
    pass


class NotImplemented(Exception):
    pass


class Api(object):
    """Initialize a new Api handler object

    Args:
        api_url (str, required): Root url for API calls, I.E. https://api.domain.com/common/path
                                    Defaults to API_URL constant variable
        token (str, required): API Authorization token
        user_agent (str, optional): Any custom UserAgent header to send on requests
        debug (bool, optional): Enable some debug output

    Returns:
        None

    Raises:
        NoApiToken: Token not given
    """

    def __init__(
            self, 
            api_url: str = API_URL, 
            token: str = None, 
            user_agent: str = None,
            debug: bool = False):
        
        if token is None or token == "":
            raise NoApiToken("Token cannot be empty.")
        
        headers = requests.utils.default_headers()
        if user_agent is None:
            user_agent = headers.get('User-Agent')

        else:
            headers.update({'User-Agent': user_agent})
        
        headers.update({'Accept': 'application/vnd.github+json'})
        headers.update({'Authorization': f'Bearer: {token}'})

        self.debug = debug
        self.__api_url = api_url
        self.__api_token = token
        self.__headers = headers

    def __mk_url(self, path):
        """Construct the full API call URL
        
        Args:
            path (str, required): relative path of the API call
            
        Returns:
            str: Full path of API call
        """
        return urllib.parse.urljoin(self.__api_url, path)
    
    @staticmethod
    def __mk_params(params):
        """Turn k:v param pairs into k=v[&k=v] string for debug
        
        Args:
            params (dict): Dictionary of paramerts to send on request
            
        Returns:
            str: k=v[&k=v] string of parameters
        """
        args = ''

        for k,v in params.items():
            sep = '?' if args else '&'
            args = f'{args}{sep}{k}={v}'
            
        return args

    def __send(
            self, 
            verb: Callable,
            path: str,
            data: dict = None, 
            version: str = None, 
            debug: bool = None, 
            params: dict = None, 
            *pargs, **kwargs):
        """Generic wrapper to send the query to the website, and get it's response
        
        Args:
            verb (requests.[get|put|post|...], requred): HTTP call to make
            path (str, required): Relative path of API call
            data (dict, optional): Data to send on request
            version (str, optional): Api version to request
            debug (bool, optional): Enable debug output

        Returns:
            requests.Response
        """
        if debug is None:
            debug = self.debug

        url = self.__mk_url(path)
        fname = verb.__name__.upper()
        args = self.__mk_params(params)
        headers = copy.deepcopy(self.__headers)

        if version is not None:
            headers.update({'X-GitHub-Api-Version': version})

        if debug:
            print(f'{fname} {"".join((url, args))}')
        
        return verb(url, data=data, headers=headers, params=params)

    @rate_limit
    def get(self, *pargs, **kwargs):
        """Send a get request, see __send()

        Args:
            verb (requests.[get|put|post|...], requred): HTTP call to make
            path (str, required): Relative path of API call
            data (dict, optional): Data to send on request
            version (str, optional): Api version to request
            debug (bool, optional): Enable debug output

        Returns:
            requests.Response
        """
        return self.__send(requests.get, *pargs, **kwargs)
    
    def put(self, *pargs, **kwargs):
        """Send a PUT request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented
    
    def post(self, *pargs, **kwargs):
        """Send a POST request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented
    
    def delete(self, *pargs, **kwargs):
        """Send a DELETE request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented
    
    def head(self, *pargs, **kwargs):
        """Send a HEAD request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented

    def patch(self, *pargs, **kwargs):
        """Send a PATCH request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented

    def options(self, *pargs, **kwargs):
        """Send a OPTIONS request, not implemented
        
        Raises:
            NotImplemented
        """
        raise NotImplemented
    
    @staticmethod
    def success(
            response: requests.Response,
            status_code=200,
            output=True):
        try:
            if response.status_code != status_code:
                if response.text and output:
                    print(json.dumps(response.json(), sort_keys=True, indent=4))
                return False
            return True
        except AttributeError:
            return False


def main():
    import dotenv

    api = Api(token=os.environ['API_TOKEN'], debug=True)

    response = api.get(path='repos/kubernetes/kubernetes/pulls')
    # response = api.get(path='repos/mydor/shell-environment/pulls')
    print(json.dumps(response.json(), sort_keys=True, indent=4))

if __name__ == "__main__":
    main()