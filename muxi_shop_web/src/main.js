import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import "@/assets/css/config.css"
//引入iconfont样式
import "@/assets/iconfont/iconfont.css"
//引入element-plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
//引入element-plus图标（全局注册）
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App);

// 全局注册所有Element Plus图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(store).use(router).use(ElementPlus).mount('#app')