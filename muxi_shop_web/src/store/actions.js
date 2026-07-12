import { getCartCounts } from "@/network/cart"

const actions={
    updateCart({commit,state}){
       getCartCounts().then(res=>{
            console.log(res.data)
            let count = 0
            if(res.data.total_count>0){
                count = res.data.total_count
            }
            window.localStorage.setItem("count",count)
            //提交到mutations来更新state中的数据
            commit("updateCartCount",{"count":count})
        }) 
    }
}

export default actions