"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""

from ellar.common import Body, Controller, ControllerBase, get, post
from pydantic import EmailStr
from sqlalchemy import select

from .models.users import User


@Controller
class DbController(ControllerBase):
    @get("/")
    def index(self):
        return {"detail": "Welcome Db Resource"}

    @post("/users")
    def create_user(self, username: Body[str], email: Body[EmailStr]):
        session = User.get_db_session()
        user = User(username=username, email=email)

        session.add(user)
        session.commit()

        return user.dict()

    @get("/users/{user_id:int}")
    def get_user_by_id(self, user_id: int):
        session = User.get_db_session()
        stmt = select(User).filter(User.id == user_id)
        user = session.execute(stmt).scalar()
        return user.dict()

    @get("/users")
    async def get_all_users(self):
        session = User.get_db_session()
        stmt = select(User)
        rows = session.execute(stmt.offset(0).limit(100)).scalars()
        return [row.dict() for row in rows]
