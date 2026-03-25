from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExerciseViewSet,
    FavoriteExerciseViewSet,
    FavoriteMealViewSet,
    MealViewSet,
    RoutineViewSet,
)

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercise')
router.register(r'routines', RoutineViewSet, basename='routine')
router.register(r'meals', MealViewSet)
router.register(r'favorites/exercises', FavoriteExerciseViewSet, basename='favorite-exercises')
router.register(r'favorites/meals', FavoriteMealViewSet, basename='favorite-meals')

urlpatterns = [
    path('', include(router.urls)),
]