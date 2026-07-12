<!-- MessageContent.vue - 电商Agent消息内容渲染组件
  企业级简约风格，支持多种结构化数据类型渲染：
  - product_list: 商品卡片列表（含推荐理由）
  - score_summary: 评分摘要
  - comment_list: 评论列表
  - purchase_recommendation: 购买建议
  - sentiment_analysis: 口碑分析
  - positive_points / negative_points: 优缺点
  - sentiment_comparison: 商品对比
  - 无结构化数据: 渲染纯文本
-->
<template>
  <div class="msg-content">
    <!-- 纯文本部分（intro或完整回复） -->
    <div v-if="text" class="text-section" v-html="formattedText"></div>

    <!-- 结构化数据渲染 -->
    <template v-if="data">
      <!-- 商品列表 -->
      <div v-if="data.type === 'product_list'" class="product-list">
        <div class="block-title">商品推荐</div>
        <div
          v-for="(p, idx) in (data.products || [])"
          :key="idx"
          class="product-card"
        >
          <a :href="p.product_url || '#'" target="_blank" class="product-link">
            <div class="product-image-wrap">
              <img
                :src="p.image_url || ''"
                :alt="p.name"
                class="product-image"
                @error="onImgError"
              />
            </div>
            <div class="product-info">
              <div class="product-name">{{ p.name }}</div>
              <div class="product-meta">
                <span v-if="p.main_brand" class="meta-tag">{{ p.main_brand }}</span>
                <span v-if="p.main_category" class="meta-tag">{{ p.main_category }}</span>
              </div>
              <div v-if="p.reason" class="product-reason">
                <span class="reason-label">推荐理由</span>
                <span class="reason-text">{{ p.reason }}</span>
              </div>
              <div class="product-price">¥{{ formatPrice(p.price) }}</div>
            </div>
          </a>
        </div>
      </div>

      <!-- 评分摘要 -->
      <div v-else-if="data.type === 'score_summary'" class="score-summary">
        <div class="block-title">评分摘要</div>
        <div
          v-for="(p, idx) in (data.products || [])"
          :key="idx"
          class="score-row"
        >
          <div class="score-row-info">
            <div class="score-row-name">{{ p.name }}</div>
            <div class="score-row-sub">{{ p.total_comments || 0 }} 条评论</div>
          </div>
          <div class="score-row-value">
            <span class="score-num">{{ p.avg_score || '-' }}</span>
            <span class="score-max">/ 5</span>
          </div>
        </div>
      </div>

      <!-- 评论列表 -->
      <div v-else-if="data.type === 'comment_list'" class="comment-list">
        <div class="block-title">{{ data.product_name || '商品' }} 的评论</div>
        <div class="comment-summary">
          <span class="summary-score">综合评分 {{ data.avg_score || '-' }} / 5</span>
          <span class="summary-count">共 {{ data.total_comments || 0 }} 条</span>
        </div>
        <div
          v-for="(c, idx) in (data.comments || []).slice(0, 3)"
          :key="idx"
          class="comment-item"
        >
          <div class="comment-header">
            <span class="comment-nickname">{{ c.nickname || '匿名' }}</span>
            <span class="comment-meta">{{ c.score || '-' }} 分<span v-if="c.create_time"> · {{ c.create_time }}</span></span>
          </div>
          <div class="comment-content">{{ cleanComment(c.content) }}</div>
        </div>
        <div v-if="(data.comments || []).length > 3" class="comment-more">
          仅显示前 3 条评论
        </div>
      </div>

      <!-- 购买建议 -->
      <div v-else-if="data.type === 'purchase_recommendation'" class="purchase-rec">
        <div class="block-title">{{ data.product_name || '商品' }} 购买建议</div>
        <div class="rec-header">
          <span class="rec-badge" :class="recBadgeClass(data.recommendation)">
            {{ data.recommendation_text || data.recommendation || '' }}
          </span>
          <span class="rec-stats">好评率 {{ data.positive_rate || 0 }}% · {{ data.total_reviews || 0 }} 条评价</span>
        </div>
        <div v-if="data.pros && data.pros.length" class="rec-section">
          <div class="section-label pros-label">优点</div>
          <div class="tag-list">
            <span v-for="(p, i) in data.pros.slice(0, 3)" :key="'p'+i" class="tag pros-tag">{{ p }}</span>
          </div>
        </div>
        <div v-if="data.cons && data.cons.length" class="rec-section">
          <div class="section-label cons-label">注意</div>
          <div class="tag-list">
            <span v-for="(c, i) in data.cons.slice(0, 3)" :key="'c'+i" class="tag cons-tag">{{ c }}</span>
          </div>
        </div>
        <div v-if="data.summary" class="rec-summary">
          <span class="summary-label">总结</span>{{ data.summary }}
        </div>
      </div>

      <!-- 口碑分析 -->
      <div v-else-if="data.type === 'sentiment_analysis'" class="sentiment-analysis">
        <div class="block-title">{{ data.product_name || '商品' }} 口碑分析</div>
        <div class="stats-grid">
          <div class="stat-item stat-positive">
            <div class="stat-value">{{ data.sentiment_distribution?.positive_rate || 0 }}%</div>
            <div class="stat-label">好评率</div>
          </div>
          <div class="stat-item stat-neutral">
            <div class="stat-value">{{ data.total_reviews || 0 }}</div>
            <div class="stat-label">评论数</div>
          </div>
          <div class="stat-item stat-warning">
            <div class="stat-value">{{ data.divergence_score || 0 }}</div>
            <div class="stat-label">分歧度</div>
          </div>
        </div>
        <div class="dist-bar">
          <span class="dist-item dist-positive">好评 {{ data.sentiment_distribution?.positive || 0 }}</span>
          <span class="dist-item dist-negative">差评 {{ data.sentiment_distribution?.negative || 0 }}</span>
          <span class="dist-item dist-neutral">中评 {{ data.sentiment_distribution?.neutral || 0 }}</span>
        </div>
        <div v-if="data.top_positive_points && data.top_positive_points.length" class="rec-section">
          <div class="section-label pros-label">主要优点</div>
          <div class="tag-list">
            <span v-for="(p, i) in data.top_positive_points.slice(0, 3)" :key="'tp'+i" class="tag pros-tag">{{ p.point }}</span>
          </div>
        </div>
        <div v-if="data.top_negative_points && data.top_negative_points.length" class="rec-section">
          <div class="section-label cons-label">主要槽点</div>
          <div class="tag-list">
            <span v-for="(p, i) in data.top_negative_points.slice(0, 3)" :key="'tn'+i" class="tag cons-tag">{{ p.point }}</span>
          </div>
        </div>
        <div v-if="data.summary" class="rec-summary">
          <span class="summary-label">综合评价</span>{{ data.summary }}
        </div>
      </div>

      <!-- 正面评价 -->
      <div v-else-if="data.type === 'positive_points'" class="points-list">
        <div class="block-title pros-title">正面评价（共 {{ data.total || 0 }} 条）</div>
        <div
          v-for="(p, idx) in (data.points || [])"
          :key="idx"
          class="point-item pros-item"
        >
          <span class="point-text">{{ p.point }}</span>
          <span class="point-meta">评分 {{ p.score || '-' }} · 置信度 {{ Math.round((p.confidence || 0) * 100) }}%</span>
        </div>
      </div>

      <!-- 负面评价 -->
      <div v-else-if="data.type === 'negative_points'" class="points-list">
        <div class="block-title cons-title">负面评价（共 {{ data.total || 0 }} 条）</div>
        <div
          v-for="(p, idx) in (data.points || [])"
          :key="idx"
          class="point-item cons-item"
        >
          <span class="point-text">{{ p.point }}</span>
          <span class="point-meta">评分 {{ p.score || '-' }} · 置信度 {{ Math.round((p.confidence || 0) * 100) }}%</span>
        </div>
      </div>

      <!-- 商品对比 -->
      <div v-else-if="data.type === 'sentiment_comparison'" class="comparison-list">
        <div class="block-title">商品口碑对比</div>
        <div
          v-for="(p, idx) in (data.products || [])"
          :key="idx"
          class="comparison-item"
        >
          <div class="comp-name">{{ p.product_name }}</div>
          <div class="comp-bar-wrap">
            <div class="comp-bar" :style="{ width: (p.positive_rate || 0) + '%', background: barColor(p.positive_rate) }"></div>
          </div>
          <span class="comp-rate" :style="{ color: barColor(p.positive_rate) }">{{ p.positive_rate || 0 }}%</span>
          <div class="comp-sub">{{ p.total_reviews || 0 }} 条评论 · 分歧度 {{ p.divergence_score || 0 }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'MessageContent',
  props: {
    text: { type: String, default: '' },
    data: { type: Object, default: null }
  },
  computed: {
    formattedText() {
      if (!this.text) return ''
      let html = this.escapeHtml(this.text)
      html = html.replace(/\n/g, '<br>')
      // 价格高亮
      html = html.replace(/¥\d+(\.\d+)?/g, '<span class="price-highlight">$&</span>')
      return html
    }
  },
  methods: {
    escapeHtml(unsafe) {
      if (!unsafe) return ''
      return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
    },
    formatPrice(p) {
      if (p === null || p === undefined || p === '') return ''
      const n = Number(p)
      return isNaN(n) ? '' : n.toFixed(2)
    },
    onImgError(e) {
      e.target.src = 'https://via.placeholder.com/80x80?text=No+Image'
    },
    cleanComment(content) {
      if (!content) return ''
      let c = String(content).trim()
      c = c.replace(/商品名称[:：][^\n\r]*[\n\r]?/g, '')
      c = c.replace(/评论内容[:：]/g, '')
      c = c.replace(/评分[:：][^\n\r]*/g, '')
      c = c.replace(/昵称[:：][^\n\r]*/g, '')
      return c.trim()
    },
    recBadgeClass(rec) {
      if (rec === 'recommended') return 'badge-green'
      if (rec === 'neutral') return 'badge-orange'
      return 'badge-red'
    },
    barColor(rate) {
      if (rate >= 70) return '#059669'
      if (rate >= 50) return '#d97706'
      return '#dc2626'
    }
  }
}
</script>

