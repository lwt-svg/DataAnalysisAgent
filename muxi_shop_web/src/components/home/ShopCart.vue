<template>
    <div class="main">
        <div class="shopcart">
            <el-badge :value="$store.state.cartCount" class="item">
                <span class="iconfont icon-gouwuche"></span>
            </el-badge>
            <span><a href="/cart/detail">我的购物车</a></span>
        </div>
    </div>
</template>

<script setup>

</script>

<style lang="less" scoped>
@red: #e2231a;

.main {
    height: 140px;
    margin-top: 45px;
    margin-left: 20px;

    .shopcart {
        border: 1px solid #e3e4e5;
        width: 130px;
        height: 35px;
        line-height: 35px;
        text-align: center;
        padding-top: 3px;

        .item {
            height: 25px;
            line-height: 25px;

            >span {
                color: @red;
                font-weight: 700;
            }
        }

        &:hover {
            cursor: pointer;
            border: 1px solid @red;
        }

        >span {
            margin-left: 20px;
            //加>表示子span
            a {
                color: @red;
            }

        }
    }
}
</style>