<template>
  <div class="strategy-container">
    <div class="back-button-container">
      <button @click="goBack" class="back-btn">Назад к аналитике</button>
    </div>

    <h2>Торговая стратегия (назвать стратегию)</h2>
    <div v-if="statistics" class="stats-block">

      <div class="stat-card">
        <span class="stat-label">Доходность стратегии (руб.)</span>
        <span class="stat-value">{{ formatCurrency(statistics.strategy_abs_profit) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Доходность стратегии (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.strategy_return_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Календарные дни</span>
        <span class="stat-value">{{ statistics.calendar_days || '—' }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Годовая доходность стратегии (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.strategy_annual_return_pct) }}</span>
      </div>

      <div class="stat-card">
        <span class="stat-label">Доходность "Купи и держи" (руб.)</span>
        <span class="stat-value">{{ formatCurrency(statistics.buy_hold_abs_profit) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Доходность "Купи и держи" (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.buy_hold_return_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Годовая доходность "Купи и держи" (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.buy_hold_annual_return_pct) }}</span>
      </div>

      <div class="stat-card">
        <span class="stat-label">Profit/Loss Index (%)</span>
        <span class="stat-value" :class="getPlIndexClass(statistics.pl_index)">
          {{ formatPercent(statistics.pl_index) }}
        </span>
      </div>

      <div class="stat-card">
        <span class="stat-label">Начальный капитал (руб.)</span>
        <span class="stat-value">{{ formatCurrency(statistics.initial_capital) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Конечный капитал (руб.)</span>
        <span class="stat-value">{{ formatCurrency(statistics.final_capital) }}</span>
      </div>
    </div>

    <div ref="priceChart" class="chart" style="height: 500px;"></div>

    <div v-if="trades.length" class="trades-table">
      <h3>Сделки</h3>
      <table>
        <thead>
          <tr><th>Дата входа</th><th>Цена входа</th><th>Дата выхода</th><th>Цена выхода</th><th>Тип</th><th>Доходность (%)</th></tr>
        </thead>
        <tbody>
          <tr v-for="(t, idx) in trades" :key="idx">
            <td>{{ t.entry_date }}</td><td>{{ t.entry_price }}</td>
            <td>{{ t.exit_date }}</td><td>{{ t.exit_price }}</td>
            <td>{{ t.type }}</td>
            <td :class="t.return_pct >= 0 ? 'profit' : 'loss'">{{ (t.return_pct * 100).toFixed(2) }}</td>
          </tr>
          <tr class="total-row">
            <td colspan="5"><strong>Итого прибыль (денег)</strong></td>
            <td><strong>{{ formatCurrency(statistics?.strategy_abs_profit) }}</strong></td>
          </tr>
          <tr class="total-row">
            <td colspan="5"><strong>Итоговая доходность (%)</strong></td>
            <td><strong>{{ formatPercent(statistics?.strategy_return_pct) }}</strong></td>
          </tr>
        </tbody>
       </table>
    </div>
    <div v-else-if="!loading && backtestRun" class="no-data">Нет сделок по заданным параметрам</div>

    <div v-if="statistics" class="stats-block stats-block-bottom">
      <div class="stat-card">
        <span class="stat-label">Макс. снижение баланса от нач. капитала (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.max_drawdown_from_initial_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Средний убыток (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.avg_loss_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Средняя прибыль (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.avg_profit_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Максимальный убыток по сделке (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.max_loss_pct) }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Максимальная прибыль по сделке (%)</span>
        <span class="stat-value">{{ formatPercent(statistics.max_profit_pct) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'StrategyView',
  data() {
    return {
      filename: '',
      loading: false,
      backtestRun: false,
      indicators: null,
      trades: [],
      signals: [],
      statistics: null,
      priceChart: null,
    };
  },
  created() {
    this.filename = this.$route.params.filename;
    if (!this.filename) {
      this.$router.push('/');
    }
  },
  mounted() {
    this.priceChart = echarts.init(this.$refs.priceChart);
    this.runBacktest();
  },
  beforeDestroy() {
    if (this.priceChart) this.priceChart.dispose();
  },
  methods: {
    async runBacktest() {
      if (!this.filename) return;
      this.loading = true;
      this.backtestRun = true;

      try {
        const indicatorsRes = await fetch('http://localhost:8000/api/get_signals/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: this.filename }),
        });
        const indicatorsData = await indicatorsRes.json();
        if (!indicatorsRes.ok) throw new Error(indicatorsData.message || 'Ошибка загрузки индикаторов');
        this.indicators = indicatorsData;

        const backtestRes = await fetch('http://localhost:8000/api/test_strategy/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: this.filename }),
        });
        const backtestData = await backtestRes.json();
        if (!backtestRes.ok) throw new Error(backtestData.message || 'Ошибка бэктеста');
        this.trades = backtestData.trades || [];
        this.signals = backtestData.signals || [];
        this.statistics = backtestData.statistics;

        this.renderPriceChart();
      } catch (err) {
        console.error(err);
        this.$emit('error', err.message);
      } finally {
        this.loading = false;
      }
    },

    renderPriceChart() {
      if (!this.indicators) return;
      const { dates, close } = this.indicators;
      const buyPoints = this.signals.filter(s => s.type === 'buy').map(s => [s.date, s.price]);
      const sellPoints = this.signals.filter(s => s.type === 'sell').map(s => [s.date, s.price]);

      const option = {
        title: { text: 'График цены с сигналами' },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: ['Цена закрытия', 'Покупка', 'Продажа'] },
        xAxis: { type: 'category', data: dates, name: 'Дата' },
        yAxis: { type: 'value', name: 'Цена' },
        series: [
          {
            name: 'Цена закрытия',
            type: 'line',
            data: close,
            lineStyle: { color: '#4682B4', width: 1.5 },
          },
          {
            name: 'Покупка',
            type: 'scatter',
            data: buyPoints,
            symbol: 'triangle',
            symbolSize: 14,
            itemStyle: { color: '#00aa00', borderColor: '#006600' },
            label: { show: true, formatter: '▲', position: 'top', color: '#00aa00', fontWeight: 'bold' },
          },
          {
            name: 'Продажа',
            type: 'scatter',
            data: sellPoints,
            symbol: 'triangle',
            symbolSize: 14,
            itemStyle: { color: '#cc0000', borderColor: '#990000' },
            label: { show: true, formatter: '▼', position: 'bottom', color: '#cc0000', fontWeight: 'bold' },
          },
        ],
      };
      this.priceChart.setOption(option, true);
    },

    goBack() {
      this.$router.push(`/analysis/${this.filename}`);
    },

    formatCurrency(value) {
      if (value === null || value === undefined) return '—';
      return value.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },

    formatPercent(value) {
      if (value === null || value === undefined) return '—';
      return value.toFixed(2) + '%';
    },

    getPlIndexClass(value) {
      if (value === null || value === undefined) return '';
      if (value > 0) return 'positive';
      if (value < 0) return 'negative';
      return '';
    }
  },
};
</script>

<style scoped>

.stats-block-bottom {
  margin-top: 30px;
  border-top: 1px solid #d0d0d0;
  padding-top: 20px;
}

.stat-label {
  font-size: 12px;
  color: #555;
  display: block;
  margin-bottom: 4px;
  font-weight: normal;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
}

.positive {
  color: #006400;
}

.negative {
  color: #8b0000;
}

.strategy-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  color: #1a1a1a;
}

.back-button-container {
  margin-bottom: 20px;
}

.back-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.back-btn:hover {
  background: #45a049;
}

h2 {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 700;
  color: #000;
}

.stats-block {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #f9f9f9;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #000;
  min-width: 160px;
}

.chart {
  width: 100%;
  height: 500px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  background: white;
  margin-bottom: 30px;
}

.trades-table {
  margin-top: 30px;
  overflow-x: auto;
}

.trades-table h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 700;
  color: #000;
}

.trades-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  color: #000;
}

.trades-table th,
.trades-table td {
  border: 1px solid #999;
  padding: 10px 12px;
  text-align: center;
  color: #000;
  font-weight: 500;
}

.trades-table th {
  background: #e9ecef;
  font-weight: 700;
  color: #000;
}

.trades-table .total-row,
.trades-table .total-row td,
.trades-table tr.total-row td {
  background: #e8e8e8;
  font-weight: 400;
  color: #000;
  font-size: 14px;
}

.trades-table .total-row td strong {
  color: #000;
  font-weight: 600;
}

.trades-table td.profit,
td.profit {
  color: #006400;
  font-weight: 700;
}

.trades-table td.loss,
td.loss {
  color: #8b0000;
  font-weight: 700;
}

.no-data {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  background: #f9f9f9;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  color: #000;
  font-weight: 500;
}
</style>
