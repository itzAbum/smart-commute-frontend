from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import logout
from django.conf import settings

from .models import (
    UserLocation,
    Building,
    Schedule,
    ClassSchedule
)

from .forms import LocationForm
from .utils import geocode_address


# ------------------------------
# BASIC PAGES
# ------------------------------

def index(request):
    return render(request, 'home/index.html')


# ------------------------------
# AUTHENTICATION
# ------------------------------

import requests

API = "https://smart-commute-backend-production.up.railway.app"

def logout_view(request):
    logout(request)
    request.session.flush()  # will clear api_user_id 
    return redirect("login")

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(request, "home/register.html", {"error": "Passwords do not match."})

        # Register in FastAPI backend
        response = requests.post(f"{API}/register", json={
            "username": username,
            "password": password
        })

        if response.status_code == 400:
            return render(request, "home/register.html", {"error": "Username already taken."})

        if response.status_code != 200:
            return render(request, "home/register.html", {"error": "Registration failed. Try again."})

        # Also create in Django for session management
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password)

        return redirect("login")

    return render(request, "home/register.html")


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        response = requests.post(f"{API}/login", json={
            "username": username,
            "password": password
        })

        print("FASTAPI STATUS:", response.status_code)
        print("FASTAPI RESPONSE:", response.json())

        if response.status_code == 200:
            api_user_id = response.json()["user_id"]
            print("GOT API USER ID:", api_user_id)

            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_unusable_password()
                user.save()

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            request.session['api_user_id'] = api_user_id
            request.session.save()
            print("SESSION SET:", request.session.get('api_user_id'))

            return redirect("home")
        else:
            return render(request, "home/login.html", {"error": "Invalid username or password"})

    return render(request, "home/login.html")


@login_required
def settings_view(request):
    return render(request, "home/settings.html")

@login_required
def change_username(request):
    if request.method == "POST":
        new_username = request.POST.get("username")
        api_user_id = request.session.get('api_user_id')
        print("API USER ID:", api_user_id)

        response = requests.put(f"{API}/users/{api_user_id}/username", json={
            "username": new_username
        }, timeout=10)

        if response.status_code == 200:
            # Update Django user too - check for conflicts first
            if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                # Username taken in Django but not FastAPI - just skip Django update
                pass
            else:
                request.user.username = new_username
                request.user.save()
            return render(request, "home/settings.html", {"success_username": "Username updated!"})
        else:
            return render(request, "home/settings.html", {"error_username": "Username already taken."})

    return redirect("settings")

@login_required
def change_password(request):
    if request.method == "POST":
        new_password = request.POST.get("password")
        api_user_id = request.session.get('api_user_id')

        response = requests.put(f"{API}/users/{api_user_id}/password", json={
            "password": new_password
        }, timeout=10)

        if response.status_code == 200:
            # Update Django user too
            request.user.set_password(new_password)
            request.user.save()
            return render(request, "home/settings.html", {"success_password": "Password updated!"})
        else:
            return render(request, "home/settings.html", {"error_password": "Failed to update password."})

    return redirect("settings")

@login_required
def reset_data(request):
    if request.method == "POST":
        api_user_id = request.session.get('api_user_id')
        requests.delete(f"{API}/users/{api_user_id}/schedules", timeout=10)
        return render(request, "home/settings.html", {"success_reset": "All data has been reset."})
    return redirect("settings")

# ------------------------------
# SCHEDULE
# ------------------------------

@login_required
def schedule(request):
    print("API USER ID IN SESSION:", request.session.get('api_user_id'))
    
    schedules = Schedule.objects.filter(user=request.user).order_by("day", "start_time")
    buildings = Building.objects.all()

    return render(request, "home/schedule.html", {
        "schedules": schedules,
        "buildings": buildings
    })


@login_required
def add_schedule(request):
    if request.method == "POST":
        course_name = request.POST.get("course")
        building_id = request.POST.get("building")
        days = request.POST.getlist("days")
        start_time = request.POST.get("start")
        end_time = request.POST.get("end")

        building = Building.objects.get(id=building_id)

        for day in days:
            Schedule.objects.create(
                user=request.user,
                course_name=course_name,
                building=building,
                day=day,
                start_time=start_time,
                end_time=end_time
            )

    return redirect("schedule")


