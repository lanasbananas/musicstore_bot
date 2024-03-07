from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, select, update

Base = declarative_base()
engine = create_async_engine('mysql+aiomysql://user:password@localhost/db')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    userid = Column(String(50), default='0')
    user_name = Column(String(50), default='-')


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_user(userid, user_name):
    async with async_session() as session:
        async with session.begin():
            user = Users(userid=userid, user_name=user_name)
            session.add(user)
            await session.commit()


async def get_id_on_userid(userid):
    async with async_session() as session:
        return (await session.execute(select(Users.id).where(Users.userid == userid))).scalars().all()



