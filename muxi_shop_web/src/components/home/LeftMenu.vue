<template>
    <div class="left-menu" @mouseleave="noItem()">
        <ul>
            <!--在vue循环中的语法设计是：第一个参数是当前元素，第二个参数是索引
            item是遍历的元素字典 index自增索引-->
            <li v-for="(item, index) in showMainData" 
            :key="index"
            @mouseenter="showItem(item.index)">
                <span v-for="(data, id) in item.data" :key="id">
                    <a :href="'/goods_list/'+data.name +'/1/1'">{{ data.name }}</a>
                    <!--当v-if等于0时就不打印 就是最后一个/不打印-->
                    <span v-if="item.data.length - id - 1">/</span>
                </span>
            </li>
        </ul>
        <div class="second-item" v-show="isShowItem">
            <SecondMenu :showSecondMenuIndex="showSecondMenuIndex"></SecondMenu>
        </div>
    </div>
</template>

<script setup>
import { getMainMenu } from '@/network/home';
import { computed, onMounted, ref } from 'vue';
import SecondMenu from './SecondMenu.vue';

let leftMenuData = ref([])
const init_menu_data = menuData => {
    leftMenuData.value = menuData; //获取全部的菜单信息
}
onMounted(() => {
    getMainMenu().then(res => {
        init_menu_data(res.data);  //将获取的数据传给初始化函数来操作
    })
})

//接口访问数据需要自己加工 基本结构是{index:1,data:[{name:url},{},{}]}
const showMainData = computed(() => { //计算属性（缓存、响应式依赖）
    let resultList = [];
    let result = { "index": '', data: [] }
    for (let i in leftMenuData.value) {
        let id = leftMenuData.value[i].main_menu_id;
        let data = { "name": leftMenuData.value[i].main_menu_name };
        if (result['index'] != null && id == result["index"]) {
            result['data'].push(data);
        }
        else {
            result = { "index": '', data: [] }
            result["index"] = id;
            result['data'].push(data);
            resultList.push(result);
        }
    }
    return resultList
})

//显示二级菜单
let isShowItem = ref(false);
let showSecondMenuIndex = ref();
const showItem = (index)=>{
    isShowItem.value = true;
    showSecondMenuIndex.value = index;
}
//隐藏二级菜单
const noItem=()=>{
    isShowItem.value=false
}
</script>

<style lang="less" scoped>
@red: #e2231a;

.left-menu {
    position: relative;
    background-color: #fff;
    width: 190px;
    height: 470px;

    ul {
        padding-top: 15px;

        li {
            padding-left: 15px;
            height: 25px;
            line-height: 25px;
            &:hover {
                cursor: pointer;
                background-color: #d9d9d9;
            }

            & span {
                //& span表示改变孙span的样式  >span表示改变子span的样式
                margin-left: 2px;
                margin-right: 2px;
            }
        }

        a {
            font-size: 14px;
            color: #333;

            &:hover {
                cursor: pointer;
                color: @red;
            }
        }
    }

    .second-item {
        position: absolute;
        top:0px;
        left:190px;
        z-index: 999;
    }
}
</style>