from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Test view from facelog app is working!")