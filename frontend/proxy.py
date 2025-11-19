from __future__ import print_function
from flask import Blueprint, request, Response

try:
    from urllib import request as _urllib_request
    from urllib.error import HTTPError, URLError
except:
    import urllib2 as _urllib_request
    from urllib2 import HTTPError, URLError

proxy_bp = Blueprint("proxy", __name__)
BACKEND_BASE = "http://127.0.0.1:5000"

@proxy_bp.route("/api/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH","OPTIONS","HEAD"])
def proxy(path):
    qs = request.query_string.decode("utf-8", "ignore")
    url = BACKEND_BASE + "/api/" + path
    if qs:
        url += "?" + qs

    body = request.get_data() or None
    req = _urllib_request.Request(url, data=body)
    req.get_method = lambda: request.method.upper()

    for hk in ["Content-Type", "User-Agent", "Accept", "Accept-Language"]:
        hv = request.headers.get(hk)
        if hv:
            try:
                req.add_header(hk, hv)
            except:
                pass

    try:
        resp = _urllib_request.urlopen(req, timeout=10)
        data = resp.read()
        status = getattr(resp, "code", 200)
        headers = []
        for hk in resp.headers:
            if hk.lower() in ("transfer-encoding","content-encoding",
                              "connection","keep-alive","proxy-authenticate",
                              "proxy-authorization","te","trailers","upgrade"):
                continue
            headers.append((hk, resp.headers.get(hk)))
        return Response(data, status=status, headers=headers)
    except HTTPError as e:
        return Response(e.read(), status=e.code)
    except URLError as e:
        msg = (str(getattr(e,"reason",e)) or "backend unavailable").encode("utf-8")
        return Response(msg, status=502)
    except Exception as e:
        return Response(("proxy error: %s" % e).encode("utf-8"), status=500)
