from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
# Create your models here.

"""
These are the preferences for the user profile
"""
class PaymentMethod(models.Model):
    """
    in Addition to the payment methods we Add ourselves (Cash, Paypal, Venmo, ...ETC) `thus te many to many relationship`
    The user has the option to add their own usual payment method 
    """
    title = models.CharField(max_length = 50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    daily_amount = models.FloatField()
    payment_methods = models.ManyToManyField(PaymentMethod)
    currency = models.TextField()
    def __str__(self):
        return self.user.username


class UsualExpense(models.Model):
    """
    The usual expenses that the user has, groceries, bills ETC.
    """
    title = models.CharField(max_length = 50, unique=True)
    usual_payment_method = models.ForeignKey(PaymentMethod, null=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Subscription(models.Model):
    """
    Expenses that are billed on a regular basis
    """
    title = models.CharField(max_length = 50, unique=True)
    platform = models.CharField(max_length = 50)
    billed_every = models.PositiveSmallIntegerField()
    payment_method = models.ForeignKey(PaymentMethod, null=True, on_delete=models.SET_NULL)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)



class DailyBudget(models.Model):
    date = models.DateField(default=datetime.today)
    starting_budget = models.FloatField(validators=[MinValueValidator(0.0)],)
    total_expenditure = models.FloatField(validators=[MinValueValidator(0.0)],)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date}: {self.starting_budget} : {self.profile.user.username}" 
    
    class Meta:
        unique_together = ('date', 'profile',)

class Expense(models.Model):
    title = models.CharField(max_length = 50)
    amount = models.FloatField(validators=[MinValueValidator(0.0)],)
    payment_method = models.ForeignKey(PaymentMethod, null=True, on_delete=models.SET_NULL)
    date_time = models.DateTimeField(default=datetime.now)
    note = models.TextField(blank=True, null=True)
    daily = models.ForeignKey(DailyBudget, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date_time} : {self.title} : {self.amount}"
    



