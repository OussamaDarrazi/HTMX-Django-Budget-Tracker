from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Profile)
admin.site.register(DailyBudget)
admin.site.register(Expense)
admin.site.register(PaymentMethod)
