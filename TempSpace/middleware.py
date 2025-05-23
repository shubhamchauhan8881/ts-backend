from rest_framework.response import Response
from django.conf import settings
class GlobalErrorHandler:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            print("ASdfasdfasdf")
            response = self.get_response(request)
        except:
            print("error")
            response = Response()
        return response 
    
    def process_exception(self, request, exception):
        if not settings.DEBUG:
            if exception:
                message = "{url}\n{error}\n{tb}".format(
                    url=request.build_absolute_uri(),
                    error=repr(exception),
                    tb=traceback.format_exc()
                )
                # Do whatever with the message now
            return HttpResponse("Error processing the request.", status=500)
