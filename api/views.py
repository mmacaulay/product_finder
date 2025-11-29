from django.http import HttpResponse


def health_check(request):
    """
    Health check endpoint to verify that the API is running.
    """
    return HttpResponse("ok\n", status=200)
