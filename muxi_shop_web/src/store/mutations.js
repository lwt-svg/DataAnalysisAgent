const mutations = {
    setIsLogin(state,pyload){
        state.user.isLogin = pyload
    },
    setUserName(state,pyload){
        state.user.name = pyload
    },
    updateCartCount(state,pyload){
        state.cartCount=pyload.count;
    }
}

export default mutations