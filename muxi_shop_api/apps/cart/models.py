# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.db.models.functions import Now


class ShoppingCart(models.Model):
    sku_id = models.CharField(max_length=255)
    nums = models.IntegerField()
    is_delete = models.IntegerField()
    email = models.CharField(max_length=255)
    create_time = models.DateTimeField(default=Now())

    class Meta:
        managed = False
        db_table = 'shopping_cart'
