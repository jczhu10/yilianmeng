"""初始化风格词汇字典数据：20 个预置风格词"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app.models.style_tags import StyleTag

STYLE_TAGS = [
    ("写实风", "真实还原事物样貌", 1),
    ("国潮风", "中国传统文化+潮流元素", 2),
    ("二次元", "日系动漫/漫画风格", 3),
    ("极简风", "简洁干净，留白为主", 4),
    ("赛博朋克", "霓虹科技感、未来主义", 5),
    ("水墨风", "中国传统水墨画风格", 6),
    ("油画风", "西方油画质感、厚重笔触", 7),
    ("插画风", "手绘插画、扁平卡通", 8),
    ("科幻风", "太空、机甲、未来科技", 9),
    ("复古风", "年代感、怀旧色调", 10),
    ("治愈系", "温暖柔和、心灵治愈", 11),
    ("暗黑系", "冷色调、哥特、神秘", 12),
    ("萌系", "Q版、可爱、低龄向", 13),
    ("森系", "自然清新、植物元素", 14),
    ("蒸汽波", "复古未来、粉紫霓虹", 15),
    ("扁平风", "几何色块、无渐变阴影", 16),
    ("3D立体", "三维建模渲染风格", 17),
    ("像素风", "8-bit 复古像素画", 18),
    ("哥特风", "华丽黑暗、宗教建筑元素", 19),
    ("低多边形", "Low Poly 几何多边形", 20),
]


def main():
    with app.app_context():
        existing = StyleTag.query.count()
        if existing > 0:
            print(f"风格词汇已存在 {existing} 条，跳过初始化。")
            return

        for name, desc, order in STYLE_TAGS:
            db.session.add(StyleTag(name=name, description=desc, sort_order=order))

        db.session.commit()
        print(f"成功初始化 {len(STYLE_TAGS)} 条风格词汇。")


if __name__ == "__main__":
    main()
