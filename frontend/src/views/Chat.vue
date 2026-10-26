<template>
  <div class="chat-page fade-rise">
    <div class="chat-scrim" :class="{ show: historyOpen }" @click="historyOpen = false" />

    <aside class="history-sidebar" :class="{ open: historyOpen }">
      <div class="archive-head">
        <p class="panel-kicker">CONVERSATIONS</p>
        <div class="archive-title-row">
          <h2>对话档案</h2>
          <span class="archive-count">{{ String(history.length).padStart(2, '0') }}</span>
        </div>
        <p class="archive-desc">每个资料库单独保存问答记录。选中一条，可以重新读当时的回答。</p>
      </div>

      <div class="kb-picker">
        <label>当前资料库</label>
        <el-select
          v-model="currentKbId"
          placeholder="选择资料库"
          class="kb-select"
          @change="onKbChange"
        >
          <el-option
            v-for="kb in kbList"
            :key="kb.id"
            :label="kb.name"
            :value="kb.id"
          />
        </el-select>
      </div>

      <div class="history-list" v-loading="historyLoading">
        <button
          v-for="(item, index) in history"
          :key="item.id"
          type="button"
          class="history-item"
          :class="{ active: activeHistoryId === item.id }"
          @click="selectHistory(item)"
        >
          <span class="history-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="history-copy">
            <span class="history-question">{{ item.question }}</span>
            <span class="history-time">{{ formatTime(item.created_at) }}</span>
          </span>
          <span
            class="history-delete"
            role="button"
            tabindex="0"
            aria-label="删除这条对话"
            @click.stop="onDeleteHistory(item, $event)"
            @keydown.enter.stop="onDeleteHistory(item, $event)"
          >
            <el-icon><Close /></el-icon>
          </span>
        </button>

        <div v-if="!history.length && !historyLoading" class="history-empty">
          <span class="history-empty-mark">✳</span>
          <p>这个资料库还没有对话。<br />从右边问第一个问题吧。</p>
        </div>
      </div>

      <div v-if="currentKbId && history.length" class="sidebar-foot">
        <button type="button" class="clear-history" @click="onClearHistory">
          <el-icon><Delete /></el-icon>
          清空当前档案
        </button>
      </div>
    </aside>

    <section class="chat-main">
      <header class="chat-head">
        <div class="chat-head-left">
          <button type="button" class="mobile-history" @click="historyOpen = true">
            <el-icon><Menu /></el-icon>
            档案
          </button>
          <span class="chat-status-dot" />
          <div class="chat-head-copy">
            <span class="chat-head-title">{{ activeKb?.name || '问答台' }}</span>
            <span class="chat-head-sub">RAG 检索 · 回答引用原文</span>
          </div>
        </div>
        <button
          v-if="currentKbId"
          type="button"
          class="head-action"
          :disabled="!messages.length"
          @click="onNewConversation"
        >
          <el-icon><Plus /></el-icon>
          新对话
        </button>
      </header>

      <div v-if="!currentKbId" class="chat-empty-main">
        <span class="empty-number">01</span>
        <p class="page-kicker">START A CONVERSATION</p>
        <h2>先从资料室选一个知识库</h2>
        <p>AI 会从你整理的资料里找依据，再回答你的问题。</p>
        <div v-if="kbList.length" class="empty-kb-list">
          <button
            v-for="kb in kbList"
            :key="kb.id"
            type="button"
            class="empty-kb-item"
            @click="selectKb(kb)"
          >
            <span class="empty-kb-name">{{ kb.name }}</span>
            <span class="empty-kb-meta">{{ kb.document_count }} 份文档</span>
            <el-icon><Right /></el-icon>
          </button>
        </div>
        <el-button v-else text type="primary" @click="$router.push('/knowledge')">
          去资料室建一个
        </el-button>
      </div>

      <template v-else>
        <div ref="messagesRef" class="messages-container">
          <div v-if="!messages.length" class="chat-welcome">
            <span class="welcome-number">01</span>
            <p class="page-kicker">READY TO WRITE</p>
            <h2>今天想聊哪一段？</h2>
            <p class="welcome-lead">问设定、问人物动机、问剧情漏洞，或者让 AI 从资料里给你几个开篇方案。</p>
            <div class="suggestions">
              <button
                v-for="prompt in suggestions"
                :key="prompt"
                type="button"
                class="suggestion"
                @click="askSuggestion(prompt)"
              >
                <span>{{ prompt }}</span>
                <el-icon><Right /></el-icon>
              </button>
            </div>
          </div>

          <article
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-item"
            :class="msg.role"
          >
            <div v-if="msg.role === 'assistant'" class="message-meta">
              <span class="ai-mark">✳</span>
              <span>写作助手</span>
              <button
                v-if="msg.content && !msg.streaming"
                type="button"
                class="copy-message"
                @click="copyMessage(msg.content)"
              >
                复制
              </button>
            </div>

            <div class="message-content">
              <span v-if="msg.role === 'user'">{{ msg.content }}</span>
              <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>

              <span v-if="msg.streaming" class="cursor">|</span>
            </div>

            <div v-if="msg.sources && msg.sources.length" class="sources">
              <span class="sources-label">
                参考 {{ uniqueSourceCount(msg.sources) }} 份文档 · {{ msg.sources.length }} 个片段
              </span>
              <div class="source-list">
                <el-tag
                  v-for="(s, si) in msg.sources"
                  :key="si"
                  size="small"
                  class="source-tag"
                >
                  {{ s.filename }} #{{ s.chunk_index ?? si + 1 }}
                </el-tag>
              </div>
            </div>
          </article>
        </div>

        <div class="input-area">
          <div class="input-shell">
            <el-input
              ref="inputRef"
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="问你的资料库：这个角色的动机成立吗？"
              :disabled="streaming"
              @keydown="onKeydown"
              resize="none"
            />
            <div class="input-footer">
              <span class="input-hint">Enter 发送 · Shift + Enter 换行</span>
              <button
                type="button"
                class="send-button"
                :disabled="streaming || !inputText.trim()"
                @click="onSend"
              >
                <el-icon v-if="!streaming"><Promotion /></el-icon>
                <el-icon v-else class="is-loading"><Loading /></el-icon>
                {{ streaming ? '生成中' : '发送' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound, Close, Delete, Loading, Menu, Plus, Promotion, Right,
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { listKnowledge } from '../api/knowledge'
import { chatStream, getHistory, deleteHistory, clearHistory as clearHistoryApi } from '../api/chat'

const route = useRoute()

const kbList = ref([])
const currentKbId = ref(null)
const historyOpen = ref(false)

const messages = ref([])
const history = ref([])
const historyLoading = ref(false)
const activeHistoryId = ref(null)

const inputText = ref('')
const streaming = ref(false)
const messagesRef = ref()
const inputRef = ref()

const suggestions = [
  '根据资料，给我三个开篇方案',
  '梳理这本书目前的核心冲突',
  '这个角色的动机站得住吗？',
]

const activeKb = computed(() => kbList.value.find((kb) => kb.id === currentKbId.value))

marked.setOptions({ breaks: true, gfm: true })

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked.parse(text || ''), {
    USE_PROFILES: { html: true },
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

async function fetchKbList() {
  try {
    kbList.value = await listKnowledge()
    if (route.params.id) {
      currentKbId.value = parseInt(route.params.id)
      onKbChange()
    }
  } catch {
    // handled by interceptor
  }
}

async function onKbChange() {
  if (!currentKbId.value) return
  messages.value = []
  activeHistoryId.value = null
  historyOpen.value = false
  await fetchHistory()
}

function selectKb(kb) {
  currentKbId.value = kb.id
  onKbChange()
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    history.value = await getHistory(currentKbId.value)
  } finally {
    historyLoading.value = false
  }
}

function selectHistory(item) {
  activeHistoryId.value = item.id
  messages.value = [
    { role: 'user', content: item.question },
    { role: 'assistant', content: item.answer, sources: item.sources || [] },
  ]
  historyOpen.value = false
  scrollToBottom()
}

function onNewConversation() {
  activeHistoryId.value = null
  messages.value = []
  inputText.value = ''
  nextTick(() => inputRef.value?.focus())
}

async function onDeleteHistory(item, e) {
  e.stopPropagation()
  await ElMessageBox.confirm('确定删除该条对话记录？', '提示', { type: 'warning' })
    .then(async () => {
      await deleteHistory(item.id)
      ElMessage.success('已删除')
      if (activeHistoryId.value === item.id) {
        messages.value = []
        activeHistoryId.value = null
      }
      fetchHistory()
    }).catch(() => {})
}

async function onClearHistory() {
  await ElMessageBox.confirm('确定清空当前知识库的所有对话历史？', '提示', { type: 'warning' })
    .then(async () => {
      await clearHistoryApi(currentKbId.value)
      ElMessage.success('已清空')
      messages.value = []
      activeHistoryId.value = null
      fetchHistory()
    }).catch(() => {})
}

function askSuggestion(prompt) {
  inputText.value = prompt
  nextTick(() => inputRef.value?.focus())
}

async function copyMessage(content) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择文本')
  }
}

