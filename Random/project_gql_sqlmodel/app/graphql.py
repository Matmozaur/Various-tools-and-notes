from ariadne import QueryType, MutationType, make_executable_schema, gql
from ariadne.asgi import GraphQL
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Book
from app.database import async_session


# Define type definitions (schema)
type_defs = gql("""
    type Book {
        id: ID!
        title: String!
        author: String!
    }

    type Query {
        books: [Book]!
        book(id: ID!): Book
    }

    type Mutation {
        createBook(title: String!, author: String!): Book
    }
""")

# Resolvers
query = QueryType()
mutation = MutationType()

# Resolver to get list of books
@query.field("books")
async def resolve_books(_, info):
    session: AsyncSession = info.context["session"]
    result = await session.execute(select(Book))
    return result.scalars().all()

# Resolver to get a single book by ID
@query.field("book")
async def resolve_book(_, info, id):
    session: AsyncSession = info.context["session"]
    result = await session.execute(select(Book).where(Book.id == id))
    return result.scalar_one_or_none()

# Resolver to create a new book
@mutation.field("createBook")
async def resolve_create_book(_, info, title, author):
    session: AsyncSession = info.context["session"]
    book = Book(title=title, author=author)
    session.add(book)
    await session.commit()
    return book

# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)

async def context_value(request):
    async with async_session() as session:
        return {"session": session}


# Create GraphQL app
graphql_app = GraphQL(schema, context_value=context_value)
