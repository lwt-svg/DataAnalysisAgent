// src/network/order.js
import { request } from "./requestConfig";

export function createOrderData(data) {
    return request({
        url: "/order/",
        method: 'post',
        data
    });
}

export function getAllOrders(data) {
    return request({
        url: "/order?pay_status=" + data,
        method: 'get',
    });
}

export function deleteOrders(data) {
    return request({
        url: "/order/delete",
        method: 'post',
        data: { trade_no: data }
    });
}

export function getAllOrdersByTradeNo(data) {
    return request({
        url: "/order/goods/?trade_no=" + data,
        method: 'get',
    });
}

export function updateOrderInfoData(data) {
    return request({
        url: "/order/update/",
        method: 'post',
        data
    });
}

export function toAliPayPage(data) {
    return request({
        url: 'pay/create/',
        method: 'post',
        data: data
    });
}

// 检查支付状态
export function checkPaymentStatus(tradeNo) {
    return request({
        url: 'pay/status/',
        method: 'get',
        params: { trade_no: tradeNo }
    });
}

// 创建订单
export function createOrder(data) {
    return request({
        url: 'order/create/',
        method: 'post',
        data: data
    });
}

// 获取订单详情
export function getOrderDetail(tradeNo) {
    return request({
        url: 'order/detail/',
        method: 'get',
        params: { trade_no: tradeNo }
    });
}