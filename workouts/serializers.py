from django.contrib.auth import get_user_model
from rest_framework import serializers

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
    MealLog,
    MealPlan,
    MealItem,
    MealRating,
    Profile,
    Routine,
    RoutineExercise,
    Workout,
    WorkoutSet,
)

User = get_user_model()


# ---------------------------------------------------
# 👤 USER
# ---------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = ["id", "username", "email"]


# ---------------------------------------------------
# 👤 PROFILE
# ---------------------------------------------------

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "avatar_url", "bio", "updated_at"]
        read_only_fields = ["id", "user", "updated_at"]


# ---------------------------------------------------
# 🏋️ EXERCISE
# ---------------------------------------------------

class ExerciseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "id",
            "user",
            "name",
            "muscle_group",
            "description",
            "image_url",
            "equipment_photo",
            "display_image_url",
        ]
        read_only_fields = ["id", "user"]


class ExerciseRatingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ExerciseRating
        fields = ["id", "user", "exercise", "score", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class FavoriteExerciseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteExercise
        fields = ["id", "user", "exercise", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# ---------------------------------------------------
# 🥗 MEAL
# ---------------------------------------------------

class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = [
            "id",
            "name",
            "calories",
            "carbs_g",
            "protein_g",
            "fat_g",
            "is_predefined",
        ]
        read_only_fields = ["id"]


class MealRatingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MealRating
        fields = ["id", "user", "meal", "score", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class FavoriteMealSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteMeal
        fields = ["id", "user", "meal", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# ---------------------------------------------------
# 📋 ROUTINES
# ---------------------------------------------------

class RoutineExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutineExercise
        fields = [
            "id",
            "sort_order",
            "exercise",
            "target_sets",
            "target_reps",
            "rest_seconds",
        ]
        read_only_fields = ["id"]


class RoutineSerializer(serializers.ModelSerializer):
    exercises = RoutineExerciseSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.CharField(source='user.username', read_only=True)
    estimated_calories = serializers.SerializerMethodField()

    class Meta:
        model = Routine
        fields = [
            "id",
            "user",
            "author",
            "name",
            "goal",
            "description",
            "is_public",
            "created_at",
            "exercises",
            "estimated_calories",
        ]
        read_only_fields = ["id", "user", "created_at", "estimated_calories"]

    def get_estimated_calories(self, obj):
        return obj.estimated_calories()

    def validate_exercises(self, value):
        orders = [item["sort_order"] for item in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError(
                "Exercise order must be unique within a routine"
            )
        return value

    def create(self, validated_data):
        exercises_data = validated_data.pop("exercises", [])
        routine = Routine.objects.create(**validated_data)

        routine_exercises = [
            RoutineExercise(routine=routine, **exercise)
            for exercise in exercises_data
        ]
        RoutineExercise.objects.bulk_create(routine_exercises)

        return routine

    def update(self, instance, validated_data):
        exercises_data = validated_data.pop("exercises", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if exercises_data is not None:
            instance.exercises.all().delete()

            routine_exercises = [
                RoutineExercise(routine=instance, **exercise)
                for exercise in exercises_data
            ]
            RoutineExercise.objects.bulk_create(routine_exercises)

        return instance


# ---------------------------------------------------
# 🏋️ WORKOUTS
# ---------------------------------------------------

class WorkoutSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSet
        fields = [
            "id",
            "exercise",
            "set_number",
            "reps",
            "weight",
            "rest_seconds",
            "is_warmup",
        ]
        read_only_fields = ["id"]


class WorkoutSerializer(serializers.ModelSerializer):
    sets = WorkoutSetSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Workout
        fields = [
            "id",
            "user",
            "routine",
            "started_at",
            "duration_minutes",
            "notes",
            "sets",
        ]
        read_only_fields = ["id", "user"]

    def create(self, validated_data):
        sets_data = validated_data.pop("sets", [])
        workout = Workout.objects.create(**validated_data)

        workout_sets = [
            WorkoutSet(workout=workout, **set_data)
            for set_data in sets_data
        ]
        WorkoutSet.objects.bulk_create(workout_sets)

        return workout


# ---------------------------------------------------
# 📊 DAILY LOGS
# ---------------------------------------------------

class MealLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealLog
        fields = ["id", "meal", "daily_log", "eaten_at", "quantity", "meal_type"]
        read_only_fields = ["id"]


class DailyLogSerializer(serializers.ModelSerializer):
    meals = MealLogSerializer(many=True, read_only=True)

    class Meta:
        model = DailyLog
        fields = [
            "id",
            "user",
            "log_date",
            "total_calories_consumed",
            "total_calories_burned",
            "meals",
        ]
        read_only_fields = ["id"]


# ---------------------------------------------------
# 🎯 DAILY GOALS
# ---------------------------------------------------

class DailyGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyGoal
        fields = [
            "id",
            "user",
            "goal_date",
            "burn_calories_target",
            "burn_calories_current",
            "completed",
        ]
        read_only_fields = ["id"]


# ---------------------------------------------------
# 🏆 ACHIEVEMENTS
# ---------------------------------------------------

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "user", "title", "description", "achieved_at"]
        read_only_fields = ["id", "achieved_at"]


# ---------------------------------------------------
# 🛒 EQUIPMENT
# ---------------------------------------------------

class EquipmentRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentRecommendation
        fields = ["id", "name", "category", "description", "link"]
        read_only_fields = ["id"]


# ---------------------------------------------------
# 🍽️ MEAL PLANS
# ---------------------------------------------------

class MealItemSerializer(serializers.ModelSerializer):
    meal_name = serializers.CharField(source='meal.name', read_only=True)
    meal_calories = serializers.IntegerField(source='meal.calories', read_only=True)

    class Meta:
        model = MealItem
        fields = [
            "id",
            "meal",
            "meal_name",
            "meal_calories",
            "quantity",
            "meal_type",
            "sort_order",
        ]
        read_only_fields = ["id"]


class MealPlanSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.CharField(source='user.username', read_only=True)
    total_calories = serializers.SerializerMethodField()

    class Meta:
        model = MealPlan
        fields = [
            "id",
            "user",
            "author",
            "name",
            "description",
            "is_public",
            "created_at",
            "updated_at",
            "items",
            "total_calories",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "total_calories"]

    def get_total_calories(self, obj):
        return obj.total_calories()
