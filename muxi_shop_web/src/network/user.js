import { request } from "./requestConfig"; //加{} 导入export {具体名称}的内容

export function loginRequest(userinfo){
    return request({
        url:"/user/login/",
        method:"post",
        data:userinfo //userinfo用于后端进行用户验证
    })
}
// 更新用户信息请求函数
export function updateUserInfo(userData) {
    return request({
        url: "/user/update/",  
        method: "post",       
        data: userData
    })
}
// 获取用户信息
export function getUserInfo() {
    return request({
        url: "/user/",  // 获取当前用户信息
        method: "get"
    })
}
//修改密码
export function changePassword(passwordData) {
    return request({
        url: "/user/change-password/",
        method: "post",
        data: passwordData
    })
}