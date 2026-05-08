from django.http import HttpResponse
from django.shortcuts import render


def landing(request):
    return render(request, "landing.html")


def about(request):
    return render(request, "about.html")


def disclaimer(request):
    return render(request, "legal/disclaimer.html")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")
