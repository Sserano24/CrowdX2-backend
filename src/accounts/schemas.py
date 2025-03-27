from ninja import Schema

class UserCreateSchema(Schema):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str

class UserCreatedResponse(Schema):
    message: str
