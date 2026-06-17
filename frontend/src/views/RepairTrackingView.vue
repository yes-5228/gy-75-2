<script setup>
import { computed, reactive, ref } from 'vue'
import { ListPlus, Loader2 } from 'lucide-vue-next'
import { repairApi } from '../api/modules'
import DataTable from '../components/DataTable.vue'
import SectionHeader from '../components/SectionHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const props = defineProps({
  faults: { type: Array, required: true },
  logs: { type: Array, required: true },
})

const emit = defineEmits(['created'])

const VALID_TRANSITIONS = {
  Pending: ['In Progress', 'Review'],
  'In Progress': ['In Progress', 'Review', 'Completed'],
  Review: ['In Progress', 'Review', 'Completed'],
  Completed: [],
  待受理: ['处理中', '待复核'],
  处理中: ['处理中', '待复核', '已完成'],
  待复核: ['处理中', '待复核', '已完成'],
  已完成: [],
}

const form = reactive({
  faultId: '',
  action: '',
  handler: '',
  status: 'In Progress',
  cost: 0,
})

const submitting = ref(false)
const errorMessage = ref('')

const allowedStatuses = computed(() => {
  if (!form.faultId) return ['In Progress']
  const fault = props.faults.find(f => f.id === Number(form.faultId))
  if (!fault) return ['In Progress']
  return VALID_TRANSITIONS[fault.status] || []
})

const isCompleted = computed(() => allowedStatuses.value.length === 0)
const isDisabled = computed(() => isCompleted.value || submitting.value)

function onFaultChange() {
  errorMessage.value = ''
  const fault = props.faults.find(f => f.id === Number(form.faultId))
  if (fault) {
    const allowed = VALID_TRANSITIONS[fault.status] || []
    if (allowed.length > 0 && !allowed.includes(form.status)) {
      form.status = allowed[0]
    }
  }
}

async function submit() {
  if (isDisabled.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    await repairApi.createTracking({
      ...form,
      faultId: Number(form.faultId),
      cost: Number(form.cost),
    })
    Object.assign(form, {
      faultId: '',
      action: '',
      handler: '',
      status: 'In Progress',
      cost: 0,
    })
    emit('created')
  } catch (err) {
    try {
      const parsed = JSON.parse(err.message)
      if (parsed.error) {
        errorMessage.value = parsed.error
        if (parsed.allowed && parsed.allowed.length > 0) {
          errorMessage.value += ` 当前可选择的状态：${parsed.allowed.join('、')}`
        }
      } else if (parsed.current && parsed.target) {
        let msg = `状态流转不合法：不能从「${parsed.current}」直接变更为「${parsed.target}」。`
        if (parsed.allowed && parsed.allowed.length > 0) {
          msg += `当前可选择的状态：${parsed.allowed.join('、')}`
        } else {
          msg += `当前故障工单已处于终态，不能再追加任何跟踪记录。`
        }
        errorMessage.value = msg
      } else {
        errorMessage.value = parsed.error || parsed.message || '提交失败，请稍后重试'
      }
    } catch {
      const raw = err.message || ''
      if (raw.includes('Failed to fetch') || raw.includes('NetworkError')) {
        errorMessage.value = '网络连接失败，请检查网络后重试'
      } else if (raw.includes('500') || raw.includes('502') || raw.includes('503')) {
        errorMessage.value = '服务器暂时无法处理请求，请稍后重试'
      } else if (raw.includes('404')) {
        errorMessage.value = '请求的资源不存在，请刷新页面后重试'
      } else if (raw.includes('401') || raw.includes('403')) {
        errorMessage.value = '没有权限执行该操作，请重新登录'
      } else if (raw.trim()) {
        errorMessage.value = raw
      } else {
        errorMessage.value = '提交失败，请稍后重试'
      }
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="view-stack">
    <section class="panel">
      <SectionHeader title="Repair Tracking" description="Add progress, status, and repair cost" />
      <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>
      <form class="form-grid" @submit.prevent="submit">
        <label>
          <span>Fault ticket</span>
          <select v-model="form.faultId" required @change="onFaultChange" :disabled="submitting">
            <option value="" disabled>Select fault ticket</option>
            <option v-for="fault in faults" :key="fault.id" :value="fault.id">
              #{{ fault.id }} {{ fault.elevatorCode }} - {{ fault.faultType }} - {{ fault.status }}
            </option>
          </select>
        </label>
        <label>
          <span>Handler</span>
          <input v-model="form.handler" required placeholder="Repair engineer" :disabled="isDisabled" />
        </label>
        <label>
          <span>Status</span>
          <select v-model="form.status" :disabled="isDisabled">
            <option v-for="s in allowedStatuses" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label>
          <span>Cost</span>
          <input v-model.number="form.cost" type="number" min="0" step="0.01" :disabled="isDisabled" />
        </label>
        <label class="wide">
          <span>Action log</span>
          <textarea v-model="form.action" required rows="3" placeholder="Arrival, diagnosis, replacement, and review notes" :disabled="isDisabled"></textarea>
        </label>
        <button class="primary-action" type="submit" :disabled="isDisabled">
          <Loader2 v-if="submitting" :size="17" class="spin" />
          <ListPlus v-else :size="17" />
          <span>{{ isCompleted ? 'Fault already completed' : submitting ? 'Submitting...' : 'Add Tracking' }}</span>
        </button>
      </form>
    </section>

    <section class="panel">
      <SectionHeader title="Tracking Details" description="Repair process and status changes" />
      <DataTable
        :columns="[
          { key: 'createdAt', label: 'Time' },
          { key: 'faultId', label: 'Fault' },
          { key: 'handler', label: 'Handler' },
          { key: 'status', label: 'Status' },
          { key: 'cost', label: 'Cost' },
          { key: 'action', label: 'Action' },
        ]"
        :rows="logs"
      >
        <template #faultId="{ row }">#{{ row.faultId }}</template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #cost="{ row }">${{ row.cost }}</template>
      </DataTable>
    </section>
  </div>
</template>
