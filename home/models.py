from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.db import models




class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.address}"
    


class Building(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name
    
class ShuttleStop(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

class ShuttleRoute(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, default="#000000")
    stops = models.ManyToManyField(ShuttleStop, related_name="routes")

    def __str__(self):
        return self.name

class ClassSchedule(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True)
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course_name} ({self.day})"
    

class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100)
    building = models.ForeignKey("home.Building", on_delete=models.CASCADE)
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course_name} ({self.day})"
