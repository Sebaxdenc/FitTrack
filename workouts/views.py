from django.db.models import Q
from django.shortcuts import render
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Exercise,
    FavoriteExercise,
    FavoriteMeal,
    Meal,
    Routine,
)

from .serializers import (
    ExerciseSerializer,
    FavoriteExerciseSerializer,
    FavoriteMealSerializer,
    MealSerializer,
    RoutineSerializer,
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permite solo lectura a cualquiera.
    Permite modificar solo al dueño (user).
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None)
        return owner == request.user


class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        exercise = self.get_object()
        FavoriteExercise.objects.get_or_create(
            user=request.user,
            exercise=exercise
        )
        return Response({"status": "favorited"})



class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        meal = self.get_object()
        FavoriteMeal.objects.get_or_create(
            user=request.user,
            meal=meal
        )
        return Response({"status": "favorited"})


class RoutineViewSet(viewsets.ModelViewSet):
    serializer_class = RoutineSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly
    ]

    def get_queryset(self):
        user = self.request.user
        queryset = Routine.objects.prefetch_related("exercises")

        if user.is_authenticated:
            return queryset.filter(
                Q(is_public=True) | Q(user=user)
            )

        return queryset.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class FavoriteExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteExercise.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteMealViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteMealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteMeal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Template views
def home_view(request):
    """
    Vista principal de la aplicación.
    Muestra información general y enlaces a las principales secciones.
    """
    return render(request, 'home.html')


def feed_view(request):
    """
    Vista del feed social donde los usuarios pueden ver
    y compartir rutinas y planes de la comunidad.
    """
    return render(request, 'feed.html')