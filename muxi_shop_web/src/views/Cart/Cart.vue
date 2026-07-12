<template>
    <div class="shop_cart">
        <Shortcut></Shortcut>
        <Header></Header>
        <div class="goods">
            <div class="goods-num">
                全部商品&nbsp;&nbsp;{{ $store.state.cartCount }}
            </div>
            <table>
                <thead>
                    <tr>
                        <th>
                            <input type="checkbox" :checked="allChecked" @click="checkedAll()">
                            全选
                        </th>
                        <th>商品</th>
                        <th></th>
                        <th>单价</th>
                        <th>数量</th>
                        <th>小计</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(item, index) in cartListData" :key="index">
                        <td>
                            <input type="checkbox" :checked="item.checked" @click="changeCheck(item.sku_id)">
                        </td>
                        <td>
                            <img :src="item.goods.image_url" alt="">
                        </td>
                        <td>
                            {{ item.goods.name }}
                        </td>
                        <td>
                            ￥{{ item.goods.p_price }}
                        </td>
                        <td>
                            <el-input-number v-model="item.nums"
                                @change="(newValue, oldValue) => handleChange(newValue, oldValue, item.sku_id)" :min="1"
                                :max="10" lable="描述文字"></el-input-number>
                        </td>
                        <td>
                            <!-- toFixed保留几位小数 -->
                            ￥{{ (item.goods.p_price * item.nums).toFixed(2) }}
                        </td>
                        <td>删除</td>
                    </tr>
                </tbody>
            </table>
            <div class="bottom-tool">
                <div class="tool-left">
                    <span class="delete-selected" @click="deleteGoods(0)">删除选中商品</span>
                    <span class="clear-cart" @click="deleteGoods(1)">清空购物车</span>
                </div>
                <div class="tool-right">
                    <span class="selected-goods">已选择<em>{{ selectedGoodsCount }}</em>件商品</span>
                    <span class="price-count">总价：<em>￥{{ priceCount.toFixed(2) }}</em></span>
                    <a href="#" class="go-order" @click="goOrder">去结算</a>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import Shortcut from '@/components/common/Shortcut.vue';
