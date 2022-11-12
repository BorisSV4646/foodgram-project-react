from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный слаг')
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет в HEX')

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='В чем измеряется'
    )

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name


class Ingredient_amount(models.Model):
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        verbose_name='название ингредиента',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='название рецепта',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество')


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        db_index=True,
    )
    text = models.TextField(
        max_length=1000,
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Описание рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='ингредиент',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True,
    )

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'


class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        help_text='ссылка на объект пользователя, который подписывается',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        help_text='ссылка на объект пользователя, на которого подписываются',
        verbose_name='Автор',
    )
