<template>
    <div>
        <Shortcut></Shortcut>
        <div class="profile">
            <div class="header">
                <div class="title clearfix">
                    <div class="logo fl">
                        <Logo></Logo>
                    </div>
                    <div class="shop-name fl">慕希商城</div>
                    <div class="name fl">个人中心</div>
                    <div class="cart fr">
                        <ShopCart></ShopCart>
                    </div>
                </div>
            </div>
            <div class="main1 clearfix">
                <div class="content">
                    <div class="left-menu fl">
                        <div class="basic" :class="activeIndex == 1 ? 'active-menu' : false" @click="changeComponent(1)">基本信息
                        </div>
                        <div class="address" :class="activeIndex == 2 ? 'active-menu' : false" @click="changeComponent(2)">
                            地址管理</div>
                        <div class="order" :class="activeIndex == 3 ? 'active-menu' : false" @click="changeComponent(3)">我的订单
                        </div>
                        <div class="security" :class="activeIndex == 4 ? 'active-menu' : false" @click="changeComponent(4)">
                            安全设置</div>
                    </div>
                    <div class="right-content fl">
                        <component :is="activeComponentName"></component>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Shortcut from '@/components/common/Shortcut.vue';
import ShopCart from '@/components/home/ShopCart.vue';
import Logo from '@/components/common/Logo.vue';
import { useRouter, useRoute } from 'vue-router';
import { onMounted, ref } from 'vue';
import BasicInfo from '@/components/Profile/BasicInfo.vue'
import AddressManager from '@/components/Profile/AddressManager.vue';
import MyOrder from '@/components/Profile/MyOrder.vue';
import SecuritySettings from '@/components/Profile/SecuritySettings.vue';

export default {
    name: "Profile",
    setup() {
        const router = useRouter()
        const route = useRoute()
        let activeComponentName = ref("BasicInfo")
        let activeIndex = ref(1)
        let activeComponent = ref([
            { index: 1, ComponentName: "BasicInfo" },
            { index: 2, ComponentName: "AddressManager" },
            { index: 3, ComponentName: "MyOrder" },
            { index: 4, ComponentName: "SecuritySettings" },
        ])

        const changeComponent = (index) => {
            activeIndex.value = index
            activeComponent.value.forEach((element) => {
                if (element.index == activeIndex.value) {
                    activeComponentName.value = element.ComponentName
                }
            })
            router.push("/profile?activeIndex=" + index)
        }

        onMounted(() => {
            activeIndex.value = route.query.activeIndex?parseInt(route.query.activeIndex):1
            activeComponent.value.forEach((element) => {
                if (element.index == activeIndex.value) {
                    activeComponentName.value = element.ComponentName
                }
            })
        })
        return {
            activeComponentName,
            activeIndex,
            activeComponent,
            changeComponent
        }
    },
    components:{
        BasicInfo,
        AddressManager,
        MyOrder,
        SecuritySettings,
        Shortcut,
        Logo,
        ShopCart
    }
}


</script>

<style lang="less" scoped>
.profile {
    .header {
        border-bottom: 2px solid #f00c0c;
        height: 120px;
        line-height: 120px;

        .title {
            width: var(--content-width);
            height: 80px;
            margin: 0 auto;
            line-height: 80px;

            .logo {
                height: 40px;
            }

            .shop-name {
                font-size: 40px;
                margin-left: 10px;
                margin-top: 30px;
                font-weight: 700;
                color: #f00c0c;
            }

            .name {
                font-size: 25px;
                margin-left: 10px;
                margin-top: 30px;
            }
            .cart{
                margin-top: 30px;
            }
        }
    }

    .main1 {

        .content {
            width: var(--content-width);
            margin: 0 auto;

            .left-menu {
                color: #333;
                font-size: 14px;
                margin-top: 20px;

                div {
                    margin-top: 20px;
                    border-bottom: 1px solid #f5f5f5;

                    &:hover {
                        cursor: pointer;
                        color: #f00c0c;
                        border-bottom: 1px solid #f00c0c;
                    }
                }

                .active-menu {}
            }

            .right-content {
                margin-top: 50px;
                margin-left: 20px;
                background-color: #fff;
            }
        }
    }
}
</style>