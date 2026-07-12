<!-- AgentChat.vue - 智能助手聊天页面（极简版） -->
<template>
  <div class="agent-chat-page">
    <!-- 页头 -->
    <div class="agent-header">
      <Shortcut />
      <div class="agent-nav">
        <div class="nav-container">
          <router-link to="/" class="back-home">
            <span>← 返回首页</span>
          </router-link>
          <div class="agent-title">
            <span class="agent-icon">
              <el-icon :size="24"><ChatDotRound /></el-icon>
            </span>
            <h1>电商智能助手</h1>
            <div class="agent-status" :class="{ 'online': isOnline }">
              <span class="status-dot"></span>
              {{ isOnline ? '在线' : '离线' }}
            </div>
          </div>
          <div class="nav-right">
            <button class="help-btn" @click="showHelp = true">
              <el-icon><QuestionFilled /></el-icon>
              <span>使用帮助</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="agent-main">
      <!-- 侧边栏（历史会话 + 用户状态） -->
      <div class="agent-sidebar" v-if="showSidebar">
        <div class="sidebar-section history-section">
          <h3>历史会话</h3>
          <div class="history-list">
            <div
              v-for="(session, index) in savedSessions"
              :key="index"
              class="history-item"
              @click="loadSession(session.file_name)"
            >
              <div class="history-preview">{{ session.preview }}</div>
              <div class="history-time">{{ formatTime(session.time) }}</div>
            </div>
            <div v-if="savedSessions.length === 0" class="no-history">
              暂无历史会话
            </div>
          </div>
        </div>

        <div class="sidebar-section user-section">
          <h3>登录状态</h3>
          <div class="user-status">
            <div v-if="isUserLoggedIn" class="logged-in">
              <div class="user-info">
                <span class="user-icon">
                  <el-icon :size="20"><UserFilled /></el-icon>
                </span>
                <div>
                  <div class="user-name">{{ userNickname }}</div>
                  <div class="user-email">{{ currentUserEmail }}</div>
                </div>
              </div>
              <button @click="logout" class="logout-btn">退出登录</button>
            </div>
            <div v-else class="logged-out">
              <div class="login-prompt">
                <el-icon style="color:#f59e0b"><WarningFilled /></el-icon>
                <span>未登录</span>
              </div>
              <router-link to="/login" class="login-link">
                <button class="login-btn">前往登录</button>
              </router-link>
              <p class="login-hint">登录后可使用购物车、订单等功能</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 聊天主区域 -->
      <div class="chat-container" :class="{ 'full-width': !showSidebar }">
        <div class="chat-box">
          <!-- 消息区域 -->
          <div class="messages-area" ref="messagesContainer">
            <!-- 欢迎消息 -->
            <div v-if="messages.length === 0" class="welcome-message">
              <div class="welcome-avatar">
                <el-icon :size="32"><ChatDotRound /></el-icon>
              </div>
              <div class="welcome-content">
                <h3>欢迎使用电商智能助手</h3>
                <p>我是您的专属购物助手，可以帮您搜索商品、查询价格、查看评论、管理购物车与订单。</p>
                <ul>
                  <li><el-icon><Search /></el-icon> 搜索商品</li>
                  <li><el-icon><Money /></el-icon> 查询价格</li>
                  <li><el-icon><StarFilled /></el-icon> 查看评论</li>
                  <li v-if="isUserLoggedIn"><el-icon><ShoppingCart /></el-icon> 管理购物车</li>
                  <li v-if="isUserLoggedIn"><el-icon><Document /></el-icon> 订单管理</li>
                  <li><el-icon><MagicStick /></el-icon> 智能推荐</li>
                </ul>
                <p v-if="!isUserLoggedIn" class="login-reminder">
                  <el-icon><WarningFilled /></el-icon> 登录后可使用个人功能
                </p>
                <p>试试下面的快速提问或直接输入您的问题！</p>
              </div>
            </div>

            <!-- 聊天消息 -->
            <div
              v-for="(message, index) in messages"
              :key="index"
              :class="['message', message.role]"
            >
              <div class="message-avatar">
                <el-icon v-if="message.role === 'user'" :size="20"><UserFilled /></el-icon>
                <el-icon v-else :size="20"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">
                  <MessageContent :text="message.content" :data="message.structured_data" />
                </div>
                <div class="message-meta">
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  <span v-if="message.role === 'assistant'" class="message-actions">
                    <button
                      class="action-btn"
                      @click="copyToClipboard(message.content)"
                      title="复制"
                    >
                      <el-icon><CopyDocument /></el-icon>
                    </button>
                  </span>
                </div>
              </div>
            </div>

            <!-- 加载指示器（流式状态） -->
            <div v-if="isLoading" class="message assistant">
              <div class="message-avatar">
                <el-icon :size="20"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="loading-indicator">
                  <div class="typing-dots">
                    <span></span><span></span><span></span>
                  </div>
                  <span>{{ statusText || '正在思考中...' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-area">
            <div class="input-wrapper">
              <textarea
                v-model="userInput"
                placeholder="输入您的问题，例如：帮我找一个预算3000元以内的电子产品"
                @keydown.enter.exact.prevent="sendMessage"
                @keydown.enter.shift.exact.prevent="userInput += '\n'"
                :disabled="isLoading || !isOnline"
                rows="2"
                ref="textArea"
              ></textarea>
              <div class="input-controls">
                <button
                  @click="toggleSidebar"
                  class="control-btn"
                  :title="showSidebar ? '隐藏侧边栏' : '显示侧边栏'"
                >
                  <el-icon v-if="showSidebar"><DArrowLeft /></el-icon>
                  <el-icon v-else><DArrowRight /></el-icon>
                </button>
                <button
                  @click="clearChat"
                  class="control-btn"
                  :disabled="messages.length === 0"
                  title="清空对话"
                >
                  <el-icon><Delete /></el-icon>
                </button>
                <button
                  @click="sendMessage"
                  :disabled="!userInput.trim() || isLoading || !isOnline"
                  class="send-btn"
                >
                  <span v-if="!isLoading">发送</span>
                  <span v-else>发送中...</span>
                  <el-icon class="send-icon"><Promotion /></el-icon>
                </button>
              </div>
            </div>
            <div class="input-hints">
              <span>按 Enter 发送，Shift+Enter 换行</span>
              <span v-if="!isOnline" class="offline-warning">
                <el-icon><WarningFilled /></el-icon> 助手暂时离线
              </span>
            </div>
          </div>

          <!-- 快捷操作 -->
          <div class="quick-actions-bar">
            <div class="quick-actions-grid">
              <button
                v-for="(action, index) in quickActions"
                :key="index"
                @click="selectQuickAction(action)"
                class="quick-action-btn"
                :disabled="isLoading"
              >
                {{ action }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 帮助对话框 -->
    <div v-if="showHelp" class="modal-overlay" @click.self="showHelp = false">
      <div class="help-modal">
        <div class="modal-header">
          <h2><el-icon><QuestionFilled /></el-icon> 使用帮助</h2>
          <button @click="showHelp = false" class="close-btn">
            <el-icon><CircleCloseFilled /></el-icon>
          </button>
        </div>
        <div class="modal-content">
          <div class="help-section">
            <h3><el-icon><ChatDotRound /></el-icon> 助手介绍</h3>
            <p>电商智能助手是基于AI技术的购物助手，能理解自然语言需求并提供个性化建议。</p>
          </div>
          <div class="help-section">
            <h3>常用功能</h3>
            <div class="help-examples">
              <div class="example"><strong>搜索商品：</strong><code>"帮我找一款适合打游戏的笔记本电脑"</code></div>
              <div class="example"><strong>查询价格：</strong><code>"华为P50的价格是多少"</code></div>
              <div class="example"><strong>查看评论：</strong><code>"想看看小米电视的评论怎么样"</code></div>
              <div class="example" v-if="isUserLoggedIn"><strong>管理购物车：</strong><code>"查看我的购物车"</code></div>
              <div class="example" v-if="isUserLoggedIn"><strong>订单操作：</strong><code>"我想取消订单ORD123456"</code></div>
            </div>
          </div>
          <div class="help-section">
            <h3>登录状态</h3>
            <p v-if="isUserLoggedIn"><el-icon><CircleCheckFilled /></el-icon> 您已登录，可使用全部功能。</p>
            <p v-else><el-icon><WarningFilled /></el-icon> 您尚未登录，购物车与订单功能不可用。</p>
          </div>
          <div class="help-section">
            <h3>技术支持</h3>
            <p>邮箱：support@example.com | 电话：400-123-4567</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import Shortcut from '@/components/common/Shortcut.vue'
import MessageContent from '@/components/Ecommerce/MessageContent.vue'
import { sendChatMessageStream, checkEcommerceHealth } from '@/network/ecommerce'
import { useStore } from 'vuex'
import {
  UserFilled,
  ChatDotRound,
  CopyDocument,
  Delete,
  Promotion,
  DArrowLeft,
  DArrowRight,
  QuestionFilled,
  WarningFilled,
  CircleCheckFilled,
  CircleCloseFilled,
  StarFilled,
  Search,
  Money,
  ShoppingCart,
  Document,
  MagicStick
} from '@element-plus/icons-vue'

const store = useStore()
const router = useRouter()

// 响应式数据
const messages = ref([])
const userInput = ref('')
const isLoading = ref(false)
const isOnline = ref(false)
const showSidebar = ref(true)
const showHelp = ref(false)
const messagesContainer = ref(null)
const textArea = ref(null)
const debugInfo = ref(null)
const savedSessions = ref([])
const sessionId = ref(null)
const token = localStorage.getItem('token') || ''
const currentSessionFile = ref(null)
const statusText = ref('')  // 流式状态文本
const currentController = ref(null)  // SSE请求控制器（用于取消）

const userNickname = computed(() => {
  return store.state.user.name || currentUserEmail.value.split('@')[0] || '用户'
})

const currentUserMessages = computed(() => {
  return messages.value.filter(m => m.role === 'user').slice(-5).reverse()
})

const isUserLoggedIn = computed(() => store.state.user.isLogin)
const currentUserEmail = computed(() => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.username || ''
    } catch (error) {
      return ''
    }
  }
  return ''
})