<style lang="less" scoped>
/* ========== 企业级简约风格 ========== */
.msg-content {
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;

  .text-section {
    margin-bottom: 8px;
    word-break: break-word;
    :deep(.price-highlight) {
      color: #dc2626;
      font-weight: 600;
    }
  }

  .block-title {
    font-size: 14px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e7eb;
  }
}

/* 商品列表 */
.product-list {
  margin-top: 4px;
  .product-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
    &:hover {
      border-color: #93c5fd;
      box-shadow: 0 1px 4px rgba(37, 99, 235, 0.08);
    }
    &:last-child { margin-bottom: 0; }
  }
  .product-link {
    display: flex;
    text-decoration: none;
    color: inherit;
  }
  .product-image-wrap {
    flex-shrink: 0;
    width: 80px;
    height: 80px;
    background: #f9fafb;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .product-image {
    width: 80px;
    height: 80px;
    object-fit: cover;
    display: block;
  }
  .product-info {
    flex: 1;
    min-width: 0;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .product-name {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .product-meta {
    margin-top: 4px;
    .meta-tag {
      display: inline-block;
      font-size: 11px;
      color: #6b7280;
      background: #f3f4f6;
      padding: 1px 6px;
      border-radius: 3px;
      margin-right: 4px;
    }
  }
  .product-reason {
    margin-top: 4px;
    font-size: 12px;
    line-height: 1.4;
    .reason-label {
      color: #2563eb;
      font-weight: 500;
      margin-right: 4px;
    }
    .reason-text {
      color: #4b5563;
    }
  }
  .product-price {
    margin-top: 4px;
    font-size: 16px;
    font-weight: 600;
    color: #dc2626;
  }
}

/* 评分摘要 */
.score-summary {
  margin-top: 4px;
  .score-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    margin-bottom: 6px;
    &:last-child { margin-bottom: 0; }
  }
  .score-row-info {
    flex: 1;
    min-width: 0;
  }
  .score-row-name {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .score-row-sub {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 2px;
  }
  .score-row-value {
    flex-shrink: 0;
    text-align: right;
  }
  .score-num {
    font-size: 20px;
    font-weight: 600;
    color: #dc2626;
  }
  .score-max {
    font-size: 12px;
    color: #9ca3af;
  }
}

/* 评论列表 */
.comment-list {
  margin-top: 4px;
  .comment-summary {
    font-size: 13px;
    color: #6b7280;
    margin-bottom: 8px;
    .summary-score {
      color: #dc2626;
      font-weight: 500;
      margin-right: 12px;
    }
  }
  .comment-item {
    padding: 8px 10px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    margin-bottom: 6px;
    &:last-child { margin-bottom: 0; }
  }
  .comment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 4px;
    .comment-nickname {
      font-weight: 500;
      color: #374151;
    }
  }
  .comment-content {
    font-size: 13px;
    line-height: 1.5;
    color: #1f2937;
    word-break: break-word;
  }
  .comment-more {
    font-size: 12px;
    color: #9ca3af;
    text-align: center;
    margin-top: 6px;
  }
}

