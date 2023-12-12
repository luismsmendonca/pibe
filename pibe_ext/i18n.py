import gettext
import funcy as fn
from .session import g
from .http import http, expectation_failed

__all__ = ("get_language", "language_middleware")

@fn.memoize
def get_language(language_code):
    return gettext.translation(
        language_code, localedir="locales/", languages=[language_code]
    )


@http.middleware()
def language_middleware(req, **opts):
    language_code = (
        req.headers.get("X-Language-Code") or req.params.get("language_code") or "en"
    )

    if language_code not in ["en", "pt_PT"]:
        expectation_failed(error="Invalid language requested.")

    req.environ["language_code"] = language_code
    g.language_code = language_code

    if language_code == "en":
        gettext.install("base", "locales")
    else:
        language = get_language(language_code)
        language.install()
