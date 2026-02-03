"""
URL configuration for dev_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.http import JsonResponse, HttpResponse
from django.views.static import serve
from django.conf import settings
import os

def smart_static(request, path):
    """
    Simulates logic of MicroPython http server:
    - styles.css  → upload/web/css/styles.css
    - app.js      → upload/web/js/app.js
    - config.html → upload/web/config.html (bez podfolderu)
    - obrazek.png → upload/web/assets/obrazek.png (lub inny folder jeśli chcesz)
    """
    if not path:
        path = "index.html"  # domyślna strona

    ext_to_folder = {
        '.css': 'css',
        '.js':  'js',
        '.png': 'assets',
        '.jpg': 'assets',
        '.jpeg':'assets',
        '.gif': 'assets',
        '.svg': 'assets',
        '.ico': 'assets',
        '.woff': 'assets',
        '.woff2':'assets',
        '.ttf': 'assets',
    }

    ext = os.path.splitext(path)[1].lower()
    folder = ext_to_folder.get(ext, '')  # jeśli nie ma reguły → szukaj w root web/

    # Budujemy pełną ścieżkę
    full_path = os.path.join(settings.STATICFILES_DIRS[0], folder, path.lstrip('/'))
    print(f'full_path = {full_path}')

    # Jeśli plik istnieje → serwuj go
    if os.path.exists(full_path):
        return serve(request, os.path.basename(full_path), os.path.dirname(full_path))

    # Jeśli nie istnieje → spróbuj w root (np. index.html, config.html)
    fallback_path = os.path.join(settings.STATICFILES_DIRS[0], path.lstrip('/'))
    if os.path.exists(fallback_path):
        return serve(request, path.lstrip('/'), settings.STATICFILES_DIRS[0])

    # 404 jeśli naprawdę nie ma
    from django.http import Http404
    raise Http404(f"Plik nie znaleziony: {path}")

urlpatterns = [
    # Bazowy endpoint z Django
    path('admin/', admin.site.urls),

    # Serwowanie plików statycznych z katalogu z upload/web/
    re_path(r'^(?P<path>.*)$', smart_static), 
]
