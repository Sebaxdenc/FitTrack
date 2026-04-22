from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import (
    Exercise,
    FavoriteExercise,
    FavoriteMeal,
    Meal,
    MealPlan,
    Routine,
)

from .serializers import (
    ExerciseSerializer,
    FavoriteExerciseSerializer,
    FavoriteMealSerializer,
    MealSerializer,
    MealPlanSerializer,
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
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Exercise.objects.all()
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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

        favorite = FavoriteMeal.objects.filter(
            user=request.user,
            meal=meal
        ).first()

        if favorite:
            favorite.delete()
            return Response({"status": "removed"})
        else:
            FavoriteMeal.objects.create(
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


# ---------------------------------------------------
# 🌍 SOCIAL FEED
# ---------------------------------------------------

class SocialRoutineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista solo rutinas públicas para el feed social.
    Todos los usuarios (autenticados o no) pueden ver las rutinas públicas.
    """
    serializer_class = RoutineSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Routine.objects.filter(is_public=True).prefetch_related("exercises").order_by("-created_at")


class SocialMealPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista solo planes de comidas públicos para el feed social.
    Todos los usuarios (autenticados o no) pueden ver los planes públicos.
    """
    serializer_class = MealPlanSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return MealPlan.objects.filter(is_public=True).prefetch_related("items").order_by("-created_at")


# ---------------------------------------------------
# 🤖 AI RECOMMENDATIONS
# ---------------------------------------------------

class AIRecommendationsView(APIView):
    """
    Endpoint para obtener recomendaciones de IA basadas en las estadísticas del usuario.
    Requiere autenticación.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Recibe las estadísticas del usuario y retorna recomendaciones de IA.
        """
        try:
            from .services import get_ai_recommendations
            
            stats_data = request.data
            
            # Obtener recomendaciones de IA
            recommendations = get_ai_recommendations(stats_data)
            
            return Response({
                "success": True,
                "recommendations": recommendations
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "error": "Error al obtener recomendaciones de IA. Por favor, intenta más tarde."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
