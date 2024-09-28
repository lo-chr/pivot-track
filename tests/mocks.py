from pivot_track.lib.connectors import CensysSourceConnector, ShodanSourceConnector

# Censys examples based on https://github.com/censys/censys-python/blob/main/tests/search/v2/test_hosts.py
CENSYS_TEST_HOST = "8.8.8.8"
CENSYS_TEST_SEARCH_QUERY = "services.service_name: HTTP"
CENSYS_HOST_JSON = {
    "services": [
        {
            "transport_protocol": "UDP",
            "truncated": False,
            "service_name": "DNS",
            "_decoded": "dns",
            "source_ip": "167.248.133.40",
            "extended_service_name": "DNS",
            "observed_at": "2021-04-01T13:40:03.755876935Z",
            "dns": {"server_type": "FORWARDING"},
            "perspective_id": "PERSPECTIVE_NTT",
            "port": 53,
            "software": [],
        }
    ],
    "ip": "8.8.8.8",
    "location_updated_at": "2021-03-30T14:53:12.980328Z",
    "location": {
        "country": "United States",
        "coordinates": {"latitude": 37.751, "longitude": -97.822},
        "registered_country": "United States",
        "registered_country_code": "US",
        "postal_code": "",
        "country_code": "US",
        "timezone": "America/Chicago",
        "continent": "North America",
    },
    "last_updated_at": "2021-04-01T14:10:10.712Z",
}
CENSYS_SEARCH_JSON = [
        {
            "services": [
                {"service_name": "HTTP", "port": 443},
                {"service_name": "HTTP", "port": 80},
            ],
            "ip": "1.0.0.0",
            "last_updated_at": "2023-07-15T08:54:31.636Z",
        },
        {
            "services": [
                {"service_name": "HTTP", "port": 443},
                {"service_name": "HTTP", "port": 80},
            ],
            "ip": "1.0.0.1",
            "last_updated_at": "2023-07-15T08:54:31.636Z",
        },
    ]

