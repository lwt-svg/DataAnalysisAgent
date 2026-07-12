<template>
    <div>
        <Shortcut></Shortcut>
        <Header></Header>
        <div class="all-goods">
            <div>
                <span>全部商品分类</span>
            </div>
        </div>
        <div class="all-goods-list">
            <div class="result-keyword">
                <span class="all-result-font">
                    全部结果&nbsp;&nbsp;>&nbsp;&nbsp;
                </span>
                <span class="search-word">
                    "{{ keyword }}"
                </span>
            </div>
            <div class="goods-list">
                <div class="search-condition">
                    <a href="#" v-for="(item, index) in orderTypes" :key="index"
                        @click="changeOrder(item.order, item.index)"
                        :class="item.isActive ? 'current-condition' : 'not-current-condition'">
                        <span>{{ item.name }}</span>
                        <img src="" alt=""></img>
                    </a>
                    <div class="list-detail clearfix">
                        <!-- toGoodsDetail 点击商品时跳转到商品详情页 -->
                        <div class="every-goods fl" v-for="(item, index) in goodsListData" :key="index"
                        @click="toGoodsDetail(item.sku_id)">
                            <div>
                                <img :src="item.image" class="goods_image" alt="">
                            </div>
                            <div class="price">
                                ￥{{ item.p_price }}
                            </div>
                            <div class="name cs dian2">
                                {{ item.name }}
                            </div>
                            <div class="comment-count">
                                <span class="count">
                                    {{ item.comment_count ? item.comment_count : 0 }}
                                </span>
                                <span class="comment">条评价</span>
                            </div>
                            <div class="shop-name">
                                {{ item.shop_name }}
                            </div>
                            <div class="add-cart cs"
                            @click.stop="addCartData(item.sku_id,1,0)">
                                <img src="@/assets/images/cart/add-cart1.png">
                                加入购物车
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="change_page">
            <div class="block">
                <span class="demonstration"> </span>
                <el-pagination layout="prev, pager, next" 
                :total="goodsCount" 
                :page-size="15" 
                @current-change="handleCurrentChange"> </el-pagination>
            </div>
        </div>
    </div>
</template>

<script setup>
import Shortcut from '@/components/common/Shortcut.vue';
import Header from '@/components/home/Header.vue';
import { onMounted, ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getGoodsListData,getKeywordGoodsCountData } from "@/network/goods"
import { toGoodsDetail } from '@/utils/goods';
import { addCartData } from '@/utils/goods';

const router = useRouter()
const route = useRoute()
let orderTypes = ref([
    { index: 1, order: 1, name: "综合", isActive: true },
    { index: 2, order: 1, name: "评论数", isActive: false },
    { index: 3, order: 2, name: "价格", isActive: false },
])

let goodsListData = ref([])
const getSearchData = (keyword, page, order) => {
    getGoodsListData(keyword, page, order).then(res => {
        goodsListData.value = []
        goodsListData.value = res.data
    })
}

let goodsCount = ref(0)
const getKeywordGoodsCount=((keyword)=>{
    getKeywordGoodsCountData(keyword).then(res=>{
        goodsCount.value = res
    })
})
//页面加载后
onMounted(() => {
    getSearchData(route.params.keyword, route.params.page, route.params.order)
    getKeywordGoodsCount(route.params.keyword)
})

let keyword = computed(() => {
    return route.params.keyword
})
let page = computed(() => {
    return route.params.page
})
let order = computed(() => {
    return route.params.order
})
watch(keyword, (newValue, oldValue) => {
    getSearchData(newValue, 1, 1);
    getKeywordGoodsCountData(newValue) //关键词变化后重新计算商品数量
})
watch(page, (newValue, oldValue) => {
    getSearchData(keyword.value, newValue, 1);
})
watch(order, (newValue, oldValue) => {
    getSearchData(keyword.value, 1, newValue);
})
const changeOrder = (currentOrder, index) => {
    //点击完成之后 要进行页面刷新
    //router.push()方法用于导航到一个已经存在于routes中的路由
    router.push("/goods_list/" + route.params.keyword + "/" + 1 + "/" + currentOrder)

    //样式切换
    for (let i in orderTypes.value) {
        if (orderTypes.value[i].index == index) {
            orderTypes.value[i].isActive = true
        }
        else {
            orderTypes.value[i].isActive = false
        }
    }
}

const handleCurrentChange=((val)=>{
    router.push("/goods_list/"+keyword.value + "/" + val + "/" + order.value)
})
</script>

<style lang="less" scoped>
.all-goods {
    border-bottom: 2px solid #f30213;

    div {
        width: var(--content-width);
        margin: 0 auto;

        span {
            display: block;
            background-color: #f30213;
            color: white;
            font-size: 14px;
            height: 33px;
            width: 190px;
            line-height: 33px;
            text-align: center;
        }
    }

}

.all-goods-list {
    width: var(--content-width);
    margin: 0 auto;
    overflow: hidden;
    .result-keyword {
        margin-top: 20px;

        .all-result-font {
            color: #666;
            font-size: 12px;
        }

        .search-word {
            color: #666666;
            font-weight: 700;
            font-size: 12px;
        }
    }

    .search-condition {
        background-color: #f1f1f1;
        height: 40px;
        line-height: 40px;

        .current-condition {
            background-color: #e4393c;
            border: 1px solid #e4393c;
            color: #fff;

            img {
                content: url("@/assets/images/goods-list/down3.png")
            }
        }

        .not-current-condition {
            background-color: #fff;
            border: 1px solid #dddddd;

            img {
                content: url("@/assets/images/goods-list/down1.png")
            }

            &:hover {
                border: 1px solid #e4393c;

                img {
                    content: url("@/assets/images/goods-list/down2.png")
                }
            }
        }

        a {
            display: inline-block;
            text-align: center;
            height: 25px;
            line-height: 25px;
            width: 80px;
            font-size: 14px;

            img {
                width: 14px !important;
                height: 14px !important;
                margin-left: 5px;
                display: inline-block;
            }

            &:first-child {
                margin-left: 10px;
            }
        }
    }

    .list-detail {
        .every-goods {
            margin-top: 10px;
            border: 1px solid #fff;
            width: 238px;
            height: 510px;

            &:hover {
                color: #999;
            }

            .goods_image {
                margin-top: 10px;
                width: 220px;
                height: 220px;
                &:hover{
                    cursor: pointer;
                }
            }

            .price {
                margin-left: 5px;
                margin-top: 10px;
                color: #e4393c;
                font-size: 20px;
            }

            .name {
                margin-left: 5px;
                margin-top: 10px;
                font-size: 12px;
                color: #666;

                &:hover {
                    color: #e4393c;
                }

                .comment-count {
                    margin-top: 5px;
                    margin-left: 5px;

                    .count {
                        color: #646fb0;
                        font-weight: 700;
                    }

                    .comment {
                        color: #a7a7a7;
                    }
                }

                .shop-name {
                    margin-top: 5px;
                    margin-left: 5px;
                    color: #999;
                }
            }

            .add-cart {
                margin-top: 10px;
                text-align: center;
                border: 1px solid #e4393c;

                img {
                    width: 20px;
                }

                &:hover {
                    color: #e4393c;
                }
            }
        }
    }
}
.change_page{
    margin-top: 20px;
    margin-left: 75%;
    margin-bottom: 20px;
}
</style>