import { addCart } from "@/network/cart"
import store from "@/store"

export function toGoodsDetail(skuId){
    window.open("/detail/"+skuId)
}

export function addCartData(skuId,nums,isDelete){
    let requestData = {
        sku_id:skuId,
        nums:nums,
        is_delete:isDelete
    }
    addCart(requestData).then((res)=>{
        if(res.status===3000){
            alert(res.data)
        }
        else{
            alert(res.data)
        }
        //dispatch是vuex中用于触发actions的一个异步操作函数
        store.dispatch("updateCart")
    })
}