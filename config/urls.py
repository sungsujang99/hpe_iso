"""
HPE URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/inventory/', include('apps.inventory.urls')),
    
    # Core (dashboard, common APIs)
    path('api/v1/', include('apps.core.urls')),
    
    # Frontend Pages
    path('', include('config.urls_frontend')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Admin site customization
admin.site.site_header = 'HPE 관리 시스템'
admin.site.site_title = 'HPE Admin'
admin.site.index_title = 'ISO 문서 & 재고관리 시스템'
