import ellar.common as ecm

from ellar_sql import model, paginate

from ..models import Book
from .schema import BookSchema


@ecm.Controller
class BooksController(ecm.ControllerBase):
    @ecm.post("/", response={201: BookSchema})
    def create_book(
        self,
        title: ecm.Body[str],
        cover: ecm.File[ecm.UploadFile],
        session: ecm.Inject[model.Session],
    ):
        book = Book(title=title, cover=cover)
        session.add(book)

        session.commit()
        session.refresh(book)

        return book

    @ecm.get("/")
    @paginate(model=Book, item_schema=BookSchema)
    def list_book(self):
        return {}
