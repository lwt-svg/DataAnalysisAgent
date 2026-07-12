import { createStore } from 'vuex'
import mutations from './mutations'
import actions from './actions'

const state = {
  user:{
    //存储user的登入状态和用户名（内存存储）
    isLogin:window.localStorage.getItem("token")?true:false,
    name:window.localStorage.getItem("username")?window.localStorage.getItem("username"):""
  },
  cartCount:window.localStorage.getItem("count") || 0
}
export default createStore({
  state,
  getters: {
  },
  mutations,
  actions,
  modules: {
  }
})
