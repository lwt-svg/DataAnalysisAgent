import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function addAddressData(data){
    return request({
        url:"/address/",
        method:"post",
        data
    })
}

export function getAllAddressData(){
    return request({
        url:"/address/",
        method:"get",
    })
}

export function deleteAddressData(id){
    return request({
        url:"/address/"+id,
        method:"delete",
    })
}

export function editAddressData(data){
    return request({
        url:"/address/edit",
        method:"post",
        data
    })
}