/* 购买建议 */
.purchase-rec {
  margin-top: 4px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  .block-title {
    border-bottom: none;
    margin-bottom: 8px;
  }
  .rec-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }
  .rec-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
    &.badge-green { background: #ecfdf5; color: #059669; }
    &.badge-orange { background: #fffbeb; color: #d97706; }
    &.badge-red { background: #fef2f2; color: #dc2626; }
  }
  .rec-stats {
    font-size: 12px;
    color: #6b7280;
  }
}

/* 口碑分析 */
.sentiment-analysis {
  margin-top: 4px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  .block-title {
    border-bottom: none;
    margin-bottom: 10px;
  }
  .stats-grid {
    display: flex;
    gap: 8px;
    margin-bottom: 10px;
  }
  .stat-item {
    flex: 1;
    text-align: center;
    padding: 8px;
    border-radius: 6px;
    .stat-value {
      font-size: 20px;
      font-weight: 600;
      line-height: 1.2;
    }
    .stat-label {
      font-size: 11px;
      color: #6b7280;
      margin-top: 2px;
    }
    &.stat-positive { background: #ecfdf5; .stat-value { color: #059669; } }
    &.stat-neutral { background: #eff6ff; .stat-value { color: #2563eb; } }
    &.stat-warning { background: #fffbeb; .stat-value { color: #d97706; } }
  }
  .dist-bar {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
    .dist-item {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 3px;
      color: #fff;
      &.dist-positive { background: #059669; }
      &.dist-negative { background: #dc2626; }
      &.dist-neutral { background: #9ca3af; }
    }
  }
}

/* 通用：优缺点区块 */
.rec-section {
  margin-top: 8px;
  .section-label {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 4px;
    &.pros-label { color: #059669; }
    &.cons-label { color: #dc2626; }
  }
  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 12px;
    line-height: 1.5;
    &.pros-tag { background: #ecfdf5; color: #059669; }
    &.cons-tag { background: #fef2f2; color: #dc2626; }
  }
}

.rec-summary {
  margin-top: 10px;
  padding: 8px 10px;
  background: #eff6ff;
  border-left: 3px solid #2563eb;
  border-radius: 0 4px 4px 0;
  font-size: 13px;
  color: #1f2937;
  .summary-label {
    font-weight: 600;
    color: #2563eb;
    margin-right: 6px;
  }
}

/* 正面/负面评价列表 */
.points-list {
  margin-top: 4px;
  .point-item {
    padding: 6px 10px;
    margin-bottom: 6px;
    border-radius: 4px;
    font-size: 13px;
    &:last-child { margin-bottom: 0; }
    .point-text {
      font-weight: 500;
    }
    .point-meta {
      display: block;
      font-size: 11px;
      color: #6b7280;
      margin-top: 2px;
    }
  }
  .pros-item {
    background: #ecfdf5;
    border-left: 3px solid #059669;
    .point-text { color: #065f46; }
  }
  .cons-item {
    background: #fef2f2;
    border-left: 3px solid #dc2626;
    .point-text { color: #991b1b; }
  }
  .pros-title { color: #059669; }
  .cons-title { color: #dc2626; }
}

/* 商品对比 */
.comparison-list {
  margin-top: 4px;
  .comparison-item {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    &:last-child { margin-bottom: 0; }
  }
  .comp-name {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 6px;
  }
  .comp-bar-wrap {
    display: inline-block;
    width: 180px;
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
    vertical-align: middle;
    margin-right: 8px;
    .comp-bar {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s;
    }
  }
  .comp-rate {
    font-size: 13px;
    font-weight: 600;
    vertical-align: middle;
  }
  .comp-sub {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 4px;
  }
}
</style>
