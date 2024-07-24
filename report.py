#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import sys

from typing import Iterable

import dotenv

from api import Api
from github import GitHub
from pull_request import PullRequest

EMAIL_FROM    = 'weekly-reports@company.com'
EMAIL_SUBJECT = 'Weekly GitHub PullRequest Report'
EMAIL_TO      = 'weekly-reports@company.com'

GITHUB_AGE   = 'weeks=-1'
GITHUB_OWNER = 'mydor'
GITHUB_REPO  = 'shell-environment'

TIMEDELTA_ARGS = ('days', 'seconds', 'microseconds', 'milliseconds', 'minutes', 'hours', 'weeks')

def send_email(args, report):
    print(f'From: {args.email_from}\n'
          f'To: {args.email_to}\n'
          f'Subject: {args.email_subject}\n\n'
          f'{report}')
    
def fix_date(delta: str | None) -> datetime.datetime:
    time = datetime.datetime.now()

    if delta is None:
        return None
    
    fix = {}
    for pair in delta.strip().split(','):
        k,v = pair.strip().split('=', maxsplit=1)
        if k not in TIMEDELTA_ARGS:
            raise Exception(f"{k} is not a valid modifier; valid options {TIMEDELTA_ARGS}")
        fix.update({k:int(v)})
    
    return time + datetime.timedelta(**fix)

def parse_args():
    parser = argparse.ArgumentParser(
        prog = os.path.basename(__file__),
        description = "Report state of pull requests"
    )
    parser.add_argument('owner', type=str, nargs='?', default=os.environ.get('OWNER', GITHUB_OWNER))
    parser.add_argument('repo', type=str, nargs='?', default=os.environ.get('REPO', GITHUB_REPO))

    parser.add_argument('--api_token', type=str, nargs='?', help='API access token', default=os.environ.get('API_TOKEN'))
    parser.add_argument('--start-date', type=str, nargs='?', default=GITHUB_AGE)
    parser.add_argument('--end-date', type=str, nargs='?', default=None)
    parser.add_argument('--debug', action=argparse.BooleanOptionalAction, default=False)

    parser.add_argument('--email-from', type=str, nargs='?', default=os.environ.get('EMAIL_FROM', EMAIL_FROM))
    parser.add_argument('--email-to', type=str, nargs='?', default=os.environ.get('EMAIL_TO', EMAIL_TO))
    parser.add_argument('--email-subject', type=str, nargs='?', default=os.environ.get('EMAIL_SUBJECT', EMAIL_SUBJECT))

    args = parser.parse_args()

    args.start_date = fix_date(args.start_date)
    args.end_date = fix_date(args.end_date)

    # Not necessary with current setup, but might not have hard set 
    # fallback values in a prod setup
    if args.owner is None or args.repo is None:
        parser.print_help()
        sys.exit(1)

    return args

def build_report(pull_requests: list[PullRequest]) -> str:
    report = ''

    def column(text: str, sep: str = ' ', alignment: list[str] | None = None, headers: bool = False, indent: int = 0) -> str:
        col_size = []
        _indent = ' '*indent

        new_table = ''

        def fmt_line(columns: list[str]):
            line = ''

            for idx, col in enumerate(columns):
                if line != '':
                    line += '  '

                try:
                    align = alignment[idx]
                except IndexError:
                    align = ''
                except TypeError:
                    align = ''
                
                fmt = f'{align}{col_size[idx]}s'
                line += f'{col:{fmt}}'

            if line == '':
                return line
            
            return f'{_indent}{line}\n'

        lines = text.strip().split('\n') # Temp storage

        for line in lines:
            for idx, col in enumerate(line.split(sep)):
                col_len = len(col)
                if len(col_size) <= idx:
                    col_size.append(col_len)
                else:
                    col_size[idx] = max(col_size[idx], col_len)

        for lineno, line in enumerate(lines):
            new_table += fmt_line(line.split(sep))
            if headers and lineno < 1:
                new_table += fmt_line([ '-'*col_size[x] for x,_ in enumerate(line.split(sep))])

        return new_table

    def format(title: str, headers: list[str], attrs: list[str], pull_requests: Iterable[PullRequest]) -> str:
        INDENT = 3
        have_headers = False

        section = f'{title}\n{'-' * len(title)}\n'
        alignment = ('>', '<', '', '', '')
        table = ''
        if headers:
            have_headers = True
            table += '\0'.join(headers) + '\n'

        lines = 0
        for pr in pull_requests:
            table += '\0'.join((getattr(pr, attr, f'ERROR: {attr}') for attr in attrs)) + '\n'
            lines += 1
        
        section += column(table, sep='\0', alignment=alignment, headers=have_headers, indent=INDENT)

        if lines == 0:
            section += ' '*INDENT + '<<< No Pull Requests found >>>\n'

        return section + '\n'

    open_headers = ('PR', 'Title', 'Created', 'Updated', 'Age')
    open_attrs = ('number', 'short_title', 'created', 'updated', 'age')
    open_prs   = filter(lambda pr: not pr.isClosed(), pull_requests)

    report += format('Open Pull Requests', headers=open_headers, attrs=open_attrs, pull_requests=open_prs)

    merged_headers = ('PR', 'Title', 'Created', 'Merged', 'Age')
    merged_attrs = ('number', 'short_title', 'created', 'merged', 'age')
    merged_prs = filter(lambda pr: pr.isMerged(), pull_requests)

    report += format('Merged Pull Requests', headers=merged_headers, attrs=merged_attrs, pull_requests=merged_prs)

    closed_headers = ('PR', 'Title', 'Created', 'Closed', 'Age')
    closed_attrs = ('number', 'short_title', 'created', 'closed', 'age')
    closed_prs = filter(lambda pr: pr.isClosed(), pull_requests)

    report += format('Closed Pull Requests', headers=closed_headers, attrs=closed_attrs, pull_requests=closed_prs)

    return report


def main():
    args = parse_args()

    api = Api(token=args.api_token, debug=True)
    github = GitHub(api=api)
    prs = github.get_pull_requests(owner=args.owner, repo=args.repo, oldest_date=args.start_date, latest_date=args.end_date, debug=args.debug)

    # print(json.dumps(dict(os.environ), sort_keys=True, indent=4))

    report = build_report(pull_requests=prs)
    send_email(args, report)


if __name__ == '__main__':
    main()
