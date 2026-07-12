<template>
    <div>
        <div class="address">
            <div class="addAddressButton" @click="addAddressdialogFormVisible = true">新增收货地址</div>
            <div class="info" v-for="(item, index) in AllAddress" :key="index">
                <div class="clearfix">
                    <span class="title fl">{{ item.signer_name }}</span>
                    <div v-if="item.default" class="default fl">默认地址</div>
                    <div @click="deleteAddress(item.id)">
                        <img class="fr cs" src="@/assets/images/profile/deletex.png" alt="">
                    </div>
                </div>
                <table>
                    <tr>
                        <td class="table-key">收货人:</td>
                        <td class="table-value">{{ item.signer_name }}</td>
                    </tr>
                    <tr>
                        <td class="table-key">所在地区:</td>
                        <td class="table-value">{{ item.district }}</td>
                    </tr>
                    <tr>
                        <td class="table-key">收货地址:</td>
                        <td class="table-value">{{ item.signer_address }}</td>
                    </tr>
                    <tr>
                        <td class="table-key">手机号:</td>
                        <td class="table-value">{{ item.telephone }}</td>
                    </tr>
                    <tr class="edit">
                        <td class="table-key"></td>
                        <td class="table-value" @click="editAddress(item.id)">编辑</td>
                    </tr>
                </table>
            </div>
            <!-- 新增地址弹出框 -->
            <el-dialog title="新增收货地址" v-model="addAddressdialogFormVisible">
                <el-form :model="form">
                    <el-form-item label="收货人" :label-width="formLabelWidth">
                        <el-input v-model="form.signer_name" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="所在地区" :label-width="formLabelWidth">
                        <el-input v-model="form.district" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="收货地址" :label-width="formLabelWidth">
                        <el-input v-model="form.signer_address" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="联系电话" :label-width="formLabelWidth">
                        <el-input v-model="form.telephone" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="是否默认地址" :label-width="formLabelWidth">
                        <el-switch v-model="form.default" active-color="#13ce66" inactive-color="#ff4949"></el-switch>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="addAddressdialogFormVisible = false">取 消</el-button>
                        <el-button type="primary" @click="saveNewAddress">保 存</el-button>
                    </span>
                </template>
            </el-dialog>

            <!-- 编辑地址弹出框 -->
            <el-dialog title="编辑收货地址" v-model="editAddressdialogFormVisible">
                <el-form :model="editAddressInfo">
                    <el-form-item label="收货人" :label-width="formLabelWidth">
                        <el-input v-model="editAddressInfo.signer_name" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="所在地区" :label-width="formLabelWidth">
                        <el-input v-model="editAddressInfo.district" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="收货地址" :label-width="formLabelWidth">
                        <el-input v-model="editAddressInfo.signer_address" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="联系电话" :label-width="formLabelWidth">
                        <el-input v-model="editAddressInfo.telephone" autocomplete="off"></el-input>
                    </el-form-item>
                    <el-form-item label="是否默认地址" :label-width="formLabelWidth">
                        <el-switch v-model="editAddressInfo.default" active-color="#13ce66" inactive-color="#ff4949"></el-switch>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <span class="dialog-footer">
                        <el-button @click="editAddressdialogFormVisible = false">取 消</el-button>
                        <el-button type="primary" @click="updateAddressInfo">更 新</el-button>
                    </span>
                </template>
            </el-dialog>
        </div>

    </div>
</template>

<script setup>
import { addAddressData, deleteAddressData, editAddressData, getAllAddressData } from '@/network/address'
import { onMounted, reactive, ref } from 'vue'
let addAddressdialogFormVisible = ref(false)
let form = reactive({
    signer_name: "",
    district: "",
    signer_address: "",
    telephone: "",
    default: false
})
let formLabelWidth = ref('120px')

const saveNewAddress = () => {
    addAddressData(form).then(res => {
        if (res.status === 7000) {
            alert("保存成功")
        }
        getAllAddress()
    })
    addAddressdialogFormVisible.value = false //保存完成之后关掉添加地址框
}

let AllAddress = ref([
    {
        id: '',
        signer_name: "",
        district: "",
        signer_address: "",
        telephone: "",
        default: false
    }
])
const getAllAddress = () => {
    getAllAddressData().then(res => {
        AllAddress.value = res.data
    })
}

const deleteAddress = (id) => {
    deleteAddressData(id).then(res => {
        if(res.status===7000){
            alert('删除成功')
        }
        getAllAddress()
        
    })
}

//编辑收货地址逻辑
let editAddressdialogFormVisible = ref(false)
let editAddressInfo=reactive({
        id: '',
        signer_name: "",
        district: "",
        signer_address: "",
        telephone: "",
        default: false
    })
    const editAddress=(id)=>{
        AllAddress.value.forEach(element=>{
            if(element.id == id){
                //把要编辑的地址数据给editAddressInfo
                Object.assign(editAddressInfo,element)
                if(editAddressInfo.default==1){
                    editAddressInfo.default=true
                }else{
                    editAddressInfo.default=false
                }
            } 
        })
        editAddressdialogFormVisible.value = true
    }
    //点击更新数据之后跳转
    /*因为editAddressInfo是响应式数据,
      当我们把数据输入到输入框的时候editAddressInfo中的数据就已经改变了
      然后点击更新就可以把数据更新到数据库里了
    */
    const updateAddressInfo=(()=>{
        editAddressData(editAddressInfo).then(res=>{
            if(res.status===7000){
                alert("更新成功")
            }
            getAllAddress()
        })
        editAddressdialogFormVisible.value = false
    })

onMounted(() => {
    getAllAddress()
})
</script>

<style lang="less" scoped>
.address {
    padding-top: 20px;
    padding-left: 20px;
    padding-bottom: 20px;
    width: 870px;

    .addAddressButton {
        width: 115px;
        height: 30px;
        background-color: #f0f9e9;
        text-align: center;
        line-height: 30px;
        border: 1px solid #bfd6af;
        font-weight: 700;

        &:hover {
            cursor: pointer;
        }
    }

    .info {
        border: 2px solid #e6e6e6;
        width: 830px;
        height: 180px;
        margin-top: 10px;

        >div {
            padding: 10px;
        }

        .title {
            font-size: 14px;
            color: #666;
        }

        .default {
            margin-left: 20px;
            width: 55px;
            height: 20px;
            text-align: center;
            line-height: 20px;
            background-color: #ffaa45;
            color: white;
        }

        img {
            width: 16px;
        }

        table {
            margin-left: 30px;

            tr {
                td {
                    padding-bottom: 10px;
                }
            }

            .table-key {
                text-align: right;
                color: #999999;

            }

            .table-value {
                padding-left: 10px;
                width: 710px;
            }

            .edit {
                text-align: right;
                color: #005ea7;

                &:hover {
                    cursor: pointer;
                    color: #e2231a;
                }
            }
        }

    }
}
</style>