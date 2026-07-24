<template>
  <div class="finance-view">
    <div class="strategy-container">
      <button @click="openStrategy" class="strategy-page" :disabled="loading">Перейти к стратегии</button>
    </div>
    <div class="analytics-container">
      <div class="analytics-tools"></div>
      <div class="analytics-graphics">
        <div class="statistics-summary" v-if="statisticsLoaded">
          <h4>Аналитика для {{ filename }}</h4>
          <h4>Аналитические показатели</h4>
          <div class="stats-grid">
            <!-- <div class="stat-card">
              <span class="stat-label">Средняя доходность (простая):</span>
              <span class="stat-value">{{ formatPercent(statistics.mean_simple) }}</span>
            </div> -->
            <div class="stat-card">
              <span class="stat-label">Средняя доходность (лог.):</span>
              <span class="stat-value">{{ formatPercent(statistics.mean_ln) }}</span>
            </div>
            <!-- <div class="stat-card">
              <span class="stat-label">Ст. отклонение (простое):</span>
              <span class="stat-value">{{ formatPercent(statistics.std_simple) }}</span>
            </div> -->
            <div class="stat-card">
              <span class="stat-label">Годовая волатильность:</span>
              <span class="stat-value">{{ formatPercent(statistics.volatility_ln) }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Коэффициент Шарпа:</span>
              <span class="stat-value">{{ statistics.sharpe_ln.toFixed(2) }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Максимальная просадка:</span>
              <span class="stat-value">{{ formatPercent(statistics.max_drawdown) }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="statisticsLoading" class="stats-loading">Загрузка статистики...</div>

        <div class="graphics-layout">
          <div class="graphics-controls-panel">
            <h4>Выбор графиков</h4>
            <div class="graphics-choices">
              <label><input type="checkbox" :disabled="closeDisabled" value="Close" v-model="checkedGraphs" /> График цены закрытия</label>
              <label><input type="checkbox" :disabled="histogramDisabled" value="Histogram" v-model="checkedGraphs" /> Столбчатая диаграмма объемов</label>
              <label><input type="checkbox" :disabled="candlesDisabled" value="Candles" v-model="checkedGraphs" /> Японские свечи</label>
              <label><input type="checkbox" value="SMA20" v-model="checkedGraphs" /> SMA 20</label>
              <label><input type="checkbox" value="SMA50" v-model="checkedGraphs" /> SMA 50</label>
            </div>
            <button @click="plotGraphs" class="plot-button" :disabled="loading">Построить</button>
          </div>

          <div ref="graphicsContainer" class="graphics"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'FinanceView',
  data() {
    return {
      filename: '',
      loading: false,
      success: false,
      error: null,
      checkedGraphs: [],
      statistics: {
        mean_simple: null,
        mean_ln: null,
        std_simple: null,
        std_ln: null,
        volatility_simple: null,
        period: null,
      },
      statisticsLoading: false,
      statisticsLoaded: false,
      smaData: { sma_20: null, sma_50: null },
      datesData: null,
      closeData: null,
    };
  },
  created() {
    this.filename = this.$route.params.filename;
    if (this.filename) {
      this.success = true;
      this.fetchStatistics();
    } else {
      this.error = 'Файл не был передан.';
    }
  },
  computed: {
    closeDisabled() {
      return this.checkedGraphs.includes('Candles');
    },
    histogramDisabled() {
      return this.checkedGraphs.includes('Candles');
    },
    candlesDisabled() {
      return this.checkedGraphs.includes('Close') || this.checkedGraphs.includes('Histogram');
    },
  },
  methods: {
    async fetchStatistics() {
      if (!this.filename) return;
      this.statisticsLoading = true;
      try {
        const response = await fetch(`http://localhost:8000/data/analytics/?filename=${this.filename}`, {
          credentials: 'include',
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const result = await response.json();
        console.log('Analytics response:', result);
        if (result.statistics) {
          this.statistics = result.statistics;
          this.datesData = result.dates;
          this.closeData = result.close;
          this.smaData.sma_20 = result.sma_20;
          this.smaData.sma_50 = result.sma_50;
          this.statisticsLoaded = true;
        } else {
          this.error = result.error || 'Ошибка загрузки статистики';
        }
      } catch (err) {
        console.error('Fetch statistics error:', err);
        this.error = err.message;
      } finally {
        this.statisticsLoading = false;
      }
    },
    async plotGraphs() {
      if (this.checkedGraphs.length < 1) {
        this.error = 'Не выбраны графики';
        return;
      }
      if (!this.filename) {
        this.error = 'Не указано имя файла';
        return;
      }
      this.error = null;
      this.loading = true;

      const requestData = {
        filename: this.filename,
        graphs: this.checkedGraphs.filter(g => g !== 'SMA20' && g !== 'SMA50'),
      };

      try {
        const response = await fetch('http://localhost:8000/data/graphics/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(requestData),
        });
        const result = await response.json();
        if (result.status === 'success') {
          const extendedData = { ...result.data };
          if (this.checkedGraphs.includes('SMA20') && this.smaData.sma_20 && this.datesData) {
            extendedData['SMA20'] = {
              y: this.smaData.sma_20,
              x: this.datesData,
              title: 'SMA 20'
            };
          }
          if (this.checkedGraphs.includes('SMA50') && this.smaData.sma_50 && this.datesData) {
            extendedData['SMA50'] = {
              y: this.smaData.sma_50,
              x: this.datesData,
              title: 'SMA 50'
            };
          }
          this.renderGraphs(extendedData);
        } else {
          this.error = result.message;
        }
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    renderGraphs(data) {
      const container = this.$refs.graphicsContainer;
      container.innerHTML = '';
      const graphDiv = document.createElement('div');
      graphDiv.style.width = '100%';
      graphDiv.style.height = '600px';
      container.appendChild(graphDiv);
      const myChart = echarts.init(graphDiv);

      const seriesList = [];
      let xAxisData = null;
      let hasPrice = false;
      let hasVolume = false;

      for (const graphType of this.checkedGraphs) {
        const graphData = data[graphType];
        if (graphData && graphData.x) {
          xAxisData = graphData.x;
          break;
        }
      }
      if (!xAxisData && this.datesData) {
        xAxisData = this.datesData;
      }

      for (const graphType of this.checkedGraphs) {
        const graphData = data[graphType];
        if (!graphData) continue;

        if (graphType === 'Close') {
          seriesList.push({
            name: graphData.title,
            yAxisIndex: 0,
            data: graphData.y,
            type: 'line',
            lineStyle: { color: '#4682B4' },
          });
          hasPrice = true;
        } else if (graphType === 'Histogram') {
          const onlyOne = this.checkedGraphs.length === 1;
          seriesList.push({
            name: graphData.title,
            yAxisIndex: onlyOne ? 0 : 1,
            data: graphData.y,
            type: 'bar',
            barWidth: '60%',
            barCategoryGap: '5%',
            itemStyle: { color: '#4682B4' },
          });
          hasVolume = true;
        } else if (graphType === 'Candles') {
          seriesList.push({
            name: graphData.title,
            type: 'candlestick',
            data: graphData.y,
            yAxisIndex: 0,
          });
          hasPrice = true;
        } else if (graphType === 'SMA20' || graphType === 'SMA50') {
          seriesList.push({
            name: graphData.title,
            type: 'line',
            data: graphData.y,
            yAxisIndex: 0,
            lineStyle: { color: graphType === 'SMA20' ? '#FFA500' : '#FF6347', width: 1.5, type: 'dashed' },
          });
        }
      }

      if (seriesList.length === 0) return;

      const yAxisList = [];
      if (hasPrice) {
        yAxisList.push({ type: 'value', name: 'Цена', position: 'left', alignTicks: true });
      }
      if (hasVolume) {
        yAxisList.push({
          type: 'value', name: 'Объём', position: 'right', alignTicks: true,
          axisLabel: { formatter: (value) => value.toLocaleString() }
        });
      }
      if (yAxisList.length === 0) yAxisList.push({ type: 'value' });

      let titleText;
      if (this.checkedGraphs.length === 1) {
        const type = this.checkedGraphs[0];
        if (type === 'Close') titleText = 'Цена закрытия';
        else if (type === 'Histogram') titleText = 'Объёмы';
        else if (type === 'Candles') titleText = 'Японские свечи';
        else titleText = 'График';
      } else {
        titleText = 'Совмещённый график';
      }

      const option = {
        title: { text: titleText },
        tooltip: { trigger: 'axis' },
        legend: { data: seriesList.map(s => s.name) },
        xAxis: { type: 'category', data: xAxisData, name: 'Дата' },
        yAxis: yAxisList,
        series: seriesList,
        dataZoom: [
          { type: 'slider', start: 0, end: 10 },
          { type: 'inside', start: 0, end: 10 }
        ]
      };
      myChart.setOption(option);
    },
    formatPercent(value) {
      if (value === null || value === undefined) return '—';
      return (value * 100).toFixed(2) + '%';
    },
    openStrategy() {
      this.$router.push({ name: 'strategy', params: { filename: this.filename }});
    },
  },


};
</script>

<style scoped>
.analytics-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}

.strategy-container {
  text-align: left;
  margin-bottom: 20px;
}
.strategy-page {
  background: #2c3e50;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.strategy-page:hover {
  background: #1e2a36;
}
.strategy-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.statistics-summary {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}
.statistics-summary h4 {
  margin: 0 0 12px 0;
  font-size: 18px;
}
.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.stat-card {
  background: white;
  border: 1px solid #eaeaea;
  border-radius: 6px;
  padding: 10px 16px;
  min-width: 180px;
}
.stat-label {
  font-size: 13px;
  color: #666;
  display: block;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #222;
}
.stats-loading {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  color: #666;
}

.graphics-controls-panel {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}
.graphics-controls-panel h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
}
.graphics-choices {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}
.graphics-choices label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
}
.plot-button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.plot-button:hover {
  background: #45a049;
}
.plot-button:disabled {
  background: #aaa;
  cursor: not-allowed;
}

.graphics {
  width: 100%;
  min-height: 500px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  padding: 8px;
}
.graphics-layout {
  display: block;
}
</style>
