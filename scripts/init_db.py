"""
数据库初始化脚本
创建表结构并插入测试数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import SystemInstruction, Prompt, User


# 创建同步引擎用于初始化脚本
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sync_engine = create_engine(settings.sync_database_url)


def init_database():
    """初始化数据库表结构"""
    from app.db.session import Base
    Base.metadata.create_all(sync_engine)
    print("✓ Database tables created successfully")


def insert_test_data():
    """插入测试数据"""
    session = Session(sync_engine)

    try:
        # 检查是否已有数据
        existing_instruction = session.query(User).first()
        if existing_instruction:
            print("⚠ Test data already exists, skipping insertion...")
            return

        # ========== 插入测试用户 ==========
        test_users = [
            User(
                username="admin",
                email="admin@konus.com",
                full_name="系统管理员",
                is_active=True,
                is_superuser=True,
                is_verified=True,
            ),
            User(
                username="testuser",
                email="test@konus.com",
                full_name="测试用户",
                is_active=True,
                is_superuser=False,
                is_verified=True,
            ),
        ]

        # 设置测试用户密码（统一为: Test123456）
        for user in test_users:
            user.set_password("Test123456")
            session.add(user)

        session.flush()
        print(f"✓ Inserted {len(test_users)} test users")
        print("  - admin / Test123456 (管理员)")
        print("  - testuser / Test123456 (普通用户)")

        # ========== 插入 System Instructions ==========
        instructions = [
            SystemInstruction(
                name="通用助手",
                description="默认的通用 AI 助手",
                content="""你是一个智能、友好、乐于助人的 AI 助手。你的职责是：

1. 理解用户的问题并提供准确、有帮助的回答
2. 使用清晰、简洁的语言进行交流
3. 如果不确定答案，诚实地告知用户
4. 保持专业和礼貌的态度
5. 可以访问互联网获取最新信息来辅助回答

请始终以用户的需求为先，提供高质量的回复。""",
                is_active=True,
                is_default=True,
                sort_order=1
            ),
            SystemInstruction(
                name="编程专家",
                description="专注于编程和开发的技术助手",
                content="""你是一个资深的编程专家和技术顾问。你的专长包括：

1. 多种编程语言（Python, JavaScript, Java, Go, Rust 等）
2. 软件架构设计
3. 算法与数据结构
4. 最佳实践和设计模式
5. 调试和性能优化

提供准确的技术建议，必要时可以搜索最新的技术文档和最佳实践。""",
                is_active=True,
                is_default=False,
                sort_order=2
            ),
            SystemInstruction(
                name="创意写作助手",
                description="帮助用户进行创意写作",
                content="""你是一位富有创意的写作助手，擅长：

1. 帮助用户构思创意
2. 改进和优化文本
3. 提供写作建议
4. 协助各种文体创作
5. 激发创作灵感

你的语言生动有趣，能够启发用户的创作灵感。""",
                is_active=True,
                is_default=False,
                sort_order=3
            ),
        ]

        for instruction in instructions:
            session.add(instruction)

        session.flush()
        print(f"✓ Inserted {len(instructions)} system instructions")

        # ========== 插入 Prompts ==========
        prompts = [
            Prompt(
                name="默认对话",
                description="默认的对话前缀提示",
                content="""请用自然、友好的语气回答用户的问题。""",
                category="通用",
                tags="对话,友好,默认",
                is_active=True,
                is_default=True,
                sort_order=1
            ),
            Prompt(
                name="简洁专业",
                description="简洁专业的回答风格",
                content="""请用简洁、专业的语言回答，直接给出核心信息，避免冗余。""",
                category="风格",
                tags="简洁,专业,高效",
                is_active=True,
                is_default=False,
                sort_order=2
            ),
            Prompt(
                name="详细解释",
                description="提供详细深入的解答",
                content="""请提供详细、深入的解答，包括背景信息、原因分析和相关示例。""",
                category="风格",
                tags="详细,深入,教学",
                is_active=True,
                is_default=False,
                sort_order=3
            ),
            Prompt(
                name="代码审查",
                description="代码审查和分析",
                content="""在分析代码时，请关注：
1. 代码逻辑和正确性
2. 潜在的 bug 和边界情况
3. 性能优化建议
4. 代码风格和可读性
5. 安全性考虑

请给出具体的改进建议。""",
                category="编程",
                tags="代码,审查,优化",
                is_active=True,
                is_default=False,
                sort_order=4
            ),
            Prompt(
                name="头脑风暴",
                description="激发创意和灵感",
                content="""让我们进行头脑风暴！请：
1. 提供多样化的想法和角度
2. 鼓励创新思维
3. 不要过早否定任何想法
4. 帮助扩展和深化思路
5. 连接不同的概念和领域

尽情发挥创造力！""",
                category="创意",
                tags="头脑风暴,创意,灵感",
                is_active=True,
                is_default=False,
                sort_order=5
            ),
        ]

        for prompt in prompts:
            session.add(prompt)

        session.commit()
        print(f"✓ Inserted {len(prompts)} prompts")

        print("\n" + "="*50)
        print("初始化完成！测试数据已成功插入。")
        print("="*50)
        print("\n测试账号:")
        print("  1. admin / Test123456 (管理员账户)")
        print("  2. testuser / Test123456 (普通用户)")
        print("\n默认配置:")
        print(f"  - 默认 System Instruction: 通用助手 (ID: 1)")
        print(f"  - 默认 Prompt: 默认对话 (ID: 1)")
        print("\n你可以通过以下 API 查看和管理:")
        print(f"  - API 文档: http://localhost:8000/docs")
        print(f"  - 用户认证: /api/v1/auth/*")
        print(f"  - System Instructions: /api/v1/system-instructions")
        print(f"  - Prompts: /api/v1/prompts")

    except Exception as e:
        session.rollback()
        print(f"✗ Error inserting test data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("="*50)
    print("Konus Mate - Database Initialization")
    print("="*50)
    print(f"\nDatabase: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print()

    # 创建表结构
    init_database()

    # 插入测试数据
    insert_test_data()

    print("\n✓ Database initialization completed!")