const quickActions = computed(() => {
  const baseActions = [
    '帮我找一个预算3000元以内的电子产品',
    '华为手机的价格是多少？',
    '查看笔记本电脑的评论',
    '推荐一些2000元以下的服装',
  ]
  if (isUserLoggedIn.value) {
    return [...baseActions, '查询我的购物车', '如何支付订单？', '查看我的订单']
  }
  return baseActions
})

// 检查Agent服务状态
const checkAgentStatus = async () => {
  try {
    const data = await checkEcommerceHealth()
    isOnline.value = data.status === 'healthy'
  } catch (error) {
    isOnline.value = false
  }
}

// 发送消息（SSE流式）
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || isLoading.value) return

  const needLoginKeywords = ['购物车', '订单', '我的', '结算', '支付', '取消订单', '查看我的']
  const needsLogin = needLoginKeywords.some(keyword => message.includes(keyword))

  if (needsLogin && !isUserLoggedIn.value) {
    messages.value.push({ role: 'assistant', content: '此功能需要登录后才能使用！请先登录。', structured_data: null, timestamp: new Date() })
    scrollToBottom()
    return
  }

  messages.value.push({ role: 'user', content: message, structured_data: null, timestamp: new Date() })
  userInput.value = ''
  scrollToBottom()
  isLoading.value = true
  statusText.value = '正在处理您的请求...'

  // 创建一个空的assistant消息用于流式填充
  const assistantMsg = ref({
    role: 'assistant',
    content: '',
    structured_data: null,
    timestamp: new Date()
  })
  messages.value.push(assistantMsg.value)
  const assistantIdx = messages.value.length - 1

  try {
    const localToken = localStorage.getItem('token') || ''
    const historyMessages = messages.value.slice(-11, -1).map(msg => ({
      role: msg.role,
      content: msg.content || ''
    })).filter(msg => msg.role && msg.content.trim() !== '')

    if (!sessionId.value) {
      sessionId.value = 'session_' + Date.now()
      localStorage.setItem('chat_session_id', sessionId.value)
    }

    const payload = { message, session_id: sessionId.value, token: localToken, history: historyMessages }

    currentController.value = sendChatMessageStream(payload, {
      onStart: (event) => {
        statusText.value = event.message || '正在处理...'
        isOnline.value = true
      },
      onIntent: (event) => {
        // 可选：显示意图（这里不展示给用户，避免干扰）
      },
      onToolStart: (event) => {
        statusText.value = event.message || '正在查询...'
      },
      onToolEnd: (event) => {
        statusText.value = '正在整理结果...'
      },
      onChunk: (event) => {
        statusText.value = '正在回复...'
        // 追加LLM流式文本
        messages.value[assistantIdx].content += event.message || ''
        scrollToBottom()
      },
      onDone: (event) => {
        // 设置文本响应
        messages.value[assistantIdx].content = event.response || ''
        if (event.session_id) {
          sessionId.value = event.session_id
          localStorage.setItem('chat_session_id', sessionId.value)
        }

        // 如果有商品列表，逐个显示卡片（流式体验）
        if (event.structured_data && event.structured_data.products && event.structured_data.products.length > 1) {
          const allProducts = [...event.structured_data.products]
          // 直接赋值带空products的结构化数据（响应式对象）
          messages.value[assistantIdx].structured_data = { ...event.structured_data, products: [] }
          isLoading.value = false
          statusText.value = ''
          currentController.value = null
          allProducts.forEach((product, idx) => {
            setTimeout(() => {
              // 直接操作响应式对象的products数组，触发视图更新
              messages.value[assistantIdx].structured_data.products.push(product)
              scrollToBottom()
            }, idx * 150)
          })
        } else {
          messages.value[assistantIdx].structured_data = event.structured_data || null
          isLoading.value = false
          statusText.value = ''
          currentController.value = null
        }
        scrollToBottom()
      },
      onError: (event) => {
        messages.value[assistantIdx].content = event.message || '抱歉，处理请求时出错了。'
        messages.value[assistantIdx].structured_data = null
        isLoading.value = false
        statusText.value = ''
        currentController.value = null
        if (event.message && event.message.includes('未响应')) {
          isOnline.value = false
        }
        scrollToBottom()
      }
    })
  } catch (error) {
    isOnline.value = false
    let errorText = '抱歉，处理请求时出错了。'
    if (error.message && error.message.includes('HTTP')) {
      errorText = '智能助手服务内部错误，请稍后重试。'
    } else if (error.message && error.message.includes('fetch')) {
      errorText = '无法连接到智能助手服务，请检查网络连接或服务是否运行。'
    }
    messages.value[assistantIdx].content = errorText
    messages.value[assistantIdx].structured_data = null
    isLoading.value = false
    statusText.value = ''
    currentController.value = null
    scrollToBottom()
  }
}

