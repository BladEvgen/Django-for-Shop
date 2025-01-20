from eshop_app.models import Action
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Создаёт или обновляет действия в модели Action на основе предоставленных slug."

    ACTIONS = {
        "moder_seller": "Доступ к модерации продавцов.",
        "UsersModeratePage_view": "Доступ к просмотру страницы модерации пользователей.",
        "ModerateSite": "Доступ к модерации сайта.",
        "CreateItemCategory": "Создание категории товаров.",
        "UsersModeratePage_ban": "Блокировка пользователя на странице модерации.",
        "UsersModeratePage_unban": "Разблокировка пользователя на странице модерации.",
        "UsersModeratePage_delete": "Удаление пользователя на странице модерации.",
    }

    def handle(self, *args, **kwargs):
        slugs = list(self.ACTIONS.keys())
        existing_actions = Action.objects.in_bulk(slugs, field_name="slug")

        to_create = []
        to_update = []

        for slug, description in self.ACTIONS.items():
            if slug in existing_actions:
                action = existing_actions[slug]
                if action.description != description:
                    action.description = description
                    to_update.append(action)
            else:
                to_create.append(Action(slug=slug, description=description))

        if to_create:
            Action.objects.bulk_create(to_create)

        if to_update:
            Action.objects.bulk_update(to_update, ["description"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано {len(to_create)} новых действий. Обновлено {len(to_update)} существующих действий."
            )
        )
