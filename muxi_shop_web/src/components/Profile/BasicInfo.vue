<template>
    <div class="basic-info">
        <table>
            <tr>
                <td class="table-key">
                    <span>昵称:</span>
                </td>
                <td class="table-value">
                    <el-input v-model="nickname" placeholder="请输入昵称"></el-input>
                </td>
            </tr>
            <tr>
                <td class="table-key">
                    <span>性别:</span>
                </td>
                <td class="table-value">
                    <el-radio v-model="gender" label="1" size="medium">男</el-radio>
                    <el-radio v-model="gender" label="2" size="medium">女</el-radio>
                    <el-radio v-model="gender" label="3" size="medium">保密</el-radio>
                </td>
            </tr>
            <tr>
                <td class="table-key">
                    <span>生日:</span>
                </td>
                <td class="table-value">
                    <el-date-picker 
                        v-model="birthday" 
                        type="date" 
                        placeholder="选择日期"
                        value-format="YYYY-MM-DD"
                    ></el-date-picker>
                </td>
            </tr>
             <tr>
                <td class="table-key"></td>
                <td class="submit">
                    <el-button type="success" @click="handleUpdate" :loading="loading">提交</el-button>
                </td>
            </tr>
        </table>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { updateUserInfo,getUserInfo } from '@/network/user';

// 响应式数据
const nickname = ref('')
const gender = ref('1')
const birthday = ref('')
const loading = ref(false)

// 获取用户信息
const fetchUserInfo = async () => {
    try {
        const response = await getUserInfo();
        const userData = response.data;
        
        // 填充用户当前信息
        nickname.value = userData.name || '';
        gender.value = userData.gender?.toString() || '1';
        birthday.value = userData.birthday || '';
        
    } catch (error) {
        console.error('获取用户信息失败:', error);
        ElMessage.error('获取用户信息失败');
    }
};

// 更新用户信息处理函数
const handleUpdate = async () => {
    // 前端验证
    if (!nickname.value.trim()) {
        ElMessage.error('请输入昵称');
        return;
    }

    loading.value = true;

    try {
        // 准备更新数据 - 根据你的后端接口调整字段名
        const updateData = {
            name: nickname.value.trim(),
            gender: parseInt(gender.value),
            birthday: birthday.value
        };

        // 发送更新请求
        const response = await updateUserInfo(updateData);
        
        // 更新成功处理
        ElMessage.success('信息更新成功！');
        console.log('更新响应:', response);
        // 最简单直接的方法：同时更新 localStorage 和强制刷新页面
        window.localStorage.setItem("username", nickname.value.trim());
        
        ElMessage.success('信息更新成功！');
        
        // 强制刷新页面，让导航栏重新初始化
        setTimeout(() => {
            window.location.reload();
        }, 1000);
        
    } catch (error) {
        // 更新失败处理
        console.error('更新失败:', error);
        ElMessage.error('更新失败: ' + (error.response?.data?.message || '请稍后重试'));
    } finally {
        loading.value = false;
    }
};

// 组件挂载时获取用户信息
onMounted(() => {
    fetchUserInfo();
});
</script>

<style lang="less" scoped>
.basic-info {
    background-color: #f5f5f5;
    width: 800px;
    height: 300px;

    table {
        padding-top: 20px;
        tr {
            .table-key {
                padding-left: 20px;
                font-weight: 700;
            }

            .table-value {
                padding-left: 10px;
            }
            .submit{
                padding-top: 20px;
                padding-left: 50px;
            }
        }
        
    }

}
</style>