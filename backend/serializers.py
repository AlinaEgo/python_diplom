from rest_framework import serializers

from .models import (User, Shop, ShopCategory, Order, OrderItem, Category, Contact,
                     ConfirmToken, Product, ProductInfo, ProductParameter, Parameter)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = "__all__"
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ('id',)


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = "__all__"
        read_only_fields = ('id',)


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = "__all__"
        read_only_fields = ('id',)


class ProductParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductParameter
        fields = "__all__"
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ('id',)


class ProductInfoInOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = "__all__"
        read_only_fields = ('id',)


class OrderItemsInOrderSerializer(serializers.ModelSerializer):
    product_info = ProductInfoInOrderSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ('id',)


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemsInOrderSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ('id',)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }
