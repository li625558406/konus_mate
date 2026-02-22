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
from app.models import SystemInstruction, User, ConversationMemory, UserCustomPrompt, CharacterEmotionState


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
        # 检查 admin 用户是否已存在
        existing_admin = session.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("⚠ Admin user already exists, skipping test data insertion...")
            print("  If you want to re-insert test data, please delete existing users first.")
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

        session.commit()
        print(f"✓ Inserted {len(instructions)} system instructions")

        # ========== 插入 User Custom Prompts ==========
        # 为 admin 用户 (id=1) 添加自定义 prompt
        custom_prompts = [
            # admin 用户对"通用助手"的自定义 prompt
            UserCustomPrompt(
                user_id=1,
                system_instruction_id=1,
                name="管理员专业模式",
                description="管理员专用的专业回复模式",
                content="""你正在与管理员用户对话。请特别注意：
1. 使用更专业、更技术化的语言
2. 优先提供系统层面的解决方案
3. 在回答问题时，考虑到用户具有技术背景
4. 可以直接提供代码示例和技术建议
5. 保持高效、精准的沟通风格""",
                is_active=True,
                sort_order=1
            ),
            # admin 用户对"编程专家"的自定义 prompt
            UserCustomPrompt(
                user_id=1,
                system_instruction_id=2,
                name="资深架构师模式",
                description="架构师级别的技术咨询",
                content="""你是一位资深软件架构师，为管理员提供技术咨询。请特别注意：
1. 从架构层面思考问题，考虑可扩展性、可维护性
2. 推荐业界最佳实践和设计模式
3. 关注代码质量和性能优化
4. 提供完整的解决方案，包括代码结构、测试策略
5. 可以深入讨论底层原理和实现细节""",
                is_active=True,
                sort_order=1
            ),
            # testuser 用户 (id=2) 对"通用助手"的自定义 prompt
            UserCustomPrompt(
                user_id=2,
                system_instruction_id=1,
                name="友好助手模式",
                description="更加友好、轻松的对话风格",
                content="""你是一位友好的 AI 助手，正在为测试用户服务。请特别注意：
1. 使用亲切、易懂的语言
2. 避免过于专业的术语，必要时提供解释
3. 保持耐心和鼓励的态度
4. 提供实用的建议和帮助
5. 让对话氛围轻松愉快""",
                is_active=True,
                sort_order=1
            ),
            # testuser 用户对"创意写作助手"的自定义 prompt
            UserCustomPrompt(
                user_id=2,
                system_instruction_id=3,
                name="中文写作专家",
                description="专注于中文创意写作",
                content="""你是一位专业的中文写作专家，擅长各类中文创作。请特别注意：
1. 深入理解中文表达的美感和韵律
2. 掌握各种中文文体（古文、现代散文、诗歌、小说等）
3. 注重修辞手法和文字的意境
4. 提供有创意、有深度的写作建议
5. 鼓励用户发挥想象力和创造力""",
                is_active=True,
                sort_order=1
            ),
        ]

        for custom_prompt in custom_prompts:
            session.add(custom_prompt)

        session.commit()
        print(f"✓ Inserted {len(custom_prompts)} user custom prompts")
        print("  - admin user: 2 custom prompts (通用助手、编程专家)")
        print("  - testuser: 2 custom prompts (通用助手、创意写作助手)")

        print("\n" + "="*50)
        print("初始化完成！测试数据已成功插入。")
        print("="*50)
        print("\n测试账号:")
        print("  1. admin / Test123456 (管理员账户)")
        print("  2. testuser / Test123456 (普通用户)")
        print("\n默认配置:")
        print(f"  - 默认 System Instruction: 通用助手 (ID: 1)")
        print("\n你可以通过以下 API 查看和管理:")
        print(f"  - API 文档: http://localhost:8000/docs")
        print(f"  - 用户认证: /api/v1/auth/*")
        print(f"  - System Instructions: /api/v1/system-instructions")

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
