from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Tag(TimeStampedModel):
	name = models.CharField(max_length=64, unique=True)

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return self.name


class Exercise(TimeStampedModel):
	class Difficulty(models.TextChoices):
		BEGINNER = 'beginner', 'Beginner'
		INTERMEDIATE = 'intermediate', 'Intermediate'
		ADVANCED = 'advanced', 'Advanced'

	name = models.CharField(max_length=128, unique=True)
	muscle_group = models.CharField(max_length=128)
	equipment = models.CharField(max_length=128, blank=True)
	difficulty = models.CharField(
		max_length=16,
		choices=Difficulty.choices,
		default=Difficulty.BEGINNER,
	)
	instructions = models.TextField(blank=True)
	tags = models.ManyToManyField(Tag, related_name='exercises', blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return self.name


class WorkoutRoutine(TimeStampedModel):
	class Level(models.TextChoices):
		BEGINNER = 'beginner', 'Beginner'
		INTERMEDIATE = 'intermediate', 'Intermediate'
		ADVANCED = 'advanced', 'Advanced'

	creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
	title = models.CharField(max_length=128)
	description = models.TextField(blank=True)
	duration_minutes = models.PositiveIntegerField(default=30)
	level = models.CharField(max_length=16, choices=Level.choices, default=Level.BEGINNER)
	is_public = models.BooleanField(default=True)
	tags = models.ManyToManyField(Tag, related_name='routines', blank=True)

	class Meta:
		ordering = ['-created_at']
		unique_together = ('creator', 'title')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return self.title


class WorkoutStep(models.Model):
	routine = models.ForeignKey(WorkoutRoutine, on_delete=models.CASCADE, related_name='steps')
	exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='steps')
	order = models.PositiveIntegerField()
	sets = models.PositiveIntegerField(default=3)
	reps = models.PositiveIntegerField(default=10)
	weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
	rest_seconds = models.PositiveIntegerField(default=60)

	class Meta:
		ordering = ['order']
		unique_together = ('routine', 'order')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return f"{self.routine.title} - step {self.order}"


class Meal(TimeStampedModel):
	name = models.CharField(max_length=128, unique=True)
	description = models.TextField(blank=True)
	calories = models.PositiveIntegerField(default=0)
	protein_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	carbs_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	fats_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	tags = models.ManyToManyField(Tag, related_name='meals', blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return self.name


class MealPlan(TimeStampedModel):
	creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
	title = models.CharField(max_length=128)
	description = models.TextField(blank=True)
	is_public = models.BooleanField(default=True)
	tags = models.ManyToManyField(Tag, related_name='meal_plans', blank=True)

	class Meta:
		ordering = ['-created_at']
		unique_together = ('creator', 'title')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return self.title


class MealItem(models.Model):
	plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='items')
	meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='plan_items')
	order = models.PositiveIntegerField(default=1)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ['order']
		unique_together = ('plan', 'order')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return f"{self.plan.title} - item {self.order}"


class FavoriteRoutine(TimeStampedModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_routines')
	routine = models.ForeignKey(WorkoutRoutine, on_delete=models.CASCADE, related_name='favorites')

	class Meta:
		unique_together = ('user', 'routine')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return f"{self.user} -> {self.routine}"


class FavoriteMeal(TimeStampedModel):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_meals')
	meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='favorites')

	class Meta:
		unique_together = ('user', 'meal')

	def __str__(self) -> str:  # pragma: no cover - simple repr
		return f"{self.user} -> {self.meal}"
