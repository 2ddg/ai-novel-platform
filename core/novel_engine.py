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
        """深度扫描所有章节，提取所有角色（补充中后期出现的角色）"""
        # 每章取前300字，拼成概览
        overview = "\n\n".join([
            f"第{c.chapter_num}章 {c.title or ''}：{c.content[:300]}"
            for c in chapters
        ])
        prompt = f"""请扫描以下小说各章节内容，提取所有出现的有名字的角色：

{overview[:5000]}

要求：
1. 提取所有有名字的角色（包括配角、反派、中后期才出现的角色）
2. 每个角色包含 name（姓名）、personality（性格特点）、background（身份背景）

只输出JSON数组，不要其他文字：
[{{"name":"","personality":"","background":""}}]"""

        result = await call_novel_llm(prompt, temperature=0.3, max_tokens=2000)
        try:
            start = result.find('[')
            end = result.rfind(']') + 1
            if start >= 0 and end > start:
                return __import__('json').loads(result[start:end])
        except Exception:
            pass
        return []

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
