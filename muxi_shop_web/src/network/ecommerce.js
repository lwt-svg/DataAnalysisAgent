// 电商Agent API请求模块
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建独立的axios实例
const ecommerceInstance = axios.create({
  baseURL: 'http://localhost:8001',
  timeout: 120000
})

// 请求拦截：注入token
ecommerceInstance.interceptors.request.use(config => {
  const token = window.localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = token
  }
  return config
})

// 响应拦截：统一错误处理
ecommerceInstance.interceptors.response.use(
  response => response.data,
  error => {
    console.error('电商Agent请求错误:', error)
    if (error.response) {
      const status = error.response.status
      const msg = error.response.data?.detail || '请求失败'
      ElMessage.error(`[${status}] ${msg}`)
    } else if (error.request) {
      ElMessage.error('电商助手服务未响应，请确认服务已启动（端口8001）')
    } else {
      ElMessage.error('请求配置错误: ' + error.message)
    }
    return Promise.reject(error)
  }
)

/**
 * 发送电商聊天请求（同步）
 * @param {Object} data {message, session_id, token, user_email, history}
 * @returns {Promise} 返回ChatResponse
 */
export function sendChatMessage(data) {
  return ecommerceInstance.post('/chat', data)
}

/**
 * SSE流式聊天请求
 * @param {Object} data {message, session_id, token, user_email, history}
 * @param {Object} callbacks {onStart, onIntent, onToolStart, onToolEnd, onChunk, onDone, onError}
 * @returns {AbortController} 用于取消请求
 */
export function sendChatMessageStream(data, callbacks = {}) {
  const controller = new AbortController()
  const baseURL = 'http://localhost:8001'

  const body = JSON.stringify({
    message: data.message,
    session_id: data.session_id || null,
    token: data.token || null,
    user_email: data.user_email || null,
    history: data.history || null
  })

  // 连接超时：30秒内没收到首个事件则报错
  let connectTimer = setTimeout(() => {
    controller.abort()
    callbacks.onError && callbacks.onError({ message: '连接超时，请确认电商助手服务（端口8001）已启动' })
  }, 30000)

  // 总超时：3分钟强制结束
  let totalTimer = setTimeout(() => {
    controller.abort()
    callbacks.onError && callbacks.onError({ message: '请求超时（3分钟），请稍后重试或简化问题' })
  }, 180000)

  fetch(`${baseURL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: body,
    signal: controller.signal
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let firstEventReceived = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6))
            if (!firstEventReceived) {
              firstEventReceived = true
              clearTimeout(connectTimer)
              connectTimer = null
            }
            switch (event.type) {
              case 'start':
                callbacks.onStart && callbacks.onStart(event)
                break
              case 'intent':
                callbacks.onIntent && callbacks.onIntent(event)
                break
              case 'tool_start':
                callbacks.onToolStart && callbacks.onToolStart(event)
                break
              case 'tool_end':
                callbacks.onToolEnd && callbacks.onToolEnd(event)
                break
              case 'chunk':
                callbacks.onChunk && callbacks.onChunk(event)
                break
              case 'done':
                clearTimeout(totalTimer)
                totalTimer = null
                callbacks.onDone && callbacks.onDone(event)
                break
              case 'error':
                clearTimeout(totalTimer)
                totalTimer = null
                callbacks.onError && callbacks.onError(event)
                break
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    if (connectTimer) { clearTimeout(connectTimer); connectTimer = null }
    if (totalTimer) { clearTimeout(totalTimer); totalTimer = null }
  }).catch(err => {
    if (connectTimer) { clearTimeout(connectTimer); connectTimer = null }
    if (totalTimer) { clearTimeout(totalTimer); totalTimer = null }
    if (err.name === 'AbortError') {
      console.log('SSE请求已取消')
    } else {
      console.error('SSE请求错误:', err)
      callbacks.onError && callbacks.onError({ message: err.message })
    }
  })

  return controller
}

/**
 * 健康检查
 */
export function checkEcommerceHealth() {
  return ecommerceInstance.get('/health')
}

/**
 * 获取工具列表
 */
export function getEcommerceTools() {
  return ecommerceInstance.get('/tools')
}

/**
 * 获取Token消耗统计
 */
export function getEcommerceTokenUsage() {
  return ecommerceInstance.get('/token-usage')
}
