from django.urls import path
from .views import responseToSpring
urlpatterns = [
    path('responseToSpring',responseToSpring,name='responseToSpring'),
    
]