from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created

from .models import ConfirmToken, User


new_user_registered = Signal()
new_order = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """ Отправка письма с подтверждением сброса пароля """
    msg = EmailMultiAlternatives(subject=f"Сброс токена почты для пользователя {reset_password_token.user}",
                                 body=reset_password_token.key,
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[reset_password_token.user.email]
                                 )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """ Отправка письма с подтверждением регистрации """
    token, i = ConfirmToken.objects.get_or_create(user_id=user_id)
    msg = EmailMultiAlternatives(subject=f"Токен успешно зарегистрирован для почты {token.user.email}",
                                 body=token.key,
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[token.user.email]
                                 )
    msg.send()


@receiver(new_order)
def new_order_signal(user_id, **kwargs):
    """ Отправка письма с подтверждением оформления заказа """
    user = User.objects.get(id=user_id)
    msg = EmailMultiAlternatives(subject=f"Обработка вашего заказа",
                                 body=f'Заказ успешно оформлен. Спасибо за покупку!',
                                 from_email=settings.EMAIL_HOST_USER,
                                 to=[user.email]
                                 )
    msg.send()