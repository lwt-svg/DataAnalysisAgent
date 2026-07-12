<template>
  <!--我们不要再app.vue下写代码，因为这里是入口，除非你真的有
  所有的页面都需要的公共的内容需要写在这里
  要不然我们就自己单独去写views-->
  <router-view/>
</template>
<script setup>
  import { getMainMenu } from './network/home';
  getMainMenu().then(res=>{
    console.log(res)
  })
</script>
<style lang="less">

</style>
