import json

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader

from .models import (Shop, Category, Product, ProductInfo, Parameter, ProductParameter,
                     Order, OrderItem, Contact, ConfirmToken, User)
from .serializers import (UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer,
                          ContactSerializer, ProductSerializer, ProductInfoSerializer, ProductParameterSerializer,
                          ParameterSerializer)
from .signals import new_user_registered, new_order


class UserRegister(APIView):
    """
    Регистрация пользователя
    Поля: first_name, last_name, email, password, company, position
    """
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', }.issubset(request.data):
            request.data._mutable = True
            request.data.update({})
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered.send(sender=self.__class__, user_id=user.id)
                return Response({'Status': True, 'Comment': f'Пользователь {user.email} создан'}, status=201)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': user_serializer.errors}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)


class ConfirmAccount(APIView):
    """
    Подтверждение аккаунта
    Поля: email, token
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmToken.objects.filter(user__email=request.data['email'],
                                                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'Status': True})
            else:
                return Response({"Status": False, "Errors": "Неправильно указан токен или email"}, status=400)
        return Response({"Status": False, "Errors": "Указаны не все аргументы"}, status=400)


class LoginAccount(APIView):
    """
    Авторизация пользователя
    Поля: username, password
    """
    def post(self, request, *args, **kwargs):
        if {'username', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['username'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, i = Token.objects.get_or_create(user=user)
                    return Response({'Status': True, 'Comment': 'Вход выполнен', 'Token': token.key})
            return Response({"Status": False, "Errors": "Не удалось авторизовать"}, status=403)
        return Response({"Status": False, "Errors": "Указаны не все аргументы"}, status=400)


class AccountDetails(APIView):
    """
    Получение и редактирование данных аккаунта
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        else:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        if 'password' in request.data:
            errors = {}
            # проверка пароля на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return Response({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'Status': True})
        else:
            return Response({'Status': False, 'Errors': user_serializer.errors})


class UserContact(APIView):
    """
    Получение, создание, изменение и удаление контактов пользователей
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        if {'city', 'street', 'house', 'phone'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'Status': True})
            else:
                Response({'Status': False, 'Errors': serializer.errors})
        return Response({'Status': False, 'Errors': 'Необходимо указать все требуемые данные'})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({'Status': True, 'Удаление данных': deleted_count})
        return Response({'Status': False, 'Errors': 'Не указаны все необходимые данные'})

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Требуется вход'}, status=403)
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(
                    id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(
                        contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response({'Status': True})
                    else:
                        Response(
                            {'Status': False, 'Errors': serializer.errors})
        return Response({'Status': False, 'Errors': 'Не указаны все необходимые данные'})


class CategoryView(ListAPIView):
    """
    Просмотр категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Просмотр списка магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Просмотр информации о продукте
    с возможностью фильтрации по магазину и категории
    """
    def get(self, request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInfo.objects.filter(query)
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data, status=200)


class OrderView(APIView):
    """
    Получение и создание заказа
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                order = Order.objects.filter(user_id=request.user.id, id=request.data['id'])
                if order:
                    is_updated = (Order.objects.filter(user_id=request.user.id, id=request.data['id'])
                                  .update(state='in_progress'))
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return Response({'Status': True, 'Comment': 'Данные обновлены'}, status=200)
                else:
                    Response({'Status': False, 'Comment': 'Error', 'Errors': 'Данные не найдены'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)


class BasketView(APIView):
    """
    Создание, изменение, получение и удаление корзины
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        basket = Order.objects.filter(user_id=request.user.id, state='new')
        serializer = OrderSerializer(basket, many=True)
        if serializer:
            return Response(serializer.data, status=200)
        return Response({'Status': False, 'Comment': 'Error', 'Error': 'Неверный формат запроса'}, status=401)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_dict = json.loads(items_sting)
            basket, i = Order.objects.get_or_create(user_id=request.user.id, state='new')
            total_sum = 0
            objects_created = 0
            for order_item in items_dict:
                order_item.update({'order': basket.id})
                pi = ProductInfo.objects.filter(id=order_item["product_info"])[0]
                total_sum += pi.price * order_item["quantity"]
                serializer = OrderItemSerializer(data=order_item)
                if serializer.is_valid():
                    serializer.save()
                    objects_created += 1
                else:
                    return Response({'Status': False, 'Comment': f'Ошибка. {objects_created} добавлено',
                                     'Errors': serializer.errors}, status=400)
            ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
            return Response({'Status': True, 'Comment': f'{objects_created} добавлено'}, status=201)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket = Order.objects.filter(user_id=request.user.id, state='new')[0]
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=int(order_item_id))
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                order_items = OrderItem.objects.filter(order=basket.id)
                total_sum = 0
                for pib in order_items:
                    pi = ProductInfo.objects.filter(id=pib.product_info_id)[0]
                    total_sum += pi.price * pib.quantity
                ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
                return Response({'Status': True, 'Comment': f'{deleted_count} удалено'}, status=200)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Данные не найдены'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_dict = json.loads(items_sting)
            basket = Order.objects.filter(user_id=request.user.id, state='new')[0]
            if basket:
                objects_updated = 0
                for order_item in items_dict:
                    if isinstance(order_item['id'], int) and isinstance(order_item['quantity'], int):
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])
                    else:
                        return Response({'Status': False, 'Comment': f'Ошибка. {objects_updated} изменено',
                                         'Errors': f'{order_item} - неверный формат'}, status=400)
                order_items = OrderItem.objects.filter(order=basket.id)
                total_sum = 0
                for pib in order_items:
                    pi = ProductInfo.objects.filter(id=pib.product_info_id)[0]
                    total_sum += pi.price * pib.quantity
                ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
                return Response({'Status': True, 'Comment': f'{objects_updated} изменено'}, status=200)
            else:
                Response({'Status': False, 'Comment': 'Error', 'Errors': 'Корзина не найдена'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)


class PartnerUpdate(APIView):
    """
    Обновление прайса магазина
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        user_type = User.objects.filter(id=request.user.id).values('type')
        if user_type[0]['type'] != 'shop':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Функция доступна только для магазинов'}, status=403)
        url = request.data.get('url')
        if url:
            stream = get(url).content
            data = load_yaml(stream, Loader=Loader)
            shop, i = Shop.objects.get_or_create(name=data['shop'], url=url, user_id=request.user.id)
            for category in data['categories']:
                category_object, i = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, i = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          name=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, i = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return Response({'Status': True, 'Comment': 'Информация обновлена'}, status=200)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Неверный формат запроса'}, status=400)


class PartnerState(APIView):
    """Статус прайса магазина"""
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Функция доступна только для магазинов'}, status=403)
        shop = Shop.objects.filter(user_id=request.user.id)[0]
        st = 'on' if shop.state else 'off'
        return Response({'Name': shop.name, 'State': st}, status=200)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Функция доступна только для магазинов'}, status=403)
        state = request.data.get('state')
        if state:
            if state in ['on', 'off']:
                state = True if state == 'on' else False
                Shop.objects.filter(user_id=request.user.id).update(state=state)
                return Response({'Status': True, 'Comment': 'Информация обновлена'})
            else:
                return Response({'Status': False, 'Errors': 'Статус может быть только on или off'}, status=400)
        return Response({'Status': False, 'Errors': 'Неверный формат запроса'}, status=400)


class PartnerOrders(APIView):
    """
    Заказы магазина
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Ошибка авторизации'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Функция доступна только для магазинов'}, status=403)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)



