from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ExerciseViewSet,
    FavoriteMealViewSet,
    FavoriteRoutineViewSet,
    MealPlanViewSet,
    MealViewSet,
    TagViewSet,
    WorkoutRoutineViewSet,
)

router = DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'routines', WorkoutRoutineViewSet, basename='routine')
router.register(r'meals', MealViewSet)
router.register(r'meal-plans', MealPlanViewSet, basename='meal-plan')
router.register(r'favorites/routines', FavoriteRoutineViewSet, basename='favorite-routines')
router.register(r'favorites/meals', FavoriteMealViewSet, basename='favorite-meals')

urlpatterns = [
    path('', include(router.urls)),
]
