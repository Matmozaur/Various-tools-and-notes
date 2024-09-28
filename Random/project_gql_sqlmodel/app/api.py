from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Book
from app.crud import create_book, get_books, get_book, update_book, delete_book

router = APIRouter()

@router.post("/books/", response_model=Book)
async def create_new_book(book: Book, db: AsyncSession = Depends(get_session)):
    return await create_book(db, book)

@router.get("/books/", response_model=list[Book])
async def read_books(db: AsyncSession = Depends(get_session)):
    return await get_books(db)

@router.get("/books/{book_id}", response_model=Book)
async def read_book(book_id: int, db: AsyncSession = Depends(get_session)):
    book = await get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/books/{book_id}", response_model=Book)
async def update_existing_book(book_id: int, book: Book, db: AsyncSession = Depends(get_session)):
    return await update_book(db, book_id, book)

@router.delete("/books/{book_id}", response_model=Book)
async def delete_existing_book(book_id: int, db: AsyncSession = Depends(get_session)):
    return await delete_book(db, book_id)
