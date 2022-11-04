from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from django.shortcuts import get_object_or_404
from recipes.models import (Tag, Ingredient, Ingredient_amount,
                            Recipe, ShoppingCart, Favourite, Follow)
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField


User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'required': True},
        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        subscribed = Follow.objects.filter(user=request.user, author=obj.id)
        return subscribed.exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient
        read_only_fields = '__all__'


class Ingredient_amountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = Ingredient_amount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateIngredient_amountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ('id', 'amount')
        model = Ingredient_amount


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = Ingredient_amountSerializer(
        source='recipe_ingredient', many=True, read_only=True)
    author = CustomUserSerializer(many=False, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = ['id', 'image', 'name', 'text',
                  'cooking_time', 'author', 'ingredients', 'tags',
                  'is_favorited', 'is_in_shopping_cart']
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        favorite = Favourite.objects.filter(user=request.user, recipe=obj.id)
        return favorite.exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=obj.id)
        return shopping_cart.exists()


class CreateRecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(many=False, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = CreateIngredient_amountSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ['image', 'name', 'text', 'cooking_time',
                  'author', 'ingredients', 'tags']

    def validate(self, data):
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Должен быть хотя бы один тег'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться')
        ingredients = data['ingredients']
        if not ingredients or len(ingredients) < 1:
            raise serializers.ValidationError(
                'Минимум должен быть один ингредиент для рецепта'
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_item['id']
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) <= 0:
                raise serializers.ValidationError(
                    'Значение количества ингредиента дожно быть больше 0'
                )
        cooking_time = data['cooking_time']
        if int(cooking_time) < 0:
            raise serializers.ValidationError(
                'Время приготовления должно больше нуля'
            )
        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            Ingredient_amount.objects.create(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount'],
            )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, recipe, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ListRecipeSerializer(
            instance, context=context).data


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = Follow

    def get_is_subscribed(self, obj):
        follow = Follow.objects.filter(user=obj.user, author=obj.author)
        return follow.exists()

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj.author)
        return recipes.count()

    def get_recipes(self, obj):
        queryset = Recipe.objects.filter(author=obj.author)
        return ShortRecipeSerializer(queryset, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = ('user', 'recipe', 'id', 'name', 'image', 'cooking_time')
        model = Favourite


class ShoppingSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ShoppingCart


class ListIngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = Ingredient_amount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=Ingredient_amount.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class ListRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = ListIngredientRecipeSerializer(
        source='recipe_ingredient',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author', 'tags',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        fields = ['id', 'image', 'name', 'cooking_time']
        model = Recipe
