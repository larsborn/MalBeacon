#!/usr/bin/env python3
import argparse
import logging
import typing
import json
import os
import re
import datetime

import requests
import requests.adapters

__version__ = '1.0.0'


class FixedTimeoutAdapter(requests.adapters.HTTPAdapter):
    def send(self, *pargs, **kwargs):
        if kwargs['timeout'] is None:
            kwargs['timeout'] = 5
        return super(FixedTimeoutAdapter, self).send(*pargs, **kwargs)


class DateTimeFactory:
    @staticmethod
    def to_str(dt: datetime) -> str:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def to_date_str(dt: datetime) -> str:
        return dt.strftime('%Y-%m-%d')

    @staticmethod
    def to_time_str(dt: datetime) -> str:
        return dt.strftime('%H:%M:%S')

    @staticmethod
    def from_str(s: str) -> datetime:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


class MalBeaconException(Exception):
    pass


def print_histogram(data, target_width=80 - 10):
    factor = float(target_width) / float(max(data.values()))
    for key in sorted(data.keys()):
        if data[key]:
            width = round(data[key] * factor)
            bar = 'o' * width
            print(F'{key:2}: {bar} ({data[key]})')


class MalBeaconApiException(MalBeaconException):
    def __init__(self, message, url):
        super().__init__(F'{message} while requesting "{url}"')


class MalBeaconUnauthorizedException(MalBeaconApiException):
    def __init__(self, url):
        super().__init__('Unauthorized', url)


class MalBeaconRequestExceedQuotaException(MalBeaconApiException):
    def __init__(self, url):
        super().__init__('RequestExceedQuota', url)


class MalBeaconPrivilegedAccountRequiredException(MalBeaconApiException):
    def __init__(self, url):
        super().__init__('PrivilegedAccountRequired', url)


class MalBeaconBadRequestException(MalBeaconApiException):
    def __init__(self, url):
        super().__init__('BadRequest', url)


class MalBeaconParsingException(MalBeaconException):
    pass


class CookieId:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class CountryCode:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return DateTimeFactory.to_str(o)
        elif isinstance(o, C2Beacon):
            return {
                'timestamp': o.timestamp,
                'actor_asn_organization': o.actor_asn_organization,
                'actor_city': o.actor_city,
                'actor_country_code': o.actor_country_code,
                'actor_hostname': o.actor_hostname,
                'actor_ip': o.actor_ip,
                'actor_location': o.actor_location,
                'actor_region': o.actor_region,
                'actor_timezone': o.actor_timezone,
                'c2': o.c2,
                'c2_asn_org': o.c2_asn_org,
                'c2_city': o.c2_city,
                'c2_country_code': o.c2_country_code,
                'c2_domain': o.c2_domain,
                'c2_domain_resolved': o.c2_domain_resolved,
                'c2_hostname': o.c2_hostname,
                'c2_location': o.c2_location,
                'c2_region': o.c2_region,
                'c2_timezone': o.c2_timezone,
                'cookie_id': o.cookie_id,
                'user_agent': o.user_agent,
                'tags': o.tags,
            }
        elif isinstance(o, GeoLocation):
            return {'latitude': o.latitude, 'longitude': o.longitude}
        elif isinstance(o, CookieId):
            return o.value
        elif isinstance(o, Tag):
            return o.value
        else:
            super().default(o)


class GeoLocation:
    def __init__(self, latitude: int, longitude: int):
        self.latitude = latitude
        self.longitude = longitude

    @staticmethod
    def from_string(s):
        # regex that matches on geo-location with 4 digits precision
        m = re.match(r'^(-?\d+(?:\.\d{4})?),\s*(-?\d+(?:\.\d{4})?)$', s)
        if not m:
            raise MalBeaconParsingException(F'Invalid GeoLocation: {s}')
        return GeoLocation(
            int(m.group(1).replace('.', ''), 10),
            int(m.group(2).replace('.', ''), 10)
        )

    def __str__(self):
        return F'{float(self.latitude) / 4:.4f},{float(self.longitude) / 4:.4f}'


