from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user}"

class DailyGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_goals")
    goal_date = models.DateField()
    burn_calories_target = models.IntegerField()
    burn_calories_current = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "goal_date")

    def __str__(self):
        return f"{self.user} - {self.goal_date}"
    
class Achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=255)
    description = models.TextField()
    achieved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Meal(models.Model):
    name = models.CharField(max_length=255)
    calories = models.IntegerField()
    carbs_g = models.IntegerField()
    protein_g = models.IntegerField()
    fat_g = models.IntegerField()
    is_predefined = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    
class FavoriteMeal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_meals")
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "meal")
        
class MealRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="ratings")
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "meal")
        
class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_logs")
    log_date = models.DateField()
    total_calories_consumed = models.IntegerField(default=0)
    total_calories_burned = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "log_date")
        
class MealLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name="meals")
    eaten_at = models.DateTimeField()
    quantity = models.FloatField()
    meal_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user} - {self.meal}"
    
class Exercise(models.Model):
    name = models.CharField(max_length=255)
    muscle_group = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    equipment = models.CharField(max_length=255, blank=True)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return self.name

class FavoriteExercise(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_exercises")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise")

class ExerciseRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="ratings")
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "exercise")

class Routine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routines")
    name = models.CharField(max_length=255)
    goal = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
class RoutineExercise(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE, related_name="exercises")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sort_order = models.IntegerField()
    target_sets = models.IntegerField()
    target_reps = models.IntegerField()
    rest_seconds = models.IntegerField()

    class Meta:
        ordering = ["sort_order"]
        unique_together = ("routine", "sort_order")

class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workouts")
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE)
    started_at = models.DateTimeField()
    duration_minutes = models.IntegerField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.started_at}"
    
    
class WorkoutSet(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name="sets")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    set_number = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField()
    rest_seconds = models.IntegerField()
    is_warmup = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.workout} - Set {self.set_number}"

class EquipmentRecommendation(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField()
    link = models.URLField()

    def __str__(self):
        return self.name        
