from django.contrib import admin

from .models import (
    Achievement,
    DailyGoal,
    DailyLog,
    EquipmentRecommendation,
    Exercise,
    ExerciseRating,
    FavoriteExercise,
    FavoriteMeal,
    Meal,
    MealCategory,
    MealLog,
    MealRating,
    Profile,
    Routine,
    RoutineExercise,
    RoutineSchedule,
    Workout,
    WorkoutSet,
)



class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 0

class WorkoutSetInline(admin.TabularInline):
    model = WorkoutSet
    extra = 0

class MealLogInline(admin.TabularInline):
    model = MealLog
    extra = 0

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    inlines = [RoutineExerciseInline]
    list_display = ("name", "user", "goal", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("name", "goal")

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    inlines = [WorkoutSetInline]
    list_display = ("user", "routine", "started_at", "duration_minutes")
    list_filter = ("started_at",)
    search_fields = ("user__username",)

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("name", "calories", "protein_g", "carbs_g", "fat_g", "is_predefined")
    list_filter = ("is_predefined",)
    search_fields = ("name",)

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    inlines = [MealLogInline]
    list_display = ("user", "log_date", "total_calories_consumed", "total_calories_burned")
    list_filter = ("log_date",)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "achieved_at")
    search_fields = ("title",)

admin.site.register(Profile)
admin.site.register(Exercise)
admin.site.register(ExerciseRating)
admin.site.register(FavoriteExercise)
admin.site.register(FavoriteMeal)
admin.site.register(MealRating)
admin.site.register(DailyGoal)
admin.site.register(WorkoutSet)
admin.site.register(EquipmentRecommendation)
admin.site.register(RoutineSchedule)
admin.site.register(MealCategory)