import Header from '@/components/home/Header.vue';
import { getCartDetailData, updateCartGoodsNumData, deleteCartGoods } from '@/network/cart';
import { createOrderData } from '@/network/order';
import { onMounted, ref, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

let cartListData = ref([])
let cartSumNums = ref(0) //全部商品的数量

onMounted(() => {
    getCartDetailData().then((res) => {
        cartListData.value = res.data
        for (let i in res.data) {
            cartSumNums.value += res.data[i].nums
        }
    })
})

const store = useStore()
const handleChange = (newValue, oldValue, skuId) => {
    let data = ref({
        sku_id: skuId,
        nums: newValue
    })
    updateCartGoodsNumData(data.value).then((res) => {
        store.dispatch("updateCart")
        console.log(res.data)
    })
}

//全选与取消全选逻辑
let allChecked = ref(false)
const checkedAll = () => {
    //点击全选
    if (allChecked.value == false) {
        for (let i in cartListData.value) {
            cartListData.value[i].checked = true //动态添加checked为true
        }
        allChecked.value = true
        selectedGoodsCount.value = cartListData.value.length //计算商品件数
    } else {
        //取消全选
        for (let i in cartListData.value) {
            cartListData.value[i].checked = false
        }
        allChecked.value = false
        selectedGoodsCount.value = 0
    }
}

let selectedGoodsCount = ref(0)
let priceCount = ref(0)

watch(() => cartListData.value, (newValue, oldValue) => {
    priceCount.value = 0
    cartListData.value.forEach((item) => {
        if (item.checked) {
            priceCount.value += item.goods.p_price * item.nums
        }
    })
}, {
    deep: true
}) //加一个深度监听才能监听到ref变量中包含的列表

//单个选中与取消商品逻辑
const changeCheck = (id) => {
    for (let i in cartListData.value) {
        if (cartListData.value[i].sku_id == id) {
            cartListData.value[i].checked = !cartListData.value[i].checked
        }
        //修改选中商品的数量
        selectedGoodsCount.value = 0
        cartListData.value.forEach((element) => {
            if (element.checked == true) {
                selectedGoodsCount.value += 1
            }
        })
        //更新全选框的状态
        if (selectedGoodsCount.value == cartListData.value.length) {
            allChecked.value = true
        }
        else {
            allChecked.value = false
        }
    }
}

//记录要删除的商品
let deleteGoodsList = ref([])
let noDeleteGoodsList = ref([])

//如果deleteStatus是0就是删除选中商品,如果是1就是清空购物车
const deleteGoods = (deleteStatus) => {
    deleteGoodsList.value = []
    noDeleteGoodsList.value = []
    if (deleteStatus == 0) {
        cartListData.value.forEach((element) => {
            if (element.checked) {
                deleteGoodsList.value.push(element.sku_id)
            }
            else {
                noDeleteGoodsList.value.push(element)
            }
        })
        if (deleteGoodsList.value.length == 0) {
            alert("请先选择要删除的商品")
        }
        let res = confirm("此操作将会永久把商品移除购物车,是否继续？") //弹出一个确认框让你确认是否要永久删除
        if (res) {
            //请求后端删除接口
            deleteCartGoods(deleteGoodsList.value).then(res => {
                alert("删除成功")
                //1.删除成功后重新加载页面
                // location.reload()
                //2.改变cartListData的值,然后动态渲染
                cartListData.value = noDeleteGoodsList.value
                store.dispatch("updateCart") //删除商品后更新后端商品总数
                selectedGoodsCount.value = 0
            })
        } else {
            alert("取消删除")
        }
    }
    else {
        let res = confirm("将要清空购物车,是否继续？") //弹出一个确认框让你确认是否要永久删除
        if (res) {
            cartListData.value.forEach((element)=>{
                deleteGoodsList.value.push(element.sku_id)
            })
            //请求后端删除接口
            deleteCartGoods(deleteGoodsList.value).then(res => {
                alert("清空购物车成功")
                //1.删除成功后重新加载页面
                // location.reload()
                //2.改变cartListData的值,然后动态渲染
                cartListData.value = noDeleteGoodsList.value
                store.dispatch("updateCart") //删除商品后更新后端商品总数
                selectedGoodsCount.value = 0
            })
        } else {
            alert("取消删除")
        }
    }
} 

//去结算,创建订单功能实现
let orderGoodsList=  ref([])
const router = useRouter()
const goOrder=()=>{
    for(let i in cartListData.value){
        if(cartListData.value[i].checked==true){
            orderGoodsList.value.push(cartListData.value[i])
        }
    }
    let orderData = ref({
        trade:{
            order_amount:priceCount.value
        },
        goods:orderGoodsList.value
    })
    //往后端发送网络请求
    let orderNo=ref("")
    createOrderData(orderData.value).then((res)=>{
        orderNo.value = res.data.trade_no
        router.push("/order/"+orderNo.value)
        store.dispatch("updateCart")
    })
}
</script>

<style lang="less" scoped>
.shop_cart {
    .goods {
        width: var(--content-width);
        margin: 0 auto;

        .goods-num {
            color: #e2231a;
            font-size: 16px;
            font-weight: 700;
        }

        table {
            border-collapse: collapse;

            tr {
                border: 1px solid #f0f0f0;

                th {
                    background-color: #f3f3f3;
                    height: 45px;

                    &:nth-child(1) {
                        //选择父类元素的第一个子元素
                        width: 80px;
                        text-align: center;
                        padding-left: 10px;
                    }
                }

                td {
                    padding-top: 10px;
                    padding-bottom: 10px;

                    &:nth-child(1) {
                        // width: 35px;
                        text-align: center;
                    }

                    &:nth-child(3) {
                        width: 600px;
                        padding-left: 20px;
                        padding-right: 50px;

                        &:hover {
                            cursor: pointer;
                            color: #e2231a;
                        }
                    }

                    &:nth-child(4) {
                        width: 80px;
                        text-align: center;
                    }

                    &:nth-child(5) {
                        width: 80px;
                        text-align: center;
                    }

                    &:nth-child(6) {
                        width: 120px;
                        text-align: center;
                        font-weight: 700;
                    }

                    &:nth-child(7) {
                        width: 80px;
                        text-align: center;
                    }

                    img {
                        width: 80px;
                        height: 80px;
                        border: 1px solid #eeeeee;
                    }
                }
            }
        }
    }

    .bottom-tool {
        height: 50px;
        line-height: 50px;
        margin-top: 10px;
        border: 1px solid #f0f0f0;

        .tool-left {
            float: left;
            padding-left: 20px;

            span {
                padding: 0 10px;

                &:hover {
                    color: #e2231a;
                    cursor: pointer;
                }
            }

            .clear-cart {
                font-size: 14px;
                font-weight: 700;
            }
        }

        .tool-right {
            float: right;
            text-align: right;

            span {
                font-weight: 700;
                color: #acacac;

                em {
                    color: #e2231a;
                    font-weight: 700;
                    padding: 0 5px;
                }
            }

            .price-count {
                em {
                    font-size: 16px;
                }
            }

            .go-order {
                display: inline-block;
                width: 95px;
                height: 50px;
                background-color: #e2231a;
                color: white;
                line-height: 50px;
                text-align: center;
                font-size: 18px;
                font-weight: 700;
            }
        }
    }
}
</style>