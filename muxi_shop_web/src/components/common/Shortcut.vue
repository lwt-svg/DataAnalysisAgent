<template>
    <div class="warpper">
        <div class="header">
            <span v-if="isLogin==false">
                <a href="/login">你好，请登入</a>
                <a href="#">免费注册</a> &nbsp;&nbsp;|  <!--&nbsp是空格-->
            </span>
            <span v-else>
                <a href="/profile?activeIndex=1">{{ userName }},欢迎访问</a>
                <a href="/login" @click="logout">退出</a> &nbsp;&nbsp;|  <!--&nbsp是空格-->
            </span>
            <a href="/profile?activeIndex=3">我的订单</a>
        </div>
    </div>
</template>

<script setup>
    import { computed } from 'vue';
    import { useRouter } from 'vue-router';
    import { useStore } from 'vuex';
    const store = useStore()
    const isLogin = computed(()=>store.state.user.isLogin)
    const userName = computed(()=>store.state.user.name)
    
    const router = useRouter()
    const logout = ()=>{
        window.localStorage.setItem("token","")
        store.commit("setIsLogin",false)
        router.push("/")
    }
</script>

<style lang="less" scoped>
    .warpper{
        background-color: #e3e4e5;
        height: 30px;
        .header{
            width: var(--content-width); //src/assets/config.css中自定义的样式可以这样使用
            margin: 0 auto; //让header水平居中
            text-align: right; //行内内容靠右
            line-height: 30px; //文字垂直居中
        } 
        a{
          color: var(--font-gray);
          //:hover用于定义鼠标悬停时的样式  而&是在嵌套中写伪类、伪元素时必须用&
          &:hover{
            color: var(--font-red);
          }
          margin-left: 10px;
        }
    }
</style>
