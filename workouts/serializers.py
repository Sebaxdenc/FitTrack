from django.contrib.auth import get_user_model
from rest_framework import serializers

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


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Exercise
        fields = [
            'id',
            'name',
            'muscle_group',
            'equipment',
            'difficulty',
            'instructions',
            'tags',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        exercise = Exercise.objects.create(**validated_data)
        self._set_tags(exercise, tags)
        return exercise

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            self._set_tags(instance, tags)
        return instance

    def _set_tags(self, instance, tags_data):
        tag_objs = [Tag.objects.get_or_create(name=tag['name'])[0] for tag in tags_data]
        instance.tags.set(tag_objs)


class WorkoutStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutStep
        fields = ['id', 'order', 'exercise', 'sets', 'reps', 'weight_kg', 'rest_seconds']
        read_only_fields = ['id']


class WorkoutRoutineSerializer(serializers.ModelSerializer):
    steps = WorkoutStepSerializer(many=True)
    tags = TagSerializer(many=True, required=False)
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = WorkoutRoutine
        fields = [
            'id',
            'creator',
            'title',
            'description',
            'duration_minutes',
            'level',
            'is_public',
            'tags',
            'steps',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        steps = validated_data.pop('steps', [])
        routine = WorkoutRoutine.objects.create(**validated_data)
        self._set_tags(routine, tags)
        self._set_steps(routine, steps)
        return routine

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        steps = validated_data.pop('steps', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            self._set_tags(instance, tags)
        if steps is not None:
            instance.steps.all().delete()
            self._set_steps(instance, steps)
        return instance

    def validate_steps(self, value):
        orders = [step['order'] for step in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError('Step order must be unique within a routine')
        return value

    def _set_tags(self, routine, tags_data):
        tag_objs = [Tag.objects.get_or_create(name=tag['name'])[0] for tag in tags_data]
        routine.tags.set(tag_objs)

    def _set_steps(self, routine, steps_data):
        steps = [WorkoutStep(routine=routine, **step) for step in steps_data]
        WorkoutStep.objects.bulk_create(steps)


class MealSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Meal
        fields = [
            'id',
            'name',
            'description',
            'calories',
            'protein_g',
            'carbs_g',
            'fats_g',
            'tags',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        meal = Meal.objects.create(**validated_data)
        self._set_tags(meal, tags)
        return meal

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            self._set_tags(instance, tags)
        return instance

    def _set_tags(self, instance, tags_data):
        tag_objs = [Tag.objects.get_or_create(name=tag['name'])[0] for tag in tags_data]
        instance.tags.set(tag_objs)


class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = ['id', 'order', 'meal', 'notes']
        read_only_fields = ['id']


class MealPlanSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True)
    tags = TagSerializer(many=True, required=False)
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MealPlan
        fields = [
            'id',
            'creator',
            'title',
            'description',
            'is_public',
            'tags',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def validate_items(self, value):
        orders = [item['order'] for item in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError('Item order must be unique within a plan')
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        items = validated_data.pop('items', [])
        plan = MealPlan.objects.create(**validated_data)
        self._set_tags(plan, tags)
        self._set_items(plan, items)
        return plan

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        items = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            self._set_tags(instance, tags)
        if items is not None:
            instance.items.all().delete()
            self._set_items(instance, items)
        return instance

    def _set_tags(self, plan, tags_data):
        tag_objs = [Tag.objects.get_or_create(name=tag['name'])[0] for tag in tags_data]
        plan.tags.set(tag_objs)

    def _set_items(self, plan, items_data):
        items = [MealItem(plan=plan, **item) for item in items_data]
        MealItem.objects.bulk_create(items)


class FavoriteRoutineSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteRoutine
        fields = ['id', 'user', 'routine', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FavoriteMealSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FavoriteMeal
        fields = ['id', 'user', 'meal', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']
