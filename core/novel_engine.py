"""小说写作引擎 - 大纲生成、章节写作、记忆管理"""
import re
import logging
from typing import Optional, List

from core.novel_llm_client import call_novel_llm, call_novel_llm_stream

logger = logging.getLogger(__name__)

DEFAULT_STYLE_GUIDE = """# 写作风格指南

## 文笔风格
- 参考江南：细腻描写、情感刻画、氛围营造
- 对话有张力，情感表达含蓄但有力

## 核心特色
- 括号内心OS：用括号插入角色内心吐槽
- 短句快节奏：对话简洁，节奏明快
- 轻松幽默：使用语气词

## 章节规范
- 每章2000字左右
- 以对话和互动推进剧情
- 结尾最好有钩子（不是必须）

## 排版规范
- 每段首行缩进两格
- 段落之间不空行
- 对话独立成段"""


class NovelEngine:
    """小说写作引擎"""

    @staticmethod
    async def generate_outline(
        title: str,
        genre: str,
        description: str,
        characters: str = "",
        style_guide: str = "",
        user_ideas: str = "",
    ) -> str:
        """生成小说大纲（支持用户想法补足）"""
        style = style_guide or DEFAULT_STYLE_GUIDE

        ideas_section = ""
        if user_ideas:
            ideas_section = f"""
【作者的想法/思路】
{user_ideas}

请以上述想法为核心，补足并完善整个大纲。作者的思路优先级最高，围绕它展开剧情。"""
        else:
            ideas_section = ""

        prompt = f"""请为以下小说生成一个详细的章节大纲（10-20章）：

小说名：{title}
类型：{genre or '玄幻/都市'}
简介：{description}
{ideas_section}
{style}
{('主要角色：' + characters) if characters else ''}

要求：
1. 每章包含：章节标题、主要事件、关键冲突
2. 剧情要有起承转合，节奏紧凑
3. 角色性格鲜明，对话推动剧情
4. 每章结尾留钩子
5. 用中文输出，格式清晰"""

        result = await call_novel_llm(prompt, temperature=0.8, max_tokens=2000)
        return result

    @staticmethod
    def build_chapter_prompt(
        chapter_num: int,
        chapter_outline: str,
        characters: str,
        memory: str,
        prev_summaries: str,
        style_guide: str,
    ) -> str:
        """构建章节写作的精简 Prompt（省 Token）"""
        style = style_guide or DEFAULT_STYLE_GUIDE
        return f"""{style}

【角色设定】
{characters}

【当前状态/记忆】
{memory}

【前面章节摘要】
{prev_summaries}

【第{chapter_num}章要求】
{chapter_outline}

请以中文写第{chapter_num}章，约2000字。注意：括号内心OS、短句快节奏、对话推进、结尾钩子。"""

    @staticmethod
    async def write_chapter_stream(
        chapter_num: int,
        chapter_outline: str,
        characters: str,
        memory: str,
        prev_summaries: str,
        style_guide: str = "",
    ):
        """流式写作单个章节"""
        prompt = NovelEngine.build_chapter_prompt(
            chapter_num, chapter_outline, characters, memory, prev_summaries, style_guide
        )
        system_prompt = "你是一位专业的小说作者，请严格按照风格指南和章节要求进行创作。"
        async for chunk in call_novel_llm_stream(
            prompt, temperature=0.85, max_tokens=2500, system_prompt=system_prompt
        ):
            yield chunk

    @staticmethod
    async def write_chapter(
        chapter_num: int,
        chapter_outline: str,
        characters: str,
        memory: str,
        prev_summaries: str,
        style_guide: str = "",
    ) -> str:
        """非流式写作单个章节"""
        prompt = NovelEngine.build_chapter_prompt(
            chapter_num, chapter_outline, characters, memory, prev_summaries, style_guide
        )
        system_prompt = "你是一位专业的小说作者，请严格按照风格指南和章节要求进行创作。"
        result = await call_novel_llm(
            prompt, temperature=0.85, max_tokens=2500, system_prompt=system_prompt
        )
        return result

    @staticmethod
    async def compress_memory(
        current_memory: str,
        new_chapter_content: str,
        chapter_num: int,
    ) -> str:
        """压缩记忆：保留关键状态，丢弃冗余（返回单章记忆文本）"""
        prompt = f"""你是一位小说记忆管理员。请根据以下章节内容，提取第{chapter_num}章的关键状态记忆。

【新章节摘要（第{chapter_num}章）】
{new_chapter_content[:800]}

请只保留第{chapter_num}章的：
1. 角色当前状态（位置、情绪、关键决策）
2. 未解决的伏笔/悬念
3. 关键剧情进展（不超过5条）
4. 重要物品/技能变化

要求：
- 简洁，不超过300字
- 用条目列出
- 只记录本章新增/变化的信息"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=500)
        return result

    @staticmethod
    async def summarize_chapter(content: str, chapter_num: int) -> str:
        """为章节生成50字摘要（省 Token）"""
        prompt = f"""请为以下小说章节生成一句50字以内的摘要：

