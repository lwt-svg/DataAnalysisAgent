import axios from 'axios'; //不加{} 导入export default的内容
import store from '@/store';
import { ElMessage } from 'element-plus';
export function request(config){
    const instance = axios.create({
        // baseURL:'http://192.168.1.119:8000',
        baseURL:process.env.VUE_APP_BASE_URL || 'http://localhost:8000/api/',
        timeout:15000,
    })

    //请求拦截
    instance.interceptors.request.use(request => {
    // 防御性检查：如果 url 无效，直接报错并打印调用栈
        if (!request.url || typeof request.url !== 'string') {
            console.error('❌ 请求 URL 无效:', request.url)
            console.trace('无效请求调用栈')  // 展开控制台就能看到是哪个组件发起的
            return Promise.reject(new Error('无效请求 URL'))
        }

        // 原有 token 逻辑
        const token = window.localStorage.getItem("token")
        if (token) {
            request.headers.Authorization = token
        }
        return request
        }, err => {
            return Promise.reject(err)
        })

    //响应拦截
    instance.interceptors.response.use(response=>{
        if(response.data.status==false){ //如果用户认证失效（比如token过时）
            window.localStorage.setItem("token","")
            store.commit("setIsLogin",false)
        }
        if (response.config.url.includes('/pay/alipay')) {
            return response.data;
        }
        if (response.data && response.data.status === false) {
            // 如果用户认证失效
            window.localStorage.setItem("token", "");
            store.commit("setIsLogin", false);
        }
        return response.data?response.data:response;
    },err=>{
        //响应错误在这里处理，比如404 500这些特殊状态码
        //这里跳转一个特殊的处理页面
        // 统一错误处理
        console.error('响应错误:', err);
        
        if (err.response) {
            const status = err.response.status;
            switch (status) {
                case 400:
                    ElMessage.error('请求参数错误');
                    break;
                case 401:
                    ElMessage.error('未授权，请重新登录');
                    window.localStorage.setItem("token", "");
                    store.commit("setIsLogin", false);
                    break;
                case 404:
                    ElMessage.error('请求的资源不存在');
                    break;
                case 500:
                    ElMessage.error('服务器内部错误');
                    break;
                case 502:
                    ElMessage.error('网关错误，请稍后重试');
                    break;
                default:
                    ElMessage.error(`请求失败: ${status}`);
            }
        } else if (err.request) {
            ElMessage.error('网络连接失败，请检查网络');
        } else {
            ElMessage.error(`请求配置错误: ${err.message}`);
        }
        
        return Promise.reject(err);

    })
    return instance(config);
}