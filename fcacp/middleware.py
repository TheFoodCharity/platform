from django.contrib.messages import get_messages
from django.template.loader import render_to_string
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh


class HtmxMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            not request.htmx
            or response.status_code >= 300
            or isinstance(response, (HttpResponseClientRedirect, HttpResponseClientRefresh))
            or not response.get("Content-Type", "").startswith("text/html")
        ):
            return response
        # Iterating get_messages() marks messages as used; MessageMiddleware
        # clears them in its own process_response, which runs after ours because
        # we are appended last in MIDDLEWARE (response path is reversed).
        messages = list(get_messages(request))
        if messages:
            response.write(
                render_to_string(
                    "components/_toasts_oob.html",
                    {"messages": messages},
                    request=request,
                )
            )
        return response
