from django.shortcuts import render

def home(request):
    print(request)
    return render(request, "index.html")