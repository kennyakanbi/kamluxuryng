from django.urls import path
from . import views


app_name = "listings"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("activities/", views.activities, name="activities"),
    path("properties/", views.property_list, name="property_list"),
    path("properties/<slug:slug>/", views.property_detail, name="detail"),
]

