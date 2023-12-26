from django.urls import path
from .views import responseToSpring
from .views import summaryToSpring

urlpatterns = [
    path('responseToSpring',responseToSpring,name='responseToSpring'),
    path('summaryToSpring',summaryToSpring,name='summaryToSpring'),
]