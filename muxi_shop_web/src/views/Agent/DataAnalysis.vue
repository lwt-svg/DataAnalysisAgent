<!-- DataAnalysis.vue - B端数据分析助手主页面
  设计风格：企业级B端，简约专业
  布局：顶部导航 + 左侧快捷指令/历史 + 中间聊天 + 右侧图表
-->
<template>
  <div class="analysis-page">
    <!-- ============ 顶部导航栏 ============ -->
    <header class="top-bar">
      <div class="top-bar-inner">
        <div class="brand">
          <router-link to="/" class="back-link">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回商城</span>
          </router-link>
          <div class="brand-divider"></div>
          <h1 class="brand-title">
            <el-icon class="brand-icon"><DataAnalysis /></el-icon>
            <span>数据分析助手</span>
          </h1>
          <span class="brand-tag">B端 · Multi-Agent</span>
        </div>

        <div class="top-actions">
          <el-tooltip content="服务健康状态" placement="bottom">
            <div class="health-status" :class="{ healthy: isHealthy }">
              <span class="health-dot"></span>
              {{ isHealthy ? '服务正常' : '服务异常' }}
            </div>
          </el-tooltip>
          <el-tooltip content="Token消耗统计" placement="bottom">
            <button class="icon-btn" @click="showTokenUsage = true">
              <el-icon><Coin /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="工具列表" placement="bottom">
            <button class="icon-btn" @click="showToolsList = true">
              <el-icon><Tools /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </div>
    </header>

    <!-- ============ 主体区域 ============ -->
    <div class="main-layout">
      <!-- 左侧栏：快捷指令 + 历史会话 -->
      <aside class="left-sidebar" :class="{ collapsed: !showSidebar }">
        <div class="sidebar-toggle" @click="showSidebar = !showSidebar">
          <el-icon><Fold v-if="showSidebar" /><Expand v-else /></el-icon>
        </div>

        <div v-show="showSidebar" class="sidebar-content">
          <!-- 快捷指令 -->
          <div class="sidebar-section">
            <div class="section-title">
              <el-icon><MagicStick /></el-icon>
              <span>快捷指令</span>
            </div>
            <div class="quick-commands">
              <button
                v-for="cmd in quickCommands"
                :key="cmd.text"
                class="command-btn"
                :class="{ active: loading && currentCommand === cmd.text }"
                @click="sendQuickCommand(cmd.text)"
                :disabled="loading"
              >
                <el-icon><component :is="cmd.icon" /></el-icon>
                <span>{{ cmd.label }}</span>
              </button>
            </div>
          </div>

          <!-- 使用提示 -->
          <div class="sidebar-section">
            <div class="section-title">
              <el-icon><InfoFilled /></el-icon>
              <span>使用提示</span>
            </div>
            <div class="tips-list">
              <div v-for="tip in tips" :key="tip" class="tip-item">
                <el-icon class="tip-icon"><Promotion /></el-icon>
                <span>{{ tip }}</span>
              </div>
            </div>
          </div>

          <!-- 历史会话 -->
          <div class="sidebar-section">
            <div class="section-title">
              <el-icon><Clock /></el-icon>
              <span>历史会话</span>
              <button class="clear-btn" @click="clearHistory" v-if="historyList.length">清空</button>
            </div>
            <div class="history-list">
              <div
                v-for="(item, idx) in historyList"
                :key="idx"
                class="history-item"
                @click="loadHistory(item)"
              >
                <div class="history-preview">{{ item.preview }}</div>
                <div class="history-time">{{ item.time }}</div>
              </div>
              <div v-if="!historyList.length" class="empty-history">
                暂无历史会话
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间聊天区 -->
      <main class="chat-area">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesBox">
          <!-- 欢迎引导 -->
          <div v-if="!messages.length" class="welcome-screen">
            <div class="welcome-icon">
              <el-icon :size="48"><DataAnalysis /></el-icon>
            </div>
            <h2 class="welcome-title">数据分析助手</h2>
            <p class="welcome-desc">
              基于 Multi-Agent 架构的电商数据分析系统，支持销售查询、趋势分析、商品排行、用户分群、异常检测、报告生成
            </p>
            <div class="welcome-features">
              <div v-for="f in features" :key="f.title" class="feature-card">
                <el-icon class="feature-icon" :size="24"><component :is="f.icon" /></el-icon>
                <div class="feature-title">{{ f.title }}</div>
                <div class="feature-desc">{{ f.desc }}</div>
              </div>
            </div>
          </div>

          <!-- 消息气泡 -->
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-row"
            :class="msg.role"
          >
            <div class="message-avatar">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else><DataAnalysis /></el-icon>
            </div>
            <div class="message-body">
              <div class="message-meta">
                <span class="message-author">{{ msg.role === 'user' ? '我' : '数据助手' }}</span>
                <span class="message-time">{{ msg.time }}</span>
                <span v-if="msg.source" class="message-source">{{ msg.source }}</span>
              </div>
              <div class="message-content">
                <!-- Markdown渲染 -->
                <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              </div>
              <!-- 图表渲染（仅助手消息且有chart_data） -->
              <div v-if="msg.role === 'assistant' && msg.chart_data" class="message-chart">
                <ChartRender :chart-data="msg.chart_data" />
              </div>
            </div>
          </div>

          <!-- 加载中提示（SSE进度） -->
          <div v-if="loading" class="message-row assistant">
            <div class="message-avatar">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="message-body">
              <div class="loading-indicator">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-text">{{ loadingText }}</span>
              </div>
              <!-- SSE进度步骤 -->
              <div v-if="progressSteps.length > 0" class="progress-steps">
                <div v-for="(step, idx) in progressSteps" :key="idx" class="progress-step">
                  <span class="step-icon">{{ step.icon }}</span>
                  <span class="step-text">{{ step.text }}</span>
                </div>
              </div>
              <!-- 流式输出内容（实时显示） -->
              <div v-if="streamingContent" class="streaming-content" v-html="renderMarkdown(streamingContent)"></div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入您的分析问题，如：今天GMV多少？本周热销TOP10？今日有异常吗？"
              resize="none"
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="loading"
            />
            <button
              class="send-btn"
              @click="sendMessage"
              :disabled="!inputText.trim() || loading"
            >
              <el-icon><Promotion /></el-icon>
              <span>发送</span>
            </button>
          </div>
          <div class="input-hint">
            按 Enter 发送 · Shift+Enter 换行 · 数据来源：MySQL实时查询
          </div>
        </div>
      </main>
    </div>

    <!-- ============ 弹窗：Token消耗 ============ -->
    <el-dialog v-model="showTokenUsage" title="Token消耗统计" width="600px">
      <div v-if="tokenUsage" class="token-stats">
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-label">总调用次数</div>
            <div class="stat-value">{{ tokenUsage.total_calls }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">总Token</div>
            <div class="stat-value">{{ tokenUsage.total_tokens }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">输入Token</div>
            <div class="stat-value">{{ tokenUsage.total_prompt_tokens }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">输出Token</div>
            <div class="stat-value">{{ tokenUsage.total_completion_tokens }}</div>
          </div>
        </div>
        <h4>按意图分组</h4>
        <el-table :data="intentTable" stripe size="small">
          <el-table-column prop="intent" label="意图" />
          <el-table-column prop="calls" label="调用次数" width="100" />
          <el-table-column prop="total_tokens" label="总Token" width="120" />
        </el-table>
      </div>
    </el-dialog>

    <!-- ============ 弹窗：工具列表 ============ -->
    <el-dialog v-model="showToolsList" title="Agent工具列表（按子Agent分组）" width="700px">
      <el-table :data="toolsList" stripe size="small">
        <el-table-column prop="agent_group" label="所属Agent" width="140">
          <template #default="{ row }">
            <el-tag :type="agentTagType(row.agent_group)" size="small">{{ row.agent_group }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="工具名" width="220" />
        <el-table-column prop="description" label="说明" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import ChartRender from '@/components/DataAnalysis/ChartRender.vue'
import {
  sendAnalysisMessage,
  sendAnalysisMessageStream,
  checkAnalysisHealth,
  getTokenUsage,
  getAnalysisTools
} from '@/network/analysis'

// 简易Markdown渲染（避免XSS，仅支持基础语法）
function renderMarkdown(text) {
  if (!text) return ''
  // 转义HTML
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 表格（必须先处理）
  html = html.replace(/^\|(.+)\|\n\|([-:\s|]+)\|\n((?:\|.+\|\n?)*)/gm, (match, header, sep, body) => {
    const headers = header.split('|').map(h => h.trim()).filter(Boolean)
    const rows = body.trim().split('\n').map(r =>
      r.split('|').map(c => c.trim()).filter(Boolean)
    )
    let table = '<table class="md-table"><thead><tr>'
    headers.forEach(h => table += `<th>${h}</th>`)
    table += '</tr></thead><tbody>'
    rows.forEach(r => {
      table += '<tr>'
      r.forEach(c => table += `<td>${c}</td>`)
      table += '</tr>'
    })
    table += '</tbody></table>'
    return table
  })
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  // 分割线
  html = html.replace(/^---$/gm, '<hr/>')
  // 加粗（**text** → <strong>）
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 列表（支持 - 和 * 两种标记）
  html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  // 换行
  html = html.replace(/\n/g, '<br/>')
  // 修复表格内的br
  html = html.replace(/<br\/><table/g, '<table')
  html = html.replace(/<\/table><br\/>/g, '</table>')
  return html
}

export default {
  name: 'DataAnalysisPage',
  components: { ChartRender },
  data() {
    return {
      inputText: '',
      messages: [],
      loading: false,
      loadingText: '正在分析数据...',
      progressSteps: [],
      streamingContent: '',
      sseController: null,
      currentCommand: '',
      sessionId: null,
      isHealthy: false,
      showSidebar: true,
      showTokenUsage: false,
      showToolsList: false,
      tokenUsage: null,
      toolsList: [],
      historyList: [],
      quickCommands: [
        { label: '今日日报', text: '今日日报', icon: 'Document' },
        { label: '本周周报', text: '本周周报', icon: 'Calendar' },
        { label: '异常巡检', text: '异常巡检', icon: 'WarningFilled' },
        { label: '热销TOP10', text: '最近30天商品销量排行榜TOP10', icon: 'Trophy' },
        { label: '用户分群', text: '最近30天用户RFM分群分析', icon: 'UserFilled' },
        { label: '销售趋势', text: '最近7天GMV趋势', icon: 'TrendCharts' }
      ],
      tips: [
        '支持自然语言提问',
        '所有数据来自实时查询',
        '可指定时间范围',
        '复杂报告自动生成图表'
      ],
      features: [
        { title: '销售查询', desc: 'GMV、订单量、客单价', icon: 'Money' },
        { title: '趋势分析', desc: '环比、同比、走势图', icon: 'TrendCharts' },
        { title: '商品排行', desc: '销量榜、收入榜、品类', icon: 'Trophy' },
        { title: '用户分群', desc: 'RFM分析、核心用户', icon: 'UserFilled' },
        { title: '异常检测', desc: 'Z-Score、指标监控', icon: 'WarningFilled' },
        { title: '报告生成', desc: '日报、周报自动生成', icon: 'Document' }
      ]
    }
  },
  computed: {
    intentTable() {
      if (!this.tokenUsage || !this.tokenUsage.by_intent) return []
      return Object.entries(this.tokenUsage.by_intent).map(([intent, stats]) => ({
        intent,
        calls: stats.calls,
        total_tokens: stats.total_tokens
      }))
    }
  },
  mounted() {
    this.checkHealth()
    // 每30秒检查一次健康状态
    setInterval(this.checkHealth, 30000)
    // 从localStorage恢复历史会话
    this.loadHistoryFromStorage()
  },
  methods: {
    renderMarkdown,
    async checkHealth() {
      try {
        const res = await checkAnalysisHealth()
        this.isHealthy = res.status === 'healthy'
      } catch {
        this.isHealthy = false
      }
    },
    async sendQuickCommand(text) {
      this.inputText = text
      await this.sendMessage()
    },
    async sendMessage() {
      const text = this.inputText.trim()
      if (!text || this.loading) return

      // 添加用户消息
      const now = this.formatTime()
      this.messages.push({
        role: 'user',
        content: text,
        time: now
      })

      this.inputText = ''
      this.loading = true
      this.loadingText = '正在分析数据...'
      this.progressSteps = []
      this.streamingContent = ''
      this.currentCommand = text

      // 滚动到底部
      this.$nextTick(() => this.scrollToBottom())

      const token = window.localStorage.getItem('token')

      // 使用SSE流式请求
      this.sseController = sendAnalysisMessageStream(
        {
          message: text,
          session_id: this.sessionId,
          token: token,
          // history排除最后一条（当前刚添加的用户消息），避免与message字段重复
          history: this.messages
            .filter(m => m.role === 'user' || m.role === 'assistant')
            .slice(0, -1)
            .slice(-4)
            .map(m => ({ role: m.role, content: m.content }))
        },
        {
          onStart: (event) => {
            this.loadingText = event.message
          },
          onIntent: (event) => {
            this.loadingText = event.message
            this.progressSteps.push({ icon: '🎯', text: event.message })
          },
          onStep: (event) => {
            this.loadingText = event.message
            this.progressSteps.push({ icon: '⚙️', text: event.message })
          },
          onToolStart: (event) => {
            this.loadingText = event.message
            this.progressSteps.push({ icon: '🔧', text: event.message })
          },
          onToolEnd: (event) => {
            this.progressSteps.push({ icon: '✅', text: event.message })
          },
          onChunk: (event) => {
            this.loadingText = '正在生成回复...'
            this.streamingContent += event.message
            this.$nextTick(() => this.scrollToBottom())
          },
          onDone: (event) => {
            // 添加最终助手回复
            this.messages.push({
              role: 'assistant',
              content: event.response || '（无回复）',
              time: this.formatTime(),
              source: event.source,
              chart_data: event.chart_data
            })

            if (event.session_id) {
              this.sessionId = event.session_id
            }

            this.addToHistory(text)
            this.loading = false
            this.loadingText = ''
            this.progressSteps = []
            this.streamingContent = ''
            this.currentCommand = ''
            this.sseController = null
            this.$nextTick(() => this.scrollToBottom())
          },
          onError: (event) => {
            this.messages.push({
              role: 'assistant',
              content: '⚠️ 分析失败：' + (event.message || '服务异常'),
              time: this.formatTime()
            })
            this.loading = false
            this.loadingText = ''
            this.progressSteps = []
            this.streamingContent = ''
            this.currentCommand = ''
            this.sseController = null
            this.$nextTick(() => this.scrollToBottom())
          }
        }
      )
    },
    addToHistory(text) {
      this.historyList.unshift({
        preview: text.length > 30 ? text.slice(0, 30) + '...' : text,
        time: this.formatTime(),
        messages: [...this.messages]
      })
      if (this.historyList.length > 20) {
        this.historyList = this.historyList.slice(0, 20)
      }
      this.saveHistoryToStorage()
    },
    loadHistory(item) {
      if (item.messages) {
        this.messages = [...item.messages]
        this.$nextTick(() => this.scrollToBottom())
      }
    },
    clearHistory() {
      this.$confirm('确定清空所有历史会话？', '提示', {
        type: 'warning'
      }).then(() => {
        this.historyList = []
        localStorage.removeItem('analysis_history')
        this.$message.success('已清空')
      }).catch(() => {})
    },
    // 历史会话持久化到localStorage
    saveHistoryToStorage() {
      try {
        // 只保存必要字段，避免chart_data等大对象撑爆localStorage
        const toSave = this.historyList.map(h => ({
          preview: h.preview,
          time: h.time,
          messages: (h.messages || []).map(m => ({
            role: m.role,
            content: m.content,
            time: m.time,
            source: m.source
            // 注意：不保存chart_data，避免localStorage超限（5MB）
          }))
        }))
        localStorage.setItem('analysis_history', JSON.stringify(toSave))
      } catch (e) {
        console.warn('历史会话保存失败:', e)
      }
    },
    loadHistoryFromStorage() {
      try {
        const stored = localStorage.getItem('analysis_history')
        if (stored) {
          this.historyList = JSON.parse(stored)
        }
      } catch (e) {
        console.warn('历史会话恢复失败:', e)
        this.historyList = []
      }
    },
    async loadTokenUsage() {
      try {
        this.tokenUsage = await getTokenUsage()
      } catch (err) {
        this.$message.error('获取Token统计失败')
      }
    },
    async loadToolsList() {
      try {
        const res = await getAnalysisTools()
        this.toolsList = res.tools || []
      } catch (err) {
        this.$message.error('获取工具列表失败')
      }
    },
    agentTagType(group) {
      const map = { sql_agent: 'primary', analysis_agent: 'success', report_agent: 'warning' }
      return map[group] || 'info'
    },
    formatTime() {
      const d = new Date()
      return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
    },
    scrollToBottom() {
      const box = this.$refs.messagesBox
      if (box) box.scrollTop = box.scrollHeight
    }
  },
  watch: {
    showTokenUsage(val) {
      if (val) this.loadTokenUsage()
    },
    showToolsList(val) {
      if (val) this.loadToolsList()
    }
  }
}
</script>

<style scoped>
/* ============ 全局 ============ */
.analysis-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", "Segoe UI", sans-serif;
  color: #1d2129;
  font-size: 14px;
}

/* ============ 顶部导航 ============ */
.top-bar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e5e6eb;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.top-bar-inner {
  height: 100%;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #4e5969;
  font-size: 13px;
  text-decoration: none;
  transition: color 0.2s;
}
.back-link:hover { color: #1e80ff; }

.brand-divider {
  width: 1px;
  height: 18px;
  background: #e5e6eb;
}

.brand-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  margin: 0;
}
.brand-icon { color: #1e80ff; }

.brand-tag {
  padding: 2px 8px;
  background: #e8f3ff;
  color: #1e80ff;
  font-size: 11px;
  border-radius: 4px;
  font-weight: 500;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.health-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff7e8;
  color: #ff7d00;
  border-radius: 4px;
  font-size: 12px;
}
.health-status.healthy {
  background: #e8ffea;
  color: #00b42a;
}
.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff7d00;
}
.health-status.healthy .health-dot {
  background: #00b42a;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #4e5969;
  transition: all 0.2s;
}
.icon-btn:hover {
  background: #f2f3f5;
  color: #1e80ff;
}

/* ============ 主体布局 ============ */
.main-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ============ 左侧栏 ============ */
.left-sidebar {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e5e6eb;
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  position: relative;
  flex-shrink: 0;
}
.left-sidebar.collapsed {
  width: 0;
}

.sidebar-toggle {
  position: absolute;
  right: -16px;
  top: 16px;
  width: 32px;
  height: 32px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: #4e5969;
}
.sidebar-toggle:hover {
  color: #1e80ff;
  border-color: #1e80ff;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.sidebar-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #86909c;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.section-title .clear-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #86909c;
  font-size: 11px;
  cursor: pointer;
}
.section-title .clear-btn:hover { color: #f53f3f; }

.quick-commands {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.command-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f7f8fa;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  color: #1d2129;
  font-size: 13px;
  transition: all 0.2s;
  text-align: left;
}
.command-btn:hover {
  background: #e8f3ff;
  color: #1e80ff;
  border-color: #bedaff;
}
.command-btn.active {
  background: #e8f3ff;
  color: #1e80ff;
  border-color: #1e80ff;
}
.command-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #4e5969;
  line-height: 1.6;
}
.tip-icon {
  color: #1e80ff;
  margin-top: 2px;
  flex-shrink: 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.history-item {
  padding: 8px 10px;
  background: #f7f8fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}
.history-item:hover {
  background: #e8f3ff;
}
.history-preview {
  font-size: 12px;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-time {
  font-size: 11px;
  color: #86909c;
  margin-top: 4px;
}
.empty-history {
  font-size: 12px;
  color: #c9cdd4;
  text-align: center;
  padding: 16px;
}

/* ============ 聊天区 ============ */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fa;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 欢迎页 */
.welcome-screen {
  max-width: 800px;
  margin: 60px auto;
  text-align: center;
}
.welcome-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f3ff 0%, #d4e8ff 100%);
  border-radius: 20px;
  color: #1e80ff;
}
.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 12px;
}
.welcome-desc {
  font-size: 14px;
  color: #4e5969;
  line-height: 1.8;
  margin: 0 auto 32px;
  max-width: 540px;
}
.welcome-features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 720px;
  margin: 0 auto;
}
.feature-card {
  padding: 20px 16px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  transition: all 0.2s;
  text-align: left;
}
.feature-card:hover {
  border-color: #1e80ff;
  box-shadow: 0 4px 12px rgba(30,128,255,0.1);
  transform: translateY(-2px);
}
.feature-icon {
  color: #1e80ff;
  margin-bottom: 8px;
}
.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}
.feature-desc {
  font-size: 12px;
  color: #86909c;
}

/* 消息气泡 */
.message-row {
  display: flex;
  gap: 12px;
  max-width: 1000px;
  margin: 0 auto 20px;
}
.message-row.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}
.message-row.user .message-avatar {
  background: #1e80ff;
  color: #fff;
}
.message-row.assistant .message-avatar {
  background: linear-gradient(135deg, #1e80ff 0%, #00b42a 100%);
  color: #fff;
}

.message-body {
  flex: 1;
  min-width: 0;
}
.message-row.user .message-body {
  max-width: 70%;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}
.message-row.user .message-meta {
  justify-content: flex-end;
}
.message-author {
  font-weight: 600;
  color: #1d2129;
}
.message-time {
  color: #86909c;
}
.message-source {
  padding: 1px 6px;
  background: #e8f3ff;
  color: #1e80ff;
  border-radius: 3px;
  font-size: 11px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}
.message-row.user .message-content {
  background: #1e80ff;
  color: #fff;
  border-top-right-radius: 2px;
}
.message-row.assistant .message-content {
  background: #fff;
  color: #1d2129;
  border: 1px solid #e5e6eb;
  border-top-left-radius: 2px;
}

.message-chart {
  margin-top: 12px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px;
}

/* Markdown样式 */
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #1d2129;
}
.markdown-body :deep(h1) { font-size: 18px; }
.markdown-body :deep(h2) { font-size: 16px; }
.markdown-body :deep(h3) { font-size: 14px; }
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e6eb;
  margin: 12px 0;
}
.markdown-body :deep(strong) {
  font-weight: 600;
  color: #1d2129;
}
.markdown-body :deep(ul) {
  padding-left: 20px;
  margin: 8px 0;
}
.markdown-body :deep(li) {
  list-style: disc;
  margin: 4px 0;
}
.markdown-body :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
}
.markdown-body :deep(.md-table th),
.markdown-body :deep(.md-table td) {
  border: 1px solid #e5e6eb;
  padding: 6px 10px;
  text-align: left;
}
.markdown-body :deep(.md-table th) {
  background: #f7f8fa;
  font-weight: 600;
}
.markdown-body :deep(.md-table tr:nth-child(even)) {
  background: #fafbfc;
}

