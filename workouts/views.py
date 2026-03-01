from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
	Exercise,
	FavoriteMeal,
	FavoriteRoutine,
	Meal,
	MealPlan,
	Tag,
	WorkoutRoutine,
)
from .serializers import (
	ExerciseSerializer,
	FavoriteMealSerializer,
	FavoriteRoutineSerializer,
	MealPlanSerializer,
	MealSerializer,
	TagSerializer,
	WorkoutRoutineSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.method in permissions.SAFE_METHODS:
			return True
		owner = getattr(obj, 'creator', None)
		return owner == request.user


class TagViewSet(viewsets.ModelViewSet):
	queryset = Tag.objects.all()
	serializer_class = TagSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ExerciseViewSet(viewsets.ModelViewSet):
	queryset = Exercise.objects.prefetch_related('tags').all()
	serializer_class = ExerciseSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class WorkoutRoutineViewSet(viewsets.ModelViewSet):
	serializer_class = WorkoutRoutineSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

	def get_queryset(self):
		user = self.request.user
		if user.is_authenticated:
			return WorkoutRoutine.objects.prefetch_related('tags', 'steps').filter(
				Q(is_public=True) | Q(creator=user)
			)
		return WorkoutRoutine.objects.prefetch_related('tags', 'steps').filter(is_public=True)

	def perform_create(self, serializer):
		serializer.save(creator=self.request.user)

	@action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
	def favorite(self, request, pk=None):
		routine = self.get_object()
		FavoriteRoutine.objects.get_or_create(user=request.user, routine=routine)
		return Response({'status': 'favorited'})


class MealViewSet(viewsets.ModelViewSet):
	queryset = Meal.objects.prefetch_related('tags').all()
	serializer_class = MealSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]

	@action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
	def favorite(self, request, pk=None):
		meal = self.get_object()
		FavoriteMeal.objects.get_or_create(user=request.user, meal=meal)
		return Response({'status': 'favorited'})


class MealPlanViewSet(viewsets.ModelViewSet):
	serializer_class = MealPlanSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

	def get_queryset(self):
		user = self.request.user
		if user.is_authenticated:
			return MealPlan.objects.prefetch_related('tags', 'items').filter(
				Q(is_public=True) | Q(creator=user)
			)
		return MealPlan.objects.prefetch_related('tags', 'items').filter(is_public=True)

	def perform_create(self, serializer):
		serializer.save(creator=self.request.user)


class FavoriteRoutineViewSet(viewsets.ModelViewSet):
	serializer_class = FavoriteRoutineSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return FavoriteRoutine.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class FavoriteMealViewSet(viewsets.ModelViewSet):
	serializer_class = FavoriteMealSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return FavoriteMeal.objects.filter(user=self.request.user)

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)
