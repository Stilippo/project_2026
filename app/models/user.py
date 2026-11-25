from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    username: str
    name: str
    email: str


class User(UserBase, table=True):
    username: str = Field(primary_key=True)


class UserCreate(UserBase):
    pass
