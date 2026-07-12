<template>
    <div class="nav">
        <div class="main clearfix">
            <div class="menu fl">
                <LeftMenu></LeftMenu>
            </div>
            <div class="banner fl">
                <Banner></Banner>
            </div>
        </div>
    </div>
        
</template>

<script setup>
    import LeftMenu from './LeftMenu.vue';
    import Banner from './Banner.vue';
</script>

<style lang="less" scoped>
.nav {
    .main {
        padding-top: 15px;
        width: var(--content-width);
        margin: 0 auto;
        .banner{
            margin-left: 10px;
        }
    }
}
</style>