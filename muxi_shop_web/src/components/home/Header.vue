<template>
    <div class="main">
       <div class="content">
            <div class="logo fl">
                <Logo></Logo>
            </div>
            <div class="search fl">
                <div class="input-search">
                    <SearchBox></SearchBox>
                </div>
            </div>
            <div class="shopcart fl">
                <ShopCart></ShopCart>
            </div>
            <div class="right fr" >
                <img src="@/assets/images/header-right.png" alt="">
            </div>
       </div>
    </div>
</template>

<script setup>
    import Logo from '../common/Logo.vue';
    import SearchBox from './SearchBox.vue';
    import ShopCart from './ShopCart.vue';
</script>

<style lang="less" scoped>
    .main{
        .content{
            width: var(--content-width);
            margin: 0 auto;
            height: 140px;
            overflow: hidden;
        }
        .search{
            width: 680px;
        }
        .right{
            img{
                width: 200px;
            }
            line-height: 140px;
            margin-left: auto; //左边距自动就是尽可能多占用左边内容以实现靠右的效果
        }
    }
</style>