# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import decimal
import json
from django.db import models

from django.conf import settings



class Goods(models.Model):
    type_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    sku_id = models.CharField(max_length=255, blank=True, null=True)
    target_url = models.CharField(max_length=255, blank=True, null=True)
    jd_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    p_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    shop_id = models.IntegerField(blank=True, null=True)
    spu_id = models.CharField(max_length=255, blank=True, null=True)
    mk_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vender_id = models.IntegerField(blank=True, null=True)
    find = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'goods'

    def to_dict(self):
        res={}
        res['type_id']=self.type_id
        res['name']=self.name
        res['sku_id']=self.sku_id
        res['target_url']=self.target_url
        res['jd_price']=self.jd_price
        res['p_price']=self.p_price
        res['image']=settings.IMAGE_URL + self.image
        res['shop_name']=self.shop_name
        res['shop_id']=self.shop_id
        res['spu_id']=self.spu_id
        res['mk_price']=self.mk_price
        res['vender_id']=self.vender_id
        res['find']=self.find
        encoder = DecimalEncoder()
        for key, value in res.items():
            if isinstance(value, decimal.Decimal):
                res[key] = encoder.default(value)
        return res
    
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o,decimal.Decimal):
            return float(o)