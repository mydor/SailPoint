"""GitHub Api module to handle all the GitHub logic"""
import datetime
import os
import sys

import api

from pull_request import PullRequest

class GetPullRequestsError(Exception):
    """Error during get_pull_requests"""
    pass


class GitHub(object):
    """Initialize a new GitHub Api object
    
    Args:
        api (Api, required): Api object
        
    Returns:
        None
    """
    def __init__(
            self,
            api: api.Api) -> None:
        self.__api = api

    def __success(
            self, 
            debug: bool = False):
        """ Check if the query was successful by calling the api object's success method
        
        Args:
            debug (bool, optional): Debug output on error
        
        Returns:
            bool: True on success, False on failure
        """
        return self.__api.success(self.__response, output=debug)
   
    @staticmethod
    def __date_filter(
            pull_requests: list[PullRequest], 
            oldest_date: datetime.datetime, 
            latest_date: datetime.datetime) -> list[dict]:
        """Filter requests to a date range

        Args:
            pull_requests (list[dict], required): List of pull_requests dict's
            oldest_date (datetime.datetime | None, optional): Oldest date to accept
            latest_date (datetime.datetime | None, optional): Newest date to accept

        Returns:
            list[dict]: List of pull_request dicts that match the date range
        """
        def filter_func(pull_request: PullRequest) -> bool:
            """filter function for the filter() builtin
            
            Args:
                pull_request (dict, required): Pull request to compare
                
            Returns:
                bool: True if matched date range, False if not
            """
            # short circuit checks if we're not looking to limit
            if oldest_date is None and latest_date is None:
                return True
            
            if oldest_date is not None and pull_request.updated < oldest_date.isoformat():
                return False
            
            if latest_date is not None and pull_request.updated > latest_date.isoformat():
                return False
            
            return True
        
        return list(filter(filter_func, pull_requests))

    def get_pull_requests(
            self,
            owner: str,
            repo: str,
            oldest_date: datetime.datetime | None = None,
            latest_date: datetime.datetime | None = None,
            per_page: int = 30, 
            params: dict | None = None, 
            debug: bool = False, 
            *pargs, **kwargs) -> list[PullRequest]:
        """Get all pull requests for GitHub {owner}/{repo}, optionally matching a date range
        
        Args:
            owner (str, required): GitHub owner to query
            repo (str, requred): GitHub repo to query
            oldest_date (datetime.datetime | None, optional): Oldest pull request to retrieve
            newest_date (datetime.datetime | None, optional): Newest pull request to retrieve
            per_page (int, optional): Requests per query to retrieve
            params (dict | None, optional): Params to send to send on query
            debug (bool, optional): Enable some debug output
            
        Returns:
            list[PullRequest]: List of pull_request objects

        Raises:
            GetPulllRequestError
        """
        if params is None:
            params = {}

        # Construct API Query URL
        path = '/'.join(('repos', owner, repo, 'pulls'))
        params['page'] = 0 # Start on first page
        params['per_page'] = per_page # Set number of PRs to get at a time

        # We want to get ALL PRs, sorted by descending Update time
        params.update({
            'state': 'all',
            'sort': 'updated',
            'direction': 'desc'
        })

        pull_reqs: list[PullRequest] = []
        while True:
            params['page'] += 1
            if debug:
                print(f'page: {params['page']} @ {params['per_page']} per page', file=sys.stderr)

            self.__response = self.__api.get(path=path, debug=debug, params=params, *pargs, **kwargs)
            if not self.__success(debug=True):
                raise GetPullRequestsError

            # PRs retrieved this query iteration            
            partial_pull_reqs: list[PullRequest] = list(map(lambda x: PullRequest(x), self.__response.json()))
            count = len(partial_pull_reqs)

            # If we have something, filter it for date, and store it
            if count > 0:
                pull_reqs += self.__date_filter(partial_pull_reqs, oldest_date, latest_date)

            # Stop checking for more, if
            # 1) we got fewer results that our page limit (EOR)
            # 2) the last record's update_at time is older than our
            #    requested oldest_date
            if count < per_page or (
                    oldest_date is not None and
                    partial_pull_reqs[-1].updated < oldest_date.isoformat()
                    ):
                break

        return pull_reqs
    
    @staticmethod
    def filter_state(prs: list[PullRequest], state: str):
        return list(filter(lambda qr: qr.state == state, prs))
    

def main():
    import json
    import dotenv

    _api = api.Api(token=os.environ['API_TOKEN'], debug=True)
    github = GitHub(_api)

    # start = datetime.datetime.now() + datetime.timedelta(days=-7)
    # end = None
    # prs = github.get_pull_requests('kubernetes', 'kubernetes', debug=True, oldest_date=start, latest_date=end)
    start = datetime.datetime.now() + datetime.timedelta(hours=-12)
    prs = github.get_pull_requests('mydor', 'shell-environment', begin_date=start, debug=True)
    print(len(prs))
    open = github.filter_state(prs, 'open')
    closed = github.filter_state(prs, 'closed')
    
    print(f'open: {len(open)}')
    print(f'closed: {len(closed)}')
    print(json.dumps([x.raw for x in prs], sort_keys=True, indent=4))
    # for pr in prs:
    #     print(json.dumps(pr, sort_keys=True, indent=4))

    # pass

if __name__ == '__main__':
    main()