/* 加载指示 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  border-top-left-radius: 2px;
}
.loading-dot {
  width: 6px;
  height: 6px;
  background: #1e80ff;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }
.loading-text {
  margin-left: 8px;
  color: #86909c;
  font-size: 13px;
}
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* SSE进度步骤 */
.progress-steps {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.progress-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #4e5969;
  padding: 2px 0;
  animation: fadeIn 0.3s ease;
}
.step-icon {
  font-size: 14px;
}
.step-text {
  color: #86909c;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 流式输出内容 */
.streaming-content {
  margin-top: 12px;
  padding: 12px 14px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.7;
  color: #1d2129;
  max-height: 300px;
  overflow-y: auto;
}

/* 输入区 */
.input-area {
  padding: 12px 24px 16px;
  background: #fff;
  border-top: 1px solid #e5e6eb;
  flex-shrink: 0;
}
.input-wrapper {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid #e5e6eb;
  padding: 10px 14px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}
.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #1e80ff;
  box-shadow: 0 0 0 2px rgba(30,128,255,0.1);
}
.send-btn {
  height: 56px;
  padding: 0 20px;
  background: #1e80ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}
.send-btn:hover:not(:disabled) {
  background: #1572e8;
}
.send-btn:disabled {
  background: #c9cdd4;
  cursor: not-allowed;
}
.input-hint {
  max-width: 1000px;
  margin: 8px auto 0;
  font-size: 11px;
  color: #86909c;
  text-align: center;
}

/* ============ 弹窗 ============ */
.token-stats {
  padding: 0 4px;
}
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 8px;
  text-align: center;
}
.stat-label {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e80ff;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

/* 滚动条 */
.messages-container::-webkit-scrollbar,
.sidebar-content::-webkit-scrollbar {
  width: 6px;
}
.messages-container::-webkit-scrollbar-thumb,
.sidebar-content::-webkit-scrollbar-thumb {
  background: #c9cdd4;
  border-radius: 3px;
}
.messages-container::-webkit-scrollbar-thumb:hover,
.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: #86909c;
}

/* 响应式 */
@media (max-width: 1024px) {
  .left-sidebar { width: 200px; }
  .welcome-features { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .left-sidebar { display: none; }
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
