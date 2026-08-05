import request from './index'

// 知识库列表
export const listKnowledge = () => request.get('/knowledge/list')

// 创建知识库
export const createKnowledge = (data) => request.post('/knowledge/create', data)

// 删除知识库
export const deleteKnowledge = (id) => request.delete(`/knowledge/${id}`)

// 上传文档
export const uploadDocument = (id, files) => {
  const formData = new FormData()
  // 支持单文件或多文件
  const fileList = Array.isArray(files) ? files : [files]
  fileList.forEach((f) => formData.append('files', f))
  return request.post(`/knowledge/${id}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

// 文档列表
export const listDocuments = (id) => request.get(`/knowledge/${id}/documents`)

// 删除文档
export const deleteDocument = (kbId, docId) => request.delete(`/knowledge/${kbId}/documents/${docId}`)
