<!-- src/views/Order/OrderPay.vue -->
<template>
    <div>
        <Shortcut></Shortcut>
        <div class="order-pay">
            <!-- 头部 -->
            <div class="header">
                <div class="title clearfix">
                    <div class="logo fl">
                        <Logo></Logo>
                    </div>
                    <div class="shop-name fl">慕希商城</div>
                    <div class="name fl">收银台</div>
                </div>
            </div>
            
            <!-- 订单信息 -->
            <div class="order-info">
                <!-- 订单号 -->
                <div class="order-num">
                    <div class="order-title">订单提交成功，请尽快付款！</div>
                    <div class="order-detail">
                        订单号: <span class="trade-no">{{ tradeNo }}</span>
                    </div>
                </div>
                
                <!-- 支付信息 -->
                <div class="pay-info">
                    <div class="amount-section">
                        <div class="amount-label">应付金额：</div>
                        <div class="amount-value">¥<span class="pay-count">{{ orderAmount }}</span></div>
                    </div>
                    
                    <div class="payment-method">
                        <div class="method-title">选择支付方式</div>
                        <div class="method-item active">
                            <img src="@/assets/images/order/alipay.png" alt="支付宝">
                            <span>支付宝支付</span>
                            <span class="method-desc">推荐使用支付宝支付</span>
                        </div>
                    </div>
                </div>
                
                <!-- 支付按钮和提示 -->
                <div class="payment-action">
                    <button 
                        class="pay-button" 
                        @click="toAliPay" 
                        :disabled="loading || !tradeNo"
                    >
                        <span v-if="loading">
                            <i class="el-icon-loading"></i> 支付处理中...
                        </span>
                        <span v-else>立即支付</span>
                    </button>
                    
                    <!-- 错误信息 -->
                    <div v-if="errorMsg" class="error-message">
                        <i class="el-icon-warning"></i>
                        <span>{{ errorMsg }}</span>
                    </div>
                    
                    <!-- 操作按钮组 -->
                    <div class="action-buttons">
                        <button class="secondary-button" @click="manualCheckPayment">
                            手动检查支付状态
                        </button>
                        <button class="secondary-button" @click="backToShoppingCart">
                            返回购物车列表
                        </button>
                    </div>
                    
                    <!-- 支付提示 -->
                    <div class="payment-tips">
                        <div class="tips-title">支付提示：</div>
                        <div class="tips-content">
                            <p>1. 支付完成后，请不要立即关闭页面，等待自动跳转</p>
                            <p>2. 如果支付遇到问题，请尝试刷新页面或重新支付</p>
                            <p>3. 支付成功后，您可以在"我的订单"中查看订单详情</p>
                            <p>4. 如有疑问，请联系客服：400-123-4567</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import Shortcut from '@/components/common/Shortcut.vue';
import Logo from '@/components/common/Logo.vue';
import { useRoute, useRouter } from 'vue-router';
import { onMounted, ref, onUnmounted } from 'vue';
import { toAliPayPage, checkPaymentStatus } from '@/network/order';
// 只在组件中导入 ElMessage
import { ElMessage, ElMessageBox } from 'element-plus';

const route = useRoute();
const router = useRouter();

const tradeNo = ref('');
const orderAmount = ref('');
const loading = ref(false);
const errorMsg = ref('');
const paymentTimer = ref(null);

onMounted(() => {
    // 从路由参数获取订单信息
    tradeNo.value = route.query.tradeNo || '';
    orderAmount.value = route.query.orderAmount || '';
    
    if (!tradeNo.value) {
        errorMsg.value = '订单号不存在，请重新下单';
        ElMessage.error('订单信息不完整');
    }
});

onUnmounted(() => {
    if (paymentTimer.value) {
        clearInterval(paymentTimer.value);
        paymentTimer.value = null;
    }
});