async function onSend() {
  const question = inputText.value.trim()
  if (!question || streaming.value) return

  messages.value.push({ role: 'user', content: question })
  inputText.value = ''
  scrollToBottom()

  const aiMsg = { role: 'assistant', content: '', sources: [], streaming: true }
  messages.value.push(aiMsg)
  scrollToBottom()

  streaming.value = true
  activeHistoryId.value = null

  try {
    const resp = await chatStream({
      question,
      kb_id: currentKbId.value,
      top_k: 5,
    })

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const lines = part.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const evt = JSON.parse(data)
            if (evt.type === 'sources') {
              aiMsg.sources = evt.data
            } else if (evt.type === 'chunk') {
              aiMsg.content += evt.data
              scrollToBottom()
            } else if (evt.type === 'error') {
              aiMsg.content = '抱歉，出现错误：' + evt.data
              aiMsg.streaming = false
              streaming.value = false
              scrollToBottom()
              return
            }
          } catch {
            aiMsg.content += data
            scrollToBottom()
          }
        }
      }
    }

    aiMsg.streaming = false
    ElMessage.success('回答完成')
    fetchHistory()
  } catch (e) {
    aiMsg.content = '抱歉，出现错误：' + (e.message || '未知错误')
    aiMsg.streaming = false
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onSend()
  }
}

