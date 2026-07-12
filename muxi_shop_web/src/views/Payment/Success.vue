<template>
    <div class="payment-result">
        <Shortcut></Shortcut>
        
        <div class="result-container">
            <div class="success-icon">
                <i class="el-icon-success"></i>
            </div>
            
            <h1 class="result-title">支付成功！</h1>
            <p class="result-message">您的订单已支付成功，我们会尽快为您处理</p>
            
            <div class="order-details">
                <div class="detail-item">
                    <span class="label">订单号：</span>
                    <span class="value">{{ tradeNo }}</span>
                </div>
                <div class="detail-item" v-if="orderAmount">
                    <span class="label">支付金额：</span>
                    <span class="value">¥{{ orderAmount }}</span>
                </div>
                <div class="detail-item">
                    <span class="label">支付时间：</span>
                    <span class="value">{{ paymentTime }}</span>
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="primary-btn" @click="viewOrder">
                    查看购物车详情
                </button>
                <button class="secondary-btn" @click="backToHome">
                    返回首页
                </button>
            </div>
            
            <div class="tips">
                <p>💡 温馨提示：</p>
                <p>1. 您可以在"我的订单"中查看订单状态</p>
                <p>2. 如有疑问，请联系客服：400-888-8888</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router';
import { ref, onMounted } from 'vue';
import Shortcut from '@/components/common/Shortcut.vue';

const route = useRoute();
const router = useRouter();

const tradeNo = ref('');
const orderAmount = ref('');
const paymentTime = ref('');

onMounted(() => {
    // 设置页面标题
    document.title = '支付成功 - 慕希商城';
    
    // 获取参数
    tradeNo.value = route.query.tradeNo || '';
    orderAmount.value = route.query.orderAmount || '';
    
    console.log('支付成功页面接收到的参数:', route.query);
    
    // 设置支付时间
    const now = new Date();
    paymentTime.value = now.toLocaleString();
});

const viewOrder = () => {

    router.push('/cart/detail');

};

const backToHome = () => {
    router.push('/');
};
</script>


<style scoped>
.payment-result {
    min-height: 100vh;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.result-container {
    max-width: 600px;
    margin: 50px auto;
    padding: 40px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.success-icon {
    font-size: 80px;
    color: #67c23a;
    margin-bottom: 20px;
}

.result-title {
    font-size: 32px;
    color: #333;
    margin-bottom: 15px;
}

.result-message {
    font-size: 18px;
    color: #666;
    margin-bottom: 30px;
}

.order-details {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 25px;
    margin: 30px 0;
    text-align: left;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px dashed #dee2e6;
}

.detail-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.label {
    color: #666;
    font-weight: 500;
}

.value {
    color: #333;
    font-weight: bold;
}

.action-buttons {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin: 30px 0;
}

.primary-btn {
    padding: 15px 40px;
    background: linear-gradient(135deg, #409EFF 0%, #66b1ff 100%);
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(64, 158, 255, 0.3);
}

.secondary-btn {
    padding: 15px 40px;
    background: white;
    color: #409EFF;
    border: 2px solid #409EFF;
    border-radius: 25px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}

.secondary-btn:hover {
    background: #f0f7ff;
}

.tips {
    margin-top: 30px;
    padding: 20px;
    background: #f0f7ff;
    border-radius: 10px;
    text-align: left;
}

.tips p {
    margin: 8px 0;
    color: #666;
}

.tips p:first-child {
    color: #409EFF;
    font-weight: bold;
    margin-bottom: 15px;
}

@media (max-width: 768px) {
    .result-container {
        margin: 20px;
        padding: 20px;
    }
    
    .action-buttons {
        flex-direction: column;
    }
    
    .primary-btn,
    .secondary-btn {
        width: 100%;
    }
}
</style>