@login_required
def delete_schedule(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    schedule.delete()
    return redirect('schedule')


@login_required
def edit_schedule(request, id):
    schedule_obj = get_object_or_404(Schedule, id=id)

    if request.method == "POST":
        schedule_obj.course_name = request.POST.get("course")
        schedule_obj.day = request.POST.get("day")
        schedule_obj.start_time = request.POST.get("start")
        schedule_obj.end_time = request.POST.get("end")
        schedule_obj.building_id = request.POST.get("building")
        schedule_obj.save()
        return redirect('schedule')

    buildings = Building.objects.all()

    return render(request, "home/edit_schedule.html", {
        "schedule": schedule_obj,
        "buildings": buildings
    })


# ------------------------------
# LOCATION
# ------------------------------

@login_required
def starting_location(request):
    user = request.user

    try:
        location = UserLocation.objects.get(user=user)
    except UserLocation.DoesNotExist:
        location = None

    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)

        if form.is_valid():
            lat, lng = geocode_address(form.cleaned_data['address'])

            UserLocation.objects.update_or_create(
                user=user,
                defaults={
                    'address': form.cleaned_data['address'],
                    'latitude': lat,
                    'longitude': lng,
                }
            )
            return redirect("location")

    else:
        form = LocationForm(instance=location)

    return render(request, "home/location.html", {
        "form": form,
        "saved_location": location.address if location else None
    })


@login_required
def save_location(request):
    if request.method == "POST":
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        UserLocation.objects.update_or_create(
            user=request.user,
            defaults={
                "latitude": lat,
                "longitude": lng,
                "address": "Live Location"
            }
        )

        return JsonResponse({"status": "saved"})


# ------------------------------
# ROUTING
# ------------------------------

@login_required
def route_old(request):
    """Auto-route to next class."""
    next_class = ClassSchedule.objects.filter(
        user=request.user,
        start_time__gte=timezone.now()
    ).order_by('start_time').first()

    if not next_class:
        return render(request, "no_upcoming_class.html")

    building_id = next_class.building.id
    return redirect(f"/departure?building={building_id}")


@login_required
def route(request):
    """Main route page using coordinates."""
    building_id = request.GET.get("building")
    if not building_id:
        return HttpResponse("Error: No building selected.")

    building = Building.objects.get(id=building_id)

    user_location = UserLocation.objects.filter(user=request.user).first()
    if not user_location:
        return HttpResponse("Error: No saved location found.")

    
    return render(request, "home/route.html", {
        "start_lat": user_location.latitude,
        "start_lng": user_location.longitude,
        "end_lat": building.latitude,
        "end_lng": building.longitude,
    })


# ------------------------------
# DEPARTURE TIME
# ------------------------------

@login_required
def departure(request):
    from datetime import datetime

    api_user_id = request.session.get('api_user_id')
    if not api_user_id:
        return redirect('login')

    user_location = UserLocation.objects.filter(user=request.user).first()
    if not user_location or not user_location.latitude:
        return render(request, "home/departure.html", {
            "error": "Please save your starting location first.",
            "next_class": None
        })

    import requests as req

    response = req.get(f"{API}/schedules/{api_user_id}")
    schedules = response.json()

    now = datetime.now()
    today = now.strftime("%A")
    current_time = now.time()

    next_class = None
    next_class_building = None

    for s in schedules:
        if today in s['days']:
            start_dt = datetime.fromisoformat(s['start'])
            if start_dt.time() > current_time:
                building = Building.objects.filter(id=s['building_id']).first()
                next_class = s
                next_class_building = building
                break

    if not next_class:
        return render(request, "home/departure.html", {"next_class": None})

    maps_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    maps_response = req.get(maps_url, params={
        "origins": f"{user_location.latitude},{user_location.longitude}",
        "destinations": f"{next_class_building.latitude},{next_class_building.longitude}",
        "mode": "driving",
        "departure_time": "now",
        "key": "AIzaSyCPpUHaZ651VoNnSKa9uMwKaIWTd7EAhRc"
    }).json()

    try:
        travel_seconds = maps_response['rows'][0]['elements'][0]['duration_in_traffic']['value']
    except (KeyError, IndexError):
        travel_seconds = maps_response['rows'][0]['elements'][0]['duration']['value']

    travel_minutes = round(travel_seconds / 60)
    buffer_minutes = 10

    start_dt = datetime.fromisoformat(next_class['start'])
    recommended_departure = start_dt - timedelta(minutes=travel_minutes + buffer_minutes)

    return render(request, "home/departure.html", {
        "next_class": next_class,
        "next_class_building": next_class_building,
        "start_location": user_location,
        "travel_time_minutes": travel_minutes,
        "buffer_minutes": buffer_minutes,
        "arrival_time": start_dt.strftime("%I:%M %p"),
        "recommended_departure": recommended_departure.strftime("%I:%M %p"),
    })


# ------------------------------
# MISC PAGES
# ------------------------------

def notifications(request):
    return render(request, 'home/notifications.html')

def settings(request):
    return render(request, 'home/settings.html')

def datastorage(request):
    return render(request, 'home/datastorage.html')