const fetchSessions = async () => {
  const token = localStorage.getItem('token')
  try {
    const res = await axios.get('http://localhost:8001/chat/sessions/list', {
      headers: { Authorization: token }
    })
    savedSessions.value = res.data
  } catch (err) {
    console.error('获取会话列表失败', err)
  }
}

const saveCurrentSession = async () => {
  if (messages.value.length === 0) return
  const token = localStorage.getItem('token')
  try {
    await axios.post('http://localhost:8001/chat/sessions/save', {
      messages: messages.value.map(m => ({ role: m.role, content: m.content, timestamp: m.timestamp })),
      end_time: new Date().toISOString(),
      file_name: currentSessionFile.value
    }, { headers: { Authorization: token } })
    fetchSessions()
  } catch (err) {
    console.error('保存会话失败', err)
  }
}

const loadSession = async (fileName) => {
  await saveCurrentSession()
  try {
    const token = localStorage.getItem('token')
    const res = await axios.get(`http://localhost:8001/chat/sessions/load/${fileName}`, {
      headers: { Authorization: token }
    })
    // 兼容旧会话：补上structured_data字段
    messages.value = (res.data.messages || []).map(m => ({
      role: m.role,
      content: m.content || '',
      structured_data: m.structured_data || null,
      timestamp: m.timestamp
    }))
    currentSessionFile.value = fileName
    scrollToBottom()
  } catch (err) {
    console.error('加载会话失败', err)
  }
}

