<!--
  数据仪表板视图（可选）
  显示系统统计信息和数据概览
-->
<template>
  <div class="dashboard-view">
    <el-page-header @back="handleBack">
      <template #content>
        <span class="page-header-title">数据仪表板</span>
      </template>
    </el-page-header>
    
    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ statistics.totalObjects }}</div>
              <div class="stat-label">空间对象总数</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ statistics.totalCategories }}</div>
              <div class="stat-label">类别数量</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ queryCount }}</div>
              <div class="stat-label">查询次数</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ resultCount }}</div>
              <div class="stat-label">结果总数</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 图表区域 -->
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>查询趋势</span>
            </template>
            <div class="chart-container">
              <!-- 这里可以集成ECharts图表 -->
              <el-empty description="图表待实现" />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>类别分布</span>
            </template>
            <div class="chart-container">
              <!-- 这里可以集成ECharts图表 -->
              <el-empty description="图表待实现" />
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 最近查询 -->
      <el-card style="margin-top: 20px">
        <template #header>
          <span>最近查询</span>
        </template>
        <el-table :data="recentQueries" style="width: 100%">
          <el-table-column prop="text" label="查询文本" />
          <el-table-column prop="timestamp" label="时间" :formatter="formatTime" />
          <el-table-column prop="k" label="结果数" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button type="primary" link @click="handleViewQuery(scope.row)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { getDataStatistics } from '@/services/data.service';
import { getQueryHistory } from '@/services/query.service';
import { useResultStore } from '@/stores/result.store';
import dayjs from 'dayjs';

const router = useRouter();
const resultStore = useResultStore();

const statistics = ref({
  totalObjects: 0,
  totalCategories: 0,
  lastUpdateTime: '',
});

const queryCount = ref(0);
const resultCount = ref(0);
const recentQueries = ref<any[]>([]);

onMounted(async () => {
  try {
    // 加载统计数据
    const stats = await getDataStatistics();
    statistics.value = stats;
    
    // 加载查询历史
    const queries = await getQueryHistory(10);
    recentQueries.value = queries;
    queryCount.value = queries.length;
    
    // 获取结果数量
    resultCount.value = resultStore.resultCount;
  } catch (error: any) {
    ElMessage.error('加载数据失败: ' + (error.message || '未知错误'));
  }
});

function handleBack() {
  router.push('/');
}

function formatTime(row: any, column: any, cellValue: any) {
  return dayjs(cellValue).format('YYYY-MM-DD HH:mm:ss');
}

function handleViewQuery(query: any) {
  // 跳转到主页并加载查询
  router.push('/');
  // TODO: 恢复查询状态
}
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  height: 100vh;
  overflow-y: auto;
}

.page-header-title {
  font-size: 18px;
  font-weight: 600;
}

.dashboard-content {
  margin-top: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