const toAliPay = async () => {
    if (loading.value) return;
    
    if (!tradeNo.value || !orderAmount.value) {
        errorMsg.value = '订单信息不完整';
        ElMessage.error('订单信息不完整');
        return;
    }
    
    loading.value = true;
    errorMsg.value = '';
    
    try {
        const orderData = {
            tradeNo: tradeNo.value,
            orderAmount: parseFloat(orderAmount.value),
            force_mock: false
        };
        
        console.log('发送支付请求:', orderData);
        
        const response = await toAliPayPage(orderData);
        
        console.log('支付接口响应:', response);
        
        if (response && response.code === 200 && response.data?.payment_url) {
            const paymentUrl = response.data.payment_url;
            console.log('获取到支付链接:', paymentUrl);
            
            // 检查链接是否有效
            if (paymentUrl && paymentUrl.startsWith('http')) {
                // 新窗口打开
                const payWindow = window.open(paymentUrl, '_blank');
                
                if (!payWindow) {
                    ElMessageBox.confirm(
                        '支付页面被浏览器拦截，请点击下方链接手动打开支付页面',
                        '支付提示',
                        {
                            confirmButtonText: '复制链接',
                            cancelButtonText: '取消',
                            type: 'warning'
                        }
                    ).then(() => {
                        navigator.clipboard.writeText(paymentUrl);
                        ElMessage.success('支付链接已复制到剪贴板');
                    });
                    
                    errorMsg.value = '支付页面被拦截，请手动打开链接';
                    loading.value = false;
                    return;
                }
                
                // 开始轮询支付状态
                startPaymentPolling();
                
                ElMessage.success('正在跳转到支付页面...');
                
            } else {
                errorMsg.value = '支付链接格式错误';
                ElMessage.error('支付链接格式错误');
                console.error('无效的支付链接:', paymentUrl);
            }
        } else {
            const errorMessage = response?.msg || '获取支付链接失败';
            errorMsg.value = errorMessage;
            ElMessage.error(errorMessage);
            console.error('支付请求失败:', response);
        }
    } catch (error) {
        console.error('支付请求异常:', error);
        
        let errorMessage = '网络请求失败';
        if (error.response) {
            errorMessage = `请求失败: ${error.response.status}`;
        } else if (error.request) {
            errorMessage = '网络连接失败，请检查网络';
        } else {
            errorMessage = `请求配置错误: ${error.message}`;
        }
        
        errorMsg.value = errorMessage;
        ElMessage.error(errorMessage);
    } finally {
        loading.value = false;
    }
};