const selectQuickAction = (action) => {
  userInput.value = action
  sendMessage()
}

const clearChat = async () => {
  if (messages.value.length > 0 && confirm('确定要清空对话历史吗？')) {
    await saveCurrentSession()
    messages.value = []
    currentSessionFile.value = null
    sessionId.value = 'session_' + Date.now()
    localStorage.setItem('chat_session_id', sessionId.value)
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    alert('已复制到剪贴板！')
  } catch (err) {
    console.error('复制失败:', err)
  }
}

const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const logout = () => {
  localStorage.removeItem('token')
  store.commit('setIsLogin', false)
  messages.value = []
  router.push('/login')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// ================== 消息格式化工具函数（保留原逻辑） ==================
const extractLastJson = (text) => {
  let stack = [];
  let start = -1;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '{') {
      if (stack.length === 0) start = i;
      stack.push('{');
    } else if (text[i] === '}') {
      if (stack.length > 0) {
        stack.pop();
        if (stack.length === 0 && start !== -1) {
          const candidate = text.substring(start, i + 1);
          try {
            JSON.parse(candidate);
            return candidate;
          } catch (e) { }
        }
      }
    }
  }
  return null;
}

const formatMessage = (text) => {
  if (!text) return '';
  const lastJson = extractLastJson(text);
  if (lastJson) {
    try {
      const data = JSON.parse(lastJson);
      if (data.type === 'product_list' && Array.isArray(data.products)) {
        // 简化版：仅返回JSON前的文本（结构化数据由MessageContent组件渲染）
        const intro = text.split(lastJson)[0].trim();
        return intro ? intro.replace(/\n/g, '<br>') : '';
      }
      // 其他结构化类型：同样只返回前缀文本
      const intro = text.split(lastJson)[0].trim();
      return intro ? intro.replace(/\n/g, '<br>') : '';
    } catch (e) {
      console.error('解析JSON失败', e);
    }
  }
  return text.replace(/\n/g, '<br>');
};

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
}

