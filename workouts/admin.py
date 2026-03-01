from django.contrib import admin

from .models import (
	Exercise,
	FavoriteMeal,
	FavoriteRoutine,
	Meal,
	MealItem,
	MealPlan,
	Tag,
	WorkoutRoutine,
	WorkoutStep,
)


class WorkoutStepInline(admin.TabularInline):
	model = WorkoutStep
	extra = 0


class WorkoutRoutineAdmin(admin.ModelAdmin):
	inlines = [WorkoutStepInline]
	list_display = ('title', 'creator', 'level', 'is_public', 'created_at')
	list_filter = ('level', 'is_public', 'tags')
	search_fields = ('title', 'description')


class MealItemInline(admin.TabularInline):
	model = MealItem
	extra = 0


class MealPlanAdmin(admin.ModelAdmin):
	inlines = [MealItemInline]
	list_display = ('title', 'creator', 'is_public', 'created_at')
	list_filter = ('is_public', 'tags')
	search_fields = ('title', 'description')


admin.site.register(Tag)
admin.site.register(Exercise)
admin.site.register(WorkoutRoutine, WorkoutRoutineAdmin)
admin.site.register(Meal)
admin.site.register(MealPlan, MealPlanAdmin)
admin.site.register(FavoriteRoutine)
admin.site.register(FavoriteMeal)
