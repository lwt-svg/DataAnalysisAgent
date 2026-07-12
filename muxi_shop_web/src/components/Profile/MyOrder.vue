<template>
    <div class="order">
        <div class="condition">
            <span v-for="(item, index) in orderStatusDict" :key="index" @click="changeorderStatus(item.payStatus)"
                :class="item.isActive ? 'is-active' : ''">
                {{ item.payName }}
            </span>
        </div>
        <table>
            <thead>
                <tr class="table-header">
                    <th>订单详情</th>
                    <th>收货人</th>
                    <th>金额</th>
                    <th>状态</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody class="order-info" v-for="(item, index) in goodsInfo" :key="index">
                <!-- 这个tr是为了占位用的,留出来一个空行 -->
                <tr class="blank-tr"></tr>
                <tr class="info-header">
                    <td class="order-num">
                        <span>{{ item.create_time.replace("T", " ").replace("+08:00", " ") }}</span>
                        <span>订单号:</span>
                        <b>{{ item.trade_no }}</b>
                    </td>
                    <td colspan="4" class="img-td">
                        <el-popconfirm width="220" confirmButtonText="删除" cancelButtonText="不,谢谢" title="确认删除这个订单吗"
                            @confirm="deleteOrder(item.trade_no)">
                            <template #reference>
                                <img src="@/assets/images/profile/delete.png" alt="">
                            </template>
                        </el-popconfirm>
                    </td>
                </tr>
                <tr class="info-detail" v-for="(data, index) in item.order_info" :key="index">
                    <td class="goods-detail clearfix">
                        <a :href="'/detail/' + data.sku_id" target="_blank">
                            <img :src="data.image" alt="" class="fl">
                            <div>
                                <span class="dian2">{{ data.name }}</span>
                            </div>
                        </a>
                        <div class="goods-nums fl">{{ data.goods_num }}</div>
                    </td>
                    <!-- 
                        v-if="index<1" 只有第一个商品（index=0）会渲染这些单元格，其他商品不会渲染
                        :rowspan="item.order_info.length 这个单元格会向下延伸，覆盖整个订单的高度
                    -->
                    <td :rowspan="item.order_info.length" v-if="index < 1">刘文涛</td>
                    <td :rowspan="item.order_info.length" v-if="index < 1">{{ item.order_amount }}</td>
                    <td :rowspan="item.order_info.length" v-if="index < 1">{{ switchStatus(item.pay_status)[0] }}</td>
                    <td :rowspan="item.order_info.length" v-if="index < 1">
                        <span class="order-action">
                            {{ switchStatus(item.pay_status)[1] }}
                        </span>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup>
import { deleteOrders, getAllOrders } from '@/network/order';
import { onMounted, reactive, ref } from 'vue';

let goodsInfo = ref()

const getAllOrderInfo = (data) => {
    getAllOrders(data).then(res => {
        goodsInfo.value = res.data
        console.log(goodsInfo.value)
    })
}

onMounted(() => {
    getAllOrderInfo(-1)
})

//筛选条件的变量
const orderStatusDict = ref([
    {
        payStatus: -1,
        payName: "全部订单",
        isActive: true
    },
    {
        payStatus: 0,
        payName: "待确认",
        isActive: false
    },
    {
        payStatus: 1,
        payName: "待付款",
        isActive: false
    },
    {
        payStatus: 2,
        payName: "待收货",
        isActive: false
    },
    {
        payStatus: 3,
        payName: "已完成",
        isActive: false
    },
])

const switchStatus = (payStatus) => {
    const orderStatus = reactive({
        0: ["待确认", "确认订单"],
        1: ["待付款", "支付订单"],
        2: ["待收货", "确认收货"],
        3: ["已完成", "再次购买"],
    })
    return orderStatus[payStatus]
}

const changeorderStatus = (orderStatus) => {

}

const deleteOrder = (trade_no) => {
    deleteOrders(trade_no).then(res => {
        if (res.status === 6000) {
            alert("删除成功")
        }

    })
}
</script>

<style lang="less" scoped>
.order {
    padding: 20px;

    .condition {
        span {
            margin-right: 20px;

            &:hover {
                cursor: pointer;
                color: #e2231a;
            }
        }

        .is-active {
            color: #e2231a;
            font-weight: 700;
            border-bottom: 2px solid #e2231a;
        }
    }

    table {
        width: 900px;
        border-collapse: collapse;
        margin-top: 20px;

        .table-header {
            background-color: #f5f5f5;
            border: 1px solid #e5e5e5;
            height: 35px;

            th:first-child {
                width: 500px;
            }

            th:not(:first-child) {
                width: 100px;
            }
        }

        .order-info {

            //border: 1px solid #e5e5e5;
            .blank-tr {
                height: 20px;
            }

            .info-header {
                border: 1px solid #e5e5e5;
                background-color: #f5f5f5;
                height: 30px;

                .order-num {
                    span {
                        margin-left: 30px;
                    }

                    b {
                        color: #333;
                    }
                }

                .img-td {
                    text-align: right;
                    padding-right: 45px;

                    img {
                        width: 15px;
                        height: 15px;

                        &:hover {
                            cursor: pointer;
                            content: url("@/assets/images/profile/delete-red.png")
                        }
                    }
                }
            }

            .info-detail {
                border: 1px solid #e5e5e5;

                .goods-detail {
                    border: 1px solid #e5e5e5;

                    a {
                        img {
                            width: 60px;
                            height: 60px;
                            margin-left: 10px;
                        }

                        div {
                            margin-left: 10px;
                            width: 400px;
                            padding-top: 15px;

                            span {}
                        }
                    }

                    .goods-num {
                        padding-top: 15px;
                        margin-left: 70px;
                    }
                }

                td {
                    text-align: center;
                }

                .order-action {
                    display: inline-block;
                    border: 1px solid #ddd;
                    background-color: #f5f5f5;
                    width: 90px;
                    height: 30px;
                    line-height: 30px;
                    text-align: center;

                    &:hover {
                        cursor: pointer;
                        border: 1px solid #e2231a;
                        color: #e2231a;
                    }
                }
            }
        }

    }
}
</style>