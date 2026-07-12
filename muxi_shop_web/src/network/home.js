/*
    与后端服务器进行数据交互，获取、提交数据
*/
import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function getMainMenu(){
    return request({
        url:"/main_menu",
    })
}

export function getSecondMenu(mainMenuId){
    return request({
        url:"/sub_menu?main_menu_id="+mainMenuId,
    })
}

export function getFindGoods(){
    return request({
        url:"/goods/find",
    })
}

export function getCategoryGoods(categoryId,page){
    return request({
        url:"/goods/category/"+categoryId +"/"+ page,
    })
}