# Shodan examples based on https://developer.shodan.io/api
SHODAN_TEST_HOST = "8.8.8.8"
SHODAN_TEST_SEARCH_QUERY = "product:nginx"
SHODAN_HOST_JSON = {
    "region_code": None,
    "ip": 134744072,
    "postal_code": None,
    "country_code": "US",
    "city": None,
    "dma_code": None,
    "last_update": "2021-01-22T08:49:35.190817",
    "latitude": 37.751,
    "tags": [],
    "area_code": None,
    "country_name": "United States",
    "hostnames": [
        "dns.google"
    ],
    "org": "Google",
    "data": [
        {
            "_shodan": {
                "id": "cea5795b-55fd-4595-b9e5-ad5ca847cb4b",
                "options": {},
                "ptr": True,
                "module": "dns-udp",
                "crawler": "ac284849be0745621b3c518f74c14cf43cafbf08"
            },
            "hash": -553166942,
            "os": None,
            "opts": {
                "raw": "34ef818200010000000000000776657273696f6e0462696e640000100003"
            },
            "ip": 134744072,
            "isp": "Google",
            "port": 53,
            "hostnames": [
                "dns.google"
            ],
            "location": {
                "city": None,
                "region_code": None,
                "area_code": None,
                "longitude": -97.822,
                "country_code3": None,
                "country_name": "United States",
                "postal_code": None,
                "dma_code": None,
                "country_code": "US",
                "latitude": 37.751
            },
            "dns": {
                "resolver_hostname": None,
                "recursive": True,
                "resolver_id": None,
                "software": None
            },
            "timestamp": "2021-01-22T08:49:35.190817",
            "domains": [
                "dns.google"
            ],
            "org": "Google",
            "data": "\nRecursion: enabled",
            "asn": "AS15169",
            "transport": "udp",
            "ip_str": "8.8.8.8"
        }
    ],
    "asn": "AS15169",
    "isp": "Google",
    "longitude": -97.822,
    "country_code3": None,
    "domains": [
        "dns.google"
    ],
    "ip_str": "8.8.8.8",
    "os": None,
    "ports": [
        53
    ]
}
SHODAN_SEARCH_JSON = {
    "matches": [
        {
            "product": "nginx",
            "hash": -1609083510,
            "ip": 1616761883,
            "org": "Comcast Business",
            "isp": "Comcast Business",
            "transport": "tcp",
            "cpe": [
                "cpe:/a:igor_sysoev:nginx"
            ],
            "data": "HTTP/1.1 400 Bad Request\r\nServer: nginx\r\nDate: Mon, 25 Jan 2021 21:33:48 GMT\r\nContent-Type: text/html\r\nContent-Length: 650\r\nConnection: close\r\n\r\n",
            "asn": "AS7922",
            "port": 443,
            "hostnames": [
                "three.webapplify.net"
            ],
            "location": {
                "city": "Denver",
                "region_code": "CO",
                "area_code": None,
                "longitude": -104.9078,
                "country_code3": None,
                "latitude": 39.7301,
                "postal_code": None,
                "dma_code": 751,
                "country_code": "US",
                "country_name": "United States"
            },
            "timestamp": "2021-01-25T21:33:49.154513",
            "domains": [
                "webapplify.net"
            ],
            "http": {
                "robots_hash": None,
                "redirects": [],
                "securitytxt": None,
                "title": "400 The plain HTTP request was sent to HTTPS port",
                "sitemap_hash": None,
                "robots": None,
                "server": "nginx",
                "host": "96.93.212.27",
                "html": "\r\n400 The plain HTTP request was sent to HTTPS port\r\n\r\n400 Bad Request\r\nThe plain HTTP request was sent to HTTPS port\r\nnginx\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n",
                "location": "/",
                "components": {},
                "securitytxt_hash": None,
                "sitemap": None,
                "html_hash": 199333125
            },
            "os": None,
            "_shodan": {
                "crawler": "c9b639b99e5410a46f656e1508a68f1e6e5d6f99",
                "ptr": True,
                "id": "534cc127-e734-44bc-be88-2e219a56a099",
                "module": "auto",
                "options": {}
            },
            "ip_str": "96.93.212.27"
        },
        {
            "product": "nginx",
            "hostnames": [
                "kolobok.us"
            ],
            "hash": 1940048442,
            "ip": 3104568883,
            "org": "RuWeb",
            "isp": "RuWeb",
            "transport": "tcp",
            "cpe": [
                "cpe:/a:igor_sysoev:nginx:1.4.2"
            ],
            "data": "HTTP/1.1 410 Gone\r\nServer: nginx/1.4.2\r\nDate: Mon, 25 Jan 2021 21:33:50 GMT\r\nContent-Type: text/html; charset=iso-8859-1\r\nContent-Length: 295\r\nConnection: keep-alive\r\n\r\n",
            "asn": "AS49189",
            "port": 80,
            "version": "1.4.2",
            "location": {
                "city": None,
                "region_code": None,
                "area_code": None,
                "longitude": 37.6068,
                "country_code3": None,
                "latitude": 55.7386,
                "postal_code": None,
                "dma_code": None,
                "country_code": "RU",
                "country_name": "Russia"
            },
            "timestamp": "2021-01-25T21:33:51.172037",
            "domains": [
                "kolobok.us"
            ],
            "http": {
                "robots_hash": None,
                "redirects": [],
                "securitytxt": None,
                "title": "410 Gone",
                "sitemap_hash": None,
                "robots": None,
                "server": "nginx/1.4.2",
                "host": "185.11.246.51",
                "html": "\n\n410 Gone\n\nGone\nThe requested resource/\nis no longer available on this server and there is no forwarding address.\nPlease remove all references to this resource.\n\n",
                "location": "/",
                "components": {},
                "securitytxt_hash": None,
                "sitemap": None,
                "html_hash": 922034037
            },
            "os": None,
            "_shodan": {
                "crawler": "c9b639b99e5410a46f656e1508a68f1e6e5d6f99",
                "ptr": True,
                "id": "118b7360-01d0-4edb-8ee9-01e411c23e60",
                "module": "auto",
                "options": {}
            },
            "ip_str": "185.11.246.51"
        },
    ],
    "facets": {
        "country": [
            {
                "count": 7883733,
                "value": "US"
            },
            {
                "count": 2964965,
                "value": "CN"
            },
            {
                "count": 1945369,
                "value": "DE"
            },
            {
                "count": 1717359,
                "value": "HK"
            },
            {
                "count": 940900,
                "value": "FR"
            }
        ]
    },
    "total": 23047224
}

class MockShodanSourceConnector(ShodanSourceConnector):
    def __init__(self):
        pass

    def query_host(self, host:str):
        return SHODAN_HOST_JSON
    
    def query_host_search(self, query:str):
        return SHODAN_SEARCH_JSON

class MockCensysSourceConnector(CensysSourceConnector):
    def __init__(self):
        pass

    def query_host(self, host:str):
        return CENSYS_HOST_JSON
    
    def query_host_search(self, query:str):
        return CENSYS_SEARCH_JSON