from django.urls import path
from . import views

urlpatterns = [
    path('initiate/<int:order_id>/', views.initiate_payment, name='initiate-payment'),
    path('verify/', views.verify_payment, name='verify-payment'),
]