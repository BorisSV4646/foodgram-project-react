from django.contrib import admin

from .models import (Tag, Ingredient, Ingredient_amount,
                     Recipe, Follow, Favourite, ShoppingCart)


class IngredientRecipeInline(admin.StackedInline):
    model = Ingredient_amount


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'color')
    list_editable = ('color',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_editable = ('measurement_unit',)
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class Ingredient_amountAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredient', 'recipe', 'amount')
    list_filter = ('recipe',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'image', 'text', 'cooking_time')
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    inlines = [IngredientRecipeInline]


class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_filter = ('user',)
    empty_value_display = '-пусто-'


class ShoppingAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_filter = ('user', )
    empty_value_display = '-пусто-'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Ingredient_amount, Ingredient_amountAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Favourite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingAdmin)
