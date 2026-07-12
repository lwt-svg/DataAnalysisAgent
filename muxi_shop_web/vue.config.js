// D:\PythonWeb\code\django\muxi_shop_web\vue.config.js
module.exports = {
  devServer: {
    proxy: {
      // 关键配置：将所有以 /api 开头的请求转发到 Django 后端 (localhost:8000)
      '/api': {
        target: 'http://localhost:8000', // 你的Django服务地址和端口
        changeOrigin: true, // 改变请求头中的host，对后端透明
        ws: true, // 如果需要代理WebSocket
      }
    }
  }
}