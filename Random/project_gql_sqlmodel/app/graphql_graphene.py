import graphene
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models import Book

# Define GraphQL types
class BookType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    author = graphene.String()

# Queries
class Query(graphene.ObjectType):
    books = graphene.List(BookType)
    book = graphene.Field(BookType, id=graphene.ID(required=True))

    async def resolve_books(self, info):
        session: AsyncSession = info.context["session"]
        result = await session.execute(select(Book))
        return result.scalars().all()

    async def resolve_book(self, info, id):
        session: AsyncSession = info.context["session"]
        result = await session.execute(select(Book).where(Book.id == id))
        return result.scalar_one_or_none()

# Mutations
class CreateBook(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        author = graphene.String(required=True)

    book = graphene.Field(BookType)

    async def mutate(self, info, title, author):
        session: AsyncSession = info.context["session"]
        book = Book(title=title, author=author)
        session.add(book)
        await session.commit()
        return CreateBook(book=book)

class Mutation(graphene.ObjectType):
    create_book = CreateBook.Field()

# Create executable schema
schema = graphene.Schema(query=Query, mutation=Mutation)

# Define the context function for database session
async def context_value(request):
    async with async_session() as session:
        return {"session": session}

# GraphQL app configuration
from starlette_graphene3 import GraphQLApp

graphql_app = GraphQLApp(schema=schema, context_value=context_value)