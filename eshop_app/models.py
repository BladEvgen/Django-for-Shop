import uuid
import logging

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.crypto import get_random_string
from django.core.validators import FileExtensionValidator

logger = logging.getLogger(__name__)

def user_avatar_path(instance, filename):
    username = instance.user.username
    return f"user_images/{username}/avatar_{username}.{filename.split('.')[-1]}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    avatar = models.ImageField(
        upload_to=user_avatar_path, null=True, blank=True, verbose_name="Аватар"
    )
    is_banned = models.BooleanField(default=False, verbose_name="Статус Бана")
    phonenumber = models.CharField(max_length=20, verbose_name="Номер телефона")
    address = models.TextField(verbose_name="Адрес доставки")

    def get_avatar_url(self):
        return self.avatar.url if self.avatar else None

    def ban_user(self):
        self.user.is_active = False
        self.user.save()

    def unban_user(self):
        self.user.is_active = True
        self.user.save()

    def delete_user(self):
        self.user.delete()

    def check_access(self, action_slug: str = ""):
        try:
            user: User = self.user
            action: Action = Action.objects.get(slug=action_slug)
            intersections = GroupExtend.objects.filter(users=user, actions=action)
            if len(intersections) > 0:
                return True
            return False
        except Exception as error:
            logger.error("error check_access: ", error)
            return False

    def get_actions(self):
        try:
            user: User = self.user
            group_extends = GroupExtend.objects.filter(users=user)
            actions = Action.objects.filter(groupextend__in=group_extends).distinct()

            return actions
        except GroupExtend.DoesNotExist:
            return []

    def has_action(self, action_slug: str):
        return self.get_actions().filter(slug=action_slug).exists()

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)


class Action(models.Model):
    slug = models.SlugField(
        verbose_name="Ссылка",
        max_length=500,
        unique=True,
    )
    description = models.TextField(
        verbose_name="Описание",
        default="",
    )

    class Meta:
        app_label = "auth"
        ordering = ("slug",)
        verbose_name = "Действие"
        verbose_name_plural = "Действия"

    def __str__(self):
        return f"Действие: {self.slug} - {self.description[:50]}"


class GroupExtend(models.Model):
    name = models.CharField(
        verbose_name="Название группы",
        max_length=300,
        unique=True,
    )
    users = models.ManyToManyField(
        verbose_name="Пользователи принадлежащие к группе",
        to=User,
    )
    actions = models.ManyToManyField(
        verbose_name="Возможности доступные этой группе",
        to=Action,
    )

    class Meta:
        app_label = "auth"
        ordering = ("name",)
        verbose_name = "Кастомные права"
        verbose_name_plural = "Кастомные права"

    def __str__(self):
        return f"Группа: {self.name}"

    def has_action(self, action_slug: str):
        return self.actions.filter(slug=action_slug).exists()


class CategoryItem(models.Model):
    title = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Наименование",
    )
    slug = models.SlugField(
        max_length=255,
        verbose_name="Ссылка",
        null=False,
        editable=True,
        unique=True,
    )

    class Meta:
        app_label = "eshop_app"
        ordering = ("-title",)
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return f"Категория(id={self.id}, Название={self.title}, Ссылка={self.slug})"


class TagItem(models.Model):
    title = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Наименование",
    )
    slug = models.SlugField(
        max_length=255, verbose_name="Ссылка", null=False, editable=True, unique=True
    )

    class Meta:
        app_label = "eshop_app"
        ordering = ("-title",)
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self) -> str:
        return f"Тэг(id={self.id}, Название={self.title}, Ссылка={self.slug})"


class Item(models.Model):
    author = models.ForeignKey(
        verbose_name="Автор",
        db_index=True,
        primary_key=False,
        editable=True,
        blank=True,
        null=False,
        default=None,
        to=User,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255, verbose_name="Наименование")
    image = models.ImageField(
        upload_to="product_pictures/",
        null=True,
        blank=True,
        editable=True,
        default=None,
        verbose_name="Основное фото",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])
        ],
    )
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.PositiveIntegerField(verbose_name="Цена")
    category = models.ForeignKey(
        "CategoryItem", on_delete=models.CASCADE, verbose_name="Категория"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активность объявления")
    tags = models.ManyToManyField("TagItem", blank=True, verbose_name="Тэги")
    discounted_price = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Скидочная цена",
        help_text="Цена со скидкой, если применена",
    )
    discount_percentage = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Процент скидки",
        editable=False,
    )

    def calculate_discount_percentage(self):
        if self.discounted_price is not None and self.price > 0:
            discount = ((self.price - self.discounted_price) / self.price) * 100
            return round(discount, 2)
        return 0.0
    
    def clean_title(self):
        import re
        return re.sub(r"[^\w\s-]", "", self.title).replace(" ", "_").lower()
    
    def save(self, *args, **kwargs):
        import os
        from eshop_app.utils import transliterate
        from django.core.files.storage import default_storage
        if self.image and not self.image.name.startswith("product_pictures/"):
            extension = os.path.splitext(self.image.name)[1]
            clean_title = transliterate(self.clean_title())
            new_filename = f"product_pictures/{clean_title}{extension}".lower()

            if default_storage.exists(new_filename):
                count = 1
                while default_storage.exists(f"product_pictures/{clean_title}_{count}{extension}"):
                    count += 1
                new_filename = f"product_pictures/{clean_title}_{count}{extension}"

            self.image.name = new_filename

        super().save(*args, **kwargs)
    def get_image_url(self):
        return self.image.url if self.image else None
    def get_additional_images(self):
        return [img.image.url for img in self.images.all()]
    
    class Meta:
        app_label = "eshop_app"
        ordering = ("is_active", "title")
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        status = "Активен" if self.is_active else "Продано"
        return f"Товар(id={self.id}, Название={self.title}, Цена={self.price}, Категория={self.category.title}, Статус={status})"
    