// 轮询支付状态
const startPaymentPolling = () => {
    if (paymentTimer.value) {
        clearInterval(paymentTimer.value);
    }
    
    let pollCount = 0;
    const maxPolls = 60;
    
    paymentTimer.value = setInterval(async () => {
        pollCount++;
        
        if (pollCount > maxPolls) {
            clearInterval(paymentTimer.value);
            paymentTimer.value = null;
            ElMessage.warning('支付状态查询超时，请手动确认支付结果');
            return;
        }
        
        try {
            console.log(`第${pollCount}次查询支付状态...`);
            
            const response = await checkPaymentStatus(tradeNo.value);
            console.log('支付状态查询结果:', response);
            
            if (response && response.code === 200) {
                const paymentStatus = response.data?.status;
                
                if (paymentStatus === 'paid' || paymentStatus === 'success') {
                    clearInterval(paymentTimer.value);
                    paymentTimer.value = null;
                    
                    ElMessage.success('支付成功！');
                    
                    setTimeout(() => {
                        router.push({
                            path: '/payment/success',
                            query: { 
                                tradeNo: tradeNo.value, 
                                amount: orderAmount.value 
                            }
                        });
                    }, 1000);
                    
                } else if (paymentStatus === 'failed' || paymentStatus === 'canceled') {
                    clearInterval(paymentTimer.value);
                    paymentTimer.value = null;
                    
                    ElMessage.error('支付失败或已取消');
                    
                    setTimeout(() => {
                        router.push({
                            path: '/payment/fail',
                            query: { tradeNo: tradeNo.value }
                        });
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('轮询支付状态失败:', error);
        }
    }, 5000);
    
    setTimeout(() => {
        if (paymentTimer.value) {
            clearInterval(paymentTimer.value);
            paymentTimer.value = null;
            console.log('支付状态轮询已停止');
        }
    }, 300000);
};

const manualCheckPayment = async () => {
    try {
        loading.value = true;
        const response = await checkPaymentStatus(tradeNo.value);
        
        if (response && response.code === 200) {
            const status = response.data?.status;
            
            if (status === 'paid') {
                ElMessage.success('支付成功！');
                router.push({
                    path: '/payment/success',
                    query: { tradeNo: tradeNo.value, amount: orderAmount.value }
                });
            } else {
                ElMessage.info(`当前订单状态: ${status}`);
            }
        }
    } catch (error) {
        console.error('手动检查支付状态失败:', error);
        ElMessage.error('检查支付状态失败');
    } finally {
        loading.value = false;
    }
};

const backToShoppingCart = () => {
    router.push('/profile?activeIndex=3');
};
</script>

<style scoped>
.order-pay {
    max-width: 800px;
    margin: 30px auto;
    padding: 30px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.header {
    padding-bottom: 20px;
    margin-bottom: 30px;
    border-bottom: 2px solid #409EFF;
}

.title {
    display: flex;
    align-items: center;
}

.logo {
    margin-right: 20px;
}

.shop-name {
    font-size: 26px;
    font-weight: 700;
    color: #409EFF;
    margin-right: 20px;
}

.name {
    font-size: 22px;
    color: #333333;
    font-weight: 500;
}

.order-info {
    padding: 20px 0;
}

.order-num {
    margin-bottom: 40px;
    padding: 25px;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
    border-radius: 8px;
}

.order-title {
    font-size: 20px;
    color: #333;
    font-weight: 600;
    margin-bottom: 12px;
}

.order-detail {
    font-size: 16px;
    color: #666;
}

.trade-no {
    color: #409EFF;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    background: #f0f7ff;
    padding: 4px 12px;
    border-radius: 4px;
    margin-left: 8px;
}

.pay-info {
    margin-bottom: 40px;
    padding: 30px;
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    background: #fafafa;
}

.amount-section {
    display: flex;
    align-items: baseline;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px dashed #dcdfe6;
}

.amount-label {
    font-size: 18px;
    color: #666;
    margin-right: 15px;
}

.amount-value {
    font-size: 36px;
    color: #f56c6c;
    font-weight: 700;
}

.pay-count {
    font-size: 42px;
}

.payment-method {
    margin-top: 20px;
}

.method-title {
    font-size: 18px;
    color: #333;
    font-weight: 600;
    margin-bottom: 20px;
}

.method-item {
    display: flex;
    align-items: center;
    padding: 20px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.method-item.active {
    border-color: #409EFF;
    background: #f0f7ff;
}

.method-item:hover {
    border-color: #409EFF;
    background: #f5f9ff;
}

.method-item img {
    width: 40px;
    height: 40px;
    margin-right: 15px;
}

.method-item span:first-of-type {
    font-size: 18px;
    color: #333;
    font-weight: 500;
    margin-right: 15px;
}

.method-desc {
    color: #67c23a;
    font-size: 14px;
}

.payment-action {
    text-align: center;
}

.pay-button {
    width: 100%;
    max-width: 300px;
    height: 56px;
    background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
    color: white;
    border: none;
    border-radius: 28px;
    font-size: 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    margin: 20px 0;
    box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.pay-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
}

.pay-button:active:not(:disabled) {
    transform: translateY(0);
}

.pay-button:disabled {
    background: #c0c4cc;
    cursor: not-allowed;
    box-shadow: none;
}

.error-message {
    background: #fef0f0;
    color: #f56c6c;
    padding: 15px 25px;
    border-radius: 8px;
    margin: 20px auto;
    max-width: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid #fde2e2;
}

.error-message i {
    margin-right: 10px;
    font-size: 18px;
}

.action-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 25px 0;
}

.secondary-button {
    padding: 12px 30px;
    background: #fff;
    color: #409EFF;
    border: 2px solid #409EFF;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.secondary-button:hover {
    background: #f0f7ff;
    transform: translateY(-2px);
}

.payment-tips {
    margin-top: 40px;
    padding: 25px;
    background: #f8f9fa;
    border-radius: 10px;
    text-align: left;
}

.tips-title {
    font-size: 18px;
    color: #333;
    font-weight: 600;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e4e7ed;
}

.tips-content p {
    margin: 10px 0;
    color: #666;
    font-size: 15px;
    line-height: 1.6;
}

.tips-content p:before {
    content: "•";
    color: #409EFF;
    margin-right: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .order-pay {
        margin: 15px;
        padding: 20px;
    }
    
    .shop-name {
        font-size: 22px;
    }
    
    .name {
        font-size: 18px;
    }
    
    .amount-value {
        font-size: 28px;
    }
    
    .pay-count {
        font-size: 32px;
    }
    
    .action-buttons {
        flex-direction: column;
        align-items: center;
    }
    
    .secondary-button {
        width: 100%;
        max-width: 300px;
        margin-bottom: 10px;
    }
}
</style>