第{chapter_num}章内容：
{content[:2000]}

输出格式：第{chapter_num}章：[50字摘要]"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=100)
        return result

    @staticmethod
    def get_prev_summaries(
        chapters: List, current_chapter_num: int, max_prev: int = 3
    ) -> str:
        """获取前N章的摘要（精简版）"""
        summaries = []
        start = max(1, current_chapter_num - max_prev)
        for i in range(start, current_chapter_num):
            if i - 1 < len(chapters) and chapters[i - 1].summary:
                summaries.append(chapters[i - 1].summary)
        return "\n".join(summaries) if summaries else "（开篇，无前文）"

    # ============ 续写：导入TXT解析 ============

    @staticmethod
    def split_chapters(text: str) -> list:
        """将整本小说TXT按章节标记拆分（支持「第X章」「第X回」等）"""
        # 匹配常见的章节标题：第1章、第一章、第1回、Chapter 1 等
        pattern = r'(?m)^\s*第[零一二三四五六七八九十百千\d]+[章回卷节]\s*[^\n]*'
        parts = re.split(pattern, text)
        titles = re.findall(pattern, text)
        chapters = []
        # parts[0] 是第一章前的内容（简介/楔子），跳过
        for i, title in enumerate(titles):
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if content:
                clean_title = title.strip()
                # 提取章节号
                num_match = re.search(r'第([零一二三四五六七八九十百千\d]+)', clean_title)
                chapter_num = i + 1
                if num_match:
                    chapter_num = NovelEngine._cn_to_num(num_match.group(1)) or (i + 1)
                chapters.append({
                    "chapter_num": chapter_num,
                    "title": clean_title,
                    "content": content,
                })
        return chapters

    @staticmethod
    def _cn_to_num(cn: str) -> int:
        """中文数字转阿拉伯数字（简单版）"""
        if cn.isdigit():
            return int(cn)
        digit_map = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
        if len(cn) == 1:
            return digit_map.get(cn, 0)
        # 十X
        if cn.startswith('十'):
            return 10 + digit_map.get(cn[1:], 0)
        # X十
        if cn.endswith('十'):
            return digit_map.get(cn[0], 0) * 10
        # X十Y
        if '十' in cn:
            parts = cn.split('十')
            return digit_map.get(parts[0], 0) * 10 + digit_map.get(parts[1], 0)
        return 0

    @staticmethod
    async def parse_imported_novel(text: str) -> dict:
        """AI解析导入的小说文本：提取角色、生成大纲摘要和初始记忆"""
        chapters = NovelEngine.split_chapters(text)
        if not chapters:
            # 没有章节标记，整篇作为第1章
            chapters = [{"chapter_num": 1, "title": "第1章", "content": text.strip()}]

        # 取前3章完整内容 + 所有章节标题+前100字，让AI全面提取
        sample = "\n\n".join([f"{c['title']}\n{c['content'][:1500]}" for c in chapters[:3]])
        all_chapters_brief = "\n".join([
            f"第{c['chapter_num']}章 {c['title']}：{c['content'][:100]}"
            for c in chapters
        ])

        prompt = f"""请分析以下小说文本，提取关键信息：

【小说前几章详细内容】
{sample[:4000]}

【所有章节标题和开头概览】
{all_chapters_brief[:2500]}

请输出以下内容（用JSON格式）：

1. "characters"：所有出现的主要角色列表（请扫描所有章节，不要遗漏中后期出现的角色），每个角色包含 name、personality、background
2. "outline"：基于已有章节生成的完整大纲（每章一行，格式：第X章：主要事件），覆盖所有章节
3. "description"：一句话简介（不超过100字）
4. "genre"：小说类型（如玄幻/都市/言情等）

只输出JSON，不要其他文字。格式：
{{"characters":[{{"name":"","personality":"","background":""}}],"outline":"","description":"","genre":""}}"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=2500)

        # 尝试解析JSON
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = __import__('json').loads(result[start:end])
            else:
                data = {}
        except Exception:
            data = {}

        # 生成全局记忆
        global_memory = ""
        try:
            global_memory = await NovelEngine.generate_global_memory_from_chapters(chapters)
        except Exception:
            global_memory = ""

        return {
            "chapters": chapters,
            "characters": data.get("characters", []),
            "outline": data.get("outline", ""),
            "description": data.get("description", ""),
            "genre": data.get("genre", ""),
            "global_memory": global_memory,
        }

    @staticmethod
    async def generate_memory_for_chapter(content: str, chapter_num: int) -> str:
        """为导入的章节生成记忆"""
        return await NovelEngine.compress_memory("", content, chapter_num)

    @staticmethod
    async def generate_global_memory_from_chapters(chapters: list) -> str:
        """根据所有章节内容生成全局记忆（世界观、核心矛盾、关键设定）"""
        # 用所有章节的前200字拼成概览，省Token
        overview = "\n\n".join([
            f"第{c['chapter_num']}章 {c.get('title', '')}：{c['content'][:200]}"
            for c in chapters
        ])
        prompt = f"""请分析以下小说各章节概览，提取全局记忆（贯穿整本小说的关键信息）：

