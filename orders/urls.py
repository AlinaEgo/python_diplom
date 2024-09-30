"""
URL configuration for orders project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from backend.views import (UserRegister, ConfirmAccount, LoginAccount, AccountDetails, CategoryView,
                           ShopView, PartnerUpdate, PartnerState, PartnerOrders, BasketView, OrderView,
                           ProductInfoView, UserContact)
from rest_framework.routers import DefaultRouter
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm


r = DefaultRouter()
urlpatterns = r.urls
urlpatterns += [path('admin/', admin.site.urls)]
urlpatterns += [path('user/register',
                     UserRegister.as_view(), name='user-register')]
urlpatterns += [path('user/register/confirm',
                     ConfirmAccount.as_view(), name='user-register-confirm')]
urlpatterns += [path('user/login', LoginAccount.as_view(), name='user-login')]
urlpatterns += [path('user/password_reset', reset_password_request_token, name='password-reset')]
urlpatterns += [path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm')]
urlpatterns += [path('user/details', AccountDetails.as_view(), name='user-details')]
urlpatterns += [path('user/contact', UserContact.as_view(), name='user-contact')]
urlpatterns += [path('partner/update', PartnerUpdate.as_view(), name='partner-update')]
urlpatterns += [path('partner/state', PartnerState.as_view(), name='partner-state')]
urlpatterns += [path('partner/orders', PartnerOrders.as_view(), name='partner-orders')]
urlpatterns += [path('categories', CategoryView.as_view(), name='categories')]
urlpatterns += [path('shops', ShopView.as_view(), name='shops')]
urlpatterns += [path('basket', BasketView.as_view(), name='basket')]
urlpatterns += [path('order', OrderView.as_view(), name='order')]
urlpatterns += [path('products', ProductInfoView.as_view(), name='shops')]