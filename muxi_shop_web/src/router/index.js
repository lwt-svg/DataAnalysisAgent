/*
  控制用户在浏览器中访问哪个页面，实现单页面应用（SPA）的页面切换
*/
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import GoodsList from '@/views/Goods/GoodsList.vue'
import Detail from '@/views/Goods/Detail.vue'
import Login from '@/views/Login/Login.vue'
import Cart from '@/views/Cart/Cart.vue'
import Order from '@/views/Order/Order.vue'
import Profile from '@/views/Profile/Profile.vue'
import OrderPay from '@/views/Order/OrderPay.vue'
import AgentChat from '@/views/Agent/AgentChat.vue'
import DataAnalysis from '@/views/Agent/DataAnalysis.vue'

import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta:{  //存储路由相关的自定义信息
      title:"慕希商城首页"
    }
  },
  {
    path: '/goods_list/:keyword/:page/:order?',
    name: 'GoodsList',
    component: GoodsList,
    meta:{  //存储路由相关的自定义信息
      title:"商品列表页"
    }
  },
  {
    path: '/detail/:sku_id',
    name: 'Detail',
    component: Detail,
    meta:{  //存储路由相关的自定义信息
      title:"商品详情页",
      // ifAuthRequiredtrue:true
    }
  },
    {
    path: '/login',
    name: 'Login',
    component: Login,
    meta:{  //存储路由相关的自定义信息
      title:"欢迎登入"
    }
  },
    {
    path: '/cart/detail/',
    name: 'Cart',
    component: Cart,
    meta:{  //存储路由相关的自定义信息
      title:"购物车",
      ifAuthRequiredtrue:true  //在需要用户认证的页面加入路由守卫
    }
  },
  {
    path: '/order/:trade_no',
    name: 'Order',
    component: Order,
    meta:{  //存储路由相关的自定义信息
      title:"订单详情页",
      ifAuthRequiredtrue:true
    } 
  },
    // 支付页面
  {
    path: '/order/pay',
    name: 'OrderPay',
    component: () => import('@/views/Order/OrderPay.vue'),
    meta:{  //存储路由相关的自定义信息
      title:"收银台",
      ifAuthRequiredtrue:true
    } 
  },
  
  // 支付成功页面
  {
    path: '/payment/success',
    name: 'PaymentSuccess',
    component: () => import('@/views/Payment/Success.vue'),
    meta:{  //存储路由相关的自定义信息
      title:"支付成功",
      ifAuthRequiredtrue:true
    } 
  },
  
  // 支付失败页面
  {
    path: '/payment/fail',
    name: 'PaymentFail',
    component: () => import('@/views/Payment/Fail.vue'),
    meta:{  //存储路由相关的自定义信息
      title:"支付失败",
      ifAuthRequiredtrue:true
    } 
  },
    {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta:{  //存储路由相关的自定义信息
      title:"个人中心",
      ifAuthRequiredtrue:true
    } 
  },
  {
    path: '/agent',
    name: 'agent',
    component: AgentChat,
    meta: {
      title: '智能助手 - 电商平台'
    }
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: DataAnalysis,
    meta: {
      title: '数据分析助手 - B端管理',
      ifAuthRequiredtrue: true  // 需要登录（管理员权限）
    }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

//在路由跳转之前判断是否符合跳转条件
router.beforeEach((to,from,next)=>{
  document.title = to.meta.title;
  if(to.meta.ifAuthRequiredtrue==true && store.state.user.isLogin == false)
    next("/login")
  else{
    next()
  }
})

export default router