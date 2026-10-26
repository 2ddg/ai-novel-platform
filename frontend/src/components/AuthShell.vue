<template>
  <div class="auth-shell">
    <aside class="auth-story">
      <router-link to="/login" class="story-brand">
        <span class="story-mark">✳</span>
        <span class="story-brand-copy">
          <span class="story-name">AI 小说创作</span>
          <span class="story-sub">WRITING STUDIO</span>
        </span>
      </router-link>

      <div class="story-body">
        <p class="story-kicker">{{ kicker }}</p>
        <h1 class="story-heading">{{ heading }}</h1>
        <p class="story-lead">{{ lead }}</p>

        <div class="manuscript">
          <div class="manuscript-top">
            <span>CHAPTER 01</span>
            <span>草稿 · 未完成</span>
          </div>
          <p class="manuscript-quote">“{{ quote }}”</p>
          <div class="manuscript-lines">
            <span />
            <span />
            <span />
          </div>
          <div class="manuscript-footer">
            <span>由你执笔 · 由 AI 陪写</span>
            <span class="manuscript-dot" />
          </div>
        </div>
      </div>

      <footer class="story-footer">
        <span>MANUSCRIPT STUDIO</span>
        <span>{{ year }}</span>
      </footer>
    </aside>

    <main class="auth-panel">
      <div class="auth-panel-inner">
        <div class="panel-top">
          <span class="panel-label">作者入口</span>
          <span class="panel-index">{{ panelIndex }}</span>
        </div>
        <div class="panel-content">
          <slot />
        </div>
        <p class="panel-footnote">本地创作空间 · 你的故事只属于你</p>
      </div>
    </main>
  </div>
</template>

<script setup>
defineProps({
  kicker: { type: String, default: 'A ROOM FOR STORIES' },
  heading: { type: String, required: true },
  lead: { type: String, default: '' },
  quote: { type: String, default: '初稿不必漂亮，它只需要存在。' },
  panelIndex: { type: String, default: '01 / 02' },
})

const year = new Date().getFullYear()
</script>

<style scoped>
.auth-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.06fr) minmax(420px, 0.94fr);
  background: var(--color-canvas);
}

.auth-story {
  min-height: 100vh;
  padding: 44px 56px 32px;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(ellipse at 82% 0%, rgba(204, 120, 92, 0.2), transparent 42%),
    radial-gradient(ellipse at 0% 100%, rgba(232, 165, 90, 0.09), transparent 46%),
    var(--color-surface-dark);
  color: var(--color-on-dark);
  position: relative;
  overflow: hidden;
}

.auth-story::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(
    90deg,
    transparent 0,
    transparent 119px,
    rgba(250, 249, 245, 0.045) 120px
  );
  pointer-events: none;
}

.story-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.story-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-on-dark);
  font-size: 24px;
  line-height: 1;
  box-shadow: 0 8px 28px rgba(204, 120, 92, 0.36);
}

.story-brand-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.story-name {
  font-family: var(--font-serif);
  font-size: 17px;
  letter-spacing: -0.3px;
  line-height: 1.1;
}

.story-sub {
  font-size: 9px;
  letter-spacing: 2px;
  color: var(--color-on-dark-soft);
}

.story-body {
  margin: auto 0;
  max-width: 620px;
  padding: 56px 0 40px;
  position: relative;
  z-index: 1;
  animation: story-in 760ms var(--ease-out) both;
}

.story-kicker {
  font-size: 10px;
  letter-spacing: 2.4px;
  color: var(--color-on-dark-soft);
  margin-bottom: 26px;
}

.story-heading {
  font-family: var(--font-serif);
  font-size: clamp(42px, 4.5vw, 68px);
  font-weight: 400;
  line-height: 1.04;
  letter-spacing: -1.8px;
  color: var(--color-on-dark);
  margin-bottom: 24px;
  white-space: pre-line;
}

.story-lead {
  max-width: 430px;
  font-size: 14.5px;
  line-height: 1.8;
  color: var(--color-on-dark-soft);
  margin-bottom: 44px;
  white-space: pre-line;
}

.manuscript {
  max-width: 430px;
  padding: 22px 24px 18px;
  border: 1px solid rgba(250, 249, 245, 0.14);
  border-radius: 14px;
  background: rgba(250, 249, 245, 0.055);
  backdrop-filter: blur(8px);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
  transform: rotate(-1.2deg);
}

.manuscript-top,
.manuscript-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 1.2px;
  color: var(--color-on-dark-soft);
}

.manuscript-quote {
  font-family: var(--font-serif);
  font-size: 22px;
  line-height: 1.5;
  letter-spacing: -0.3px;
  color: var(--color-on-dark);
  margin: 22px 0;
}

.manuscript-lines {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 20px;
}

.manuscript-lines span {
  height: 1px;
  background: rgba(250, 249, 245, 0.12);
}

.manuscript-lines span:nth-child(2) {
  width: 82%;
}

.manuscript-lines span:nth-child(3) {
  width: 56%;
}

.manuscript-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 12px var(--color-primary);
}

.story-footer {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 1.6px;
  color: #75716a;
  position: relative;
  z-index: 1;
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background:
    radial-gradient(ellipse at 100% 0%, rgba(204, 120, 92, 0.08), transparent 44%),
    var(--color-canvas);
  position: relative;
}

.auth-panel-inner {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  min-height: 540px;
  animation: panel-in 680ms 100ms var(--ease-out) both;
}

.panel-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--color-hairline);
  margin-bottom: 44px;
}

.panel-label {
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--color-muted);
  text-transform: uppercase;
}

.panel-index {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--color-muted-soft);
}

.panel-content {
  flex: 1;
}

.panel-footnote {
  margin-top: 42px;
  font-size: 10.5px;
  letter-spacing: 0.4px;
  color: var(--color-muted-soft);
  text-align: center;
}

@keyframes story-in {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes panel-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 980px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .auth-story {
    min-height: auto;
    padding: 28px 28px 34px;
  }

  .story-body {
    padding: 52px 0 8px;
  }

  .story-heading {
    font-size: clamp(38px, 8vw, 56px);
  }

  .story-lead,
  .manuscript {
    display: none;
  }

  .story-footer {
    display: none;
  }

  .auth-panel {
    padding: 40px 24px 52px;
  }

  .auth-panel-inner {
    min-height: auto;
    max-width: 460px;
  }

  .panel-top {
    margin-bottom: 34px;
  }
}

@media (max-width: 520px) {
  .auth-story {
    padding: 22px 20px 28px;
  }

  .story-body {
    padding-top: 38px;
  }

  .story-kicker {
    margin-bottom: 16px;
  }

  .story-heading {
    font-size: 36px;
    letter-spacing: -1px;
  }

  .auth-panel {
    padding: 32px 20px 44px;
  }

  .panel-footnote {
    margin-top: 28px;
  }
}
</style>
