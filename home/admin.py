from django.contrib import admin
from .models import Building, ShuttleStop, ShuttleRoute, ClassSchedule

admin.site.register(Building)
admin.site.register(ShuttleStop)
admin.site.register(ShuttleRoute)
admin.site.register(ClassSchedule)
