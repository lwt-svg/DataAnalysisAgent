<template>
    <div>
        <Header></Header>
        <div class="goods">
            <div class="good clearfix">
                <div class="fl">
                    <img :src="goodsList.data.image_url" alt="">
                </div>
                <div class="good-content fl">
                    <div class="desc">{{ goodsList.data.name }}</div>
                    <div class="price">{{ goodsList.data.p_price }}</div>
                    <div class="count">
                        <el-input-number v-model="num" @change="handleChange" :min="1" :max="10"
                            label="描述文字"></el-input-number>
                    </div>
                    <a href="#" class="add-cart" @click="addCartData(goodsList.data.sku_id,num,0)">加入购物车</a>
                </div>
            </div>
            <div class="comment">
                <Comment :skuId="route.params.sku_id"></Comment>
            </div>
        </div>
    </div>
</template>

<script setup>
import Header from '@/components/home/Header.vue';
import { getGoodsDetail } from '@/network/goods';
import { onMounted, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import Comment from '@/components/GoodsDetail/Comment.vue';
import { addCartData } from '@/utils/goods';

let skuId = ref('')
let goodsList = reactive({
    data: {}
})
const route = useRoute()
onMounted(() => {
    skuId.value = route.params.sku_id
    getGoodsDetail(skuId.value).then(res => {
        goodsList.data = res.data
    })
})

let num = ref(1)
const handleChange = (value) => {
    num.value = value
}
</script>

<style lang="less" scoped>
.goods {
    width: var(--content-width);
    margin: 0 auto;

    .good {
        img {
            width: 350px;
            height: 350px;
        }

        .good-content {
            margin-top: 70px;
            margin-left: 20px;
            width: 600px;
            .desc{
                font-size: 16px;
                color: #666;
            }
            .price{
                color: #e4393c;
                margin-top: 10px;
                font-size: 22px;
            }
            .count{
                margin-top: 10px;
            }   
            .add-cart{
                margin-top: 10px;
                display: inline-block;
                width: 150px;
                height: 45px;
                background-color: #df3033;
                font-size: 18px;
                color: white;
                font-weight: 700;
                text-align: center;
                line-height: 45px;
            }
        }
    }
    .comment {
        margin-top: 20px;
    }
}
</style>