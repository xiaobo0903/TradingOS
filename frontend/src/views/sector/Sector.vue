<script setup lang="ts">
import { ref } from 'vue'
import CsvImport from './CsvImport.vue'

const activeTab = ref('list')
</script>

<template>
  <div class="sector">
    <el-tabs v-model="activeTab" class="sector-tabs">
      <el-tab-pane label="板块列表" name="list">
        <div class="placeholder">
          <p>板块列表功能开发中...</p>
          <p>当前可通过 CSV 导入功能导入板块数据</p>
        </div>
      </el-tab-pane>
      <el-tab-pane label="CSV导入" name="import">
        <CsvImport />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.sector {
  padding: 0;
}

.sector-tabs {
  background: #fff;
}

.placeholder {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.placeholder p {
  margin: 10px 0;
}
</style>
