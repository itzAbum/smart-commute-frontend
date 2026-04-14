from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home
    path('', views.index, name='home'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path("logout/", views.logout_view, name="logout"),

    # Schedule
    path('schedule/', views.schedule, name='schedule'),
    path('schedule/add/', views.add_schedule, name='add_schedule'),
    path('schedule/edit/<int:id>/', views.edit_schedule, name='edit_schedule'),
    path('schedule/delete/<int:id>/', views.delete_schedule, name='delete_schedule'),

    # Location
    path('location/', views.starting_location, name='location'),
    path("save-location/", views.save_location, name="save_location"),

    # Routing
    path('route/', views.route, name='route'),          # main route page
    path('auto-route/', views.route_old, name='auto_route'),  # auto-route to next class

    # Departure
    path('departure/', views.departure, name='departure'),

    # Misc
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/username/', views.change_username, name='change_username'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/reset/', views.reset_data, name='reset_data'),
    path('datastorage/', views.datastorage, name='datastorage'),
]