class Timezone:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Tag:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class C2Beacon:
    def __init__(self, timestamp: datetime, actor_asn_organization: str, actor_city: str,
                 actor_country_code: CountryCode, actor_hostname: str, actor_ip: str, actor_location: GeoLocation,
                 actor_region: str, actor_timezone: Timezone, c2: str, c2_asn_org: str, c2_city: str,
                 c2_country_code: CountryCode, c2_domain: str, c2_domain_resolved: str, c2_hostname: str,
                 c2_location: GeoLocation, c2_region: str, c2_timezone: Timezone, cookie_id: CookieId, user_agent: str,
                 tags: typing.List[Tag]):
        self.timestamp = timestamp
        self.actor_asn_organization = actor_asn_organization
        self.actor_city = actor_city
        self.actor_country_code = actor_country_code
        self.actor_hostname = actor_hostname
        self.actor_ip = actor_ip
        self.actor_location = actor_location
        self.actor_region = actor_region
        self.actor_timezone = actor_timezone
        self.c2 = c2
        self.c2_asn_org = c2_asn_org
        self.c2_city = c2_city
        self.c2_country_code = c2_country_code
        self.c2_domain = c2_domain
        self.c2_domain_resolved = c2_domain_resolved
        self.c2_hostname = c2_hostname
        self.c2_location = c2_location
        self.c2_region = c2_region
        self.c2_timezone = c2_timezone
        self.cookie_id = cookie_id
        self.user_agent = user_agent
        self.tags = tags

    @staticmethod
    def from_response_line(response):
        return C2Beacon(
            DateTimeFactory.from_str(response["tstamp"]),
            None if response["actorasnorg"] == 'NA' else response["actorasnorg"],
            None if response["actorcity"] == 'NA' else response["actorcity"],
            None if response["actorcountrycode"] == 'NA' else response["actorcountrycode"],
            None if response["actorhostname"] == 'NA' else response["actorhostname"],
            None if response["actorip"] == 'NA' else response["actorip"],
            None if response["actorloc"] == 'NA' else GeoLocation.from_string(response["actorloc"]),
            None if response["actorregion"] == 'NA' else response["actorregion"],
            None if response["actortimezone"] == 'NA' else response["actortimezone"],
            None if response["c2"] == 'NA' else response["c2"],
            None if response["c2asnorg"] == 'NA' else response["c2asnorg"],
            None if response["c2city"] == 'NA' else response["c2city"],
            None if response["c2countrycode"] == 'NA' else response["c2countrycode"],
            None if response["c2domain"] == 'NA' else response["c2domain"],
            None if response["c2domainresolved"] == 'NA' else response["c2domainresolved"],
            None if response["c2hostname"] == 'NA' else response["c2hostname"],
            GeoLocation.from_string(response["c2loc"]),
            None if response["c2region"] == 'NA' else response["c2region"],
            None if response["c2timezone"] == 'NA' else response["c2timezone"],
            CookieId(response["cookie_id"]),
            None if response["useragent"] == 'NA' else response["useragent"],
            [] if response["tags"] == 'NA' else [Tag(response["tags"])],
        )

    def __repr__(self):
        return F'<{self.__class__.__name__} {DateTimeFactory.to_str(self.timestamp)} ' \
               F'{self.actor_ip} {self.c2} {self.cookie_id} {self.user_agent}' \
               F'>'


