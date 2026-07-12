import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function getCommentCountData(skuId){
    return request({
        url:"/comment/count/" + skuId,
    })
}

export function getGoodsCommentData(skuId,page){
    return request({
        url:"/comment/detail/"+skuId + "/" + page,
    })
}