{overview[:4000]}

请输出全局记忆，包含：
1. 世界观设定（时代背景、修真体系/科技水平、重要地点）
2. 核心矛盾（主角的最终目标、主要对手、关键冲突）
3. 关键设定（特殊能力、重要物品、核心规则）
4. 主线进度（目前已进行到什么阶段）

用简洁的条目式输出，总长度300字以内。"""

        return await call_novel_llm(prompt, temperature=0.3, max_tokens=500)

    @staticmethod
    async def extract_characters_from_chapters(chapters: list) -> list:
        """深度扫描所有章节，提取所有角色（滑动窗口逐章扫描前500字累计去重）"""
        all_chars = {}
        window_size = 5
        for i in range(0, len(chapters), window_size):
            window = chapters[i:i + window_size]
            overview = "\n".join([
                f"第{c.chapter_num}章 {c.title or ''}：{c.content[:500]}"
                for c in window
            ])
            prompt = f"""请扫描以下小说章节内容，提取所有出现的有名字的角色：

{overview[:4000]}

要求：
1. 提取所有有名字的角色（包括配角、反派、中后期才出现的角色）
2. 每个角色包含 name（姓名）、personality（性格特点）、background（身份背景）
3. 只提取本段内容中出现的角色

只输出JSON数组，不要其他文字：
[{{"name":"","personality":"","background":""}}]"""

            result = await call_novel_llm(prompt, temperature=0.3, max_tokens=2000)
            try:
                start = result.find('[')
                end = result.rfind(']') + 1
                if start >= 0 and end > start:
                    chars = __import__('json').loads(result[start:end])
                    for c in chars:
                        if c.get("name") and c["name"] not in all_chars:
                            all_chars[c["name"]] = c
            except Exception:
                pass

        return list(all_chars.values())

    @staticmethod
    async def generate_outline_from_chapters(chapters: list) -> str:
        """根据已有章节内容重新生成完整大纲"""
        overview = "\n\n".join([
            f"第{c.chapter_num}章 {c.title or ''}：{c.content[:200]}"
            for c in chapters
        ])
        prompt = f"""请根据以下已有章节内容，生成完整的大纲（覆盖所有章节）：

{overview[:4000]}

要求：
1. 每章一行，格式：第X章：主要事件（20-40字概括）
2. 覆盖所有已有章节
3. 最后追加2-3章的后续大纲建议（标注"【后续建议】"）

直接输出大纲，不要其他说明。"""

        return await call_novel_llm(prompt, temperature=0.3, max_tokens=1500)

    # ============ AI修改意见 ============

    @staticmethod
    async def review_chapters(
        chapters_data: list,
        characters: str = "",
        memory: str = "",
        style_guide: str = "",
        outline: str = "",
    ) -> str:
        """扫描选中的章节，提出修改建议（不改写原文）。
        会基于角色设定、记忆、风格指南、大纲进行综合评审。"""
        combined = ""
        for ch in chapters_data:
            combined += f"\n\n=== {ch['title']}（第{ch['chapter_num']}章）===\n{ch['content'][:3000]}\n"

        # 构建上下文段落（只在有内容时添加）
        context_parts = []
        if style_guide:
            context_parts.append(f"【风格指南】\n{style_guide}")
        if characters:
            context_parts.append(f"【角色设定】\n{characters}")
        if outline:
            context_parts.append(f"【大纲】\n{outline[:1500]}")
        if memory:
            context_parts.append(f"【记忆（前文状态/伏笔/剧情进展）】\n{memory[:2000]}")
        context = "\n\n".join(context_parts)

        prompt = f"""你是一位资深小说编辑。请根据以下设定和上下文，审阅章节内容并提出修改建议（只提建议，不要改写原文）。

