import request from './index'

// 普通问答
export const chat = (data) => request.post('/chat', data)

// 流式问答（SSE），返回可读流（走 Vite 代理到后端 8001）
export const chatStream = (data) => {
  return fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify(data),
  })
}

// 对话历史
export const getHistory = (kbId) => request.get('/chat/history', { params: { kb_id: kbId } })

// 删除历史
export const deleteHistory = (id) => request.delete(`/chat/history/${id}`)

// 清空历史
export const clearHistory = (kbId) => request.delete('/chat/history', { params: { kb_id: kbId } })

// RAG评估
export const evaluateRAG = (data) => request.post('/chat/evaluate', data)
export const evaluateBatch = (testCases) => request.post('/chat/evaluate/batch', { test_cases: testCases })

// 可观测性
export const getTraces = (limit = 50) => request.get('/chat/observability/traces', { params: { limit } })
export const getTrace = (traceId) => request.get(`/chat/observability/traces/${traceId}`)
export const getObservabilityStats = () => request.get('/chat/observability/stats')

// 安全审计
export const securityAudit = (text) => request.post('/chat/security/audit', { text })