class MalBeaconClient:
    def __init__(self, api_key: str, user_agent: str, base_url: str):
        self.base_url = base_url

        self.session = requests.session()
        self.session.mount('https://', FixedTimeoutAdapter())
        self.session.mount('http://', FixedTimeoutAdapter())
        self.session.headers = {
            'X-Api-Key': api_key,
            'User-Agent': user_agent,
        }

    def _get(self, url):
        response = self.session.get(url)
        if response.status_code == 400:
            if response.json()['message'] == 'ERROR: No Results':
                return []
            raise MalBeaconApiException(F'Generic API Exception: {response.content}', url)
        if response.status_code == 401:
            if response.json()['message'] == 'ERROR: Unauthorized':
                raise MalBeaconUnauthorizedException(url)
            raise MalBeaconApiException(F'Generic API Exception: {response.content}', url)
        if response.status_code != 200:
            raise MalBeaconApiException(F'Generic API Exception: {response.content}', url)

        return response.json()

    def get_c2_by_cookies_id(self, cookie_id: CookieId) -> typing.List[C2Beacon]:
        for line in self._get(self.base_url + F'/c2/cookie_id/{cookie_id}'):
            yield C2Beacon.from_response_line(line)


class ConsoleHandler(logging.Handler):
    def emit(self, record):
        print('[%s] %s' % (record.levelname, record.msg))


def main():
    import platform

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    cookie_id_parser = subparsers.add_parser('cookie', help='List C2 beacons of specified cookie ID.')
    cookie_id_parser.add_argument('cookie_id')

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--api-key', default=os.environ.get('MALBEACON_API_KEY'))
    parser.add_argument('--base-url', default='https://api.malbeacon.com/v1')
    parser.add_argument(
        '--user-agent',
        default=F'MalBeaconClient/{__version__} (python-requests {requests.__version__}) '
                F'{platform.system()} ({platform.release()})'
    )
    args = parser.parse_args()

    logger = logging.getLogger('MalBeacon')
    logger.handlers.append(ConsoleHandler())
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    if args.debug:
        import http.client as http_client
        http_client.HTTPConnection.debuglevel = 1

    logger.debug(F'Using User-Agent string: {args.user_agent}')
    client = MalBeaconClient(args.api_key, args.user_agent, args.base_url)
    try:
        if args.command == 'cookie':
            from terminaltables import GithubFlavoredMarkdownTable as TerminalTable

            table_data = [['Timestamp', 'IP', 'URL']]
            user_agents = []
            reduced_data = False
            activity_timestamps = []
            for c2_beacon in client.get_c2_by_cookies_id(CookieId(args.cookie_id)):
                if args.json:
                    print(json.dumps(c2_beacon, cls=CustomJsonEncoder))
                else:
                    activity_timestamps.append(c2_beacon.timestamp)
                    if c2_beacon.user_agent not in user_agents:
                        user_agents.append(c2_beacon.user_agent)
                    if table_data \
                            and table_data[len(table_data) - 1][1] == c2_beacon.actor_ip \
                            and table_data[len(table_data) - 1][2] == c2_beacon.c2:
                        reduced_data = True
                        continue

                    table_data.append([
                        DateTimeFactory.to_date_str(c2_beacon.timestamp),
                        c2_beacon.actor_ip,
                        c2_beacon.c2
                    ])
            if not args.json:
                print(TerminalTable(table_data=table_data).table)
                if user_agents:
                    print('')
                    print('User-Agents:')
                    for user_agent in user_agents:
                        print(F'    {user_agent}')
                    if len(user_agents) > 5:
                        print('    ...')
                        reduced_data = True
                    print('')
                if activity_timestamps:
                    print(F'First Active: {DateTimeFactory.to_str(min(activity_timestamps))}')
                    print(F'Last Active: {DateTimeFactory.to_str(max(activity_timestamps))}')
                    print('')
                    print('Time of day histogram:')
                    hours = {}
                    for dt in activity_timestamps:
                        hour = int(dt.strftime('%H'), 10)
                        if hour not in hours.keys():
                            hours[hour] = 0
                        hours[hour] += 1
                    print_histogram(hours)
                if reduced_data:
                    logger.info('Some data was for clarity reasons, specify --json to dump everything.')
    except MalBeaconUnauthorizedException as e:
        logger.error('Not authorized! Make sure to specified the correct API-Key.')
        logger.exception(e)
    except MalBeaconException as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
