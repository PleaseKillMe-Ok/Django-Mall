"""e_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer

from Emall import settings
# 重要的是如下三行
from Emall.base_view import error_404

schema_view = get_schema_view(title='云逸电子商城开发接口文档', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer],
                              description="司云中出品!")

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('search/', SearchView(), name='search'),
    path('404/', error_404, name='404'),
    path('payment/', include('payment_app.urls', namespace='payment')),
    path('consumer/', include('user_app.urls', namespace='consumer')),
    path('order/', include('order_app.urls', namespace='order')),
    path('remark/', include('remark_app.urls', namespace='remark')),
    path('shop/', include('shop_app.urls', namespace='shop')),
    path('voucher/', include('voucher_app.urls', namespace='voucher')),
    path('chsc-syz-247179876-docs/', schema_view, name='api_doc'),
    path(r'mdeditor/', include('mdeditor.urls')),
    path('search/', include('search_app.urls', namespace='search')),
    path('oauth/', include('oauth_app.urls', namespace='oauth')),
]

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # 存放media资源