const handleBeforeUnload = () => {
  if (messages.value.length === 0) return
  const token = localStorage.getItem('token')
  const data = {
    messages: messages.value.map(m => ({ role: m.role, content: m.content, timestamp: m.timestamp })),
    end_time: new Date().toISOString(),
    token: token,
    file_name: currentSessionFile.value
  }
  const blob = new Blob([JSON.stringify(data)], { type: 'application/json' })
  navigator.sendBeacon('http://localhost:8001/chat/sessions/save', blob)
}

// 初始化
onMounted(() => {
  const savedSessionId = localStorage.getItem('chat_session_id')
  if (savedSessionId) sessionId.value = savedSessionId
  checkAgentStatus()
  const statusInterval = setInterval(checkAgentStatus, 60000)
  if (textArea.value) textArea.value.focus()
  debugInfo.value = { tokenStatus: isUserLoggedIn.value ? '有效' : '未登录', userEmail: currentUserEmail.value }
  currentSessionFile.value = null
  fetchSessions()
  window.addEventListener('beforeunload', handleBeforeUnload)
  return () => clearInterval(statusInterval)
})

onUnmounted(() => {
  // 组件卸载时取消正在进行的SSE请求
  if (currentController.value) {
    currentController.value.abort()
    currentController.value = null
  }
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

watch(userInput, () => {
  nextTick(() => {
    if (textArea.value) {
      textArea.value.style.height = 'auto'
      textArea.value.style.height = Math.min(textArea.value.scrollHeight, 120) + 'px'
    }
  })
})

watch(isUserLoggedIn, (newValue) => {
  debugInfo.value = { tokenStatus: newValue ? '有效' : '未登录', userEmail: newValue ? currentUserEmail.value : '' }
  if (newValue) fetchSessions()
})
</script>

<style lang="less" scoped>
/* ========== 极简风格样式 ========== */
* {
  box-sizing: border-box;
}

.agent-chat-page {
  min-height: 100vh;
  background: #f9fafb;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #1f2937;
}

.agent-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.agent-nav {
  background: #ffffff;
  padding: 12px 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.back-home {
  color: #374151;
  text-decoration: none;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  background: #f3f4f6;
  transition: background 0.2s;
  &:hover { background: #e5e7eb; }
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 10px;
  h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #111827;
  }
  .agent-icon {
    display: flex;
    align-items: center;
  }
}

.agent-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 20px;
  &.online { color: #059669; background: #ecfdf5; }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #d1d5db;
    .online & { background: #10b981; }
  }
}

.nav-right {
  .help-btn {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    color: #374151;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
    &:hover { background: #e5e7eb; }
    .el-icon { font-size: 16px; }
  }
}

/* 主内容区 */
.agent-main {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 0;
  height: calc(100vh - 80px);
  padding: 16px 24px;
}

.agent-sidebar {
  width: 260px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  .sidebar-section {
    h3 {
      margin: 0 0 12px;
      font-size: 13px;
      font-weight: 600;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
  }
  .history-list {
    .history-item {
      padding: 8px 12px;
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.15s;
      &:hover { background: #f3f4f6; }
      .history-preview {
        font-size: 14px;
        color: #374151;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 2px;
      }
      .history-time {
        font-size: 12px;
        color: #9ca3af;
      }
    }
    .no-history {
      font-size: 13px;
      color: #9ca3af;
      text-align: center;
      padding: 20px 0;
    }
  }
  .user-section {
    margin-top: auto;
    .user-status {
      .logged-in, .logged-out {
        padding: 12px;
        border-radius: 8px;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
      }
      .user-info {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        .user-icon {
          display: flex;
          align-items: center;
        }
        .user-name { font-size: 14px; font-weight: 500; }
        .user-email { font-size: 12px; color: #6b7280; }
      }
      .logout-btn {
        width: 100%;
        padding: 6px 12px;
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        &:hover { background: #dc2626; }
      }
      .login-prompt {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #f59e0b;
        margin-bottom: 8px;
        font-size: 14px;
      }
      .login-link { text-decoration: none; }
      .login-btn {
        width: 100%;
        padding: 6px 12px;
        background: #10b981;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        &:hover { background: #059669; }
      }
      .login-hint {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 8px;
        text-align: center;
      }
    }
  }
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 0 12px 12px 0;
  overflow: hidden;
  &.full-width { border-radius: 12px; }
}

.chat-box {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.welcome-message {
  display: flex;
  gap: 20px;
  background: #f9fafb;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  .welcome-avatar {
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f3f4f6;
    border-radius: 16px;
    color: #10b981;
  }
  .welcome-content {
    h3 { margin: 0 0 12px; font-size: 18px; color: #111827; }
    p { margin: 8px 0; color: #4b5563; font-size: 14px; }
    ul { margin: 12px 0; padding-left: 20px; li { margin: 6px 0; font-size: 14px; display: flex; align-items: center; gap: 6px; .el-icon { font-size: 14px; } } }
    .login-reminder { font-size: 13px; color: #f59e0b; display: flex; align-items: center; gap: 4px; }
  }
}

.message {
  display: flex;
  margin-bottom: 24px;
  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6b7280;
    margin-right: 12px;
    flex-shrink: 0;
  }
  &.user .message-avatar {
    background: #10b981;
    color: white;
  }
  .message-content {
    max-width: 75%;
    padding: 12px 16px;
    border-radius: 12px;
    background: #f9fafb;
    color: #1f2937;
    font-size: 15px;
    line-height: 1.5;
    position: relative;
  }
  &.user .message-content {
    background: #10b981;
    color: white;
    margin-left: auto;
  }
  .message-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 12px;
    color: #9ca3af;
    .user & { color: rgba(255,255,255,0.7); }
    .action-btn {
      background: none;
      border: none;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
      color: inherit;
      opacity: 0.5;
      display: flex;
      align-items: center;
      &:hover { opacity: 1; background: rgba(0,0,0,0.05); }
      .el-icon { font-size: 14px; }
    }
  }
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #6b7280;
  .typing-dots {
    display: flex;
    gap: 4px;
    span {
      width: 6px; height: 6px;
      border-radius: 50%;
      background: #10b981;
      animation: typing 1.4s infinite ease-in-out;
      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
    }
  }
  @keyframes typing {
    0%, 80%, 100% { opacity: 0.4; }
    40% { opacity: 1; }
  }
}

.input-area {
  border-top: 1px solid #e5e7eb;
  padding: 16px 24px;
  background: #ffffff;
  .input-wrapper {
    display: flex;
    gap: 10px;
    margin-bottom: 8px;
    textarea {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      resize: none;
      font-family: inherit;
      font-size: 14px;
      line-height: 1.5;
      background: #f9fafb;
      transition: border 0.2s;
      &:focus { outline: none; border-color: #10b981; background: white; }
      &:disabled { background: #f3f4f6; }
    }
    .input-controls {
      display: flex;
      gap: 6px;
      align-items: flex-end;
    }
    .control-btn {
      width: 36px; height: 36px;
      border: 1px solid #e5e7eb;
      background: white;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #6b7280;
      transition: all 0.2s;
      &:hover:not(:disabled) { border-color: #10b981; color: #10b981; }
      &:disabled { opacity: 0.5; }
      .el-icon { font-size: 16px; }
    }
    .send-btn {
      height: 36px;
      padding: 0 18px;
      background: #10b981;
      color: white;
      border: none;
      border-radius: 10px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      transition: background 0.2s;
      &:hover:not(:disabled) { background: #059669; }
      &:disabled { background: #d1d5db; cursor: not-allowed; }
      .send-icon { font-size: 14px; }
    }
  }
  .input-hints {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #9ca3af;
    .offline-warning { color: #ef4444; display: flex; align-items: center; gap: 4px; }
  }
}

.quick-actions-bar {
  padding: 12px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  .quick-actions-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    .quick-action-btn {
      background: white;
      border: 1px solid #e5e7eb;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      color: #374151;
      cursor: pointer;
      transition: all 0.2s;
      &:hover:not(:disabled) { background: #f3f4f6; border-color: #10b981; color: #10b981; }
      &:disabled { opacity: 0.5; }
    }
  }
}

/* 帮助弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.help-modal {
  width: 520px;
  max-height: 80vh;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.08);
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e7eb;
    h2 { margin: 0; font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .close-btn {
      background: none;
      border: none;
      font-size: 20px;
      color: #9ca3af;
      cursor: pointer;
      display: flex;
      &:hover { color: #111827; }
    }
  }
  .modal-content {
    padding: 24px;
    overflow-y: auto;
    .help-section {
      margin-bottom: 24px;
      h3 { font-size: 15px; font-weight: 600; margin: 0 0 8px; color: #111827; display: flex; align-items: center; gap: 6px; }
      p { font-size: 14px; color: #4b5563; margin: 4px 0; display: flex; align-items: center; gap: 4px; }
      .help-examples .example {
        margin: 8px 0;
        padding: 10px;
        background: #f9fafb;
        border-radius: 8px;
        font-size: 14px;
        strong { color: #374151; }
        code {
          display: block;
          margin-top: 4px;
          padding: 4px 8px;
          background: white;
          border-radius: 4px;
          font-family: monospace;
          color: #10b981;
          border: 1px solid #e5e7eb;
          font-size: 13px;
        }
      }
    }
  }
}
</style>