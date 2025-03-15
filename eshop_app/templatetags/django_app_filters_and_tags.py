import datetime

# django_app_filters_and_tags.py
from django import template
from eshop_app import models
from django.utils import formats
from django.utils import timezone
from django.utils.translation import get_language

register = template.Library()


@register.simple_tag
def item_image_url(item):
    return item.get_image_url() if item else None


@register.simple_tag
def digit_beautify(value):
    src = str(value)
    if "." in src:
        out, rnd = src.split(".")
    else:
        out, rnd = src, "0"
    chunks = [out[max(i - 3, 0) : i] for i in range(len(out), 0, -3)][::-1]
    formatted_out = " ".join(chunks)

    return f"{formatted_out}.{rnd}"


@register.filter(name="digit_beautify_filter")
def digit_beautify_filter(value):
    src = str(value)
    if "." in src:
        out, rnd = src.split(".")
    else:
        out, rnd = src, "0"
    chunks = [out[max(i - 3, 0) : i] for i in range(len(out), 0, -3)][::-1]
    formatted_out = " ".join(chunks)

    return f"{formatted_out}.{rnd}"


@register.simple_tag
def relative_time(value):
    if not isinstance(value, datetime.datetime):
        try:
            # Попытка преобразовать строку в datetime, если это необходимо
            value = timezone.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return "Неверный формат даты"
    now = timezone.now()
    delta = now - value
    
    # Пример простой реализации
    if delta.days > 0:
        return f"{delta.days} дней назад"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} часов назад"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} минут назад"
    else:
        return "Только что"

@register.filter(name="custom_cut")
def custom_cut(text, length):
    if len(str(text)) > length:
        return str(text)[:length] + "..."
    return str(text)


@register.filter(name="discount_percentage")
def discount_percentage(original_price, discounted_price):
    if original_price and discounted_price:
        original_price = (
            int(original_price)
            if isinstance(original_price, str) and original_price.isdigit()
            else original_price
        )
        discounted_price = (
            int(discounted_price)
            if isinstance(discounted_price, str) and discounted_price.isdigit()
            else discounted_price
        )

        if original_price > discounted_price:
            discount = ((original_price - discounted_price) / original_price) * 100
            return f"{discount:.2f}%"

    return "0%"


@register.simple_tag
def formatted_date(date):
    language = get_language()
    if language == "en":
        return date.strftime("%b. %d, %Y")
    elif language == "ru":
        return date.strftime("%d.%m.%Y")
    else:
        # ENG AS DEFAULT
        return date.strftime("%b. %d, %Y")


@register.simple_tag
def formatted_time(time):
    language = get_language()
    if language == "en":
        return formats.date_format(time, "M d Y g:i A")
    elif language == "ru":
        return time.strftime("%H:%M %d.%m.%Y ")
    else:
        # ENG AS DEFAULT
        return formats.date_format(time, "M d Y g:i A")


@register.simple_tag(takes_context=True)
def check_access(context: dict, action_slug: str = "") -> bool:
    user: models.User = context["request"].user
    if not user.is_authenticated:
        return False
    profile: models.UserProfile = user.profile
    is_access: bool = profile.check_access(action_slug)
    return is_access


@register.filter(name="has_action")
def has_action(user_profile, action_slug):
    return user_profile.has_action(action_slug)


@register.filter(name="chunked")
def chunked(value, chunk_size):
    try:
        chunk_size = int(chunk_size)
    except ValueError:
        return value
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


@register.filter
def multiply(value, arg):
    return value * arg
