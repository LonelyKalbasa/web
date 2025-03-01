from django.urls import path
# from .views import homePageView
from . import views

urlpatterns = [
    # path('', homePageView, name='home'),
    path('', views.book_list, name='book_list'),
    path('new/', views.book_create, name='book_create'),
    path('<int:pk>/edit/', views.book_update, name='book_update'),
    path('<int:pk>/delete/', views.book_delete, name='book_delete'),
]