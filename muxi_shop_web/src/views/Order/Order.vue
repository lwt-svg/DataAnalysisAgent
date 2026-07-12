<template>
    <div>
        <Shortcut></Shortcut>
        <div class="order">
            <div class="header">
                <div class="title clearfix">
                    <div class="logo fl">
                        <Logo></Logo>
                    </div>
                    <div class="shop-name fl">慕希商城</div>
                    <div class="name fl">结算页</div>

                </div>
            </div>
            <div class="title-text">填写并核对订单信息</div>
            <div class="order-info">
                <div class="clearfix">
                    <div class="step-title fl">
                        <h3>收货人信息</h3>
                    </div>
                    <div class="add-address fr">新增收货地址</div>
                </div>
                <div class="step-context" v-for="(item, index) in allAddress" :key="index">
                    <span class="address-name cs" 
                    :class="item.selected?'selected':''"
                    @click="changeSelected(item.id)">{{ item.signer_name }}</span>
                    <span class="address-info">{{ item.signer_address }}</span>
                    <span class="address-phone">{{ item.telephone }}</span>
                    <span class="address-default" v-show="item.default == 1">默认地址</span>
                </div>
                <hr>
                <div class="step-title">
                    <h3>支付方式</h3>
                </div>
                <div class="step-context">
                    <div class="pay-mode selected">支付宝支付</div>
                </div>
                <hr>
                <div class="step-title">
                    <h3>送货清单</h3>
                </div>
                <div class="step-context clearfix">
                    <div class="post-mode fl">
                        <div>配送方式</div>
                        <div class="selected">京东快递</div>
                        <div>标准达:<i>预计 2050年10月1日 09:00-15:00 送达</i></div>
                    </div>
                    <div class="goods-list fl">
                        <div v-for="(item, index) in goodsInfo" :key="index">
                            <div class="goods-shop-name">
                                商家:{{ item.shop_name }}
                            </div>
                            <div class="goods-detail">
                                <img :src="item.image" alt="">
                                <span class="goods-name">{{ item.name }}</span>
                                <span class="goods-price">{{ item.p_price }}</span>
                                <span class="goods-multiply">×</span>
                                <span class="goods-num">{{ item.goods_num }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="trade-foot">
                <span>应付金额:</span>
                <span class="count-price">￥{{ orderAmount }}</span>
            </div>
            <div class="commit-order">
                <button class="commit-order-button" @click="submitOrder">提交订单</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import Shortcut from '@/components/common/Shortcut.vue';
import Logo from '@/components/common/Logo.vue';
import { getAllAddressData } from '@/network/address';
import { getAllOrdersByTradeNo,updateOrderInfoData } from '@/network/order';
import { onMounted, ref } from 'vue';
import { useRoute,useRouter } from 'vue-router';

const route = useRoute()
const router = useRouter()
let allAddress = ref()
let goodsInfo = ref()
let trade_no = ref()
let orderAmount = ref()

onMounted(() => {
    trade_no.value = route.params.trade_no
    getAllAddressData().then(res => {
        allAddress.value = res.data
        // console.log(allAddress.value)
        //挂载时选择默认地址且给选择时的样式
        allAddress.value.forEach((element)=>{
            if(element.default==1){
                element.selected = true
                selectedAddressId.value = element.id
            }else{
                element.selected=false
            }
            
        })
    })
    getAllOrdersByTradeNo(trade_no.value).then(res => {
        goodsInfo.value = res.data.order_info
        orderAmount.value = res.data.order_amount
        console.log(goodsInfo.value)
    })
})

let selectedAddressId = ref()
const changeSelected=id=>{
    allAddress.value.forEach((element)=>{
        if(element.id==id){
            //如果点击对应的地址 根据id给他被选中的样式
            //并且改变selectedAddressId为选中的id
            element.selected = true
            selectedAddressId.value=id;
        }else{
            element.selected=false
        }
    })
}


const submitOrder = ()=>{
    let updateData = ref({
        address_id:selectedAddressId.value,
        trade_no:trade_no.value,
        pay_status:1
    })
    updateOrderInfoData(updateData.value).then(res=>{

    })
    router.push({
        //跳转到orderpay对应的页面  同时通过query传递参数到目标页面
        name:"OrderPay",
        query:{
            tradeNo:trade_no.value,
            orderAmount:orderAmount.value
        }
    })
}
</script>

<style lang="less" scoped>
.order {
    width: var(--content-width);
    margin: 0 auto;

    .header {
        // border-bottom: 2px solid #f00c0c;
        height: 120px;
        line-height: 120px;

        .title {
            width: var(--content-width);
            height: 80px;
            margin: 0 auto;
            line-height: 80px;

            .logo {
                height: 40px;
            }

            .shop-name {
                font-size: 40px;
                margin-left: 10px;
                margin-top: 30px;
                font-weight: 700;
                color: #f00c0c;
            }

            .name {
                font-size: 25px;
                margin-left: 10px;
                margin-top: 30px;
            }
        }
    }

    .title-text {
        height: 42px;
        line-height: 42px;
        font-size: 16px;
    }

    .order-info {
        border: 1px solid #f0f0f0;
        margin-top: 20px;

        .step-title {
            height: 40px;
            line-height: 40px;
            padding-left: 20px;

            h3 {
                font-size: 14px;
                font-weight: 700;
            }
        }

        .add-address {
            color: #005ea7;
            padding-right: 20px;
            padding-top: 20px;

            &:hover {
                cursor: pointer;
                color: #df0000;
            }
        }

        .step-context {
            padding-left: 20px;

            .address-name {
                display: inline-block;
                width: 145px;
                height: 30px;
                border: 2px solid #ddd;
                line-height: 30px;
                text-align: center;
                margin-bottom: 15px;
            }

            .address-info {
                margin-left: 30px;
            }

            .address-phone {
                margin-left: 30px;
            }

            .address-default {
                display: inline-block;
                margin-left: 30px;
                background-color: #999999;
                color: white;
                width: 60px;
                height: 25px;
                line-height: 25px;
                text-align: center;
            }
        }

        hr {
            width: 1160px;
            border: 1px solid #f0f0f0;
        }

        .pay-mode {
            width: 100px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            border: 2px solid #f0f0f0;
            &:hover {
                cursor: pointer;
                border: 2px solid #df0000;
            }
        }

        .selected {
            border: 2px solid #df0000 !important;
            background-image: url("@/assets/images/order/address-selected.png");
            background-position: 103%;
            background-repeat: no-repeat;
            background-size: 35px;
        }

        .post-mode {
            background-color: #f7f7f7;
            padding: 10px 0px 10px 20px;
            width: 350px;

            div:nth-child(1) {
                font-weight: 700;
            }

            div:nth-child(2) {
                margin-top: 20px;
                font-weight: 700;
                width: 145px;
                height: 30px;
                line-height: 30px;
                text-align: center;
            }

            div:nth-child(1) {
                margin-top: 20px;
            }
        }

        .goods-list {
            width: 780px;
            background-color: #f3fbfe;
            padding: 10px 0 10px 20px;
            margin-bottom: 20px;
            .goods-shop-name {
                margin-top: 10px;
                margin-left: 20px;
                font-weight: 700;
            }

            .goods-detail {
                display: flex;
                align-items: center;
                
                img {
                    background-color: white;
                    margin-top: 10px;
                    margin-left: 20px;
                    width: 68px;
                    height: 68px;
                    border: 1px solid #f0f0f0;
                    flex-shrink: 0;
                }

                .goods-name {
                    flex: 1;
                    margin-left: 15px;
                    margin-right: 15px;
                    // 文本溢出处理
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    max-width: 400px; // 根据需要调整
                }
                .goods-multiply{
                    margin-right: 5px;
                    flex-shrink: 0;
                }

                .goods-price {
                    color: #f00c0c;
                    margin-right: 8px;
                    font-weight: 700;
                    flex-shrink: 0;
                }

                .goods-num {
                    min-width: 30px;
                    flex-shrink: 0;
                }
            }

        }
    }

    .trade-foot {
        background-color: #f4f4f4;
        margin-top: 30px;
        height: 50px;
        line-height: 50px;
        text-align: right;
        padding-right: 40px;

        .count-price {
            margin-left: 30px;
            color: #f00c0c;
            font-size: 16px;
            font-weight: 700;
        }
    }

    .commit-order {
        margin-top: 10px;
        margin-bottom: 30px;
        text-align: right;
        margin-right: 40px;

        .commit-order-button {
            width: 135px;
            height: 35px;
            background-color: #f00c0c;
            color: white;
            border-radius: 5px;
        }
    }
}
</style>