function formatTime(str) {
  if (!str) return ''
  const d = new Date(str)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function uniqueSourceCount(sources) {
  if (!sources || !sources.length) return 0
  return new Set(sources.map((s) => s.filename)).size
}

onMounted(fetchKbList)
</script>

<style scoped>
.chat-page {
  display: flex;
  gap: 18px;
  height: calc(100vh - 150px);
  min-height: 560px;
  max-width: 1500px;
  margin: 0 auto;
  position: relative;
}

.history-sidebar {
  width: 292px;
  flex: 0 0 292px;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.62);
  overflow: hidden;
}

.archive-head {
  padding: 22px 22px 18px;
  border-bottom: 1px solid var(--color-hairline-soft);
}

.panel-kicker {
  font-size: 9px;
  letter-spacing: 1.8px;
  color: var(--color-muted-soft);
  margin-bottom: 8px;
}

.archive-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.archive-title-row h2 {
  font-family: var(--font-serif);
  font-size: 25px;
  font-weight: 400;
  letter-spacing: -0.5px;
  color: var(--color-ink);
}

.archive-count {
  font-family: var(--font-serif);
  font-size: 28px;
  line-height: 1;
  color: var(--color-primary);
}

.archive-desc {
  font-size: 11px;
  line-height: 1.65;
  color: var(--color-muted);
}

