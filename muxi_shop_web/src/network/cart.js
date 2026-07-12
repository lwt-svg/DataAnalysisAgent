import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function getCartDetailData(){
    return request({
        url:"/cart/detail",
    })
}

export function updateCartGoodsNumData(data){
    return request({
        url:"/cart/num",
        method:"post",
        data
    })
}

//添加购物车
export function addCart(data){
    return request({
        url:"/cart/",
        method:"post",
        data
    })
}
//获取商品数量
export function getCartCounts(){
    return request({
        url:"/cart/counts",
        method:"post",
    })
}

export function deleteCartGoods(data){
    return request({
        url:"/cart/delete",
        method:"post",
        data
    })
}