{context}

【待审阅章节】
{combined[:6000]}

请从以下维度分析并给出具体建议：

1. **剧情节奏**：是否有拖沓或仓促的地方？哪段需要加快/放慢？是否符合大纲走向？
2. **角色塑造（OOC检测）**：对照【角色设定】，角色是否有OOC（人设崩塌）？对话和行为是否符合其性格和背景？指出具体哪个角色哪段OOC。
3. **伏笔与一致性**：对照【记忆】，是否有未回收的伏笔？是否有前后矛盾？角色状态是否与记忆记录的一致？
4. **文笔风格**：对照【风格指南】，描写是否到位？是否有过度堆砌或过于平淡的段落？风格是否统一？
5. **读者体验**：钩子是否吸引人？情绪起伏是否合理？

输出格式：
## 总体评价
[2-3句总体印象]

## 具体问题与建议
1. 第X章 - [问题类型]：[具体描述 + 建议]
2. ...

## 优先修改项
[列出最需要改的3个问题]"""

        result = await call_novel_llm(prompt, temperature=0.4, max_tokens=2000)
        return result

    # ============ 写后审计 + 门禁 + 重写 ============

    # AI腔词汇表（15项），每项含模式、阈值、建议
    AI_TICS = [
        (r"不禁", 2, "「不禁」使用过多，AI典型用语，建议用具体动作替代"),
        (r"竟然", 2, "「竟然」使用过多，惊讶表达单一，建议换用其他方式"),
        (r"一股.*?涌上心头", 1, "「一股XX涌上心头」是AI套路化描写，建议用具体感受替代"),
        (r"——", 3, "破折号使用过多（{count}次），建议减少，用其他标点或断句替代"),
        (r"仿佛", 3, "「仿佛」使用过多（{count}次），比喻句过于密集"),
        (r"心中暗[想道]", 2, "「心中暗想/暗道」使用过多，建议用动作或表情表现内心"),
        (r"嘴角[微微]?[上勾扬]", 1, "「嘴角上扬/勾起」是AI典型表情描写，建议用更具体的微表情"),
        (r"眼中闪过[一二丝]?", 1, "「眼中闪过一丝XX」是AI套路描写，建议用更具体的眼神动作"),
        (r"深吸[一了]?口气", 1, "「深吸一口气」使用过多，建议换用其他情绪表现方式"),
        (r"不由[得自]主", 2, "「不由得/不由自主」使用过多，AI典型用语"),
        (r"一种.*?的感觉", 1, "「一种XX的感觉」是AI模糊描写，建议用具体感官细节替代"),
        (r"\.\.\.", 5, "省略号使用过多（{count}次），建议减少，用破折号或直接断句"),
        (r"这一刻[，,].*?明白了", 1, "「这一刻，他明白了XX」是AI段尾顿悟句，建议避免"),
        (r"某[个种]", 3, "「某个/某种」模糊指代使用过多（{count}次），建议明确指代"),
        (r"不由分说", 1, "「不由分说」是AI常用用语，建议避免"),
    ]

    @staticmethod
    def detect_ai_tics(content: str) -> dict:
        """检测AI腔词汇，返回 {total_count, items: [{pattern, count, suggestion}]}"""
        items = []
        total = 0
        for pattern, threshold, suggestion in NovelEngine.AI_TICS:
            matches = re.findall(pattern, content)
            count = len(matches)
            if count > 0:
                msg = suggestion.format(count=count) if "{count}" in suggestion else suggestion
                items.append({
                    "pattern": pattern,
                    "count": count,
                    "threshold": threshold,
                    "exceeded": count > threshold,
                    "suggestion": msg,
                })
                if count > threshold:
                    total += count
        return {"total_count": total, "items": items}

    @staticmethod
    async def audit_chapter(
        chapter_content: str,
        chapter_num: int,
        chapter_outline: str,
        characters: str,
        memory: str,
        style_guide: str,
        prev_summaries: str,
    ) -> dict:
        """8维度章节质量审计，返回 {score, dimensions, issues, suggestions}。
        分数<70 视为不合格，触发重写。"""
        style = style_guide or DEFAULT_STYLE_GUIDE
        prompt = f"""你是一位严苛的小说质量审计员。请对以下章节进行8维度质量评分。

