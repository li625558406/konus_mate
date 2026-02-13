# -*- coding: utf-8 -*-
"""
记忆垃圾回收脚本（简化版 - 不归档，只软删除）
每天凌晨3点运行，清理旧记忆
"""
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings


def daily_memory_cleanup():
    """每日记忆垃圾回收（简化版）"""
    print("=" * 70)
    print("记忆垃圾回收：清理旧记忆（不归档）")
    print("=" * 70)

    # 创建同步引擎
    sync_engine = create_engine(settings.sync_database_url)

    try:
        with sync_engine.connect() as conn:
            current_time = int(time.time())
            seconds_per_day = 86400

            # ========== 1. 查询所有非永久记忆 ==========
            print(f"\n[步骤 1] 查找需要检查的记忆...")
            print(f"当前时间戳：{current_time} ({time.ctime(current_time)})")

            # 查询所有 event 和 desire 类型的记忆
            result = conn.execute(text("""
                SELECT
                        id,
                        memory_category,
                        created_at_timestamp,
                        last_accessed,
                        access_count,
                        emotional_weight,
                        summary
                    FROM conversation_memories
                    WHERE memory_category IN ('event', 'desire')
                    AND is_deleted = false
                    ORDER BY created_at_timestamp DESC
                """))

            memories = result.fetchall()
            print(f"  找到 {len(memories)} 条非永久记忆")

            if not memories:
                print("  没有需要处理的记忆")
                return

            # ========== 2. 判断清理规则 ==========
            ids_to_delete = []

            for mem in memories:
                mem_id = mem[0]
                mem_category = mem[1]
                created_at = mem[2] or current_time
                last_accessed = mem[3] or created_at
                access_count = mem[4] or 1
                emotional_weight = mem[5] or 0.5
                summary = mem[6][:50]

                # 计算未访问天数
                days_since_access = (current_time - last_accessed) / seconds_per_day

                # ========== 清理规则（统一） ==========

                # 规则1：短期垃圾（event/desire，7天未访问+情绪低）
                if (mem_category in ['event', 'desire'] and
                    days_since_access > 7 and
                    emotional_weight < 0.5):
                    ids_to_delete.append(mem_id)
                    print(f"  [DELETE] ID={mem_id}: {days_since_access:.1f}天未访问, 情绪={emotional_weight:.2f} - {summary}")
                    continue

                # 规则2：冷数据清理（所有类型，30天未访问+访问少）
                if days_since_access > 30 and access_count < 3:
                    ids_to_delete.append(mem_id)
                    print(f"  [DELETE] ID={mem_id}: {days_since_access:.1f}天未访问, 访问{access_count}次 - {summary}")
                    continue

            # ========== 3. 执行批量删除 ==========
            print(f"\n[步骤 2] 执行清理...")
            if ids_to_delete:
                # 硬删除（彻底从数据库删除）
                placeholders = ', '.join([':s'] * len(ids_to_delete))
                conn.execute(text(f"""
                    DELETE FROM conversation_memories
                    WHERE id IN ({placeholders})
                """), ids_to_delete)
                conn.commit()
                print(f"  ✓ 已删除 {len(ids_to_delete)} 条记忆")
            else:
                print("  没有需要删除的记忆")

            # ========== 4. 统计 ==========
            total_processed = len(ids_to_delete)
            print("\n" + "=" * 70)
            print(f"垃圾回收完成！共处理 {total_processed} 条记忆")
            print("=" * 70)

    except Exception as e:
        print(f"\n[错误] 垃圾回收失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    daily_memory_cleanup()
