<div align="center">

<img src="https://github.com/x404xx/Asy-Proxier/assets/114883816/e4dfd505-6037-44a1-ac33-5577ef785d74" width="300">

**AsyProxier** is an asynchronous tool that helps you grab proxies from various sources and check them instantly.

<img src="https://github.com/x404xx/Asy-Proxier/assets/114883816/81a8f3e0-b10b-47df-b167-5f1e0b4be320" width="700" height="auto">

</div>

## **Installation**

To use _**AsyProxier**_, open your terminal and navigate to the folder that contains _**AsyProxier**_ content ::

```
pip install -r requirements.txt
```

## **Usage**

Running _**AsyProxier**_ using command-line ::

```
usage: main.py [-h] [-cf CONFIG_FILE] [-cu CHECK_URL] [-cc CONCURRENT] -pc {HTTP,SOCKS4,SOCKS5} [-to TIMEOUT] [-ps] [-us]

Proxy Scraper|Checker

options:
  -h, --help            show this help message and exit
  -cf CONFIG_FILE, --config-file CONFIG_FILE
                        Configuration file (Default: config.ini)
  -cu CHECK_URL, --check-url CHECK_URL
                        URL for checking proxy (Default: http://httpbin.org/ip)
  -cc CONCURRENT, --concurrent CONCURRENT
                        Concurrent requests [OPTIONAL] (Default: None)
  -pc {HTTP,SOCKS4,SOCKS5}, --proxy-choice {HTTP,SOCKS4,SOCKS5}
                        Proxy choice: HTTP, SOCKS4, SOCKS5
  -to TIMEOUT, --timeout TIMEOUT
                        Proxy timeout (Default: 10)
  -ps, --proxy-shuffle  Proxy shuffle or randomize (Default: True)
  -us, --use-semaphore  Semaphore usage (Default: True)
```

Command-line example ::

```python
python main.py -pc SOCKS4
```

## **Legal Disclaimer**

> **Note**
> This was made for educational purposes only, nobody which directly involved in this project is responsible for any damages caused. **_You are responsible for your actions._**
