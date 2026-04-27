from __future__ import annotations


class LibrarrError(Exception):
    pass


class BookNotFoundError(LibrarrError):
    def __init__(self, book_id: str) -> None:
        self.book_id = book_id
        super().__init__(f"Book {book_id} not found")


class AuthorNotFoundError(LibrarrError):
    def __init__(self, author_id: str) -> None:
        self.author_id = author_id
        super().__init__(f"Author {author_id} not found")


class DuplicateBookError(LibrarrError):
    def __init__(self, isbn: str, existing_id: str) -> None:
        self.isbn = isbn
        self.existing_id = existing_id
        super().__init__(f"Book with ISBN {isbn} already exists: {existing_id}")


class AlreadyArchivedError(LibrarrError):
    def __init__(self, book_id: str) -> None:
        self.book_id = book_id
        super().__init__(f"Book {book_id} is already archived")


class MetadataUnavailableError(LibrarrError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Metadata unavailable: {reason}")
