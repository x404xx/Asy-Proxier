import asyncio
import logging
import os
import re
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import datetime
from random import shuffle
from time import perf_counter

from httpx import AsyncClient, Response
from httpx_socks import AsyncProxyTransport
from user_agent import generate_user_agent as UserAgent

from urls import ProxyURLs


class Colors:
    GREEN = '\033[38;5;121m'
    BGREEN = '\033[38;5;82m'
    WHITE = '\033[38;5;231m'
    CYAN = '\033[38;5;10m'
    LBLUE = '\033[38;5;117m'
    LPURPLE = '\033[38;5;141m'
    BYELLOW = '\033[38;5;226m'
    LYELLOW = '\033[38;5;228m'
    RED = '\033[38;5;196m'
    END = '\033[0m'


class ProxyChecker:
    PROXY_MENU = {
        'HTTP': ProxyURLs.HTTP,
        'SOCKS4': ProxyURLs.SOCKS4,
        'SOCKS5': ProxyURLs.SOCKS5
    }

    def __init__(self, config_file):
        self._clear_console()
        self.dead_count = 0
        self.live_proxies = []
        self.proxy_type = None
        self.proxy_urls = None
        self.config = ConfigParser()
        self.config.read(config_file)
        self._configure_logging()

    @staticmethod
    def _clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    def _configure_logging(self):
        logging.basicConfig(
            filename = self.config.get('logging', 'filename'),
            level = self.config.get('logging', 'level'),
            format = self.config.get('logging', 'format'),
            datefmt = self.config.get('logging', 'datefmt'),
            filemode = self.config.get('logging', 'filemode')
        )

    @staticmethod
    def _save_proxies(proxy_type: str, live_proxies: list):
        try:
            directory = 'live_proxies'
            os.makedirs(directory, exist_ok=True)
            timestamp = datetime.now().strftime('%d%m%y_%I%M%p')
            filename = f'{directory}/{proxy_type}-{timestamp}.txt'

            with open(filename, 'w', encoding='utf8') as file:
                file.write('\n'.join(live_proxies))

            logging.info(f'Your live proxies have been saved in {filename}')
            print(f'\nYour live proxies have been saved in "{Colors.LYELLOW}{filename}{Colors.END}"')

        except Exception as exc:
            logging.error(f'Error saving proxies: {exc}')
            print(f'Error saving proxies: {exc}')

    @staticmethod
    def time_taken(started: float):
        elapsed = round((perf_counter() - started), 2)
        if elapsed < 1:
            format_elapsed = f'{Colors.LBLUE}{round(elapsed * 1000)}{Colors.END} milliseconds!'
        elif elapsed < 60:
            format_elapsed = f'{Colors.LBLUE}{elapsed}{Colors.END} seconds!'
        else:
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            format_elapsed = f'{Colors.LBLUE}{minutes}{Colors.END} minutes {Colors.LBLUE}{seconds}{Colors.END} seconds!'
        return format_elapsed

    @staticmethod
    def _get_default_concurrent(proxy_count: int):
        ranges = [(20, 5), (50, 20), (100, 50), (200, 75), (500, 125), (1000, 150), (2500, 200), (5000, 250)]
        return next((value for upper_bound, value in ranges if proxy_count <= upper_bound), 300)

    @staticmethod
    def _search_proxies(response: Response):
        pattern = re.compile(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:'
            r'(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|'
            r'65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])\b'
        )
        return pattern.findall(response.text)

    def select_proxy(self, proxy_choice: str):
        if proxy_choice.upper() in self.PROXY_MENU:
            self.proxy_type = proxy_choice.lower()
            self.proxy_urls = self.PROXY_MENU[proxy_choice]
        else:
            logging.warning('Invalid proxy choice.')
            print('Invalid proxy choice! Only (HTTP|SOCKS4|SOCKS5)')

    @staticmethod
    async def _make_request(client: AsyncClient, url: str, headers: dict):
        try:
            return await client.get(url, headers=headers)
        except Exception:
            return None

    async def _fetch_proxies(self, proxy_shuffle: bool):
        try:
            async with AsyncClient() as client:
                headers = {'User-Agent': UserAgent()}
                responses = await asyncio.gather(
                    *[self._make_request(client, url, headers) for url in self.proxy_urls]
                )
                raw_proxies = [self._search_proxies(response) for response in responses if response is not None]
                unique_proxies = list(set(
                    f'{self.proxy_type}://{proxy.strip()}'
                    for proxies in raw_proxies for proxy in proxies
                ))
                if proxy_shuffle:
                    shuffle(unique_proxies)

                logging.info(f'Found {len(unique_proxies)} {self.proxy_type.upper()} proxies!')
                print(f'Found {Colors.BYELLOW}{len(unique_proxies)} {Colors.LPURPLE}{self.proxy_type.upper()}{Colors.END} proxies!')

                while True:
                    limiter = input(f'How many proxies should be check? (press "{Colors.CYAN}ENTER{Colors.END}" to skip limit): ')
                    if not limiter.strip():
                        proxies = unique_proxies
                    elif limiter.isdigit():
                        proxies = unique_proxies[:int(limiter)]
                    else:
                        logging.warning('Invalid input for proxy limit.')
                        print('Please enter a valid digit or press "ENTER".')
                        continue

                    logging.info(f'Proxy has been limit to {len(proxies)} for checking.')
                    return proxies

        except Exception as exc:
            logging.error(f'Error fetching proxies: {exc}')
            print(f'Error fetching proxies: {exc}')

    async def _check_proxies(self, proxy: str, check_url: str, timeout: float):
        transport = AsyncProxyTransport.from_url(proxy)
        try:
            async with AsyncClient(
                transport = transport,
                timeout = timeout,
                verify = False
                ) as client:

                headers = {'User-Agent': UserAgent()}
                response = await client.get(check_url, headers=headers)
                if 200 <= response.status_code <= 299:
                    return proxy
                else:
                    self.dead_count += 1

        except Exception as exc:
            logging.error(f'Checking Exception: {type(exc).__name__}')
            self.dead_count += 1

    async def start_checker(
        self,
        timeout: float,
        check_url: str,
        custom_concurrent: int,
        use_semaphore: bool,
        proxy_shuffle: bool
        ):

        proxies = await self._fetch_proxies(proxy_shuffle)
        semaphore = None
        concurrent = None
        if use_semaphore:
            concurrent = custom_concurrent if custom_concurrent else self._get_default_concurrent(len(proxies))
            semaphore = asyncio.Semaphore(concurrent)
            logging.info(
                f'Checker started! Concurrent={concurrent}, '
                f'Timeout={timeout}, '
                f'Proxy_shuffle={proxy_shuffle}'
            )
            print(
                f'Checker started! Concurrent: {Colors.WHITE}{concurrent}{Colors.END}, '
                f'Timeout: {Colors.WHITE}{timeout}{Colors.END}, '
                f'Proxy Shuffle: {Colors.WHITE}{proxy_shuffle}{Colors.END}'
            )
        else:
            logging.info(
                f'Checker started! Timeout={timeout}, '
                f'Proxy_shuffle={proxy_shuffle}'
            )
            print(
                f'Checker started! Timeout: {Colors.WHITE}{timeout}{Colors.END}, '
                f'Proxy Shuffle: {Colors.WHITE}{proxy_shuffle}{Colors.WHITE}'
            )

        async def _semaphore_options(proxy: str):
            if use_semaphore:
                async with semaphore:
                    result = await self._check_proxies(proxy, check_url, timeout)
            else:
                result = await self._check_proxies(proxy, check_url, timeout)

            if result:
                self.live_proxies.append(result)

            print(
                f'{Colors.WHITE}Live{Colors.END}: ({Colors.BGREEN}{len(self.live_proxies)}{Colors.END}) '
                f'{Colors.WHITE}Dead{Colors.END}: ({Colors.RED}{self.dead_count}{Colors.END})',
                end='\r',
            )

        await asyncio.gather(*[_semaphore_options(proxy) for proxy in proxies])
        if self.live_proxies:
            self._save_proxies(self.proxy_type, self.live_proxies)
        else:
            logging.info('No live proxies to save.')
            print('\nNo live proxies to save.')