.kb-picker {
  padding: 16px 18px 14px;
  border-bottom: 1px solid var(--color-hairline-soft);
}

.kb-picker label {
  display: block;
  margin-bottom: 7px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.8px;
  color: var(--color-muted);
}

.kb-select {
  width: 100%;
}

.kb-select :deep(.el-select__wrapper) {
  min-height: 38px;
  border-radius: 8px;
  font-size: 12px;
}

.history-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  width: 100%;
  display: flex;
  gap: 9px;
  padding: 11px 10px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  position: relative;
  transition: background var(--dur-fast);
}

.history-item:hover {
  background: var(--color-surface-soft);
}

.history-item.active {
  background: #fff;
  box-shadow: 0 2px 10px rgba(20, 20, 19, 0.06);
}

.history-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 2px;
  border-radius: 2px;
  background: var(--color-primary);
}

.history-index {
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--color-muted-soft);
  padding-top: 2px;
  flex: 0 0 14px;
}

.history-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.history-question {
  font-size: 11.5px;
  line-height: 1.45;
  color: var(--color-ink);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  padding-right: 12px;
}

.history-time {
  font-size: 9.5px;
  color: var(--color-muted-soft);
  letter-spacing: 0.2px;
}

.history-delete {
  position: absolute;
  top: 9px;
  right: 8px;
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: var(--color-muted-soft);
  opacity: 0;
  transition: opacity var(--dur-fast), color var(--dur-fast);
}

.history-item:hover .history-delete {
  opacity: 1;
}

.history-delete:hover {
  color: var(--color-error);
}

.history-empty {
  padding: 42px 24px;
  text-align: center;
}

.history-empty-mark {
  display: inline-block;
  color: var(--color-primary);
  font-size: 18px;
  margin-bottom: 12px;
}

.history-empty p {
  font-size: 11px;
  line-height: 1.7;
  color: var(--color-muted-soft);
}

.sidebar-foot {
  padding: 10px 14px 14px;
  border-top: 1px solid var(--color-hairline-soft);
}

.clear-history {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  padding: 4px;
  font-size: 10.5px;
  color: var(--color-muted-soft);
  cursor: pointer;
}

.clear-history:hover {
  color: var(--color-error);
}

.chat-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-hairline);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.54);
  overflow: hidden;
}

.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 66px;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-hairline-soft);
  background: rgba(245, 240, 232, 0.38);
}

.chat-head-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-status-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  background: var(--color-accent-teal);
  box-shadow: 0 0 8px var(--color-accent-teal);
}

.chat-head-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.chat-head-title {
  font-family: var(--font-serif);
  font-size: 16px;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-head-sub {
  font-size: 9.5px;
  letter-spacing: 0.4px;
  color: var(--color-muted-soft);
}

.head-action {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  padding: 6px 4px;
  flex: 0 0 auto;
}

.head-action:disabled {
  color: var(--color-muted-soft);
  cursor: default;
}

.mobile-history {
  display: none;
  align-items: center;
  gap: 4px;
  border: 0;
  background: transparent;
  color: var(--color-muted);
  font-size: 11px;
  cursor: pointer;
}

.chat-empty-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
  position: relative;
  overflow: hidden;
}

.empty-number,
.welcome-number {
  position: absolute;
  right: 30px;
  top: 0;
  font-family: var(--font-serif);
  font-size: 124px;
  line-height: 1;
  letter-spacing: -7px;
  color: rgba(204, 120, 92, 0.07);
  pointer-events: none;
}

.chat-empty-main h2,
.chat-welcome h2 {
  font-family: var(--font-serif);
  font-size: 30px;
  font-weight: 400;
  letter-spacing: -0.6px;
  color: var(--color-ink);
  margin: 14px 0 8px;
}

