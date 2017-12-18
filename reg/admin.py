from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(User)
admin.site.register(Institution)
admin.site.register(System)
admin.site.register(Project)
admin.site.register(ProjectFundingSource)
admin.site.register(ProjectCategory)
admin.site.register(ProjectStatus)

