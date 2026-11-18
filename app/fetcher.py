import ipaddress
import socket

import httpx


MAX_HTML_BYTES = 1_000_000
MAX_REDIRECTS = 3
PUBLIC_IPV6_RANGE = ipaddress.ip_network("2000::/3")


class InvalidWebsiteURL(ValueError):
    pass


class WebsiteFetchError(RuntimeError):
    pass


def resolve_public_ip(url: httpx.URL) -> str:
    if url.scheme not in {"http", "https"} or not url.host or url.userinfo:
        raise InvalidWebsiteURL("Enter an HTTP or HTTPS URL without credentials.")

    port = 443 if url.scheme == "https" else 80
    if url.port not in {None, port}:
        raise InvalidWebsiteURL("Use the standard HTTP or HTTPS port.")

    try:
        records = socket.getaddrinfo(
            url.raw_host.decode("ascii"), port, type=socket.SOCK_STREAM
        )
    except OSError as exc:
        raise WebsiteFetchError("Could not resolve the website hostname.") from exc

    addresses = [ipaddress.ip_address(record[4][0]) for record in records]
    for address in addresses:
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise InvalidWebsiteURL("The website must resolve to public addresses.")
        if address.version == 6 and (
            address not in PUBLIC_IPV6_RANGE or address.teredo or address.sixtofour
        ):
            raise InvalidWebsiteURL("The website must use a public internet address.")

    if not addresses:
        raise WebsiteFetchError("The website has no usable IP address.")

    return str(min(addresses, key=lambda address: address.version))


def fetch_html(raw_url: str) -> str:
    try:
        url = httpx.URL(raw_url.strip())
    except httpx.InvalidURL as exc:
        raise InvalidWebsiteURL("Enter a valid website URL.") from exc

    try:
        with httpx.Client(
            timeout=8.0,
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(max_keepalive_connections=0),
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                ip = resolve_public_ip(url)
                headers = {
                    "Host": url.netloc.decode("ascii"),
                    "Accept-Encoding": "identity",
                }
                with client.stream(
                    "GET",
                    url.copy_with(host=ip),
                    headers=headers,
                    extensions={"sni_hostname": url.raw_host.decode("ascii")},
                ) as response:
                    if response.has_redirect_location:
                        url = url.join(response.headers["location"])
                        continue

                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    media_type = content_type.split(";", 1)[0].strip().lower()
                    if media_type not in {"text/html", "application/xhtml+xml"}:
                        raise WebsiteFetchError("The URL did not return an HTML page.")
                    encoding = response.headers.get("content-encoding", "identity")
                    if encoding.strip().lower() != "identity":
                        raise WebsiteFetchError("The website returned compressed content.")

                    body = bytearray()
                    for chunk in response.iter_raw(chunk_size=16_384):
                        if len(body) + len(chunk) > MAX_HTML_BYTES:
                            raise WebsiteFetchError("The website response is too large.")
                        body.extend(chunk)

                    return body.decode(response.encoding or "utf-8", errors="replace")
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        raise WebsiteFetchError("Could not fetch the website.") from exc

    raise WebsiteFetchError("The website redirected too many times.")