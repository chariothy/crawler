from sqlalchemy import orm, Column, String, DATE, INTEGER, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import insert, JSONB

Base = orm.declarative_base()

class Movie(Base):
    __tablename__ ='movie'
    __table_args__ = {'comment': '电影'}
    
    id = Column(INTEGER, primary_key=True, comment='ID')
    title_en = Column(String(1000), nullable=False, comment='英文标题')
    title_cn = Column(String(1000), nullable=False, comment='中文标题')
    desc = Column(Text, comment='内容简介')
    imdb = Column(Float, comment='IMDB分数')
    douban = Column(Float, comment='豆瓣分数')
    link = Column(String(200), nullable=False, comment='电影链接')
    full_link = Column(String(1000), comment='完整链接')
    country = Column(String(30), comment='国家')
    category = Column(String(20), comment='类别')
    show_date = Column(DATE, comment='上映日期')
    seen = Column(Boolean, default=False, comment='标志已看')
    created_at = Column(DATE, comment='更新日期')