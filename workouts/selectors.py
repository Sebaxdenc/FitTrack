from datetime import date

from django.db.models import Prefetch


from datetime import timedelta, date
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from .models import (
    DailyGoal,
    DailyLog,
    Workout,
    Achievement,
    Routine,
    Exercise,
    RoutineExercise, 
    RoutineSchedule
)

def get_user_exercises(user):
    return Exercise.objects.filter(user=user).order_by("name")


def get_user_routines(user):
    routine_exercises = RoutineExercise.objects.select_related("exercise").order_by("sort_order")
    return (
        Routine.objects.filter(user=user)
        .prefetch_related(Prefetch("exercises", queryset=routine_exercises))
        .order_by("-created_at", "name")
    )


def get_user_routine(user, routine_id):
    return get_user_routines(user).filter(id=routine_id).first()


def get_user_weekly_schedule(user):
    return (
        RoutineSchedule.objects.filter(user=user)
        .select_related("routine")
        .order_by("day_of_week")
    )


def get_todays_routine_schedule(user, target_date=None):
    current_date = target_date or date.today()
    return (
        RoutineSchedule.objects.filter(user=user, day_of_week=current_date.weekday())
        .select_related("routine")
        .first()
    )
    
#TODO: Create a selector to get user stats to visualize in Profile View
def get_user_stats(user):
    """
    Returns comprehensive stats for the user profile/stats dashboard.
    """
    today = date.today()
    last_7_days = today - timedelta(days=6)
    last_30_days = today - timedelta(days=29)
 
    # --- Workout stats ---
    workouts_qs = Workout.objects.filter(user=user)
 
    total_workouts = workouts_qs.count()
 
    workouts_last_7 = workouts_qs.filter(started_at__date__gte=last_7_days)
    workouts_last_30 = workouts_qs.filter(started_at__date__gte=last_30_days)
 
    total_duration_minutes = workouts_qs.aggregate(
        total=Sum("duration_minutes")
    )["total"] or 0
 
    avg_duration_minutes = workouts_qs.aggregate(
        avg=Avg("duration_minutes")
    )["avg"] or 0
 
    # Workouts per day for the last 7 days (for chart)
    workouts_by_day = (
        workouts_last_7
        .values("started_at__date")
        .annotate(count=Count("id"), total_minutes=Sum("duration_minutes"))
        .order_by("started_at__date")
    )
    workouts_by_day_map = {
        str(entry["started_at__date"]): {
            "count": entry["count"],
            "minutes": entry["total_minutes"] or 0,
        }
        for entry in workouts_by_day
    }
    # Fill in zeros for missing days
    weekly_workout_data = []
    for i in range(7):
        day = last_7_days + timedelta(days=i)
        day_str = str(day)
        weekly_workout_data.append({
            "date": day_str,
            "label": day.strftime("%a"),
            "count": workouts_by_day_map.get(day_str, {}).get("count", 0),
            "minutes": workouts_by_day_map.get(day_str, {}).get("minutes", 0),
        })
 
    # --- Calorie stats ---
    logs_qs = DailyLog.objects.filter(user=user)
    logs_last_7 = logs_qs.filter(log_date__gte=last_7_days)
    logs_last_30 = logs_qs.filter(log_date__gte=last_30_days)
 
    avg_calories_consumed_7d = logs_last_7.aggregate(
        avg=Avg("total_calories_consumed")
    )["avg"] or 0
 
    avg_calories_burned_7d = logs_last_7.aggregate(
        avg=Avg("total_calories_burned")
    )["avg"] or 0
 
    # Calories per day for last 7 days (for chart)
    calories_by_day = (
        logs_last_7
        .values("log_date")
        .order_by("log_date")
    )
    calories_map = {str(entry["log_date"]): entry for entry in logs_last_7.values("log_date", "total_calories_consumed", "total_calories_burned")}
 
    weekly_calorie_data = []
    for i in range(7):
        day = last_7_days + timedelta(days=i)
        day_str = str(day)
        entry = calories_map.get(day_str, {})
        weekly_calorie_data.append({
            "date": day_str,
            "label": day.strftime("%a"),
            "consumed": entry.get("total_calories_consumed", 0),
            "burned": entry.get("total_calories_burned", 0),
        })
 
    # --- Daily goals ---
    goals_qs = DailyGoal.objects.filter(user=user)
    total_goals = goals_qs.count()
    completed_goals = goals_qs.filter(completed=True).count()
    goal_completion_rate = round((completed_goals / total_goals * 100) if total_goals > 0 else 0, 1)
 
    # Goals for last 30 days
    goals_last_30 = goals_qs.filter(goal_date__gte=last_30_days)
    goals_by_week = []
    for week in range(4):
        week_start = last_30_days + timedelta(weeks=week)
        week_end = week_start + timedelta(days=6)
        week_goals = goals_last_30.filter(goal_date__gte=week_start, goal_date__lte=week_end)
        completed = week_goals.filter(completed=True).count()
        total = week_goals.count()
        goals_by_week.append({
            "week": f"Sem {week + 1}",
            "completed": completed,
            "total": total,
            "rate": round((completed / total * 100) if total > 0 else 0, 1),
        })
 
    # Today's goal
    todays_goal = goals_qs.filter(goal_date=today).first()
 
    # --- Achievements ---
    achievements = Achievement.objects.filter(user=user).order_by("-achieved_at")[:5]
    total_achievements = Achievement.objects.filter(user=user).count()
 
    # --- Routines ---
    total_routines = Routine.objects.filter(user=user).count()
    scheduled_days = RoutineSchedule.objects.filter(user=user).count()
 
    # --- Current streak (consecutive days with a workout) ---
    streak = 0
    check_date = today
    while True:
        if workouts_qs.filter(started_at__date=check_date).exists():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
 
    return {
        # Workout stats
        "total_workouts": total_workouts,
        "workouts_last_7": workouts_last_7.count(),
        "workouts_last_30": workouts_last_30.count(),
        "total_duration_hours": round(total_duration_minutes / 60, 1),
        "avg_duration_minutes": round(avg_duration_minutes, 1),
        "weekly_workout_data": weekly_workout_data,
        "current_streak": streak,
 
        # Calorie stats
        "avg_calories_consumed_7d": round(avg_calories_consumed_7d),
        "avg_calories_burned_7d": round(avg_calories_burned_7d),
        "weekly_calorie_data": weekly_calorie_data,
 
        # Goals
        "total_goals": total_goals,
        "completed_goals": completed_goals,
        "goal_completion_rate": goal_completion_rate,
        "goals_by_week": goals_by_week,
        "todays_goal": todays_goal,
 
        # Achievements
        "recent_achievements": achievements,
        "total_achievements": total_achievements,
 
        # Routines
        "total_routines": total_routines,
        "scheduled_days": scheduled_days,
    }
    
