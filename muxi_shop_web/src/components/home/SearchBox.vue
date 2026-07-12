<template>
    <div class="main">
        <div class="content">
            <input type="text" placeholder="" v-model="keyword">
            <span class="iconfont icon-fangdajing" @click="Keywordsearch"></span>
        </div>
        <div class="hotword">
            <a v-for="(item,key) in hotWords" :key="key" 
            :class="item.active===true?active:''" 
            @click="Hotwordsearch(item.word)"
            href="#">{{ item.word }}</a>
        </div>
    </div>
</template>

<script setup>
    import { ref } from 'vue'
    import { useRouter } from 'vue-router'
    const hotWords = ref([
        {"word":"电脑","active":true},
        {"word":"手机","active":false},
        {"word":"平板","active":false},
        {"word":"跑鞋","active":false},
        {"word":"上衣","active":false},
    ])

    const active = 'active'
    const router = useRouter()
    let keyword = ref('')
    const Keywordsearch=()=>{ //输入框关键词搜索
        router.push("/goods_list/"+keyword.value+"/1/1")
    }
    const Hotwordsearch=(hotword)=>{ //点击热词搜索
        keyword.value = hotword
        router.push("/goods_list/"+keyword.value+"/1/1")
    }
</script>

<style scoped lang="less">
@red:#e2231a;
    .main{
        height: 140px;
        margin-top: 45px;
        .content{
            width: 550px;
            height: 35px;
            border: 2px solid @red;
            margin-left: 80px;
            input{
                line-height: 35px;
                width: 485px;
                height: 35px;
                padding-left: 15px;
            }
            span{
                display: inline-block;
                background-color: @red;
                width: 50px;
                height: 35px;
                line-height: 35px;
                text-align: center;
                color: white;
                font-weight: 700;
                &:hover{
                    cursor: pointer; //放上去边手指
                    background-color: #c81623; //放上去变色
                }
            }
            .hotword{
                margin-left: 80px;
                margin-top: 10px;
                a{
                    margin-right: 5px;
                    color: #999;
                    &:hover{
                        color: @red;
                        cursor: pointer;
                    }
                }
            }
        }
    }
</style>