【风格指南】
{style}

【角色设定】
{characters}

【当前状态/记忆】
{memory}

【前面章节摘要】
{prev_summaries}

【第{chapter_num}章要求】
{chapter_outline}

【待审计章节正文】
{chapter_content[:4000]}

请从以下8个维度评分（每项1-10分，10分最高）：

1. **必需节拍**（Narrative Beats）：本章是否完成了大纲要求的核心事件？
2. **叙事进展**（Story Progress）：剧情是否有实质性推进？是否有拖沓？
3. **角色进展**（Character Progress）：角色是否有成长/变化/新信息揭示？
4. **伏笔进展**（Foreshadowing）：是否合理埋设新伏笔或回收旧伏笔？
5. **设定一致性**（Consistency）：是否与角色设定、记忆、前文保持一致？有无OOC？
6. **文笔节奏**（Prose & Pacing）：文笔是否到位？节奏是否合理？有无AI腔？
7. **结尾钩子**（Ending Hook）：结尾是否有吸引力？是否让人想读下一章？
8. **重复度**（Repetition）：是否与前文大量重复？是否有冗余描写？

只输出JSON，不要其他文字：
{{
  "dimensions": {{"必需节拍": 8, "叙事进展": 7, "角色进展": 6, "伏笔进展": 5, "设定一致性": 9, "文笔节奏": 7, "结尾钩子": 8, "重复度": 8}},
  "issues": ["具体问题1", "具体问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=800)
        try:
            import json as _json
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = _json.loads(result[start:end])
            else:
                data = {"dimensions": {}, "issues": [], "suggestions": []}
        except Exception:
            data = {"dimensions": {}, "issues": [], "suggestions": []}

        # 计算总分（8维度各10分，满分80，换算为100分制）
        dims = data.get("dimensions", {})
        total = sum(dims.values()) if dims else 0
        score = int(total * 100 / 80) if dims else 0

        # AI腔检测（纯文本扫描，不调AI，零成本）
        ai_tics = NovelEngine.detect_ai_tics(chapter_content)
        # 如果AI腔严重（超阈值项>5个），扣减分数
        exceeded_count = sum(1 for item in ai_tics["items"] if item["exceeded"])
        if exceeded_count >= 5:
            score = max(0, score - 15)
        elif exceeded_count >= 3:
            score = max(0, score - 8)

        return {
            "score": score,
            "dimensions": dims,
            "issues": data.get("issues", []),
            "suggestions": data.get("suggestions", []),
            "ai_tics": ai_tics,
        }

    @staticmethod
    async def rewrite_chapter(
        chapter_content: str,
        audit_result: dict,
        chapter_num: int,
        chapter_outline: str,
        characters: str,
        memory: str,
        prev_summaries: str,
        style_guide: str,
    ) -> str:
        """根据审计意见重写章节"""
        style = style_guide or DEFAULT_STYLE_GUIDE
        issues_text = "\n".join([f"- {i}" for i in audit_result.get("issues", [])])
        suggestions_text = "\n".join([f"- {s}" for s in audit_result.get("suggestions", [])])
        dims_text = "\n".join([f"- {k}: {v}/10" for k, v in audit_result.get("dimensions", {}).items()])

        prompt = f"""你是一位专业小说作者。你之前写的章节未通过质量审计，请根据审计意见重写。

【风格指南】
{style}

【角色设定】
{characters}

【当前状态/记忆】
{memory}

【前面章节摘要】
{prev_summaries}

【第{chapter_num}章要求】
{chapter_outline}

【原章节内容（供参考，不要照抄）】
{chapter_content[:3000]}

【审计结果】
维度得分：
{dims_text}

存在的问题：
{issues_text}

改进建议：
{suggestions_text}

请根据以上审计意见重写第{chapter_num}章（约2000字），重点解决上述问题。保留原文好的部分，修正不足。"""

        result = await call_novel_llm(prompt, temperature=0.85, max_tokens=2500,
                                       system_prompt="你是一位专业的小说作者，请严格按照审计意见改进章节。")
        return result

    # ============ 伏笔追踪 ============

    @staticmethod
    async def extract_foreshadowing(content: str, chapter_num: int) -> list:
        """AI扫描章节内容，提取本章埋设的新伏笔"""
        prompt = f"""请分析以下小说章节，提取本章埋设的伏笔（未解之谜、悬念、暗示、未交代的人物/物品/事件）。

【第{chapter_num}章内容】
{content[:3000]}

要求：
1. 只提取本章新埋设的伏笔（不是已回收的）
2. 每个伏笔简洁描述（20-50字）
3. 标注优先级：high（关键伏笔，必须回收）/ medium（重要伏笔）/ low（次要伏笔）

只输出JSON数组，不要其他文字：
[{{"content":"伏笔描述","priority":"medium"}}]

如果没有伏笔，输出空数组 []"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=500)
        try:
            import json as _json
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return _json.loads(result[start:end])
        except Exception:
            pass
        return []

    @staticmethod
    async def check_foreshadowing_resolved(
        content: str, chapter_num: int, pending_foreshadowings: list
    ) -> list:
        """AI检查本章是否回收了某个未回收的伏笔，返回被回收的伏笔ID列表"""
        if not pending_foreshadowings:
            return []

        foreshadow_text = "\n".join([
            f"ID:{f['id']} - {f['content']}"
            for f in pending_foreshadowings
        ])
        prompt = f"""请判断以下章节是否回收（解答/揭晓）了某个之前埋设的伏笔。

【第{chapter_num}章内容】
{content[:3000]}

【未回收的伏笔列表】
{foreshadow_text}

请判断哪些伏笔在本章被回收了。只输出被回收的伏笔ID列表（JSON数组）：
[1, 3, 5]

如果没有回收任何伏笔，输出空数组 []"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=200)
        try:
            import json as _json
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return _json.loads(result[start:end])
        except Exception:
            pass
        return []

    @staticmethod
    def format_pending_foreshadowings(foreshadowings: list) -> str:
        """格式化未回收伏笔列表，用于注入章节写作prompt"""
        if not foreshadowings:
            return "（无未回收伏笔）"
        lines = []
        for f in foreshadowings:
            priority_tag = {"high": "【重要】", "medium": "", "low": "【次要】"}.get(f.priority, "")
            lines.append(f"- 第{f.chapter_planted}章埋设：{priority_tag}{f.content}")
        return "\n".join(lines)

    # ============ 角色状态热更新 ============

    @staticmethod
    async def extract_character_states(content: str, chapter_num: int, character_names: list) -> dict:
        """AI从章节内容中提取每个角色的状态变更，返回 {角色名: {position, power, mood, items, knowledge}}"""
        if not character_names:
            return {}

        chars_str = "、".join(character_names)
        prompt = f"""请分析以下小说章节，提取其中出场角色的当前状态。

【第{chapter_num}章内容】
{content[:3500]}

【需要分析的角色】
{chars_str}

对每个出场角色，提取其当前状态（用简洁短语）：
- position：当前所在位置
- power：实力/战斗状态（如：全盛/受伤/突破中）
- mood：当前心情
- items：持有物品
- knowledge：本章获知的新信息

只输出JSON，不要其他文字：
{{"角色名": {{"position":"位置","power":"状态","mood":"心情","items":"物品","knowledge":"新信息"}}}}

如果某角色未出场，跳过即可。"""

        result = await call_novel_llm(prompt, temperature=0.2, max_tokens=800)
        try:
            import json as _json
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return _json.loads(result[start:end])
        except Exception:
            pass
        return {}

    @staticmethod
    def format_character_states(characters: list) -> str:
        """格式化角色当前状态，用于注入章节写作prompt"""
        if not characters:
            return ""
        lines = []
        for c in characters:
            if c.current_state:
                try:
                    import json as _json
                    state = _json.loads(c.current_state)
                    parts = []
                    if state.get("position"):
                        parts.append(f"位置:{state['position']}")
                    if state.get("power"):
                        parts.append(f"实力:{state['power']}")
                    if state.get("mood"):
                        parts.append(f"心情:{state['mood']}")
                    if state.get("items"):
                        parts.append(f"持有:{state['items']}")
                    if state.get("knowledge"):
                        parts.append(f"已知:{state['knowledge']}")
                    if parts:
                        lines.append(f"- {c.name}：{'，'.join(parts)}")
                except Exception:
                    lines.append(f"- {c.name}：（状态解析失败）")
            else:
                lines.append(f"- {c.name}：（暂无状态记录）")
        return "\n".join(lines)

    # ============ 时间线管理 ============

    @staticmethod
    async def extract_timeline_events(content: str, chapter_num: int) -> list:
        """AI从章节内容提取重大事件，返回 [{event, time_label}]"""
        prompt = f"""请分析以下小说章节，提取本章的重大事件（关键剧情转折点、重要决定、关系变化等）。

【第{chapter_num}章内容】
{content[:3500]}

要求：
1. 只提取重大事件，不要琐碎细节
2. 每个事件简洁描述（20-80字）
3. 标注相对时间（如"当夜"、"次日清晨"、"三天后"，如果无法判断则留空）

只输出JSON数组：
[{{"event":"事件描述","time_label":"时间标记"}}]

如果没有重大事件，输出空数组 []"""

        result = await call_novel_llm(prompt, temperature=0.2, max_tokens=500)
        try:
            import json as _json
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return _json.loads(result[start:end])
        except Exception:
            pass
        return []

    @staticmethod
    def format_recent_timelines(timelines: list, max_chapters: int = 5) -> str:
        """格式化最近N章的时间线，用于注入写作prompt"""
        if not timelines:
            return ""
        recent = [t for t in timelines if t.chapter_num >= (max(t.chapter_num for t in timelines) - max_chapters + 1)]
        if not recent:
            return ""
        lines = []
        for t in sorted(recent, key=lambda x: (x.chapter_num, x.id)):
            time_part = f"（{t.time_label}）" if t.time_label else ""
            lines.append(f"- 第{t.chapter_num}章{time_part}：{t.event}")
        return "\n".join(lines)

    # ============ 上下文分层组装 ============

    @staticmethod
    def assemble_context(
        chapter_num: int,
        chapter_outline: str,
        characters: list,
        character_states: str,
        foreshadowings: str,
        timelines: str,
        prev_chapters: list,
        global_memory: str,
        chapter_memories: list,
        max_tokens: int = 6000,
    ) -> str:
        """
        按优先级组装上下文，超token时按优先级截断。

        优先级：
        [必选] P0: 章节大纲 + 角色状态 + 未回收伏笔 + 最近3章详细内容
        [重要] P1: 全局记忆 + 主要角色设定 + 时间线
        [可选] P2: 更早章节摘要
        """
        segments = []

        # P0 - 必选
        if chapter_outline:
            segments.append(("P0", f"【本章大纲】\n{chapter_outline}"))
        if character_states:
            segments.append(("P0", f"【角色当前状态】\n{character_states}"))
        if foreshadowings:
            segments.append(("P0", f"【未回收伏笔】\n{foreshadowings}"))

        # 最近3章详细内容
        recent_chapters = [ch for ch in prev_chapters if ch.chapter_num >= chapter_num - 3]
        for ch in recent_chapters:
            content = ch.content or ch.summary or ""
            if content:
                segments.append(("P0", f"【第{ch.chapter_num}章】\n{content[:800]}"))

        # P1 - 重要
        if global_memory:
            segments.append(("P1", f"【全局记忆】\n{global_memory}"))
        if characters:
            chars_text = "\n".join([f"- {c.name}：{c.personality or ''}" for c in characters])
            segments.append(("P1", f"【角色设定】\n{chars_text}"))
        if timelines:
            segments.append(("P1", f"【时间线】\n{timelines}"))

        # 章节记忆摘要
        for m in chapter_memories:
            if m.get("chapter_num") and m["chapter_num"] < chapter_num - 3:
                segments.append(("P2", f"【第{m['chapter_num']}章记忆】{m.get('content', '')}"))

        # 按优先级拼接，估算token并截断
        assembled = []
        current_tokens = 0
        for priority, text in segments:
            est_tokens = len(text) // 2  # 中文约2字符=1token
            if current_tokens + est_tokens > max_tokens and priority == "P2":
                continue
            assembled.append(text)
            current_tokens += est_tokens

        return "\n\n".join(assembled)

    @staticmethod
    def format_chapter_memories(memories: list) -> list:
        """格式化章节记忆列表"""
        result = []
        for m in memories:
            result.append({
                "chapter_num": m.chapter_num,
                "content": m.content,
            })
        return result

    # ============ 文风学习 ============

    @staticmethod
    async def analyze_style(reference_text: str) -> dict:
        """分析参考文本，提取文风统计指纹"""
        prompt = f"""请分析以下小说文本的文风特征，提取具体统计数据：

【参考文本】
{reference_text[:4000]}

请分析以下维度，输出JSON：
{{
  "avg_sentence_length": 平均句长（字数）,
  "sentence_type_ratio": "{{\"短句\":比例,\"长句\":比例}}",
  "punctuation_usage": "标点使用频率（如：逗号多/句号多/感叹号多）",
  "vocabulary_features": "用词特征（如：口语化/书面化/古风/现代）",
  "rhythm": "节奏特征（如：快节奏/慢节奏/长短句交替）",
  "narrative_pov": "叙事视角（第一人称/第三人称限制/全知）",
  "description_style": "描写风格（如：白描/细腻/夸张/含蓄）",
  "style_guide": "可操作的写作指南（5-10条具体规则）"
}}"""

        result = await call_novel_llm(prompt, temperature=0.2, max_tokens=1000)
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                return __import__('json').loads(result[start:end])
        except Exception:
            pass
        return {"style_guide": "", "raw": result}

    @staticmethod
    def format_style_guide(style_data: dict) -> str:
        """将文风分析结果格式化为写作指南"""
        if not style_data:
            return ""
        lines = []
        if style_data.get("style_guide"):
            lines.append(style_data["style_guide"])
        if style_data.get("avg_sentence_length"):
            lines.append(f"平均句长约{style_data['avg_sentence_length']}字")
        if style_data.get("vocabulary_features"):
            lines.append(f"用词风格：{style_data['vocabulary_features']}")
        if style_data.get("rhythm"):
            lines.append(f"节奏：{style_data['rhythm']}")
        if style_data.get("description_style"):
            lines.append(f"描写风格：{style_data['description_style']}")
        return "\n".join(lines) if lines else ""

    # ============ 分卷规划 ============

    @staticmethod
    async def plan_volumes(novel_title: str, genre: str, description: str, total_chapters: int, num_volumes: int = 3) -> list:
        """AI生成分卷规划"""
        prompt = f"""请为以下小说制定分卷规划：

【小说标题】{novel_title}
【类型】{genre}
【简介】{description}
【预计总章数】{total_chapters}
【分卷数】{num_volumes}

要求：
1. 每卷有明确的主题和核心冲突
2. 标注每卷的起止章节
3. 标注每卷的情绪基调（如：热血/压抑/轻松/悲壮）
4. 标注每卷的高潮章节

只输出JSON数组：
[{{"volume": 1, "title": "", "start_chapter": 1, "end_chapter": 30, "theme": "", "emotion": "", "climax_chapter": 25, "summary": ""}}]"""

        result = await call_novel_llm(prompt, temperature=0.4, max_tokens=1000)
        try:
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return __import__('json').loads(result[start:end])
        except Exception:
            pass
        return []

    @staticmethod
    def format_volume_plan(volumes: list) -> str:
        """格式化分卷规划"""
        if not volumes:
            return ""
        lines = []
        for v in volumes:
            lines.append(f"第{v['volume']}卷：{v.get('title', '')}")
            lines.append(f"  章节：第{v['start_chapter']}-{v['end_chapter']}章")
            lines.append(f"  主题：{v.get('theme', '')}")
            lines.append(f"  情绪基调：{v.get('emotion', '')}")
            lines.append(f"  高潮章节：第{v.get('climax_chapter', '')}章")
            if v.get('summary'):
                lines.append(f"  概要：{v['summary']}")
            lines.append("")
        return "\n".join(lines)

    # ============ 情绪曲线 ============

    @staticmethod
    async def analyze_emotion_curve(chapters: list) -> list:
        """分析各章节情绪强度，生成情绪曲线数据"""
        if not chapters:
            return []

        # 批量分析，每次5章
        results = []
        batch_size = 5
        for i in range(0, len(chapters), batch_size):
            batch = chapters[i:i + batch_size]
            ch_info = "\n".join([f"第{c.chapter_num}章 {c.title or ''}：{(c.content or '')[:300]}" for c in batch])

            prompt = f"""请分析以下章节的情绪强度，输出0-10的分数（0=极度悲伤/压抑，5=平静，10=极度兴奋/热血）：

{ch_info}

只输出JSON数组：
[{{"chapter_num": 1, "emotion_score": 7.5, "emotion_label": "紧张"}}]"""

            result = await call_novel_llm(prompt, temperature=0.2, max_tokens=500)
            try:
                start = result.find('[')
                end = result.rfind(']') + 1
                if start >= 0 and end > start:
                    data = __import__('json').loads(result[start:end])
                    results.extend(data)
            except Exception:
                pass

        return sorted(results, key=lambda x: x.get("chapter_num", 0))
