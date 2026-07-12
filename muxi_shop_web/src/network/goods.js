import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function getGoodsListData(keyword,page,order){
    return request({
        url:"/goods/search/"+keyword+"/" + page + "/" + order,
    })
}

export function getKeywordGoodsCountData(keyword){
    return request({
        url:"/goods/get_keyword_data_count/"+keyword,
    })
}

export function getGoodsDetail(skuId){
    return request({
        url:"/goods/"+skuId,
    })
}