.chat-empty-main > p:not(.page-kicker),
.welcome-lead {
  max-width: 430px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--color-muted);
  margin-bottom: 24px;
}

.empty-kb-list {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.empty-kb-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.58);
  cursor: pointer;
  text-align: left;
  transition: border-color var(--dur-fast), transform var(--dur-fast), background var(--dur-fast);
}

.empty-kb-item:hover {
  border-color: var(--color-primary);
  background: #fff;
  transform: translateY(-2px);
}

.empty-kb-name {
  flex: 1;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-kb-meta {
  font-size: 9.5px;
  color: var(--color-muted-soft);
}

.empty-kb-item .el-icon {
  font-size: 10px;
  color: var(--color-primary);
}

.messages-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 30px 34px 18px;
}

.chat-welcome {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  position: relative;
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 0;
}

.chat-welcome .page-kicker {
  margin-bottom: 4px;
}

.welcome-lead {
  margin-bottom: 26px;
}

.suggestions {
  display: flex;
  flex-direction: column;
  gap: 7px;
  width: 100%;
}

.suggestion {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.58);
  color: var(--color-body);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--dur-fast), background var(--dur-fast), transform var(--dur-fast);
}

.suggestion:hover {
  border-color: var(--color-primary);
  background: #fff;
  transform: translateX(3px);
}

.suggestion .el-icon {
  color: var(--color-primary);
  font-size: 11px;
  flex: 0 0 11px;
}

.message-item {
  max-width: 760px;
  margin: 0 auto 26px;
  display: flex;
  flex-direction: column;
}

.message-item.user {
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 7px;
  font-size: 9.5px;
  letter-spacing: 0.4px;
  color: var(--color-muted);
}

.ai-mark {
  color: var(--color-primary);
  font-size: 13px;
}

.copy-message {
  margin-left: 6px;
  border: 0;
  background: transparent;
  padding: 0;
  font-size: 9.5px;
  color: var(--color-muted-soft);
  cursor: pointer;
  border-bottom: 1px solid transparent;
}

.copy-message:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.message-content {
  max-width: 86%;
  padding: 13px 17px;
  border-radius: 4px 14px 14px 14px;
  font-size: 13.5px;
  line-height: 1.75;
  word-break: break-word;
}

.message-item.user .message-content {
  max-width: 72%;
  border-radius: 14px 4px 14px 14px;
  background: var(--color-surface-dark);
  color: var(--color-on-dark);
  white-space: pre-wrap;
  box-shadow: 0 6px 20px rgba(24, 23, 21, 0.14);
}

.message-item.assistant .message-content {
  background: #fff;
  border: 1px solid var(--color-hairline);
  color: var(--color-body);
  box-shadow: var(--shadow-soft);
}

.markdown-body :deep(p) {
  margin: 0 0 9px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-family: var(--font-serif);
  font-weight: 400;
  color: var(--color-ink);
  letter-spacing: -0.2px;
  margin: 14px 0 7px;
}

.markdown-body :deep(h1:first-child),
.markdown-body :deep(h2:first-child),
.markdown-body :deep(h3:first-child) {
  margin-top: 0;
}

.markdown-body :deep(code) {
  background: var(--color-surface-soft);
  color: var(--color-primary-active);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 12px;
  font-family: var(--font-mono);
}

.markdown-body :deep(pre) {
  background: var(--color-surface-dark);
  color: var(--color-on-dark);
  padding: 14px 16px;
  border-radius: 9px;
  overflow-x: auto;
  margin: 9px 0;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--color-on-dark);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.markdown-body :deep(blockquote) {
  border-left: 2px solid var(--color-primary);
  padding-left: 12px;
  color: var(--color-muted);
  margin: 9px 0;
}

.markdown-body :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}

.cursor {
  display: inline-block;
  animation: blink 0.8s infinite;
  color: var(--color-primary);
  font-weight: 600;
}

@keyframes blink {
  50% { opacity: 0; }
}

.sources {
  max-width: 86%;
  margin-top: 9px;
}

