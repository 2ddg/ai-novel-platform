<template>
  <div class="novel-detail fade-rise" v-loading="loading">
    <button type="button" class="back-link" @click="$router.push('/novel')">
      <el-icon><ArrowLeft /></el-icon>
      返回书架
    </button>

    <header class="novel-hero">
      <div class="hero-cover" :style="bookCoverStyle(novel?.genre)">
        <span class="hero-cover-spine" />
        <span class="hero-cover-mark">✳</span>
        <span class="hero-cover-initial">{{ bookInitial(novel?.title) }}</span>
        <div class="hero-cover-foot">
          <span>{{ novel?.genre || '未分类' }}</span>
          <span>AI NOVEL</span>
        </div>
      </div>

      <div class="hero-copy">
        <p class="page-kicker">MANUSCRIPT · {{ String(novel?.id || '').padStart(3, '0') }}</p>
        <h1 class="hero-title">{{ novel?.title || '未命名作品' }}</h1>
        <p class="hero-desc">
          {{ novel?.description || '还没有写简介。打开「设定」，把这本书的第一句话补上。' }}
        </p>

        <div class="hero-stats">
          <div class="hero-stat">
            <strong>{{ chapters.length }}</strong>
            <span>章节</span>
          </div>
          <span class="hero-stat-rule" />
          <div class="hero-stat">
            <strong>{{ characters.length }}</strong>
            <span>角色</span>
          </div>
          <span class="hero-stat-rule" />
          <div class="hero-stat">
            <strong>{{ totalWordsLabel }}</strong>
            <span>字</span>
          </div>
          <span class="hero-stat-rule" />
          <div class="hero-stat">
            <strong>{{ averageAuditScore ?? '—' }}</strong>
            <span>平均审计</span>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <el-button type="primary" class="hero-primary" @click="focusWriting">
          继续写作
          <el-icon class="el-icon--right"><Right /></el-icon>
        </el-button>
        <el-button :disabled="!chapters.length" @click="showExportDialog = true">
          导出作品
        </el-button>
      </div>
    </header>

    <el-tabs v-model="activeTab" tab-position="left" class="studio-tabs">
      <!-- 角色设定 -->
      <el-tab-pane name="characters">
        <template #label>
          <span class="studio-tab">
            <el-icon><User /></el-icon>
            <span>角色</span>
            <span class="studio-tab-count">{{ characters.length }}</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">CAST</p>
            <h2>角色</h2>
            <p class="panel-sub">让每个人都带着自己的欲望进场。</p>
          </div>
          <div class="panel-actions">
            <el-button type="primary" :icon="Plus" @click="showCharDialog = true">添加角色</el-button>
            <el-button
              :icon="MagicStick"
              :loading="extractingChars"
              :disabled="!chapters.length"
              @click="onExtractCharacters"
            >
              从全文提取
            </el-button>
          </div>
        </div>

        <div v-if="!characters.length" class="empty-note">
          还没有角色。先写下主角的名字与欲望，故事会自己找上门。
        </div>
        <div v-else class="character-grid">
          <article v-for="char in characters" :key="char.id" class="character-card">
            <div class="character-top">
              <span class="character-avatar">{{ bookInitial(char.name) }}</span>
              <div>
                <h3>{{ char.name }}</h3>
                <p>{{ char.personality || '性格待补充' }}</p>
              </div>
            </div>
            <p class="character-bg">{{ char.background || '还没有写下背景。' }}</p>
            <div v-if="char.current_state" class="character-state">
              <span>当前状态</span>
              <strong>{{ formatCharState(char.current_state) }}</strong>
            </div>
            <div class="character-actions">
              <button type="button" @click="onEditChar(char)">编辑</button>
              <button type="button" class="danger" @click="onDeleteChar(char)">删除</button>
            </div>
          </article>
        </div>

        <el-dialog v-model="showCharDialog" :title="editingChar ? '编辑角色' : '添加角色'" width="450px">
          <el-form :model="charForm" label-width="80px">
            <el-form-item label="角色名">
              <el-input v-model="charForm.name" />
            </el-form-item>
            <el-form-item label="性格">
              <el-input v-model="charForm.personality" type="textarea" :rows="2" placeholder="性格特征、说话风格等" />
            </el-form-item>
            <el-form-item label="背景">
              <el-input v-model="charForm.background" type="textarea" :rows="2" placeholder="身世、经历、动机等" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showCharDialog = false">取消</el-button>
            <el-button type="primary" @click="onSaveChar">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- 大纲 -->
      <el-tab-pane name="outline">
        <template #label>
          <span class="studio-tab">
            <el-icon><Notebook /></el-icon>
            <span>大纲</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">STRUCTURE</p>
            <h2>大纲</h2>
            <p class="panel-sub">骨架可以改，但不能没有。</p>
          </div>
          <span class="panel-count">{{ outlineText.length }} 字</span>
        </div>

        <div class="outline-layout">
          <aside class="outline-side">
            <div class="dark-note">
              <span class="dark-note-mark">✳</span>
              <p>先写下你非写不可的那一幕，剩下的交给结构。</p>
              <span>WRITING NOTE · 01</span>
            </div>
            <label class="field-label">灵感与要求</label>
            <el-input
              v-model="outlineIdeas"
              type="textarea"
              :rows="7"
              placeholder="可选。写下想法、人物关系、想写的场面；留空则由 AI 自动补全。"
            />
            <el-button
              type="primary"
              class="outline-generate"
              :icon="MagicStick"
              :loading="generating"
              @click="onGenerateOutline"
            >
              {{ novel?.outline ? '重新生成大纲' : 'AI 生成大纲' }}
            </el-button>
            <el-button
              :loading="regeneratingOutline"
              :disabled="!chapters.length"
              class="outline-regenerate"
              @click="onRegenerateOutline"
            >
              根据已有章节生成
            </el-button>
          </aside>

          <div class="outline-main">
            <div class="outline-main-head">
              <span>故事大纲</span>
              <span>{{ outlineText.length }} 字</span>
            </div>
            <el-input
              v-model="outlineText"
              type="textarea"
              :rows="24"
              class="prose-input"
              placeholder="故事从这里开始生长。AI 生成的结果会出现在这里，也可以直接手动写。"
            />
            <div class="outline-save">
              <el-button type="primary" :loading="saving" @click="onSaveOutline">保存大纲</el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 章节 -->
      <el-tab-pane name="chapters">
        <template #label>
          <span class="studio-tab">
            <el-icon><Reading /></el-icon>
            <span>章节</span>
            <span class="studio-tab-count">{{ chapters.length }}</span>
          </span>
        </template>

        <div class="panel-heading">
          <div>
            <p class="panel-kicker">MANUSCRIPT</p>
            <h2>章节</h2>
            <p class="panel-sub">一本小说，是许多个「下一章」堆起来的。</p>
          </div>
          <div class="panel-actions">
            <span class="panel-count">共 {{ chapters.length }} 章 · {{ totalWordsLabel }} 字</span>
            <el-button :disabled="!chapters.length" @click="activeTab = 'fulltext'">审阅全文</el-button>
          </div>
        </div>

        <div v-if="!chapters.length" class="empty-note">
          还没有章节。在下方写下第一章的第一句话，AI 会接着往下写。
        </div>
        <div v-else class="chapter-grid">
          <article
            v-for="ch in chapters"
            :key="ch.id"
            class="chapter-card"
            @click="onOpenChapter(ch)"
          >
            <div class="chapter-card-top">
              <span class="chapter-no">CH. {{ String(ch.chapter_num).padStart(2, '0') }}</span>
              <el-tag
                v-if="ch.audit_score !== null && ch.audit_score !== undefined"
                :type="ch.audit_score >= 70 ? 'success' : 'warning'"
                size="small"
                effect="plain"
              >
                {{ ch.audit_score }}
              </el-tag>
              <span v-else class="chapter-unaudited">未审计</span>
            </div>
            <h3>{{ ch.title || '未命名章节' }}</h3>
            <p class="chapter-excerpt">
              {{ ch.summary || (ch.content || '').slice(0, 72) || '还没有正文。' }}
            </p>
            <div class="chapter-card-foot">
              <span>{{ (ch.content || '').length }} 字</span>
              <span v-if="ch.rewrite_count > 0">重写 {{ ch.rewrite_count }} 次</span>
              <div class="chapter-card-actions" @click.stop>
                <button type="button" @click="onOpenChapter(ch)">续写</button>
                <button type="button" @click="onEditChapter(ch)">编辑</button>
                <button type="button" class="danger" @click="onDeleteChapter(ch)">删除</button>
              </div>
            </div>
          </article>
        </div>

        <div id="write-studio" class="write-studio">
          <div class="write-head">
            <div>
              <p class="panel-kicker">WRITE NEXT</p>
              <h3>写第 {{ writeForm.chapter_num }} 章</h3>
            </div>
            <span class="write-hint">AI 会带上角色、记忆与未回收伏笔</span>
          </div>
          <el-form :model="writeForm" label-position="top" class="write-form">
            <div class="write-grid">
              <el-form-item label="章节号">
                <el-input-number v-model="writeForm.chapter_num" :min="1" :max="999" />
              </el-form-item>
              <el-form-item label="标题">
                <el-input v-model="writeForm.title" placeholder="章节标题" />
              </el-form-item>
              <el-form-item label="章节要求" class="span-2">
                <el-input
                  v-model="writeForm.chapter_outline"
                  type="textarea"
                  :rows="2"
                  placeholder="本章主要事件、冲突或想写的画面"
                />
              </el-form-item>
            </div>
            <div class="write-actions">
              <el-button type="primary" :loading="writing" @click="onGenerateChapter">AI 写作</el-button>
              <el-button class="stream-btn" :loading="streaming" @click="onStreamChapter">
                流式写作
              </el-button>
              <span class="write-footnote">初稿不需要完美，它只需要存在。</span>
            </div>
          </el-form>
        </div>

        <div v-if="writingContent" class="chapter-preview">
          <div class="preview-header">
            <span>{{ streaming ? '正在生成…' : '生成结果' }}</span>
            <el-button size="small" text @click="writingContent = ''">关闭</el-button>
          </div>
          <div class="preview-content">{{ writingContent }}</div>
        </div>
      </el-tab-pane>

      <!-- 记忆（分章节） -->
      <el-tab-pane name="memory">
        <template #label>
          <span class="studio-tab">
            <el-icon><Collection /></el-icon>
            <span>记忆</span>
            <span class="studio-tab-count">{{ memoryChapters.length }}</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">CONTINUITY</p>
            <h2>记忆</h2>
            <p class="panel-sub">AI 的连续性靠它，而不是靠运气。</p>
          </div>
        </div>
        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
          AI自动维护关键状态记忆：每章写完后自动生成对应记忆条目。记忆是给AI用的，确保续写时角色状态、伏笔、剧情不丢。
        </el-alert>

        <!-- 全局记忆 -->
        <el-card style="margin-bottom: 16px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">全局记忆（跨章节）</span>
              <el-button
                size="small"
                type="success"
                :icon="MagicStick"
                :loading="generatingGlobalMemory"
                :disabled="!chapters.length"
                @click="onGenerateGlobalMemory"
              >
                AI生成
              </el-button>
            </div>
          </template>
          <el-input
            v-model="memoryGlobal"
            type="textarea"
            :rows="4"
            placeholder="全局记忆：贯穿整本小说的关键设定（如世界观、核心矛盾等）。点击AI生成可自动分析章节内容。"
          />
        </el-card>

        <!-- 分章记忆 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
          <span style="font-weight: 600">分章记忆</span>
          <div>
            <el-button
              size="small"
              type="success"
              :icon="MagicStick"
              :loading="regeneratingMemory"
              :disabled="!chapters.length"
              @click="showRegenMemoryDialog = true"
            >
              AI重新生成记忆
            </el-button>
          </div>
        </div>
        <el-alert
          v-if="memoryChapters.length && memoryChapters.some(m => m.content && m.content.includes('临时记忆'))"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 12px"
        >
          当前记忆为导入时的临时摘要（内容前150字）。点击"AI重新生成记忆"可让AI分析章节内容，生成结构化记忆（角色状态、伏笔、剧情进展等）。
        </el-alert>
        <el-empty v-if="!memoryChapters.length" description="暂无分章记忆，写章节后会自动生成" :image-size="60" />
        <el-collapse v-else v-model="expandedMemories">
          <el-collapse-item
            v-for="mem in memoryChapters"
            :key="mem.id || mem.chapter_num"
            :name="mem.chapter_num"
          >
            <template #title>
              <span style="font-weight: 600">第{{ mem.chapter_num }}章后记忆</span>
              <el-tag v-if="mem.content && mem.content.includes('临时记忆')" size="small" type="warning" style="margin-left: 8px">临时</el-tag>
            </template>
            <el-input
              v-model="mem.content"
              type="textarea"
              :rows="6"
              placeholder="本章后的记忆状态"
            />
            <div style="margin-top: 8px; text-align: right">
              <el-button size="small" type="primary" @click="onSaveChapterMemory(mem)">保存此章记忆</el-button>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div style="margin-top: 16px; text-align: right">
          <el-button type="primary" :loading="savingMemory" @click="onSaveAllMemory">保存全部记忆</el-button>
        </div>
      </el-tab-pane>

      <!-- 伏笔追踪 -->
      <el-tab-pane name="foreshadowing">
        <template #label>
          <span class="studio-tab">
            <el-icon><Flag /></el-icon>
            <span>伏笔</span>
            <span v-if="pendingForeshadowings" class="studio-tab-count accent">{{ pendingForeshadowings }}</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">PAYOFF</p>
            <h2>伏笔</h2>
            <p class="panel-sub">埋下的每一颗种子，都要记得浇水。</p>
          </div>
          <div class="panel-actions">
            <el-button :loading="scanningFs" @click="showFsScanDialog = true">AI 扫描伏笔</el-button>
            <el-button type="primary" @click="onAddForeshadowing">添加伏笔</el-button>
          </div>
        </div>

        <div class="metric-row">
          <div class="metric">
            <span>全部</span>
            <strong>{{ foreshadowings.length }}</strong>
          </div>
          <div class="metric accent">
            <span>待回收</span>
            <strong>{{ pendingForeshadowings }}</strong>
          </div>
          <div class="metric">
            <span>已回收</span>
            <strong>{{ resolvedForeshadowings }}</strong>
          </div>
          <div v-if="fsBatchSelected.length" class="metric-batch">
            <el-button size="small" type="success" @click="onBatchResolveFs">标记回收 ({{ fsBatchSelected.length }})</el-button>
            <el-button size="small" type="danger" @click="onBatchDeleteFs">删除 ({{ fsBatchSelected.length }})</el-button>
            <el-button size="small" @click="fsBatchSelected = []">取消选择</el-button>
          </div>
        </div>

        <div class="data-card">
        <el-table :data="foreshadowings" style="width: 100%" @selection-change="fsBatchSelected = $event" empty-text="还没有伏笔。AI 会在写作后自动记录，也可以手动添加。">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="chapter_planted" label="埋设章" width="80" />
          <el-table-column prop="content" label="伏笔内容" show-overflow-tooltip />
          <el-table-column label="优先级" width="100">
            <template #default="{ row }">
              <el-tag :type="row.priority === 'high' ? 'danger' : row.priority === 'medium' ? 'warning' : 'info'" size="small">
                {{ row.priority === 'high' ? '高' : row.priority === 'medium' ? '中' : '低' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'resolved' ? 'success' : row.status === 'abandoned' ? 'info' : 'warning'" size="small">
                {{ row.status === 'resolved' ? '已回收' : row.status === 'abandoned' ? '已放弃' : '待回收' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="chapter_resolved" label="回收章" width="80" />
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" @click="onEditForeshadowing(row)">编辑</el-button>
              <el-button v-if="row.status === 'pending'" size="small" type="success" @click="onResolveForeshadowing(row)">标记回收</el-button>
              <el-button size="small" type="danger" @click="onDeleteForeshadowing(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </el-tab-pane>

      <!-- 时间线 -->
      <el-tab-pane name="timeline">
        <template #label>
          <span class="studio-tab">
            <el-icon><Clock /></el-icon>
            <span>时间线</span>
            <span class="studio-tab-count">{{ timelines.length }}</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">CHRONOLOGY</p>
            <h2>时间线</h2>
            <p class="panel-sub">谁在什么时候做了什么，别让读者替你记。</p>
          </div>
          <div class="panel-actions">
            <el-button :loading="scanningTl" @click="showTlScanDialog = true">AI 扫描事件</el-button>
            <el-button type="primary" @click="onAddTimeline">添加事件</el-button>
          </div>
        </div>

        <div class="metric-row">
          <div class="metric">
            <span>事件</span>
            <strong>{{ timelines.length }}</strong>
          </div>
          <div v-if="tlBatchSelected.length" class="metric-batch">
            <el-button size="small" type="danger" @click="onBatchDeleteTl">删除 ({{ tlBatchSelected.length }})</el-button>
            <el-button size="small" @click="tlBatchSelected = []">取消选择</el-button>
          </div>
        </div>

        <div class="data-card">
        <el-table :data="timelines" style="width: 100%" @selection-change="tlBatchSelected = $event" empty-text="还没有时间线事件。AI 会在生成章节后自动提取。">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="chapter_num" label="章节" width="80" />
          <el-table-column prop="time_label" label="时间标记" width="120" />
          <el-table-column prop="event" label="事件描述" show-overflow-tooltip />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" @click="onEditTimeline(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onDeleteTimeline(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </el-tab-pane>

      <!-- 全文 + AI修改意见 -->
      <el-tab-pane name="fulltext">
        <template #label>
          <span class="studio-tab">
            <el-icon><Document /></el-icon>
            <span>全文</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">THE WHOLE</p>
            <h2>全文</h2>
            <p class="panel-sub">退后一步，看看这本书现在的样子。</p>
          </div>
          <div class="panel-actions">
            <el-button
              :icon="MagicStick"
              :loading="reviewing"
              :disabled="!chapters.length"
              @click="showReviewDialog = true"
            >
              获取修改意见
            </el-button>
            <el-button
              type="primary"
              :icon="Download"
              :disabled="!chapters.length"
              @click="showExportDialog = true"
            >
              导出
            </el-button>
          </div>
        </div>

        <div class="metric-row">
          <div class="metric">
            <span>章节</span>
            <strong>{{ chapters.length }}</strong>
          </div>
          <div class="metric">
            <span>总字数</span>
            <strong>{{ totalWordsLabel }}</strong>
          </div>
          <div class="metric">
            <span>平均审计</span>
            <strong>{{ averageAuditScore ?? '—' }}</strong>
          </div>
        </div>

        <!-- AI审阅结果 -->
        <section v-if="reviewResult" class="review-card">
          <div class="review-card-head">
            <div>
              <p class="panel-kicker">EDITOR'S NOTE</p>
              <h3>AI 修改建议</h3>
            </div>
            <el-button size="small" text @click="reviewResult = ''">关闭</el-button>
          </div>
          <div class="review-content">{{ reviewResult }}</div>
        </section>

        <!-- 分章节表格 -->
        <div class="data-card">
        <el-table
          :data="chapters"
          style="width: 100%"
          empty-text="还没有正文。先去「章节」写下第一章。"
          @row-click="onEditChapter"
        >
          <el-table-column prop="chapter_num" label="第X章" width="80" />
          <el-table-column prop="title" label="标题" width="180" />
          <el-table-column prop="content" label="内容预览" show-overflow-tooltip>
            <template #default="{ row }">
              {{ (row.content || '').slice(0, 60) }}{{ (row.content || '').length > 60 ? '...' : '' }}
            </template>
          </el-table-column>
          <el-table-column label="审计" width="100" @click.stop>
            <template #default="{ row }">
              <el-tag v-if="row.audit_score !== null && row.audit_score !== undefined" :type="row.audit_score >= 70 ? 'success' : 'warning'" size="small">
                {{ row.audit_score }}
              </el-tag>
              <span v-else style="color: #999; font-size: 12px">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" @click.stop>
            <template #default="{ row }">
              <el-button size="small" @click.stop="onEditChapter(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
        </div>
      </el-tab-pane>

      <!-- 作品设定 -->
      <el-tab-pane name="info">
        <template #label>
          <span class="studio-tab">
            <el-icon><Setting /></el-icon>
            <span>设定</span>
          </span>
        </template>
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">THE BRIEF</p>
            <h2>设定</h2>
            <p class="panel-sub">书名、类型与写作风格，AI 续写时会参考这里。</p>
          </div>
        </div>

        <div class="settings-layout">
          <el-form :model="editForm" label-position="top" class="settings-form">
            <div class="form-grid">
              <el-form-item label="小说名">
                <el-input v-model="editForm.title" />
              </el-form-item>
              <el-form-item label="类型">
                <el-select v-model="editForm.genre" placeholder="选择类型" allow-create filterable style="width: 100%">
                  <el-option label="玄幻" value="玄幻" />
                  <el-option label="都市" value="都市" />
                  <el-option label="言情" value="言情" />
                  <el-option label="科幻" value="科幻" />
                  <el-option label="悬疑" value="悬疑" />
                  <el-option label="历史" value="历史" />
                  <el-option label="武侠" value="武侠" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="简介">
              <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="用两三句话告诉读者，这本书讲什么。" />
            </el-form-item>
            <div class="style-head">
              <span class="field-label">写作风格指南</span>
              <el-button link type="primary" @click="useDefaultStyle">使用默认风格模板</el-button>
            </div>
            <el-input v-model="editForm.style_guide" type="textarea" :rows="12" placeholder="写作风格指南（可使用默认）" />
            <div class="settings-save">
              <el-button type="primary" :loading="saving" @click="onSaveInfo">保存设定</el-button>
            </div>
          </el-form>

          <aside class="settings-aside">
            <div class="dark-note">
              <span class="dark-note-mark">✳</span>
              <p>设定是为了让故事稳定，不是为了把它关起来。</p>
              <span>THE BRIEF · 06</span>
            </div>
            <dl class="meta-list">
              <div><dt>作品编号</dt><dd>#{{ String(novel?.id || '').padStart(3, '0') }}</dd></div>
              <div><dt>当前章节</dt><dd>{{ chapters.length }}</dd></div>
              <div><dt>已写字数</dt><dd>{{ totalWordsLabel }}</dd></div>
              <div><dt>最近审计</dt><dd>{{ averageAuditScore ?? '—' }}</dd></div>
            </dl>
          </aside>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 章节编辑器 -->
    <el-dialog v-model="showChapterEditor" :title="`第${editingChapter?.chapter_num || ''}章 编辑`" width="80%" top="5vh">
      <el-form v-if="editingChapter" label-width="60px">
        <el-form-item label="标题">
          <el-input v-model="editingChapter.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="editingChapter.content" type="textarea" :rows="20" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChapterEditor = false">取消</el-button>
        <el-button type="primary" :loading="savingChapter" @click="onSaveChapter">保存</el-button>
      </template>
    </el-dialog>

    <!-- AI修改意见：选择章节 -->
    <el-dialog v-model="showReviewDialog" title="AI修改意见" width="500px">
      <p style="color: #909399; margin-bottom: 12px">选择要审阅的章节，AI会扫描内容并提出修改建议（只提建议，不改写）：</p>
      <el-checkbox-group v-model="reviewSelected">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.id">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="reviewing"
          :disabled="!reviewSelected.length"
          @click="onReview"
        >
          开始审阅（{{ reviewSelected.length }}章）
        </el-button>
      </template>
    </el-dialog>

    <!-- AI重新生成记忆：选择章节 -->
    <el-dialog v-model="showRegenMemoryDialog" title="AI重新生成记忆" width="500px">
      <p style="color: #909399; margin-bottom: 12px">
        选择要重新生成记忆的章节（AI会分析章节内容，生成结构化记忆：角色状态、伏笔、剧情进展等）：
      </p>
      <div style="margin-bottom: 12px">
        <el-button size="small" @click="regenMemorySelected = chapters.map(c => c.chapter_num)">全选</el-button>
        <el-button size="small" @click="regenMemorySelected = []">清空</el-button>
      </div>
      <el-checkbox-group v-model="regenMemorySelected">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.chapter_num">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="showRegenMemoryDialog = false">取消</el-button>
        <el-button
          type="success"
          :loading="regeneratingMemory"
          :disabled="!regenMemorySelected.length"
          @click="onRegenerateMemory"
        >
          生成（{{ regenMemorySelected.length }}章）
        </el-button>
      </template>
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog v-model="showExportDialog" title="导出章节" width="500px">
      <p style="color: #909399; margin-bottom: 12px">选择要导出的章节和格式：</p>
      <div style="margin-bottom: 12px">
        <el-button size="small" @click="exportSelected = chapters.map(c => c.id)">全选</el-button>
        <el-button size="small" @click="exportSelected = []">清空</el-button>
      </div>
      <el-checkbox-group v-model="exportSelected" style="margin-bottom: 16px">
        <div v-for="ch in chapters" :key="ch.id" style="margin-bottom: 8px">
          <el-checkbox :label="ch.id">
            第{{ ch.chapter_num }}章 {{ ch.title || '' }}
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <el-form-item label="格式" label-width="60px">
        <el-radio-group v-model="exportFormat">
          <el-radio-button label="txt">TXT</el-radio-button>
          <el-radio-button label="md">Markdown</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button
          type="success"
          :disabled="!exportSelected.length"
          @click="onExport"
        >
          导出（{{ exportSelected.length }}章）
        </el-button>
      </template>
    </el-dialog>

    <!-- 伏笔编辑对话框 -->
    <el-dialog v-model="showFsEditDialog" :title="fsEditData.id ? '编辑伏笔' : '添加伏笔'" width="500px">
      <el-form :model="fsEditData" label-width="80px">
        <el-form-item label="埋设章节">
          <el-input-number v-model="fsEditData.chapter_planted" :min="1" />
        </el-form-item>
        <el-form-item label="伏笔内容">
          <el-input v-model="fsEditData.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="fsEditData.priority">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="fsEditData.status">
            <el-option label="待回收" value="pending" />
            <el-option label="已回收" value="resolved" />
            <el-option label="已放弃" value="abandoned" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="fsEditData.status === 'resolved'" label="回收章节">
          <el-input-number v-model="fsEditData.chapter_resolved" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFsEditDialog = false">取消</el-button>
        <el-button type="primary" @click="onSaveForeshadowing">保存</el-button>
      </template>
    </el-dialog>

    <!-- 伏笔扫描对话框 -->
    <el-dialog v-model="showFsScanDialog" title="AI扫描章节伏笔" width="500px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
        选择要扫描的章节，AI将自动提取新埋设的伏笔，并检查是否回收了旧伏笔。
      </el-alert>
      <el-table :data="chapters" @selection-change="fsScanSelected = $event">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="chapter_num" label="章节" width="80" />
        <el-table-column prop="title" label="标题" />
      </el-table>
      <template #footer>
        <el-button @click="showFsScanDialog = false">取消</el-button>
        <el-button type="primary" :loading="scanningFs" @click="onScanForeshadowings">开始扫描</el-button>
      </template>
    </el-dialog>

    <!-- 时间线编辑对话框 -->
    <el-dialog v-model="showTlEditDialog" :title="tlEditData.id ? '编辑事件' : '添加事件'" width="500px">
      <el-form :model="tlEditData" label-width="80px">
        <el-form-item label="章节号">
          <el-input-number v-model="tlEditData.chapter_num" :min="1" />
        </el-form-item>
        <el-form-item label="事件">
          <el-input v-model="tlEditData.event" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="时间标记">
          <el-input v-model="tlEditData.time_label" placeholder="如：当夜、次日清晨" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTlEditDialog = false">取消</el-button>
        <el-button type="primary" @click="onSaveTimeline">保存</el-button>
      </template>
    </el-dialog>

    <!-- 时间线扫描对话框 -->
    <el-dialog v-model="showTlScanDialog" title="AI扫描章节事件" width="500px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
        选择要扫描的章节，AI将自动提取重大事件。
      </el-alert>
      <el-table :data="chapters" @selection-change="tlScanSelected = $event">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="chapter_num" label="章节" width="80" />
        <el-table-column prop="title" label="标题" />
      </el-table>
      <template #footer>
        <el-button @click="showTlScanDialog = false">取消</el-button>
        <el-button type="primary" :loading="scanningTl" @click="onScanTimelines">开始扫描</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Right, Plus, MagicStick, Download,
  Reading, User, Notebook, Collection, Flag, Clock, Document, Setting,
} from '@element-plus/icons-vue'
import {
  getNovel, updateNovel, listCharacters, createCharacter, updateCharacter, deleteCharacter,
  generateOutline, listChapters, getChapter, updateChapter, deleteChapter,
  generateChapter, getMemory, updateMemory, reviewChapters, regenerateMemory,
  extractCharacters, regenerateOutline, generateGlobalMemory,
  listForeshadowings, createForeshadowing, updateForeshadowing, deleteForeshadowing, scanForeshadowings,
  batchDeleteForeshadowings, batchUpdateForeshadowings,
  listTimelines, createTimeline, updateTimeline, deleteTimeline, scanTimelines,
  batchDeleteTimelines,
} from '../api/novel'
import { DEFAULT_STYLE_GUIDE } from '../config'
import { bookCoverStyle, bookInitial } from '../utils/bookCover'

const route = useRoute()
const novelId = computed(() => route.params.id)

const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const writing = ref(false)
const streaming = ref(false)
const savingMemory = ref(false)
const savingChapter = ref(false)
const reviewing = ref(false)
const scanningFs = ref(false)
const scanningTl = ref(false)

const novel = ref(null)
const activeTab = ref('chapters')
const outlineText = ref('')
const outlineIdeas = ref('')
const memoryGlobal = ref('')
const memoryChapters = ref([])
const expandedMemories = ref([])
const characters = ref([])
const chapters = ref([])
const writingContent = ref('')
const foreshadowings = ref([])
const timelines = ref([])

const pendingForeshadowings = computed(() => foreshadowings.value.filter(f => f.status === 'pending').length)
const resolvedForeshadowings = computed(() => foreshadowings.value.filter(f => f.status === 'resolved').length)
const maxChapterNum = computed(() => chapters.value.reduce((max, ch) => Math.max(max, ch.chapter_num || 0), 0))
const averageAuditScore = computed(() => {
  const scored = chapters.value.filter(ch => ch.audit_score !== null && ch.audit_score !== undefined)
  if (!scored.length) return null
  return Math.round(scored.reduce((sum, ch) => sum + ch.audit_score, 0) / scored.length)
})
const totalWords = computed(() => chapters.value.reduce((sum, ch) => sum + (ch.content || '').replace(/\s/g, '').length, 0))
const totalWordsLabel = computed(() => totalWords.value.toLocaleString('zh-CN'))

function focusWriting() {
  activeTab.value = 'chapters'
  nextTick(() => {
    document.getElementById('write-studio')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

// 伏笔编辑
const showFsEditDialog = ref(false)
const fsEditData = ref({})
const showFsScanDialog = ref(false)
const fsScanSelected = ref([])

// 时间线编辑
const showTlEditDialog = ref(false)
const tlEditData = ref({})
const showTlScanDialog = ref(false)
const tlScanSelected = ref([])
const fsBatchSelected = ref([])
const tlBatchSelected = ref([])

// AI审阅
const showReviewDialog = ref(false)
const reviewSelected = ref([])
const reviewResult = ref('')

// AI重新生成记忆
const showRegenMemoryDialog = ref(false)
const regenMemorySelected = ref([])
const regeneratingMemory = ref(false)

// 导出
const showExportDialog = ref(false)
const exportSelected = ref([])
const exportFormat = ref('txt')

// AI扫描补充角色 / 大纲 / 全局记忆
const extractingChars = ref(false)
const regeneratingOutline = ref(false)
const generatingGlobalMemory = ref(false)

const editForm = ref({ title: '', genre: '', description: '', style_guide: '' })

const showCharDialog = ref(false)
const editingChar = ref(null)
const charForm = ref({ name: '', personality: '', background: '' })

const showChapterEditor = ref(false)
const editingChapter = ref(null)

const writeForm = ref({ chapter_num: 1, title: '', chapter_outline: '' })

async function fetchData() {
  loading.value = true
  try {
    const [n, chars, chs, mem, fs, tl] = await Promise.all([
      getNovel(novelId.value),
      listCharacters(novelId.value),
      listChapters(novelId.value),
      getMemory(novelId.value).catch(() => ({ chapters: [], global: '' })),
      listForeshadowings(novelId.value).catch(() => []),
      listTimelines(novelId.value).catch(() => []),
    ])
    novel.value = n
    editForm.value = { title: n.title, genre: n.genre, description: n.description, style_guide: n.style_guide || '' }
    outlineText.value = n.outline || ''
    characters.value = Array.isArray(chars) ? chars : (chars?.data || [])
    chapters.value = Array.isArray(chs) ? chs : (chs?.data || [])
    foreshadowings.value = Array.isArray(fs) ? fs : (fs?.data || [])
    timelines.value = Array.isArray(tl) ? tl : (tl?.data || [])
    // 分章节记忆
    memoryGlobal.value = mem.global || ''
    memoryChapters.value = mem.chapters || []
    if (chs.length > 0) {
      const maxNum = chs.reduce((max, ch) => Math.max(max, ch.chapter_num || 0), 0)
      writeForm.value.chapter_num = maxNum + 1
    }
  } finally {
    loading.value = false
  }
}

function useDefaultStyle() {
  editForm.value.style_guide = DEFAULT_STYLE_GUIDE
}

function formatCharState(stateStr) {
  try {
    const s = JSON.parse(stateStr)
    const parts = []
    if (s.position) parts.push(`位置:${s.position}`)
    if (s.power) parts.push(`实力:${s.power}`)
    if (s.mood) parts.push(`心情:${s.mood}`)
    if (s.items) parts.push(`持有:${s.items}`)
    if (s.knowledge) parts.push(`已知:${s.knowledge}`)
    return parts.length ? parts.join('，') : '暂无'
  } catch {
    return stateStr
  }
}

async function onSaveInfo() {
  saving.value = true
  try {
    const n = await updateNovel(novelId.value, editForm.value)
    novel.value = n
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function onGenerateOutline() {
  generating.value = true
  try {
    const result = await generateOutline(novelId.value, outlineIdeas.value)
    outlineText.value = result.outline
    ElMessage.success('大纲生成成功')
  } finally {
    generating.value = false
  }
}

async function onSaveOutline() {
  saving.value = true
  try {
    await updateNovel(novelId.value, {
      title: novel.value.title,
      genre: novel.value.genre,
      description: novel.value.description,
      style_guide: novel.value.style_guide,
      outline: outlineText.value,
    })
    ElMessage.success('大纲已保存')
  } finally {
    saving.value = false
  }
}

async function onSaveAllMemory() {
  savingMemory.value = true
  try {
    await updateMemory(novelId.value, {
      global: memoryGlobal.value,
      chapters: memoryChapters.value.map(m => ({ chapter_num: m.chapter_num, content: m.content })),
    })
    ElMessage.success('全部记忆已保存')
  } finally {
    savingMemory.value = false
  }
}

async function onSaveChapterMemory(mem) {
  try {
    await updateMemory(novelId.value, { chapter_num: mem.chapter_num, content: mem.content })
    ElMessage.success(`第${mem.chapter_num}章记忆已保存`)
  } catch { /* handled by interceptor */ }
}

// AI修改意见
async function onReview() {
  reviewing.value = true
  showReviewDialog.value = false
  try {
    const result = await reviewChapters(novelId.value, reviewSelected.value)
    reviewResult.value = result.suggestions
    activeTab.value = 'fulltext'
    ElMessage.success('审阅完成')
  } finally {
    reviewing.value = false
  }
}

// AI重新生成记忆
async function onRegenerateMemory() {
  regeneratingMemory.value = true
  showRegenMemoryDialog.value = false
  try {
    const result = await regenerateMemory(novelId.value, regenMemorySelected.value)
    const okCount = result.results.filter(r => r.status === 'ok').length
    const failCount = result.results.filter(r => r.status === 'failed').length
    ElMessage.success(`记忆生成完成：成功${okCount}章${failCount ? '，失败' + failCount + '章' : ''}`)
    // 重新拉取记忆
    const mem = await getMemory(novelId.value)
    memoryChapters.value = mem.chapters || []
    // 展开刚生成的章节
    expandedMemories.value = regenMemorySelected.value
  } finally {
    regeneratingMemory.value = false
  }
}

// 导出
function onExport() {
  const selected = chapters.value
    .filter(c => exportSelected.value.includes(c.id))
    .sort((a, b) => a.chapter_num - b.chapter_num)

  if (!selected.length) {
    ElMessage.warning('请选择要导出的章节')
    return
  }

  let content = ''
  const title = novel.value?.title || '小说'
  if (exportFormat.value === 'md') {
    content = `# ${title}\n\n`
    for (const ch of selected) {
      content += `## 第${ch.chapter_num}章 ${ch.title || ''}\n\n${ch.content || ''}\n\n`
    }
  } else {
    content = `${title}\n\n`
    for (const ch of selected) {
      content += `第${ch.chapter_num}章 ${ch.title || ''}\n\n${ch.content || ''}\n\n\n`
    }
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}.${exportFormat.value}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  ElMessage.success(`已导出 ${selected.length} 章`)
  showExportDialog.value = false
}

// AI扫描补充角色
async function onExtractCharacters() {
  extractingChars.value = true
  try {
    const result = await extractCharacters(novelId.value)
    if (result.total_added > 0) {
      ElMessage.success(`扫描完成，新增 ${result.total_added} 个角色：${result.added.join('、')}`)
    } else {
      ElMessage.success('扫描完成，没有发现新角色')
    }
    const charsRes = await listCharacters(novelId.value)
    characters.value = Array.isArray(charsRes) ? charsRes : (charsRes?.data || [])
  } finally {
    extractingChars.value = false
  }
}

// 根据已有章节重新生成大纲
async function onRegenerateOutline() {
  regeneratingOutline.value = true
  try {
    const result = await regenerateOutline(novelId.value)
    outlineText.value = result.outline
    ElMessage.success('大纲已根据已有章节重新生成')
  } finally {
    regeneratingOutline.value = false
  }
}

// AI生成全局记忆
async function onGenerateGlobalMemory() {
  generatingGlobalMemory.value = true
  try {
    const result = await generateGlobalMemory(novelId.value)
    memoryGlobal.value = result.global_memory
    ElMessage.success('全局记忆已生成')
  } finally {
    generatingGlobalMemory.value = false
  }
}

async function onGenerateChapter() {
  if (!writeForm.value.chapter_outline) {
    ElMessage.warning('请填写章节要求')
    return
  }
  writing.value = true
  writingContent.value = ''
  try {
    const result = await generateChapter(novelId.value, {
      chapter_num: writeForm.value.chapter_num,
      chapter_outline: writeForm.value.chapter_outline,
      title: writeForm.value.title || `第${writeForm.value.chapter_num}章`,
    })
    writingContent.value = result.chapter.content
    ElMessage.success('章节生成成功')
    await fetchData()
    writeForm.value.title = ''
    writeForm.value.chapter_outline = ''
  } finally {
    writing.value = false
  }
}

async function onStreamChapter() {
  if (!writeForm.value.chapter_outline) {
    ElMessage.warning('请填写章节要求')
    return
  }
  streaming.value = true
  writingContent.value = ''

  const token = localStorage.getItem('token')
  try {
    const response = await fetch('/api/novel/' + novelId.value + '/chapters/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        chapter_num: writeForm.value.chapter_num,
        chapter_outline: writeForm.value.chapter_outline,
        title: writeForm.value.title || `第${writeForm.value.chapter_num}章`,
      }),
    })

    if (!response.ok) {
      ElMessage.error('请求失败: ' + response.status)
      streaming.value = false
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') {
            streaming.value = false
            fetchData()
            ElMessage.success('章节生成成功')
            return
          }
          try {
            const data = JSON.parse(dataStr)
            if (data.type === 'chunk') {
              writingContent.value += data.data
            } else if (data.type === 'audit_start') {
              writingContent.value += '\n\n--- 正在审计章节质量... ---\n'
            } else if (data.type === 'audit_done') {
              const audit = data.data
              writingContent.value += `\n审计完成：总分 ${audit.score}/100\n`
              if (audit.dimensions) {
                for (const [k, v] of Object.entries(audit.dimensions)) {
                  writingContent.value += `  ${k}: ${v}/10\n`
                }
              }
              if (audit.issues && audit.issues.length) {
                writingContent.value += '问题：\n'
                audit.issues.forEach(i => { writingContent.value += `  - ${i}\n` })
              }
              if (audit.ai_tics && audit.ai_tics.items && audit.ai_tics.items.length) {
                writingContent.value += '\nAI腔检测：\n'
                audit.ai_tics.items.forEach(item => {
                  const flag = item.exceeded ? '⚠' : '✓'
                  writingContent.value += `  ${flag} ${item.suggestion}（${item.count}次）\n`
                })
              }
            } else if (data.type === 'rewrite_start') {
              writingContent.value += `\n\n--- ${data.data} ---\n`
            } else if (data.type === 'rewrite_done') {
              writingContent.value = data.data.content
              const audit = data.data.audit
              writingContent.value += `\n\n--- 重写后审计：${audit.score}/100 ---\n`
            } else if (data.type === 'error') {
              ElMessage.error(data.data)
              streaming.value = false
              return
            } else if (data.type === 'done') {
              const d = data.data
              writingContent.value += `\n\n--- 章节已保存（ID: ${d.chapter_id}）---\n`
              if (d.audit_score !== undefined) {
                writingContent.value += `审计分数：${d.audit_score}/100`
                if (d.rewrite_count > 0) {
                  writingContent.value += `（已自动重写${d.rewrite_count}次）`
                }
                writingContent.value += '\n'
              }
              await fetchData()
              writeForm.value.title = ''
              writeForm.value.chapter_outline = ''
            }
          } catch {
            writingContent.value += dataStr
          }
        }
      }
    }
  } catch (e) {
    ElMessage.error('流式请求失败: ' + e.message)
  } finally {
    streaming.value = false
  }
}

function onOpenChapter(row) {
  editingChapter.value = { ...row }
  showChapterEditor.value = true
}

async function onEditChapter(row) {
  editingChapter.value = { ...row }
  showChapterEditor.value = true
}

async function onSaveChapter() {
  if (!editingChapter.value) return
  savingChapter.value = true
  try {
    await updateChapter(novelId.value, editingChapter.value.id, {
      title: editingChapter.value.title,
      content: editingChapter.value.content,
    })
    ElMessage.success('保存成功')
    showChapterEditor.value = false
    fetchData()
  } finally {
    savingChapter.value = false
  }
}

async function onDeleteChapter(row) {
  try {
    await ElMessageBox.confirm(`确定删除第${row.chapter_num}章？`, '删除确认', { type: 'warning' })
    await deleteChapter(novelId.value, row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* cancelled */ }
}

function onEditChar(row) {
  editingChar.value = row
  charForm.value = { name: row.name, personality: row.personality, background: row.background }
  showCharDialog.value = true
}

async function onDeleteChar(row) {
  try {
    await ElMessageBox.confirm(`确定删除角色「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteCharacter(novelId.value, row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch { /* cancelled */ }
}

async function onSaveChar() {
  if (!charForm.value.name) {
    ElMessage.warning('请填写角色名')
    return
  }
  try {
    if (editingChar.value) {
      await updateCharacter(novelId.value, editingChar.value.id, charForm.value)
    } else {
      await createCharacter(novelId.value, charForm.value)
    }
    ElMessage.success('保存成功')
    showCharDialog.value = false
    editingChar.value = null
    charForm.value = { name: '', personality: '', background: '' }
    fetchData()
  } catch { /* handled */ }
}

// ============ 伏笔管理 ============
async function loadForeshadowings() {
  try {
    const res = await listForeshadowings(novelId.value)
    console.log('loadForeshadowings res:', res)
    foreshadowings.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (e) { console.error('加载伏笔列表失败:', e) }
}

function onAddForeshadowing() {
  fsEditData.value = { chapter_planted: 1, content: '', priority: 'medium', status: 'pending' }
  showFsEditDialog.value = true
}

function onEditForeshadowing(row) {
  fsEditData.value = { ...row }
  showFsEditDialog.value = true
}

async function onSaveForeshadowing() {
  try {
    if (fsEditData.value.id) {
      await updateForeshadowing(novelId.value, fsEditData.value.id, fsEditData.value)
    } else {
      await createForeshadowing(novelId.value, fsEditData.value)
    }
    ElMessage.success('保存成功')
    showFsEditDialog.value = false
    loadForeshadowings()
  } catch { /* handled */ }
}

async function onDeleteForeshadowing(row) {
  try {
    await ElMessageBox.confirm('确定删除该伏笔？', '提示', { type: 'warning' })
    await deleteForeshadowing(novelId.value, row.id)
    ElMessage.success('已删除')
    loadForeshadowings()
  } catch { /* cancelled */ }
}

async function onResolveForeshadowing(row) {
  try {
    await updateForeshadowing(novelId.value, row.id, { status: 'resolved', chapter_resolved: maxChapterNum.value })
    ElMessage.success('已标记为回收')
    loadForeshadowings()
  } catch { /* handled */ }
}

async function onBatchDeleteFs() {
  if (!fsBatchSelected.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${fsBatchSelected.value.length} 条伏笔？`, '提示', { type: 'warning' })
    const ids = fsBatchSelected.value.map(c => c.id)
    await batchDeleteForeshadowings(novelId.value, ids)
    ElMessage.success(`已删除 ${ids.length} 条伏笔`)
    fsBatchSelected.value = []
    loadForeshadowings()
  } catch { /* cancelled */ }
}

async function onBatchResolveFs() {
  if (!fsBatchSelected.value.length) return
  try {
    await ElMessageBox.confirm(`确定将选中的 ${fsBatchSelected.value.length} 条伏笔标记为已回收？`, '提示', { type: 'warning' })
    const ids = fsBatchSelected.value.map(c => c.id)
    await batchUpdateForeshadowings(novelId.value, ids, { status: 'resolved', chapter_resolved: maxChapterNum.value })
    ElMessage.success(`已标记 ${ids.length} 条伏笔为回收`)
    fsBatchSelected.value = []
    loadForeshadowings()
  } catch { /* cancelled */ }
}

async function onScanForeshadowings() {
  if (!fsScanSelected.value.length) {
    ElMessage.warning('请选择要扫描的章节')
    return
  }
  scanningFs.value = true
  try {
    const res = await scanForeshadowings(novelId.value, fsScanSelected.value.map(c => c.id))
    ElMessage.success(`扫描完成：新发现 ${res.new_count} 条，回收 ${res.resolved_count} 条`)
    showFsScanDialog.value = false
    fsScanSelected.value = []
    loadForeshadowings()
  } catch (e) { console.error('扫描伏笔失败:', e) }
  finally { scanningFs.value = false }
}

// ============ 时间线管理 ============
async function loadTimelines() {
  try {
    const res = await listTimelines(novelId.value)
    console.log('loadTimelines res:', res)
    timelines.value = Array.isArray(res) ? res : (res?.data || [])
  } catch (e) { console.error('加载时间线失败:', e) }
}

function onAddTimeline() {
  tlEditData.value = { chapter_num: maxChapterNum.value || 1, event: '', time_label: '' }
  showTlEditDialog.value = true
}

function onEditTimeline(row) {
  tlEditData.value = { ...row }
  showTlEditDialog.value = true
}

async function onSaveTimeline() {
  try {
    if (tlEditData.value.id) {
      await updateTimeline(novelId.value, tlEditData.value.id, tlEditData.value)
    } else {
      await createTimeline(novelId.value, tlEditData.value)
    }
    ElMessage.success('保存成功')
    showTlEditDialog.value = false
    loadTimelines()
  } catch { /* handled */ }
}

async function onDeleteTimeline(row) {
  try {
    await ElMessageBox.confirm('确定删除该事件？', '提示', { type: 'warning' })
    await deleteTimeline(novelId.value, row.id)
    ElMessage.success('已删除')
    loadTimelines()
  } catch { /* cancelled */ }
}

async function onBatchDeleteTl() {
  if (!tlBatchSelected.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${tlBatchSelected.value.length} 条事件？`, '提示', { type: 'warning' })
    const ids = tlBatchSelected.value.map(c => c.id)
    await batchDeleteTimelines(novelId.value, ids)
    ElMessage.success(`已删除 ${ids.length} 条事件`)
    tlBatchSelected.value = []
    loadTimelines()
  } catch { /* cancelled */ }
}

async function onScanTimelines() {
  if (!tlScanSelected.value.length) {
    ElMessage.warning('请选择要扫描的章节')
    return
  }
  scanningTl.value = true
  try {
    const res = await scanTimelines(novelId.value, tlScanSelected.value.map(c => c.id))
    ElMessage.success(`扫描完成：新发现 ${res.new_count} 条事件`)
    showTlScanDialog.value = false
    tlScanSelected.value = []
    loadTimelines()
  } catch (e) { console.error('扫描时间线失败:', e) }
  finally { scanningTl.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.novel-detail {
  max-width: 1280px;
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 18px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--color-muted);
  font-size: 12.5px;
  cursor: pointer;
  transition: color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}

.back-link:hover {
  color: var(--color-primary);
  transform: translateX(-2px);
}

.novel-hero {
  position: relative;
  display: grid;
  grid-template-columns: 146px minmax(0, 1fr) auto;
  align-items: center;
  gap: 32px;
  margin-bottom: 22px;
  padding: 28px 32px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-xl);
  background:
    radial-gradient(520px 280px at 88% 8%, rgba(204, 120, 92, 0.09), transparent 70%),
    linear-gradient(140deg, #ffffff 0%, #f7f3eb 100%);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.novel-hero::after {
  content: "";
  position: absolute;
  right: -90px;
  bottom: -150px;
  width: 300px;
  height: 300px;
  border: 1px solid rgba(204, 120, 92, 0.16);
  border-radius: 50%;
  pointer-events: none;
}

.hero-cover {
  position: relative;
  width: 140px;
  aspect-ratio: 2 / 3;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px 9px 9px 3px;
  color: #f7f2e8;
  box-shadow: 0 18px 32px rgba(37, 30, 23, 0.24);
  overflow: hidden;
}

.hero-cover-spine {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 11px;
  width: 1px;
  background: rgba(255, 255, 255, 0.16);
}

.hero-cover-mark {
  position: absolute;
  top: 13px;
  right: 14px;
  font-size: 11px;
  color: var(--cover-accent);
  opacity: 0.85;
}

.hero-cover-initial {
  font-family: var(--font-serif);
  font-size: 56px;
  line-height: 1;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 3px 16px rgba(0, 0, 0, 0.2);
}

.hero-cover-foot {
  position: absolute;
  right: 13px;
  bottom: 12px;
  left: 20px;
  display: flex;
  justify-content: space-between;
  font-size: 7px;
  letter-spacing: 1.3px;
  color: rgba(255, 255, 255, 0.58);
  text-transform: uppercase;
}

.hero-copy {
  min-width: 0;
}

.hero-title {
  margin: 8px 0 10px;
  font-family: var(--font-serif);
  font-size: clamp(30px, 3.2vw, 42px);
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -1px;
  color: var(--color-ink);
}

.hero-desc {
  max-width: 620px;
  margin: 0 0 20px;
  color: var(--color-body);
  font-size: 13.5px;
  line-height: 1.8;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.hero-stat strong {
  font-family: var(--font-serif);
  font-size: 21px;
  font-weight: 500;
  line-height: 1;
  color: var(--color-ink);
}

.hero-stat span:last-child {
  font-size: 9px;
  letter-spacing: 1.2px;
  color: var(--color-muted);
  text-transform: uppercase;
}

.hero-stat-rule {
  width: 1px;
  height: 28px;
  background: var(--color-hairline);
}

.hero-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  align-self: center;
}

.hero-primary {
  box-shadow: 0 8px 18px rgba(204, 120, 92, 0.24);
}

/* 左侧工作台导航 */
.studio-tabs {
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.studio-tabs :deep(.el-tabs__header.is-left) {
  width: 186px;
  margin: 0;
  padding: 16px 10px;
  background: #f2eee5;
  border-right: 1px solid var(--color-hairline);
  flex-shrink: 0;
}

.studio-tabs :deep(.el-tabs__nav-wrap.is-left)::after,
.studio-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.studio-tabs :deep(.el-tabs__nav.is-left) {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
}

.studio-tabs :deep(.el-tabs__item.is-left) {
  height: 44px;
  line-height: 44px;
  justify-content: flex-start;
  padding: 0 12px !important;
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-muted);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out),
    box-shadow var(--dur-fast) var(--ease-out);
}

.studio-tabs :deep(.el-tabs__item.is-left:hover) {
  color: var(--color-ink);
  background: rgba(255, 255, 255, 0.6);
}

.studio-tabs :deep(.el-tabs__item.is-left.is-active) {
  color: var(--color-ink);
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(37, 30, 23, 0.06), 0 0 0 1px rgba(37, 30, 23, 0.03);
}

.studio-tabs :deep(.el-tabs__content) {
  padding: 26px 28px 30px;
  overflow: visible;
}

.studio-tabs :deep(#tab-chapters) { order: 1; }
.studio-tabs :deep(#tab-characters) { order: 2; }
.studio-tabs :deep(#tab-outline) { order: 3; }
.studio-tabs :deep(#tab-memory) { order: 4; }
.studio-tabs :deep(#tab-foreshadowing) { order: 5; }
.studio-tabs :deep(#tab-timeline) { order: 6; }
.studio-tabs :deep(#tab-fulltext) { order: 7; }
.studio-tabs :deep(#tab-info) { order: 8; }

.studio-tab {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
}

.studio-tab .el-icon {
  font-size: 15px;
  opacity: 0.72;
}

.studio-tab-count {
  margin-left: auto;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(41, 40, 37, 0.06);
  color: var(--color-muted);
  font-size: 10px;
}

.studio-tab-count.accent {
  background: rgba(204, 120, 92, 0.14);
  color: var(--color-primary);
}

.studio-tabs :deep(.el-tabs__item.is-active) .studio-tab-count {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

/* 面板通用 */
.panel-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--color-hairline);
}

.panel-kicker {
  margin: 0 0 6px;
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 1.8px;
  color: var(--color-primary);
}

.panel-heading h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 400;
  letter-spacing: -0.5px;
  line-height: 1.2;
  color: var(--color-ink);
}

.panel-sub {
  margin: 6px 0 0;
  color: var(--color-muted);
  font-size: 12.5px;
}

.panel-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.panel-count {
  color: var(--color-muted);
  font-size: 11.5px;
  white-space: nowrap;
}

.empty-note {
  margin: 8px 0 20px;
  padding: 30px 24px;
  border: 1px dashed var(--color-hairline);
  border-radius: var(--rounded-md);
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 13px;
  line-height: 1.8;
  text-align: center;
}

.metric-row {
  display: flex;
  align-items: stretch;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.metric {
  min-width: 104px;
  padding: 12px 16px;
  border: 1px solid var(--color-hairline);
  border-radius: 10px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric span {
  font-size: 9.5px;
  letter-spacing: 1px;
  color: var(--color-muted);
  text-transform: uppercase;
}

.metric strong {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 500;
  line-height: 1.15;
  color: var(--color-ink);
}

.metric.accent strong {
  color: var(--color-primary);
}

.metric-batch {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.data-card {
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
  overflow: hidden;
}

.data-card :deep(.el-table) {
  --el-table-border-color: var(--color-hairline-soft);
  --el-table-header-bg-color: #f6f3ec;
  --el-table-row-hover-bg-color: #faf8f2;
}

.data-card :deep(.el-table th.el-table__cell) {
  font-size: 10.5px;
  font-weight: 500;
  letter-spacing: 0.6px;
  color: var(--color-muted);
  text-transform: uppercase;
}

.data-card :deep(.el-table td.el-table__cell) {
  font-size: 12.5px;
  color: var(--color-body);
}

/* 章节 */
.chapter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 22px;
}

.chapter-card {
  padding: 17px 18px 13px;
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
  cursor: pointer;
  transition: transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out),
    border-color var(--dur-base) var(--ease-out);
}

.chapter-card:hover {
  transform: translateY(-2px);
  border-color: rgba(204, 120, 92, 0.28);
  box-shadow: 0 12px 26px rgba(37, 30, 23, 0.07);
}

.chapter-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.chapter-no {
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 1.4px;
  color: var(--color-primary);
}

.chapter-unaudited {
  font-size: 10px;
  color: var(--color-muted);
}

.chapter-card h3 {
  margin: 0 0 7px;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 500;
  line-height: 1.4;
  color: var(--color-ink);
}

.chapter-excerpt {
  min-height: 40px;
  margin: 0 0 13px;
  color: var(--color-muted);
  font-size: 12px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chapter-card-foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 9px;
  border-top: 1px solid var(--color-hairline-soft);
  color: var(--color-muted);
  font-size: 10.5px;
}

.chapter-card-actions {
  margin-left: auto;
  display: flex;
  gap: 2px;
}

.chapter-card-actions button,
.character-actions button {
  padding: 2px 6px;
  border: 0;
  border-radius: 4px;
  background: none;
  color: var(--color-muted);
  font-size: 10.5px;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}

.chapter-card-actions button:hover,
.character-actions button:hover {
  background: var(--color-surface-soft);
  color: var(--color-ink);
}

.chapter-card-actions button.danger:hover,
.character-actions button.danger:hover {
  color: #b04a3a;
}

.write-studio {
  position: relative;
  margin-top: 26px;
  padding: 22px 24px;
  border: 1px solid rgba(204, 120, 92, 0.2);
  border-radius: 14px;
  background:
    radial-gradient(380px 200px at 100% 0%, rgba(204, 120, 92, 0.08), transparent 70%),
    #fbf8f2;
  scroll-margin-top: 90px;
  overflow: hidden;
}

.write-studio::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: var(--color-primary);
}

.write-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.write-head h3 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 400;
  letter-spacing: -0.3px;
  color: var(--color-ink);
}

.write-hint {
  color: var(--color-muted);
  font-size: 10.5px;
}

.write-grid {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 0 18px;
}

.write-grid .span-2 {
  grid-column: 1 / -1;
}

.write-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.write-form :deep(.el-form-item__label) {
  padding-bottom: 4px;
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.4;
}

.write-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.write-footnote {
  margin-left: auto;
  color: var(--color-muted);
  font-family: var(--font-serif);
  font-size: 11px;
  font-style: italic;
}

.chapter-preview {
  margin-top: 20px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  overflow: hidden;
  background: #ffffff;
  box-shadow: var(--shadow-card);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 16px;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 500;
}

.preview-content {
  max-height: 480px;
  padding: 20px;
  overflow-y: auto;
  color: var(--color-body);
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
}

/* 角色 */
.character-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.character-card {
  padding: 18px;
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
  transition: transform var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out);
}

.character-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgba(37, 30, 23, 0.06);
}

.character-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 13px;
}

.character-avatar {
  width: 42px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;
  background: #2b2824;
  color: #f5efe4;
  font-family: var(--font-serif);
  font-size: 18px;
}

.character-top h3 {
  margin: 0 0 3px;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 500;
  color: var(--color-ink);
}

.character-top p {
  margin: 0;
  color: var(--color-muted);
  font-size: 11.5px;
  line-height: 1.5;
}

.character-bg {
  min-height: 40px;
  margin: 0 0 11px;
  color: var(--color-body);
  font-size: 12px;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.character-state {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 11px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--color-surface-soft);
  font-size: 10.5px;
}

.character-state span {
  color: var(--color-muted);
}

.character-state strong {
  font-weight: 500;
  color: var(--color-ink);
  text-align: right;
}

.character-actions {
  display: flex;
  gap: 6px;
  padding-top: 9px;
  border-top: 1px solid var(--color-hairline-soft);
}

/* 大纲 */
.outline-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.outline-side {
  position: sticky;
  top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dark-note {
  position: relative;
  padding: 20px;
  border-radius: 12px;
  background: #292724;
  color: #f0e9dc;
  overflow: hidden;
}

.dark-note-mark {
  color: #d99a72;
  font-size: 17px;
}

.dark-note p {
  margin: 12px 0 18px;
  font-family: var(--font-serif);
  font-size: 16px;
  line-height: 1.65;
  color: #f6f1e7;
}

.dark-note > span:last-child {
  font-size: 8.5px;
  letter-spacing: 1.6px;
  color: rgba(246, 241, 231, 0.42);
}

.field-label {
  margin-top: 6px;
  color: var(--color-muted);
  font-size: 10.5px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.outline-generate,
.outline-regenerate {
  width: 100%;
  margin-left: 0 !important;
}

.outline-regenerate {
  margin-top: 0 !important;
}

.outline-main {
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
  overflow: hidden;
}

.outline-main-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 10.5px;
  letter-spacing: 0.5px;
}

.prose-input :deep(.el-textarea__inner) {
  padding: 18px 20px;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: var(--color-body);
  font-family: var(--font-serif);
  font-size: 14.5px;
  line-height: 1.95;
  resize: vertical;
}

.prose-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.outline-save {
  display: flex;
  justify-content: flex-end;
  padding: 10px 14px;
  border-top: 1px solid var(--color-hairline-soft);
}

/* 全文 */
.review-card {
  margin-bottom: 18px;
  padding: 20px 22px;
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
  box-shadow: var(--shadow-card);
}

.review-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.review-card-head h3 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 400;
  color: var(--color-ink);
}

.review-content {
  padding: 16px 18px;
  border: 1px solid var(--color-hairline);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--rounded-md);
  background: var(--color-surface-soft);
  color: var(--color-body);
  font-size: 13.5px;
  line-height: 1.85;
  white-space: pre-wrap;
}

/* 设定 */
.settings-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 22px;
  align-items: start;
}

.settings-form {
  padding: 22px 24px;
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
}

.form-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 0 16px;
}

.settings-form :deep(.el-form-item__label) {
  padding-bottom: 5px;
  color: var(--color-muted);
  font-size: 11.5px;
  line-height: 1.4;
}

.style-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 6px 0 8px;
}

.settings-save {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.settings-aside {
  position: sticky;
  top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.meta-list {
  margin: 0;
  padding: 6px 18px;
  border: 1px solid var(--color-hairline);
  border-radius: 12px;
  background: #ffffff;
}

.meta-list div {
  display: flex;
  justify-content: space-between;
  padding: 11px 0;
  border-bottom: 1px solid var(--color-hairline-soft);
  font-size: 11.5px;
}

.meta-list div:last-child {
  border-bottom: 0;
}

.meta-list dt {
  color: var(--color-muted);
}

.meta-list dd {
  margin: 0;
  color: var(--color-ink);
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 1100px) {
  .novel-hero {
    grid-template-columns: 132px minmax(0, 1fr);
    gap: 24px;
  }

  .hero-cover {
    width: 126px;
  }

  .hero-actions {
    grid-column: 2;
    flex-direction: row;
    justify-content: flex-start;
  }

  .character-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .outline-layout {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  .settings-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .settings-aside {
    position: static;
    flex-direction: row;
    align-items: flex-start;
  }

  .settings-aside .dark-note {
    flex: 1;
  }

  .meta-list {
    flex: 1;
  }
}

@media (max-width: 860px) {
  .studio-tabs {
    display: block;
  }

  .studio-tabs :deep(.el-tabs__header.is-left) {
    width: 100%;
    padding: 8px;
    border-right: 0;
    border-bottom: 1px solid var(--color-hairline);
  }

  .studio-tabs :deep(.el-tabs__nav.is-left) {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
  }

  .studio-tabs :deep(.el-tabs__item.is-left) {
    width: auto;
    height: 36px;
    line-height: 36px;
    padding: 0 10px !important;
  }

  .studio-tab {
    gap: 6px;
  }

  .studio-tab-count {
    margin-left: 4px;
  }

  .studio-tabs :deep(.el-tabs__content) {
    padding: 20px;
  }

  .panel-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .panel-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .novel-hero {
    grid-template-columns: 1fr;
    gap: 18px;
    padding: 20px;
  }

  .hero-cover {
    width: 96px;
  }

  .hero-actions {
    grid-column: auto;
    flex-direction: column;
    align-items: stretch;
  }

  .hero-title {
    font-size: 30px;
  }

  .chapter-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .write-studio {
    padding: 18px;
  }

  .write-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .write-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .write-grid .span-2 {
    grid-column: auto;
  }

  .write-actions {
    flex-wrap: wrap;
  }

  .write-footnote {
    width: 100%;
    margin-left: 0;
  }

  .character-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .outline-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .outline-side {
    position: static;
  }

  .settings-aside {
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .metric-batch {
    margin-left: 0;
  }
}
</style>
