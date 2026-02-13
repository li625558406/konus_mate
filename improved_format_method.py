# 改进的格式化方法（支持时间实体提取）
async def format_memories_with_entities(self, memories: List[ConversationMemory]) -> str:
    """
    格式化记忆列表为prompt文本（包含时间实体信息）

    Args:
        memories: 记忆列表

    Returns:
        格式化后的文本
    """
    if not memories:
        return ""

    formatted = []
    for memory in memories:
        # 解析 entities（如果存在）
        entities_info = ""
        try:
            import json
            if memory.entities:
                entities = json.loads(memory.entities)

                # 按类型优先级显示实体信息
                if "dates" in entities and entities["dates"]:
                    entities_info += "\\n时间："
                    for date in entities["dates"]:
                        entities_info += f"  - {date}"
                if "locations" in entities and entities["locations"]:
                    entities_info += "\\n地点："
                    for loc in entities["locations"]:
                        entities_info += f"  - {loc}"
                if "people" in entities and entities["people"]:
                    entities_info += "\\n人物："
                    for person in entities["people"]:
                        entities_info += f"  - {person}"
                if "events" in entities and entities["events"]:
                    entities_info += "\\n事件："
                    for event in entities["events"]:
                        entities_info += f"  - {event}"
        except:
                pass

        formatted.append(
            f"{memory.summary}{entities_info}"
        )

    return "\\n---\\n".join(formatted)


# 在 ChatService 中添加使用
# async def _format_memories_for_prompt_improved(self, memories: List[ConversationMemory]) -> str:
#     # 改进的格式化方法
#     ...
