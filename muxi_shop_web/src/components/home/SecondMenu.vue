<template>
    <div class="second">
        <div class="menu-content" v-for="(item,index) in showSubMenuData" :key="index">
            <div class="menu-title">
                <span v-for="(data,id) in item.data" :key="id">
                    <a :href="'/goods_list/'+data.name +'/1/1'" v-show="data.type==='channel'">{{ data.name }}
                        <img src="@/assets/images/menu/arrows-white.png" alt="">
                    </a>
                </span>
            </div>
            <div class="menu-detail">
                <div class="menu-detail-item">
                    <span v-for="(data,id) in item.data" :key="id">
                        <span class="menu-detail-tit" v-if="data.type==='dt'">
                            <a :href="'/goods_list/'+data.name +'/1/1'">{{ data.name }}
                                <img src="@/assets/images/menu/arrows-black.png" alt="">
                            </a>
                        </span>
                        <span class="menu-detail-data" v-else-if="data.type==='dd'">
                            <a :href="'/goods_list/'+data.name +'/1/1'">{{ data.name }}</a>
                        </span>
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { getSecondMenu } from '@/network/home';
import {watch,ref,computed} from 'vue';

const showSecondMenuIndex = defineProps(['showSecondMenuIndex'])
watch(showSecondMenuIndex,(newValue,oldValue)=>{
    //当鼠标移动到某行会获得一级菜单id 赋值给showSecondMenuIndex
    //然后我们监听showSecondMenuIndex得到想要的id传给getSecondMenu来获取二级菜单
    getSecondMenu(newValue.showSecondMenuIndex).then(res=>{
        initMenuData(res.data);
    }) 
})
let SubMenuData=ref([])
const initMenuData=(MenuData)=>{
    //这里每次初始化的时候必须把SubMenuData设置为空
    //不然的话会出现数据累加的问题 比如id为1的二级菜单和id为2的二级菜单累加起来
    SubMenuData.value=[]
    SubMenuData.value=MenuData
}
const showSubMenuData=computed(()=>{
    let resultList=[]
    let result={"index":'','data':[]}
    for(let i in SubMenuData.value){
        let id = SubMenuData.value[i].sub_menu_id
        let data={
            "name":SubMenuData.value[i].sub_menu_name,
            "type":SubMenuData.value[i].sub_menu_type
        }
        if(result["index"]!=null && id==result["index"]){
            result["data"].push(data)
        }else{
            result={"index":'',data:[]}
            result["index"]=id
            result["data"].push(data)
            resultList.push(result)
        }
    }
    return resultList
})
</script>

<style lang="less" scoped>
@red: #e2231a;

.second {
    width: 1000px;
    background-color: #fff;
    border: 2px solid #e9e9e9;
    padding: 20px;

    .menu-content {
        .menu-title {
            a {
                display: inline-block;
                background-color: black;
                color: white;
                margin-right: 10px;
                height: 25px;
                line-height: 25px;
                padding: 0 10px;
                &:hover{
                    background-color: @red;
                }
                img {
                    height: 15px;
                }
            }

        }

        .menu-detail {
            margin-top: 10px;

            .menu-detail-item {
                .menu-detail-tit {
                    a {
                        font-size: 700;

                        img {
                            height: 18px;
                        }

                        &:hover {
                            color: @red;
                        }
                    }
                }

                .menu-detail-data {
                    a {
                        margin-left: 10px;

                        &:hover {
                            color: @red;
                        }
                    }
                }
            }
        }
    }

}
</style>