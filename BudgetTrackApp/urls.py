from django.urls import path
from BudgetTrackApp import views
urlpatterns = [
    path('', views.home, name='home'),
    path('save_expense', views.save_expense, name="save_expense"),
    path('add_expense', views.add_expense, name="add_expense"),
    path('delete', views.deletion_view, name="deletion_view"),
    path('edit-starting-budget', views.edit_starting_budget, name="edit_budget"),
    path('save-starting-budget', views.save_starting_budget, name="save_budget"),
    path("display-stats",  views.display_stats, name="display_stats"),
    path("display-line-chart",  views.display_line_chart, name="display_line_chart"),
    path("display-pie-chart",  views.display_pie_chart, name="display_pie_chart"),
    path("delete_expense/<int:expense_id>", views.delete_expense, name="delete_expense"),
    path("get-expenses/<str:date_time>", views.get_expenses, name="get_expenses")
]