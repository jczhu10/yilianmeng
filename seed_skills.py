"""技能分类与技能数据初始化脚本。
幂等执行：重复运行不会产生重复数据。
用法: python seed_skills.py
"""
from app import app, db
from app.models import SkillCategory, Skill

# 技能数据：分类 -> 子技能列表
SKILL_DATA = [
    {
        'name': '文字创作',
        'code': 'writing',
        'skills': ['小说创作', '剧本创作', '文案策划', '诗词散文', '新闻稿']
    },
    {
        'name': '视觉创作',
        'code': 'visual',
        'skills': ['平面设计', '插画', 'UI设计', '漫画', '摄影', '原画']
    },
    {
        'name': '影像类',
        'code': 'video',
        'skills': ['视频剪辑', '视频拍摄', '动画制作', '后期特效', '调色']
    },
    {
        'name': '配音',
        'code': 'voice',
        'skills': ['中文配音', '英文配音', '日语配音', '方言配音', '唱歌配音']
    },
]


def seed():
    with app.app_context():
        if SkillCategory.query.count() > 0:
            print(f'技能分类已存在 {SkillCategory.query.count()} 条，跳过初始化。')
            return

        for order, cat in enumerate(SKILL_DATA):
            category = SkillCategory(
                name=cat['name'],
                code=cat['code'],
                sort_order=order
            )
            db.session.add(category)
            db.session.flush()  # 拿到 category.id

            for s_order, skill_name in enumerate(cat['skills']):
                db.session.add(Skill(
                    category_id=category.id,
                    name=skill_name,
                    sort_order=s_order
                ))

        db.session.commit()
        print(f'初始化完成：{len(SKILL_DATA)} 个分类，'
              f'{sum(len(c["skills"]) for c in SKILL_DATA)} 个技能。')


if __name__ == '__main__':
    seed()
