<!-- ChartRender.vue - ECharts图表渲染组件
  支持4种图表类型：line（折线图）、bar（柱状图）、pie（饼图）、composite（复合图表）
  数据格式由后端工具返回的chart_data字段决定
-->
<template>
  <div class="chart-render-wrapper">
    <!-- 复合图表：递归渲染多个子图表 -->
    <template v-if="chartData && chartData.type === 'composite'">
      <div class="chart-header" v-if="chartData.title">
        <span class="chart-title">{{ chartData.title }}</span>
      </div>
      <ChartRender
        v-for="(sub, idx) in (chartData.charts || [])"
        :key="idx"
        :chart-data="sub"
      />
    </template>
    <!-- 单图表 -->
    <template v-else>
      <div class="chart-header" v-if="chartData && chartData.title">
        <span class="chart-title">{{ chartData.title }}</span>
      </div>
      <!-- 空数据提示 -->
      <div v-if="isEmpty" class="chart-empty">
        <span class="empty-text">暂无数据</span>
      </div>
      <!-- 图表容器 -->
      <div v-else ref="chartRef" class="chart-container"></div>
    </template>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'ChartRender',
  props: {
    chartData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      chart: null,
      retryCount: 0,
      maxRetries: 5
    }
  },
  computed: {
    // 判断图表数据是否为空
    isEmpty() {
      if (!this.chartData) return true
      const type = this.chartData.type
      if (type === 'composite') {
        return !this.chartData.charts || this.chartData.charts.length === 0
      }
      if (type === 'pie') {
        const data = this.chartData.data || []
        return data.length === 0
      }
      // line / bar
      const series = this.chartData.series || []
      if (series.length === 0) return true
      // 检查所有series的data是否都为空
      const allEmpty = series.every(s => !s.data || s.data.length === 0)
      return allEmpty
    }
  },
  watch: {
    chartData: {
      handler(newVal) {
        if (newVal) {
          this.retryCount = 0
          this.$nextTick(() => {
            this.renderChart()
          })
        }
      },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    if (this.chartData) {
      this.retryCount = 0
      // 使用setTimeout(0)确保DOM完全渲染和CSS应用后再初始化echarts
      setTimeout(() => {
        this.renderChart()
      }, 0)
    }
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    renderChart() {
      if (!this.chartData) return

      // 复合图表由模板递归渲染子组件，不需要初始化单个echarts实例
      if (this.chartData.type === 'composite') return

      // 空数据不需要渲染echarts
      if (this.isEmpty) return

      // 检查DOM ref是否存在
      if (!this.$refs.chartRef) {
        // DOM还没渲染，延迟重试
        if (this.retryCount < this.maxRetries) {
          this.retryCount++
          setTimeout(() => this.renderChart(), 50 * this.retryCount)
        }
        return
      }

      // 检查容器尺寸，宽度为0时延迟重试（递归渲染时常见问题）
      const width = this.$refs.chartRef.offsetWidth
      const height = this.$refs.chartRef.offsetHeight
      if (width === 0 || height === 0) {
        if (this.retryCount < this.maxRetries) {
          this.retryCount++
          setTimeout(() => this.renderChart(), 50 * this.retryCount)
        }
        return
      }

      // 重置重试计数
      this.retryCount = 0

      // 初始化或复用echarts实例
      if (!this.chart) {
        this.chart = echarts.init(this.$refs.chartRef)
      }

      const type = this.chartData.type || 'line'
      let option = {}

      if (type === 'line') {
        option = this.buildLineOption()
      } else if (type === 'bar') {
        option = this.buildBarOption()
      } else if (type === 'pie') {
        option = this.buildPieOption()
      } else {
        // 默认折线图
        option = this.buildLineOption()
      }

      this.chart.setOption(option, true)
      // 确保图表正确渲染并适应容器
      this.chart.resize()
    },

    buildLineOption() {
      const data = this.chartData
      const series = (data.series || []).map(s => ({
        name: s.name || '',
        type: 'line',
        data: s.data || [],
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.1 }
      }))

      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            let result = params[0].axisValue
            params.forEach(p => {
              const unit = data.unit || ''
              result += `<br/>${p.marker}${p.seriesName}: ${p.value}${unit}`
            })
            return result
          }
        },
        legend: {
          data: series.map(s => s.name),
          bottom: 0,
          textStyle: { fontSize: 12 }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '12%',
          top: '5%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.x_axis || [],
          axisLabel: {
            rotate: 30,
            fontSize: 11
          },
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          axisLabel: { fontSize: 11 },
          name: data.unit || ''
        },
        series: series,
        color: ['#5470c6', '#fac858', '#91cc75', '#ee6666', '#73c0de']
      }
    },

    buildBarOption() {
      const data = this.chartData
      const series = (data.series || []).map(s => ({
        name: s.name || '',
        type: 'bar',
        data: s.data || [],
        barMaxWidth: 40,
        itemStyle: { borderRadius: [4, 4, 0, 0] }
      }))

      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params) => {
            let result = params[0].axisValue
            params.forEach(p => {
              const unit = data.unit || ''
              result += `<br/>${p.marker}${p.seriesName}: ${p.value}${unit}`
            })
            return result
          }
        },
        legend: {
          data: series.map(s => s.name),
          bottom: 0,
          textStyle: { fontSize: 12 }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '12%',
          top: '5%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: data.x_axis || [],
          axisLabel: {
            rotate: 30,
            fontSize: 11,
            interval: 0
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: { fontSize: 11 },
          name: data.unit || ''
        },
        series: series,
        color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
      }
    },

    buildPieOption() {
      const data = this.chartData
      const pieData = data.data || []

      return {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: { fontSize: 12 },
          formatter: (name) => {
            const item = pieData.find(d => d.name === name)
            return item ? `${name}: ${item.value}` : name
          }
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b}: {d}%',
            fontSize: 11
          },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' }
          },
          data: pieData.map(d => ({
            name: d.name,
            value: d.value
          }))
        }],
        color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
      }
    },

    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    }
  }
}
</script>

<style scoped>
.chart-render-wrapper {
  width: 100%;
  margin-top: 12px;
  padding: 12px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.chart-header {
  margin-bottom: 8px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.chart-empty {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafbfc;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
}

.empty-text {
  font-size: 13px;
  color: #909399;
}
</style>
