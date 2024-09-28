from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import Book

async def create_book(db: AsyncSession, book: Book):
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book

async def get_books(db: AsyncSession):
    result = await db.execute(select(Book))
    return result.scalars().all()

async def get_book(db: AsyncSession, book_id: int):
    result = await db.execute(select(Book).where(Book.id == book_id))
    return result.scalar_one_or_none()

async def update_book(db: AsyncSession, book_id: int, book_data: Book):
    book = await get_book(db, book_id)
    if book:
        book.title = book_data.title
        book.author = book_data.author
        await db.commit()
        await db.refresh(book)
    return book

async def delete_book(db: AsyncSession, book_id: int):
    book = await get_book(db, book_id)
    if book:
        await db.delete(book)
        await db.commit()
    return book
