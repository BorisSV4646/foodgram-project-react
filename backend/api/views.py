from rest_framework.response import Response
from api.serializers import (TagSerializer, IngredientSerializer,
                             RecipeSerializer, CreateRecipeSerializer,
                             ShortRecipeSerializer, FollowSerializer,)
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from recipes.models import (Favorite, Tag, Ingredient,
                            Recipe, Shopping, Follow,
                            Ingredient_amount)
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from djoser.views import UserViewSet
from api.paginators import LimitPagePagination
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from api.filters import IngredientSearchFilter, RecipeFilter
from django_filters.rest_framework import DjangoFilterBackend

User = get_user_model()
