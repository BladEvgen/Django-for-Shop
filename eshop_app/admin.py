from django.contrib import admin
from .models import (
    Vip,
    Item,
    Room,
    Order,
    Action,
    Review,
    Message,
    OrderItem,
    ItemRating,
    UserProfile,
    GroupExtend,
    CategoryItem,
)


class BaseAdmin(admin.ModelAdmin):
    """Базовый класс для всех моделей."""
    list_display = ("id", "__str__")
    search_fields = ["id"]
    list_filter = []
    ordering = ["id"]
    readonly_fields = ["id"]  # Поле "id" всегда readonly


# Примеры кастомизации для моделей

@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ("id", "user", "is_banned", "phonenumber", "address")
    search_fields = ("user__username", "phonenumber", "address")
    list_filter = ("is_banned",)
    readonly_fields = ("user",)  # Пользователя нельзя изменить


@admin.register(Action)
class ActionAdmin(BaseAdmin):
    list_display = ("id", "slug", "description")
    search_fields = ("slug", "description")
    readonly_fields = ("slug",)  # Слаг защищён от изменений


@admin.register(GroupExtend)
class GroupExtendAdmin(BaseAdmin):
    list_display = ("id", "name", "users_list")
    search_fields = ("name",)
    filter_horizontal = ("users", "actions")

    def users_list(self, obj):
        return ", ".join([user.username for user in obj.users.all()])

    users_list.short_description = "Список пользователей"


@admin.register(CategoryItem)
class CategoryItemAdmin(BaseAdmin):
    list_display = ("id", "title", "slug", )
    search_fields = ("title", "slug")


@admin.register(Item)
class ItemAdmin(BaseAdmin):
    list_display = ("id", "title", "price", "is_active", "category", )
    search_fields = ("title", "description")
    list_filter = ("is_active", "category")


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = ("id", "user", "status", "date_created")
    search_fields = ("user__username", "status")
    list_filter = ("status", "date_created")
    readonly_fields = ("date_created",)


@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    list_display = ("id", "order", "item", "quantity")
    search_fields = ("order__id", "item__title")
    readonly_fields = ("order", "item")


@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ("id", "product", "user", "is_visible", "created_at")
    search_fields = ("product__title", "user__username", "content")
    list_filter = ("is_visible", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Vip)
class VipAdmin(BaseAdmin):
    list_display = ("id", "article", "priority", "expired")
    search_fields = ("article__title",)
    list_filter = ("priority", "expired")


@admin.register(ItemRating)
class ItemRatingAdmin(BaseAdmin):
    list_display = ("id", "author", "item", "is_like")
    search_fields = ("author__username", "item__title")
    readonly_fields = ("author", "item")


@admin.register(Room)
class RoomAdmin(BaseAdmin):
    list_display = ("id", "name", "user_started", "user_opponent", "created_at")
    search_fields = ("name", "user_started__username", "user_opponent__username")
    readonly_fields = ("created_at", "user_started", "user_opponent", "token", "slug" , "name" , "item")


@admin.register(Message)
class MessageAdmin(BaseAdmin):
    list_display = ("id", "user", "room", "date_added")
    search_fields = ("user__username", "room__name", "content")
    readonly_fields = ("date_added", "content", "user", "room")
