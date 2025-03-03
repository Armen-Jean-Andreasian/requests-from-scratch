import http.client
import urllib.parse
from urllib.parse import urlparse
import json
import gzip
import zlib


class Response:
    """An HTTP response object."""

    def __init__(self, status_code: int, headers: dict, payload: str):
        self.status_code = status_code
        self.headers = headers
        self.payload = payload

    @property
    def content(self) -> str:
        """Returns the response payload as a string."""
        return self.payload

    @property
    def json(self) -> dict | None:
        """Parses and returns the response payload as JSON if possible."""
        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return None

    def __str__(self) -> str:
        return (
            f"Response object. "
            f"Status: {self.status_code}, "
            f"headers: {self.headers}, "
        )


class ClientBase:
    redirect_status_codes = (301, 302, 307, 308)

    default_headers = {
        "User-Agent": "python-custom-client/1.0",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    allow_redirects = None

    @classmethod
    def init(cls, custom_headers: dict = None, allow_redirects: bool = None):
        if custom_headers:
            for k, v in custom_headers.items():
                cls.default_headers[k] = v

        if allow_redirects:
            cls.allow_redirects = True

    @staticmethod
    def _connect(raw_url: str) -> tuple[http.client.HTTPSConnection | http.client.HTTPConnection, str]:
        """Establishes an HTTP or HTTPS connection."""
        parsed_url: urllib.parse.ParseResult = urlparse(raw_url)
        scheme: str = parsed_url.scheme or "http"
        host: str = parsed_url.netloc

        # get the full request path (including query params)
        path: str = parsed_url.path or "/"
        if parsed_url.query:
            path += "?" + parsed_url.query

        # create a connection
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
        data: bytes | None,
    ) -> Response:
        """Handles HTTP redirects."""
        new_url: str | None = response.getheader("Location")

        if not new_url:
            raise RuntimeError(f"Redirect ({response.status}) but no Location header")
        connection.close()
        return cls._request(method, new_url, headers, json_data, data, max_redirects - 1)

    @classmethod
    def _decode_payload(cls, response: http.client.HTTPResponse) -> str:
        """Decodes compressed response payloads."""
        raw_data: bytes = response.read()
        encoding: str = response.getheader("Content-Encoding")

        if encoding == "gzip":
            raw_data: bytes = gzip.decompress(raw_data)
        elif encoding == "deflate":
            raw_data: bytes = zlib.decompress(raw_data)
        else:
            raise RuntimeError(f"Could not decode encoding: {encoding}")

        decoded_payload: str = raw_data.decode("utf-8", errors="replace")
        return decoded_payload

    @classmethod
    def _request(
        cls,
        method: str,
        url: str,
        headers: dict | None = None,
        json_data: dict | None = None,
        data: str | bytes | None = None,
        max_redirects: int = 5,
        allow_redirects: bool = None,
    ) -> Response:
        """Sends an HTTP request and returns a response object."""

        if max_redirects < 0:
            raise RuntimeError("Too many redirects")

        connection, path = cls._connect(url)

        # merge user-provided headers
        headers: dict = {**cls.default_headers, **(headers or {})}

        # handle JSON data
        if json_data is not None:
            data: str = json.dumps(json_data)
            headers["Content-Type"] = "application/json"

        # convert data to bytes if it's a string
        if isinstance(data, str):
            data: bytes = data.encode()

        # send request
        connection.request(method.upper(), path, body=data, headers=headers)

        # get response
        response: http.client.HTTPResponse = connection.getresponse()
        status_code: int = response.status

        # handle redirects
        if status_code in cls.redirect_status_codes:
            # redirecting only if allow_redirects is True, or allow_redirects is None but cls.allow_redirects is True
            if allow_redirects is True:
                return cls._redirect(response, max_redirects, connection, method, headers, json_data, data)
            elif allow_redirects is None and cls.allow_redirects is True:
                return cls._redirect(response, max_redirects, connection, method, headers, json_data, data)

            # passing: to pack the 3XX requests with disallowed redirects

        # decoding payload
        decoded_payload: str = cls._decode_payload(response)

        connection.close()
        return Response(
            status_code=status_code,
            headers=headers,
            payload=decoded_payload
        )


class Client(ClientBase):
    """HTTP client providing convenient methods for common requests."""

    @classmethod
    def get(cls, url: str, headers: dict | None = None) -> Response:
        return cls._request("GET", url, headers)

    @classmethod
    def post(cls, url: str, headers: dict | None = None, data: bytes | None = None,
             json_data: dict | None = None) -> Response:
        return cls._request("POST", url, headers, data, json_data)

    @classmethod
    def put(cls, url: str, headers: dict | None = None, data: bytes | None = None,
            json_data: dict | None = None) -> Response:
        return cls._request("PUT", url, headers, data, json_data)

    @classmethod
    def patch(cls, url: str, headers: dict | None = None, data: bytes | None = None,
              json_data: dict | None = None) -> Response:
        return cls._request("PATCH", url, headers, data, json_data)

    @classmethod
    def delete(cls, url: str, headers: dict | None = None) -> Response:
        return cls._request("DELETE", url, headers)

    @classmethod
    def head(cls, url: str, headers: dict | None = None) -> Response:
        return cls._request("HEAD", url, headers)

    @classmethod
    def options(cls, url: str, headers: dict | None = None) -> Response:
        return cls._request("OPTIONS", url, headers)
