from math import pi
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from bokeh.transform import cumsum
from BudgetTrackApp.models import DailyBudget, Expense, Profile
from datetime import datetime
from django.db.models import Sum, Min, F, Max
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.embed import components
from django.middleware import csrf

# Create your views here.
FONT_FAMILY = "Abel"
COLORS = ["#be1e2d","#21409a","#ffde17","#cccccc"]

def __setup_daily_budget(profile, date):
    """
    retrieve todays budget or create one in case its not created
    """
    try:
        todays_budget = DailyBudget.objects.get(date=date, profile=profile)
    except DailyBudget.DoesNotExist:
        todays_budget = DailyBudget.objects.create(profile=profile, date=date, starting_budget=profile.daily_amount, total_expenditure=0)
    return todays_budget

def __stats_line_chart(profile):
    today = timezone.now().date()
    budgets = DailyBudget.objects.filter(profile=profile, date__gte=today.replace(day=1)).order_by("-date")
    trackables = ["Starting budget", "Expenditure", "Remaining"]
    starting_budgets = [bdg.starting_budget for bdg in budgets]
    expenditures = [bdg.total_expenditure for bdg in budgets]
    remainings = [bdg.starting_budget - bdg.total_expenditure for bdg in budgets]
    days = [datetime(bdg.date.year, bdg.date.month, bdg.date.day) for bdg in budgets]
    colors = COLORS[:len(trackables)]
    cds = ColumnDataSource(data={"days":[days for _ in range(len(trackables))], "stats": [starting_budgets, expenditures, remainings], "trackables":trackables, "colors":colors})
    
    lchart = figure( sizing_mode="stretch_both", x_axis_type="datetime", title="Your progress")
    lchart.title.align = "center"
    lchart.title.text_font_size = "1rem"
    lchart.title.text_font = FONT_FAMILY
    lchart.xaxis.axis_label_text_font = FONT_FAMILY
    lchart.yaxis.axis_label_text_font = FONT_FAMILY
    lchart.multi_line(source=cds, xs="days", ys="stats", line_width=2, legend_group="trackables", line_color="colors")
    lchart.legend.location = "top_left"
    
    return components(lchart)

def __stats_pie_chart(profile):
    inf = dict()
    today = timezone.now().date()
    expenses = Expense.objects.filter(daily__profile=profile, date_time__date = today).values('title').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    overall_total = sum(expense["total_amount"] for expense in expenses)
    for expense in expenses:
        inf[expense["title"]] = 100 * expense["total_amount"]/overall_total
    #grooming to limit to 4 fields
    if len(inf)>4:
        others = list(inf.values())[3:]
        top_ones = list(inf.items())[:3]
        sum_others = sum(val for val in others)
        inf = dict([*top_ones, ("Others", sum_others)])


    data = dict(
    countries=list(inf.keys()),
    values=list(inf.values())
    )
    data['angle'] = [val / sum(data['values']) * 2 * pi for val in data['values']]
    data['color'] = COLORS[:len(inf)]
    source = ColumnDataSource(data)
    #The chart and styling
    pie_chart = figure(title="Highest expenses", sizing_mode="stretch_both", x_range=(-0.5, 1.0),toolbar_location=None, tools="hover", tooltips="@countries: @values %")
    pie_chart.wedge(x=0, y=1, radius=0.4,start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
    line_color="white", fill_color='color', legend_field='countries', source=source)
    pie_chart.title.text_font = FONT_FAMILY
    pie_chart.xaxis.axis_label_text_font = FONT_FAMILY
    pie_chart.yaxis.axis_label_text_font = FONT_FAMILY
    pie_chart.legend.label_text_font = FONT_FAMILY
    pie_chart.axis.axis_label = None
    pie_chart.axis.visible = False
    pie_chart.grid.grid_line_color = None

    return components(pie_chart)



def __get_stats(budget):
    budget_date = budget.date
    profile = budget.profile
    starting_budget = budget.starting_budget
    current_expenditure = budget.total_expenditure
    remaining= budget.starting_budget - budget.total_expenditure
    current_month_expenditure = DailyBudget.objects.filter(date__year=budget_date.year,date__month=budget_date.month, profile=profile).aggregate(total_expenditure=Sum('total_expenditure'))['total_expenditure']
    best_month_expenditure = DailyBudget.objects.filter(profile=profile).values('date__year', 'date__month').annotate(total_expenditure=Sum('total_expenditure')).aggregate(best_expenditure = Min("total_expenditure"))["best_expenditure"]
    best_remaining = DailyBudget.objects.filter(profile=profile).aggregate(max_remaining_budget=Max(F('starting_budget') - F('total_expenditure')))['max_remaining_budget']
        
    return  starting_budget,    current_expenditure,    remaining,   current_month_expenditure,    best_month_expenditure,best_remaining

@receiver(post_save, sender=Expense)
def __add_budget_total_on_expense_creation(sender , instance, created, **kwargs):
    if created:
        instance.daily.total_expenditure += float(instance.amount)
        instance.daily.save()

