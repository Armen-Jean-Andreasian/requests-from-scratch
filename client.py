import http.client
from urllib.parse import urlparse
import json
import gzip
import zlib


class Response:
    def __init__(self, status_code: int, headers: dict, payload: str):
        self.status_code = status_code
        self.headers = headers
        self.payload = payload

    @property
    def content(self):
        return self.payload

    @property
    def json(self):
        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return None

    def __str__(self):
        return (
            f"Response object. "
            f"Status: {self.status_code}, "
            f"headers: {self.headers}, "
        )


class Client:
    redirect_status_codes = (301, 302, 307, 308)

    default_headers = {
        "User-Agent": "python-custom-client/1.0",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    @staticmethod
    def _connect(raw_url: str):
        parsed_url = urlparse(raw_url)
        scheme = parsed_url.scheme or "http"
        host = parsed_url.netloc

        # Get the full request path (including query params)
        path = parsed_url.path or "/"
        if parsed_url.query:
            path += "?" + parsed_url.query

        # Create a connection
        if scheme == "https":
            connection = http.client.HTTPSConnection(host)
        elif scheme == "http":
            connection = http.client.HTTPConnection(host)
        else:
            raise NotImplementedError(f"Unsupported scheme: {scheme}")

        return connection, path

    @classmethod
    def _redirect(
        cls,
        response: http.client.HTTPResponse,
        max_redirects: int,
        connection: http.client.HTTPSConnection | http.client.HTTPConnection,
        method: str,
        headers: dict,
        json_data: dict,
        data,
    ):
        new_url = response.getheader("Location")
        if not new_url:
            raise RuntimeError(f"Redirect ({response.status}) but no Location header")
        connection.close()
        return cls._request(method, new_url, headers, json_data, data, max_redirects - 1)

    @classmethod
    def _decode_payload(cls, response: http.client.HTTPResponse, ) -> str:
        raw_data: bytes = response.read()
        encoding: str = response.getheader("Content-Encoding")

        if encoding == "gzip":
            raw_data: bytes = gzip.decompress(raw_data)
        elif encoding == "deflate":
            raw_data: bytes = zlib.decompress(raw_data)
        else:
            raise RuntimeError(f"Could not decode encoding: {encoding}")

        # Decode response
        decoded_payload: str = raw_data.decode("utf-8", errors="replace")
        return decoded_payload

    @classmethod
    def _request(cls, method: str, url: str, headers=None, json_data: dict = None, data=None, max_redirects=5):
        if max_redirects < 0:
            raise RuntimeError("Too many redirects")

        connection, path = cls._connect(url)

        # Merge user-provided headers
        headers: dict = {**cls.default_headers, **(headers or {})}

        # Handle JSON data
        if json_data is not None:
            data: str = json.dumps(json_data)
            headers["Content-Type"] = "application/json"

        # Convert data to bytes if it's a string
        if isinstance(data, str):
            data: bytes = data.encode()

        # Send request
        connection.request(method.upper(), path, body=data, headers=headers)

        # Get response
        response: http.client.HTTPResponse = connection.getresponse()
        status_code: int = response.status

        # Handle redirects
        if status_code in cls.redirect_status_codes:
            return cls._redirect(response, max_redirects, connection, method, headers, json_data, data)

        # Decoding payload
        decoded_payload: str = cls._decode_payload(response)

        connection.close()
        result = Response(
            status_code=status_code,
            headers=headers,
            payload=decoded_payload
        )

        return result

    @classmethod
    def get(cls, url: str, headers=None):
        return cls._request(method="GET", url=url, headers=headers)

    @classmethod
    def post(cls, url: str, headers=None, data=None, json_data=None):
        return cls._request(method="POST", url=url, headers=headers, data=data, json_data=json_data)


# Example Usage
response = Client.get("https://stackoverflow.com/questions/78075334/github-copilot-issue-on-pycharm")
print(response)
print(response.content)
