<template>
    <div class="basic-info">
        <table>
            <tr>
                <td class="table-key">
                    <span>旧密码:</span>
                </td>
                <td class="table-value">
                    <el-input 
                        type="password" 
                        v-model="oldPassword" 
                        placeholder="请输入旧密码"
                        show-password
                    ></el-input>
                </td>
            </tr>
            <tr>
                <td class="table-key">
                    <span>新密码:</span>
                </td>
                <td class="table-value">
                    <el-input 
                        type="password" 
                        v-model="newPassword" 
                        placeholder="请输入新密码"
                        show-password
                    ></el-input>
                </td>
            </tr>
            <tr>
                <td class="table-key">
                    <span>请再次输入新密码:</span>
                </td>
                <td class="table-value">
                    <el-input 
                        type="password" 
                        v-model="secNewPassword" 
                        placeholder="请再次输入新密码"
                        show-password
                    ></el-input>
                </td>
            </tr>
             <tr>
                <td class="table-key"></td>
                <td class="submit">
                    <el-button type="success" @click="handleChangePassword" :loading="loading">提交</el-button>
                </td>
            </tr>
        </table>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { changePassword } from '@/network/user';

let oldPassword = ref('')
let newPassword = ref('')
let secNewPassword = ref('')
let loading = ref(false)

const handleChangePassword = async () => {
    // 前端验证
    if (!oldPassword.value.trim()) {
        ElMessage.error('请输入旧密码');
        return;
    }
    
    if (!newPassword.value.trim()) {
        ElMessage.error('请输入新密码');
        return;
    }
    
    if (!secNewPassword.value.trim()) {
        ElMessage.error('请再次输入新密码');
        return;
    }
    
    if (newPassword.value !== secNewPassword.value) {
        ElMessage.error('两次输入的新密码不一致');
        return;
    }

    loading.value = true;

    try {
        const passwordData = {
            old_password: oldPassword.value,
            new_password: newPassword.value,
            confirm_password: secNewPassword.value
        };

        const response = await changePassword(passwordData);
        
        // 修改成功处理
        ElMessage.success('密码修改成功！');
        
        // 清空表单
        oldPassword.value = '';
        newPassword.value = '';
        secNewPassword.value = '';
        
        // 可以选择让用户重新登录
        setTimeout(() => {
            // 清除token并跳转到登录页
            window.localStorage.removeItem("token");
            window.location.href = "/login";
        }, 1500);
        
    } catch (error) {
        // 修改失败处理
        console.error('修改密码失败:', error);
        ElMessage.error('修改密码失败: ' + (error.response?.data?.message || '请稍后重试'));
    } finally {
        loading.value = false;
    }
}
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
                width: 150px; /* 增加宽度以适应更长的文字 */
            }

            .table-value {
                padding-left: 10px;
                
                .el-input {
                    width: 250px; /* 设置统一的输入框宽度 */
                }
            }
            .submit{
                padding-top: 20px;
                padding-left: 50px;
            }
        }
        
    }

}
</style>