def main():
    parser = ArgumentParser(
        description='Proxy Scraper|Checker'
    )
    parser.add_argument(
        '-cf',
        '--config-file',
        type=str,
        default='config.ini',
        help='Configuration file (Default: config.ini)'
    )
    parser.add_argument(
        '-cu',
        '--check-url',
        type=str,
        default='http://httpbin.org/ip',
        help='URL for checking proxy (Default: http://httpbin.org/ip)'
    )
    parser.add_argument(
        '-cc',
        '--concurrent',
        type=int,
        default=None,
        help='Concurrent requests [OPTIONAL] (Default: None)'
    )
    parser.add_argument(
        '-pc',
        '--proxy-choice',
        required=True,
        type=str,
        choices=['HTTP', 'SOCKS4', 'SOCKS5'],
        help='Proxy choice: HTTP, SOCKS4, SOCKS5'
    )
    parser.add_argument(
        '-to',
        '--timeout',
        type=float,
        default=10,
        help='Proxy timeout (Default: 10)'
    )
    parser.add_argument(
        '-ps',
        '--proxy-shuffle',
        action='store_true',
        default=True,
        help='Proxy shuffle or randomize (Default: True)'
    )
    parser.add_argument(
        '-us',
        '--use-semaphore',
        action='store_true',
        default=True,
        help='Semaphore usage (Default: True)'
    )
    args = parser.parse_args()

    proxy_tool = ProxyChecker(config_file=args.config_file)
    proxy_tool.select_proxy(proxy_choice=args.proxy_choice)
    started = perf_counter()
    asyncio.run(
        proxy_tool.start_checker(
            timeout=args.timeout,
            check_url=args.check_url,
            custom_concurrent=args.concurrent,
            use_semaphore=args.use_semaphore,
            proxy_shuffle=args.proxy_shuffle,
        )
    )
    print(f'\nTime Taken: {proxy_tool.time_taken(started)}\n')


if __name__ == '__main__':
    main()
