from rest_framework.response import Response
from api.serializers import (TagSerializer, IngredientSerializer,
                             RecipeSerializer, CreateRecipeSerializer,
                             ShortRecipeSerializer, FollowSerializer,)
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from recipes.models import (Favourite, Tag, Ingredient,
                            Recipe, ShoppingCart, Follow,
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


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class CustomUserViewSet(UserViewSet):
    pagination_class = LimitPagePagination

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        follow = Follow.objects.filter(user=request.user)
        pages = self.paginate_queryset(follow)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        if request.method == 'POST':
            return self.add_obj(request, id)
        elif request.method == 'DELETE':
            return self.delete_obj(request, id)

    def add_obj(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.user == author:
            return Response(
                {'errors': 'Вы не можете подписываться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST)
        obj = Follow.objects.filter(user=request.user, author=author)
        if obj.exists():
            return Response(
                {'errors': 'Вы уже подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        follow = Follow.objects.create(user=request.user, author=author)
        serializer = FollowSerializer(follow, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, request,  id):
        author = get_object_or_404(User, id=id)
        obj = Follow.objects.filter(user=request.user, author=author)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'ошибка отписки!'},
                        status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagePagination
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(Favourite, request.user, pk)
        elif request.method == 'DELETE':
            return self.delete_obj(Favourite, request.user, pk)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(ShoppingCart, request.user, pk)
        elif request.method == 'DELETE':
            return self.delete_obj(ShoppingCart, request.user, pk)

    @action(detail=False, methods=('get',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping.exists():
            return Response({'errors': 'Ваш список покупок пуст.'},
                            status=status.HTTP_400_BAD_REQUEST)
        ingredients = Ingredient_amount.objects.filter(
            recipe__shopping__user=user).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
                amount=Sum('amount'))
        filename = f'{user.username}_shopping_list.txt'
        shopping_list = (
            f'Список покупок({user.first_name})\n'
        )
        for ing in ingredients:
            shopping_list += (f'{ing["ingredient__name"]}: {ing["amount"]} '
                              f'{ing["ingredient__measurement_unit"]}\n')
        shopping_list += '\nFoodgram'
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def add_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            return Response({'errors': 'Рецепт уже добавлен в список'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт уже удален!'},
                        status=status.HTTP_400_BAD_REQUEST)
