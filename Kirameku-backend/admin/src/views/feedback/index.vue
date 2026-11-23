<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { message } from "@/utils/message";
import {
  getFeedbacks,
  getFeedback,
  updateFeedback,
  deleteFeedback,
  type FeedbackItem,
  type FeedbackStatus,
  type FeedbackType
} from "@/api/feedback";

defineOptions({ name: "FeedbackIndex" });
const types: Record<FeedbackType, string> = {
  bug: "问题反馈",
  suggestion: "功能建议",
  other: "其他"
};
const statuses: Record<FeedbackStatus, string> = {
  pending: "待处理",
  processing: "处理中",
  resolved: "已处理",
  ignored: "忽略"
};
const tagTypes = {
  pending: "warning",
  processing: "primary",
  resolved: "success",
  ignored: "info"
} as const;
const rows = ref<FeedbackItem[]>([]);
const loading = ref(false);
const loadError = ref(false);
const status = ref<FeedbackStatus | "">("");
const type = ref<FeedbackType | "">("");
const page = ref(1);
const size = ref(20);
const total = ref(0);
const selected = ref<FeedbackItem | null>(null);
const detailOpen = ref(false);
const saving = ref(false);
const deleting = ref<number | null>(null);
const form = reactive<{ status: FeedbackStatus; admin_note: string }>({
  status: "pending",
  admin_note: ""
});
let requestId = 0;
const formatTime = (value: string) => value.replace("T", " ").slice(0, 19);

async function load() {
  const id = ++requestId;
  loading.value = true;
  loadError.value = false;
  try {
    const result = await getFeedbacks({
      page: page.value,
      size: size.value,
      status: status.value || undefined,
      type: type.value || undefined
    });
    if (id !== requestId) return;
    rows.value = result.items;
    total.value = result.total;
  } catch {
    if (id === requestId) loadError.value = true;
  } finally {
    if (id === requestId) loading.value = false;
  }
}
function filter() {
  page.value = 1;
  load();
}
async function openDetail(row: FeedbackItem) {
  try {
    selected.value = await getFeedback(row.id);
    form.status = selected.value.status;
    form.admin_note = selected.value.admin_note;
    detailOpen.value = true;
  } catch {
    message("反馈详情加载失败，请重试", { type: "error" });
  }
}
async function save() {
  if (!selected.value || saving.value) return;
  saving.value = true;
  try {
    await updateFeedback(selected.value.id, { ...form });
    message("处理结果已保存", { type: "success" });
    detailOpen.value = false;
    await load();
  } catch {
    message("保存失败，请重试", { type: "error" });
  } finally {
    saving.value = false;
  }
}
async function remove(row: FeedbackItem) {
  if (deleting.value !== null) return;
  deleting.value = row.id;
  try {
    await deleteFeedback(row.id);
    message("反馈已删除", { type: "success" });
    if (rows.value.length === 1 && page.value > 1) page.value--;
    await load();
  } catch {
    message("删除失败，请重试", { type: "error" });
  } finally {
    deleting.value = null;
  }
}
onMounted(load);
</script>

<template>
  <div class="p-4">
    <el-card shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-semibold">反馈管理</h2>
            <p class="mt-1 text-sm text-gray-500">
              查看访客的匿名反馈，记录处理进度。
            </p>
          </div>
          <el-button :loading="loading" @click="load">刷新</el-button>
        </div>
      </template>
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <el-select
          v-model="status"
          aria-label="筛选处理状态"
          placeholder="全部状态"
          clearable
          style="width: 140px"
          @change="filter"
        >
          <el-option
            v-for="(label, value) in statuses"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
        <el-select
          v-model="type"
          aria-label="筛选反馈类型"
          placeholder="全部类型"
          clearable
          style="width: 140px"
          @change="filter"
        >
          <el-option
            v-for="(label, value) in types"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
        <span class="text-sm text-gray-500">共 {{ total }} 条反馈</span>
      </div>
      <el-alert
        v-if="loadError"
        title="反馈加载失败，请点击刷新重试"
        type="error"
        :closable="false"
        class="mb-4"
      />
      <el-table
        v-loading="loading"
        :data="rows"
        row-key="id"
        empty-text="暂无符合条件的反馈"
      >
        <el-table-column prop="id" label="编号" width="80" />
        <el-table-column label="类型" width="110"
          ><template #default="{ row }">{{
            types[row.type as FeedbackType]
          }}</template></el-table-column
        >
        <el-table-column
          prop="content"
          label="反馈内容"
          min-width="250"
          show-overflow-tooltip
        />
        <el-table-column label="联系方式" min-width="160" show-overflow-tooltip
          ><template #default="{ row }">{{
            row.contact || "未填写"
          }}</template></el-table-column
        >
        <el-table-column label="状态" width="100"
          ><template #default="{ row }"
            ><el-tag :type="tagTypes[row.status as FeedbackStatus]">{{
              statuses[row.status as FeedbackStatus]
            }}</el-tag></template
          ></el-table-column
        >
        <el-table-column label="提交时间" width="170"
          ><template #default="{ row }">{{
            formatTime(row.created_at)
          }}</template></el-table-column
        >
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)"
              >查看 / 处理</el-button
            >
            <el-popconfirm
              title="确定删除这条反馈？删除后无法恢复。"
              @confirm="remove(row)"
            >
              <template #reference
                ><el-button
                  link
                  type="danger"
                  :loading="deleting === row.id"
                  :disabled="deleting !== null"
                  >删除</el-button
                ></template
              >
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 overflow-x-auto">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="load"
          @size-change="filter"
        />
      </div>
    </el-card>
    <el-dialog
      v-model="detailOpen"
      title="反馈详情"
      width="min(600px, 94vw)"
      :close-on-click-modal="!saving"
      :close-on-press-escape="!saving"
      :show-close="!saving"
    >
      <template v-if="selected">
        <div class="mb-4 flex flex-wrap gap-3 text-sm text-gray-500">
          <span>#{{ selected.id }} · {{ types[selected.type] }}</span
          ><span>{{ formatTime(selected.created_at) }}</span>
        </div>
        <div class="whitespace-pre-wrap break-words text-base leading-relaxed">
          {{ selected.content }}
        </div>
        <p class="my-5 break-words text-sm">
          联系方式：{{ selected.contact || "未填写" }}
        </p>
        <el-form label-position="top" :disabled="saving">
          <el-form-item label="处理状态"
            ><el-select v-model="form.status"
              ><el-option
                v-for="(label, value) in statuses"
                :key="value"
                :label="label"
                :value="value" /></el-select
          ></el-form-item>
          <el-form-item label="内部处理备注（仅管理员可见）"
            ><el-input
              v-model="form.admin_note"
              type="textarea"
              :rows="4"
              :maxlength="2000"
              show-word-limit
              placeholder="记录处理结果或后续安排"
          /></el-form-item>
        </el-form>
      </template>
      <template #footer
        ><el-button :disabled="saving" @click="detailOpen = false"
          >取消</el-button
        ><el-button type="primary" :loading="saving" @click="save"
          >保存处理结果</el-button
        ></template
      >
    </el-dialog>
  </div>
</template>