.sources-label {
  display: block;
  margin-bottom: 6px;
  font-size: 9.5px;
  letter-spacing: 0.3px;
  color: var(--color-muted-soft);
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.source-tag {
  font-size: 9.5px;
  background: var(--color-surface-soft) !important;
  color: var(--color-muted) !important;
  border: 0 !important;
  border-radius: 999px;
}

.input-area {
  padding: 14px 24px 18px;
  border-top: 1px solid var(--color-hairline-soft);
  background: rgba(245, 240, 232, 0.4);
}

.input-shell {
  max-width: 860px;
  margin: 0 auto;
  border: 1px solid var(--color-hairline);
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 6px 22px rgba(20, 20, 19, 0.05);
  overflow: hidden;
  transition: border-color var(--dur-fast), box-shadow var(--dur-fast);
}

.input-shell:focus-within {
  border-color: rgba(204, 120, 92, 0.55);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.input-shell :deep(.el-textarea__inner) {
  padding: 13px 16px 4px;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  resize: none;
  font-size: 13px;
  line-height: 1.65;
  background: transparent;
}

.input-shell :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px 9px 16px;
}

.input-hint {
  font-size: 9.5px;
  color: var(--color-muted-soft);
}

.send-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 13px;
  border: 0;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--dur-fast), transform var(--dur-fast);
}

.send-button:hover:not(:disabled) {
  background: var(--color-primary-active);
  transform: translateY(-1px);
}

.send-button:disabled {
  background: var(--color-primary-disabled);
  color: var(--color-muted-soft);
  cursor: default;
}

.chat-scrim {
  display: none;
}

@media (max-width: 1100px) {
  .chat-page {
    height: calc(100vh - 138px);
  }

  .history-sidebar {
    width: 264px;
    flex-basis: 264px;
  }

  .messages-container {
    padding: 24px 22px 14px;
  }
}

@media (max-width: 900px) {
  .chat-page {
    height: calc(100vh - 118px);
    min-height: 520px;
  }

  .history-sidebar {
    position: absolute;
    inset: 0 auto 0 0;
    width: 290px;
    flex-basis: 290px;
    z-index: 30;
    transform: translateX(-106%);
    transition: transform 260ms var(--ease-out);
    background: var(--color-canvas);
    box-shadow: 24px 0 60px rgba(20, 20, 19, 0.2);
  }

  .history-sidebar.open {
    transform: translateX(0);
  }

  .chat-scrim {
    display: block;
    position: absolute;
    inset: 0;
    z-index: 25;
    background: rgba(24, 23, 21, 0.36);
    opacity: 0;
    pointer-events: none;
    transition: opacity 240ms;
  }

  .chat-scrim.show {
    opacity: 1;
    pointer-events: auto;
  }

  .mobile-history {
    display: inline-flex;
  }

  .chat-head {
    padding: 0 16px;
  }

  .messages-container {
    padding: 20px 16px 12px;
  }

  .input-area {
    padding: 11px 14px 14px;
  }

  .message-content {
    max-width: 92%;
  }

  .message-item.user .message-content {
    max-width: 84%;
  }

  .sources {
    max-width: 92%;
  }
}

@media (max-width: 600px) {
  .chat-page {
    height: calc(100vh - 104px);
    min-height: 480px;
  }

  .chat-head-sub {
    display: none;
  }

  .chat-head-title {
    font-size: 15px;
  }

  .chat-welcome h2,
  .chat-empty-main h2 {
    font-size: 25px;
  }

  .chat-welcome {
    justify-content: flex-start;
    padding-top: 26px;
  }

  .empty-number,
  .welcome-number {
    font-size: 92px;
    right: 14px;
  }

  .chat-empty-main {
    padding: 26px 20px;
  }

  .message-item {
    margin-bottom: 20px;
  }

  .input-hint {
    display: none;
  }

  .input-footer {
    justify-content: flex-end;
  }
}
</style>
