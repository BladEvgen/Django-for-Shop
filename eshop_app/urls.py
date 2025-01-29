from eshop_app import views
from django.urls import path
from eshop_app import views_a
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # * Home and User Authentication
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("about/", views.AboutView.as_view()),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # * User Profile
    path("profile/<str:username>/", views.ProfileView.as_view(), name="profile"),
    path(
        "password-reset/",
        views.password_reset_request_view,
        name="password_reset_request",
    ),
    path(
        "password-reset/<str:token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    # * Item-related URLs
    path("item/<str:item_slug>/", views.item, name="item"),
    path("create_item/", views.create_item, name="create_item"),
    path("search/", views.search, name="search"),
    path("add_review/<int:product_id>/", views.add_review, name="add_review"),
    path(
        "product_detail/<int:product_id>/", views.product_detail, name="product_detail"
    ),
    path(
        "create_category_item/",
        views.CreateCategoryItemView.as_view(),
        name="create_category_item",
    ),
    path("modify_item/<int:item_id>/", views.modify_item, name="modify_item"),
    path("user_items/", views.user_items, name="user_items"),
    path("rating/<str:item_id>/<str:is_like>/", views.rating, name="rating"),
    path("profile/<str:username>/change_data/", views.change_data, name="change_data"),
    path("delete_review/<int:product_id>/", views.delete_review, name="delete_review"),
    path('delete_item_image/<int:image_id>/', views.delete_item_image, name='delete_item_image'),
    # ! CHAT WITH TOKEN
    path("chat/", views.chat, name="chat"),
    path("chat/<slug:room_slug>/<str:token>/", views.room, name="room"),
    path("create_chat_room/", views.create_chat_room, name="create_chat_room"),
    # * MODERATE
    path("moderate/users/", views.ModerateUsersView.as_view(), name="moderate_users"),
    path('moderate/search-users/', views.SearchUsersView.as_view(), name='search_users'),

    path(
        "moderate/ban/<int:user_id>/",
        views.BanUsersView.as_view(),
        name="moderate_ban_users",
    ),
    path(
        "moderate/unban/<int:user_id>/",
        views.UnbanUsersView.as_view(),
        name="moderate_unban_users",
    ),
    path(
        "moderate/delete/<int:user_id>/",
        views.DeleteUsersView.as_view(),
        name="moderate_delete_users",
    ),
    path(
        "moderate/site/",
        views.ModerateSiteView.as_view(),
        name="ModerateSiteView",
    ),
    path(
        "create/category-item/",
        views.CreateCategoryItemView.as_view(),
        name="create_category_item",
    ),
    # * Cart Urls
    path("cart/", views.cart_detail, name="cart_detail"),
    path("add_to_cart/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "remove_from_cart/<int:item_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),
    path(
        "update_cart_quantity/<int:item_id>/",
        views.update_cart_quantity,
        name="update_cart_quantity",
    ),
    # * Order views
    path("checkout/", views.checkout, name="checkout"),
    path("order_list/", views.order_list, name="order_list"),
    path("order_detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path(
        "order-detail-user/<int:order_id>/", views.order_detail_user, name="order_detail_user"
    ),
    path(
        "update_order_status/<int:order_id>/",
        views.update_order_status,
        name="update_order_status",
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

websocket_urlpatterns = [
    path("ws/chat/<slug:room_name>/", views_a.ChatConsumer.as_asgi())
]
