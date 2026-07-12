<template>
    <div class="main">
        <div class="category clearfix">
            <div class="goods fl" v-for="(item, index) in goods" :key="index"
            @click="toGoodsDetail(item.sku_id)">
                <div class="first-row">
                    <img :src="item.image" alt="">
                </div>
                <div class="second-row dian2">
                    {{ item.name }}
                </div>
                <div class="third-row">
                    <small>￥</small><span>{{ item.jd_price }}</span>
                </div>
            </div>
        </div>
    </div>

</template>

<script setup>
import { onMounted, ref } from 'vue';
import { getCategoryGoods } from '@/network/home';
import { watch } from 'vue';
import { toGoodsDetail } from '@/utils/goods';

let categoryId = defineProps(['categoryId']) //把传来的数据（列表）传到categoryId里 要用数据时需要categoryId.categoryId
let goods = ref([])

//用来存储现在是多少页
let page = ref(1)
const getCategoryGoodsData = ((categoryId, page) => {
    getCategoryGoods(categoryId, page).then(res => {
        goods.value = [...goods.value,...res.data]  //每次有新数据在goods.value上追加
        console.log(res)
    })
})

onMounted(() => {
    getCategoryGoodsData(1, 1);
})


watch(categoryId, (newValue, oldValue) => { //监听分类ID 以此来显示数据
    goods.value = []
    console.log(newValue)
    getCategoryGoodsData(newValue.categoryId, 1) //newValue是一个对象 需要.categoryId来获取新的ID
    page.value = 1
})

const windowScroll=()=>{
    //可视区域的高度，就是我们用眼睛能看见的内容的高度
    let clientHeight = document.documentElement.clientHeight;
    //滚动条在文档中的高度的位置（滚出可见区域的高度）
    let scrollTop = document.documentElement.scrollTop;
    //所有内容过的高度
    let scrollHeight = document.body.scrollHeight;

    if(clientHeight + scrollTop >= scrollHeight){
        page.value += 1
        getCategoryGoodsData(categoryId.categoryId,page.value)
    }
}   
window.addEventListener("scroll",windowScroll) //全局监听事件 当滚动（scroll）文档或元素的时候触发

</script>

<style scoped lang="less">
.main {
    margin-top: 10px;
    .category {
        width: var(--content-width);
        margin: 0 auto;
        .goods {   
            background-color: #fff;
            width: 232px;
            height: 300px;
            margin-bottom: 10px;
            &:not(:nth-child(5n)){
                margin-right: 10px;
            }
            &:hover{
                cursor: pointer;    
            }
            .first-row {
                height: 200px;
                line-height: 210px;
                text-align: center;
                img {
                    width: 150px;
                    height: 150px;
                }
            }

            .second-row {
                width: 190px;
                height: 40px;
                font-size: 14px;
                color: #666;
                line-height: 20px;
                margin: 0 auto;
                &:hover{
                    cursor: pointer;
                    color: #c81623;
                }
            }

            .third-row {
                width: 190px;
                margin: 0 auto;
                margin-top: 10px;
                color: #c81623;
                span{
                    font-weight: 700;
                    font-size: 20px;
                }
            }
        }
    }
}
</style>