class ItemImage(models.Model):
    item = models.ForeignKey(
        Item, related_name="images", on_delete=models.CASCADE, verbose_name="Товар"
    )
    image = models.ImageField(
        upload_to="product_pictures/",
        verbose_name="Дополнительное изображение",
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])
        ],
    )

    class Meta:
        verbose_name = "Дополнительное изображение"
        verbose_name_plural = "Дополнительные изображения"

    def __str__(self):
        return f"Изображение для {self.item.title}"
    
    def save(self, *args, **kwargs):
        import re
        import os 
        from eshop_app.utils import transliterate
        if self.image:
            extension = os.path.splitext(self.image.name)[1]
            clean_title = transliterate(re.sub(r"[^\w\s-]", "", self.item.title))
            self.image.name = f"{clean_title}_additional_{self.pk or ''}{extension}".lower()

        super().save(*args, **kwargs)
        
class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def get_total_price(self):
        return (
            self.item.discounted_price
            if self.item.discounted_price
            else self.item.price
        )

    def calculate_item_total(self):
        return self.quantity * (self.item.discounted_price or self.item.price)

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"


class Order(models.Model):
    STATUS_CHOICES = [
        ("Processing", "Processing"),
        ("Confirmed", "Confirmed"),
        ("Canceled", "Canceled"),
        ("Completed", "Completed"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Processing",
        verbose_name="Статус",
    )
    items = models.ManyToManyField(
        "Item",
        through="OrderItem",
        related_name="orders",
        verbose_name="Товары в заказе",
    )

    def get_total_price(self):
        total_price = 0
        for order_item in self.order_items.all():
            total_price += (
                order_item.item.discounted_price
                if order_item.item.discounted_price
                else order_item.item.price
            ) * order_item.quantity
        return total_price

    class Meta:
        ordering = ["-date_created"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def calculate_item_total(self):
        return (
            self.item.discounted_price
            if self.item.discounted_price
            else self.item.price
        ) * self.quantity

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"


class Review(models.Model):
    product = models.ForeignKey(
        "Item", on_delete=models.CASCADE, verbose_name="Название товара"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    content = models.TextField(verbose_name="Комментарий")
    is_visible = models.BooleanField(default=True, verbose_name="Видимость")

    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Дата Создания"
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"


class Vip(models.Model):
    article = models.OneToOneField(
        Item,
        verbose_name="Объявление",
        on_delete=models.CASCADE,
        db_index=True,
    )
    priority = models.IntegerField(
        verbose_name="Приоритет",
        default=5,
    )
    expired = models.DateTimeField(
        verbose_name="Дата и Время Истечения",
        default=timezone.now,
    )

    class Meta:
        app_label = "eshop_app"
        ordering = ("priority", "-expired")
        verbose_name = "Vip объявление"
        verbose_name_plural = "Vip объявления"

    def __str__(self):
        return f"Vip: {self.article.title} ({self.id}) | Приоритет: {self.priority}"


class ItemRating(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    item = models.ForeignKey("Item", on_delete=models.CASCADE, verbose_name="Товар")
    is_like = models.BooleanField(
        default=True,
        verbose_name="Лайк",
        help_text="Статус понравился ли пользователю товар",
    )

    class Meta:
        app_label = "eshop_app"
        ordering = ("-item", "-author")
        verbose_name = "Рейтинг товара"
        verbose_name_plural = "Рейтинги товаров"

    def __str__(self):
        return f"Рэйтинг Товара (id={self.id},\n Автор={self.author.username},\n Товар={self.item.title},\n Статус Лайка={self.is_like})"


# TODO PRIVATE CHAT


class RoomManager(models.Manager):
    def with_messages(self):
        return self.prefetch_related("messages")


class Room(models.Model):
    name = models.CharField(
        verbose_name="Наименование",
        max_length=255,
        db_index=True,
        unique=False,
        editable=True,
        blank=True,
        null=False,
        default="",
    )
    slug = models.SlugField(
        verbose_name="Ссылка",
        max_length=300,
        db_index=True,
        unique=True,
        editable=True,
        blank=False,
        null=False,
        default="",
    )

    token = models.CharField(
        verbose_name="Токен",
        max_length=255,
        db_index=True,
        unique=True,
        blank=True,
        null=True,
        default=uuid.uuid4,
    )

    user_started = models.ForeignKey(
        User,
        verbose_name="Вопрощатель",
        related_name="rooms_started",
        on_delete=models.CASCADE,
    )

    user_opponent = models.ForeignKey(
        User,
        verbose_name="Ответчик",
        related_name="rooms_opponent",
        on_delete=models.CASCADE,
    )

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, verbose_name="Товар о котором идет речь"
    )

    created_at = models.DateTimeField(
        verbose_name="Дата Создания",
        editable=False,
        default=timezone.now,
    )
    objects = RoomManager()

    def get_opponent_username(self, user):
        return (
            self.user_opponent.username
            if user == self.user_started
            else self.user_started.username
        )

    def is_valid_token(self, provided_token):
        return self.token == provided_token

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"room_id_{str(uuid.uuid4())[:8]}"
        if not self.token:
            self.token = str(uuid.uuid4())
        super(Room, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        app_label = "eshop_app"
        ordering = ("-slug", "-name")

    def __str__(self):
        return f"Room: {self.name} ({self.slug})"


@receiver(post_save, sender=Room)
def create_slug_for_room(sender, instance, created, **kwargs):
    if created and not instance.slug:
        instance.slug = f"{slugify(instance.name)}-{uuid.uuid4().hex[:8]}"
        instance.save()


@receiver(post_save, sender=Room)
def create_token_for_existing_rooms(sender, instance, **kwargs):
    if not instance.token:
        instance.token = str(uuid.uuid4())
        instance.save()


class Message(models.Model):
    user = models.ForeignKey(
        verbose_name="Автор",
        to=User,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    room = models.ForeignKey(
        verbose_name="Комната",
        to=Room,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    content = models.TextField(
        verbose_name="Текст сообщения",
        default="",
        db_index=False,
        unique=False,
        editable=True,
        blank=False,
        null=False,
    )
    date_added = models.DateTimeField(
        verbose_name="Дата и Время Добавления",
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        app_label = "eshop_app"
        ordering = ("-date_added", "-room")

    def __str__(self):
        truncated_content = (
            self.content[:30] + "..." if len(self.content) > 30 else self.content
        )
        return f"Сообщение от {self.user.username} в {self.room.name}: {truncated_content} ({self.date_added})"




class PasswordResetTokenManager(models.Manager):
    def mark_as_used(self, token):
        token_obj = self.filter(token=token, _used=False).first()
        if token_obj and token_obj.is_valid():
            token_obj._used = True
            token_obj.save(update_fields=["_used"])
            return True
        return False


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    token = models.CharField(max_length=64, unique=True, verbose_name="Токен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    _used = models.BooleanField(default=False, verbose_name="Статус использования")

    objects = PasswordResetTokenManager()

    @property
    def used(self):
        return self._used

    def is_valid(self):
        expiration_time = timezone.now() - timezone.timedelta(hours=1)
        return self.created_at > expiration_time and not self._used

    @staticmethod
    def generate_token(user):
        token = get_random_string(64)
        PasswordResetToken.objects.create(user=user, token=token)
        return token

    def save(self, *args, **kwargs):
        if self.pk:
            original = PasswordResetToken.objects.get(pk=self.pk)
            if original.token != self.token:
                self.token = original.token
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Токен для сброса пароля"
        verbose_name_plural = "Токены для сброса паролей"


class PasswordResetRequestLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name="Время запроса")

    @staticmethod
    def is_recent_request(user, ip_address):
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        return PasswordResetRequestLog.objects.filter(
            user=user, ip_address=ip_address, requested_at__gte=five_minutes_ago
        ).exists()

    @staticmethod
    def get_last_request_time(user, ip_address):
        last_request = (
            PasswordResetRequestLog.objects.filter(user=user, ip_address=ip_address)
            .order_by("-requested_at")
            .first()
        )
        return last_request.requested_at if last_request else None

    @staticmethod
    def log_request(user, ip_address):
        PasswordResetRequestLog.objects.create(user=user, ip_address=ip_address)

    @staticmethod
    def can_request_again(user, ip_address):
        last_request_time = PasswordResetRequestLog.get_last_request_time(
            user, ip_address
        )
        if not last_request_time:
            return True
        return timezone.now() >= last_request_time + timezone.timedelta(minutes=5)

    class Meta:
        verbose_name = "Лог запросов на сброс пароля"
        verbose_name_plural = "Логи запросов на сброс пароля"

