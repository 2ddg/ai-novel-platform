import request from './index'

export const listNovels = () => request.get('/novel')

export const createNovel = (data) => request.post('/novel', data)

export const getNovel = (id) => request.get(`/novel/${id}`)

export const updateNovel = (id, data) => request.put(`/novel/${id}`, data)

export const deleteNovel = (id) => request.delete(`/novel/${id}`)

export const listCharacters = (novelId) => request.get(`/novel/${novelId}/characters`)

export const createCharacter = (novelId, data) => request.post(`/novel/${novelId}/characters`, data)

export const updateCharacter = (novelId, charId, data) => request.put(`/novel/${novelId}/characters/${charId}`, data)

export const deleteCharacter = (novelId, charId) => request.delete(`/novel/${novelId}/characters/${charId}`)

export const generateOutline = (novelId, ideas = '') =>
  request.post(`/novel/${novelId}/generate-outline`, { ideas }, { timeout: 300000 })

export const listChapters = (novelId) => request.get(`/novel/${novelId}/chapters`)

export const getChapter = (novelId, chapterId) => request.get(`/novel/${novelId}/chapters/${chapterId}`)

export const updateChapter = (novelId, chapterId, data) => request.put(`/novel/${novelId}/chapters/${chapterId}`, data)

export const deleteChapter = (novelId, chapterId) => request.delete(`/novel/${novelId}/chapters/${chapterId}`)

export const generateChapter = (novelId, data) =>
  request.post(`/novel/${novelId}/chapters/generate`, data, { timeout: 300000 })

export const getMemory = (novelId) => request.get(`/novel/${novelId}/memory`)

export const updateMemory = (novelId, data) => request.put(`/novel/${novelId}/memory`, data)

export const deleteMemory = (novelId, memoryId) => request.delete(`/novel/${novelId}/memory/${memoryId}`)

// 续写：导入TXT
export const importNovelText = (novelId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/novel/${novelId}/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 900000,
  })
}

// AI修改意见
export const reviewChapters = (novelId, chapterIds) =>
  request.post(`/novel/${novelId}/review`, { chapter_ids: chapterIds }, { timeout: 300000 })

// AI重新生成记忆（chapter_nums为空则全部章节）
export const regenerateMemory = (novelId, chapterNums = []) =>
  request.post(`/novel/${novelId}/regenerate-memory`, { chapter_nums: chapterNums }, { timeout: 600000 })

// AI扫描补充角色
export const extractCharacters = (novelId) =>
  request.post(`/novel/${novelId}/extract-characters`, {}, { timeout: 300000 })

// AI根据已有章节重新生成大纲
export const regenerateOutline = (novelId) =>
  request.post(`/novel/${novelId}/regenerate-outline`, {}, { timeout: 300000 })

// AI生成全局记忆
export const generateGlobalMemory = (novelId) =>
  request.post(`/novel/${novelId}/generate-global-memory`, {}, { timeout: 300000 })
