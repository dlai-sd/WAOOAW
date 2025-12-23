"""
Data models for WAOOAW Platform
"""

from .domain_factory import (
    Domain,
    Ingredient,
    Component,
    Recipe,
    Cookbook,
    ComponentIngredient,
    RecipeIngredient,
    RecipeComponent,
    CookbookRecipe,
)

__all__ = [
    "Domain",
    "Ingredient",
    "Component",
    "Recipe",
    "Cookbook",
    "ComponentIngredient",
    "RecipeIngredient",
    "RecipeComponent",
    "CookbookRecipe",
]