@receiver(pre_delete, sender=Expense)
def __subtract_budget_total_on_expense_creation(sender , instance,**kwargs):
        instance.daily.total_expenditure -= float(instance.amount)
        instance.daily.save()

@login_required
def home(request):
    
    if request.user.is_authenticated:
        today = timezone.now().date()
        profile = request.user.profile
        todays_budget = __setup_daily_budget(profile, today)
        latest_expenses = Expense.objects.filter(daily = todays_budget).order_by("-date_time")[:10]
        starting_budget,current_expenditure, remaining, current_month_expenditure,best_month_expenditure,best_remaining = __get_stats(todays_budget)
        #The line chart 
        lchart_script, lchart_div = __stats_line_chart(profile)
        #The pie chart
        pie_chart_script, pie_chart_div = __stats_pie_chart(profile)


    return render(request, 'index.html', {
        "starting_budget":starting_budget, 
        "current_expenditure":current_expenditure, 
        "remaining": remaining,
        "latest_expenses": latest_expenses, 
        "current_month_expenditure": current_month_expenditure, 
        "best_month_expenditure":best_month_expenditure, 
        "best_remaining":best_remaining, 
        "line_chart_script": lchart_script, "line_chart_div": lchart_div, 
        "pie_chart_script":pie_chart_script, "pie_chart_div":pie_chart_div
        })




def save_expense(request):
    profile = Profile.objects.get(user=request.user)
    todays_budget = DailyBudget.objects.filter(date=timezone.now().date(), profile=profile).first()
    title = request.POST.get("expense_title")
    amount = request.POST.get("expense_amount", 0)
    date_time = request.POST.get("expense_date_time", timezone.now())
    note = request.POST.get("expense_note", "")
    payment_method_id = request.POST.get("expense_payment_method", 1)

    expense = Expense.objects.create(title=title, amount=amount, date_time=date_time, note=note, payment_method_id=payment_method_id, daily=todays_budget)
    
    response_body = render(request, "components/expense_card.html", {"expense": expense})
    response = HttpResponse()
    response["HX-Trigger"] = "display-stats"
    response.content = response_body
    return response

def add_expense(request):
    return render(request, "components/expense_card.html")



def edit_starting_budget(request):
    saving_url = reverse("save_budget")
    today = timezone.now().date()
    todays_budget = __setup_daily_budget(request.user.profile, today)
    csrf_token = csrf.get_token(request)
    return HttpResponse("<input name='starting-budget' style='width:auto;' size='4' type='text' hx-post='" + saving_url + "' hx-trigger='blur'  class='amt input-field' hx-swap='outerHTML' hx-headers='{\"X-CSRFToken\": \"" + csrf_token + "\"}' value = '" + str(todays_budget.starting_budget) + "' autofocus>")

def save_starting_budget(request):
    today = timezone.now().date()
    todays_budget = __setup_daily_budget(request.user.profile, today)
    new_budget_amt = request.POST.get("starting-budget", todays_budget.starting_budget)
    try:
        float(new_budget_amt)
        todays_budget.starting_budget = new_budget_amt
        todays_budget.save()
    except ValueError:
        pass
    response = HttpResponse()
    response["HX-Trigger"] = "display-stats"
    return response


def get_expenses(request, date_time):
    expenses = Expense.objects.filter(daily__profile = request.user.profile, date_time__lt=date_time).order_by("-date_time")[:10]
    return render(request, "components/expense_card_list.html", {"latest_expenses":expenses})

def display_stats(request):
    today = timezone.now().date()
    profile = Profile.objects.get(user=request.user)
    todays_budget = __setup_daily_budget(profile, today)
    starting_budget,current_expenditure, remaining,  current_month_expenditure,best_month_expenditure,best_remaining = __get_stats(todays_budget)
    return render(request, 'components/stats.html', {
        "starting_budget":starting_budget, 
        "current_expenditure":current_expenditure, 
        "remaining": remaining,
        "current_month_expenditure": current_month_expenditure, 
        "best_month_expenditure":best_month_expenditure, 
        "best_remaining":best_remaining
    })


def display_line_chart(request):
    profile = request.user.profile
    lchart_script, lchart_div = __stats_line_chart(profile)
    return render(request, "components/line_chart.html", {"line_chart_script":lchart_script, "line_chart_div":lchart_div})


def display_pie_chart(request):
    profile = request.user.profile
    pie_chart_script, pie_chart_div = __stats_pie_chart(profile)
    return render(request, "components/pie_chart.html", {"pie_chart_script":pie_chart_script, "pie_chart_div":pie_chart_div})


def delete_expense(request, expense_id):
    if request.method=="POST":
        expense_to_delete = Expense.objects.get(id=expense_id)
        expense_to_delete.delete()
        response = HttpResponse(status=200)
        response["HX-Trigger"] = "display-stats"
        return response



def deletion_view(request):
    """
    This view is used for htmx front end deletion requests since they don't require a response
    """
    return HttpResponse(status=200)