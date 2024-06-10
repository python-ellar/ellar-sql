# **File & Image Column Types**

EllarSQL provides **File** and **Image** column type descriptors to attach files to your models. It integrates seamlessly with the [Sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/tutorial/using-files-in-models/){target="_blank"} and [EllarStorage](https://github.com/python-ellar/ellar-storage){target="_blank"} packages.

## **FileField Column**
`FileField` can handle any type of file, making it a versatile option for file storage in your database models.

```python
from ellar_sql import model

class Attachment(model.Model):
    __tablename__ = "attachments"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    name: model.Mapped[str] = model.mapped_column(model.String(50), unique=True)
    content: model.Mapped[model.typeDecorator.File] = model.mapped_column(model.typeDecorator.FileField)
```

## **ImageField Column**
`ImageField` builds on **FileField**, adding validation to ensure the uploaded file is a valid image. This guarantees that only image files are stored.

```python
from ellar_sql import model

class Book(model.Model):
    __tablename__ = "books"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    title: model.Mapped[str] = model.mapped_column(model.String(100), unique=True)
    cover: model.Mapped[model.typeDecorator.File] = model.mapped_column(
        model.typeDecorator.ImageField(
            thumbnail_size=(128, 128),
        )
    )
```

By setting `thumbnail_size`, an additional thumbnail image is created and saved alongside the original `cover` image. You can access the thumbnail via `book.cover.thumbnail`.

**Note**: `ImageField` requires the [`Pillow`](https://pypi.org/project/pillow/) package:
```shell
pip install pillow
```

### **Uploading Files**
To handle where files are saved, EllarSQL's File and Image Fields require EllarStorage's `StorageModule` setup. For more details, refer to the [`StorageModule` setup](https://github.com/python-ellar/ellar-storage?tab=readme-ov-file#storagemodulesetup){target="_blank"}.

### **Saving Files**
EllarSQL supports `Starlette.datastructures.UploadFile` for Image and File Fields, simplifying file saving directly from requests.

For example:

```python
import ellar.common as ecm
from ellar_sql import model
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
```

#### Retrieving File Object
The object retrieved from an Image or File Field is an instance of [`ellar_sql.model.typeDecorator.File`](https://github.com/python-ellar/ellar-sql/blob/master/ellar_sql/model/typeDecorator/file/file.py).

```python
@ecm.get("/{book_id:int}", response={200: BookSchema})
def get_book_by_id(
    self,
    book_id: int, 
    session: ecm.Inject[model.Session],
):
    book = session.execute(
        model.select(Book).where(Book.id == book_id)
    ).scalar_one()
    
    assert book.cover.saved  # saved is True for a saved file
    assert book.cover.file.read() is not None  # access file content
    
    assert book.cover.filename is not None  # `unnamed` when no filename is provided
    assert book.cover.file_id is not None  # UUID v4
    
    assert book.cover.upload_storage == "default"
    assert book.cover.content_type is not None
    
    assert book.cover.uploaded_at is not None
    assert len(book.cover.files) == 2  # original image and generated thumbnail image

    return book
```

#### Adding More Information to a Saved File Object
The File object behaves like a Python dictionary, allowing you to add custom metadata. Be careful not to overwrite default attributes used by the File object internally.

```python
from ellar_sql.model.typeDecorator import File
from ..models import Book

content = File(open("./example.png", "rb"), custom_key1="custom_value1", custom_key2="custom_value2")
content["custom_key3"] = "custom_value3"
book = Book(title="Dummy", cover=content)

session.add(book)
session.commit()
session.refresh(book)

assert book.cover.custom_key1 == "custom_value1"
assert book.cover.custom_key2 == "custom_value2"
assert book.cover["custom_key3"] == "custom_value3"
```

## **Extra and Headers**
`Apache-libcloud` allows you to store each object with additional attributes or headers.

You can add extras and headers in two ways:

### Inline Field Declaration
You can specify these extras and headers directly in the field declaration:

```python
from ellar_sql import model

class Attachment(model.Model):
    __tablename__ = "attachments"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    name: model.Mapped[str] = model.mapped_column(model.String(50), unique=True)
    content: model.Mapped[model.typeDecorator.File] = model.mapped_column(model.typeDecorator.FileField(
        extra={
            "acl": "private",
            "dummy_key": "dummy_value",
            "meta_data": {"key1": "value1", "key2": "value2"},
        },
        headers={
            "Access-Control-Allow-Origin": "http://test.com",
            "Custom-Key": "xxxxxxx",
        },
    ))
```

### In File Object
Alternatively, you can set extras and headers in the File object itself:

```python
from ellar_sql.model.typeDecorator import File

attachment = Attachment(
    name="Public document",
    content=File(DummyFile(), extra={"acl": "public-read"}),
)
session.add(attachment)
session.commit()
session.refresh(attachment)

assert attachment.content.file.object.extra["acl"] == "public-read"
```

## **Uploading to a Specific Storage**
By default, files are uploaded to the `default` storage specified in `StorageModule`.
You can change this by specifying a different `upload_storage` in the field declaration:

```python
from ellar_sql import model

class Book(model.Model):
    __tablename__ = "books"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    title: model.Mapped[str] = model.mapped_column(model.String(100), unique=True)
    cover: model.Mapped[model.typeDecorator.File] = model.mapped_column(
        model.typeDecorator.ImageField(
            thumbnail_size=(128, 128), upload_storage="bookstore"
        )
    )
```
Setting `upload_storage="bookstore"` ensures
that the book cover is uploaded to the `bookstore` container defined in `StorageModule`.

## **Multiple Files**
A File or Image Field column can be configured to hold multiple files by setting `multiple=True`.

For example:

```python
import typing as t
from ellar_sql import model

class Article(model.Model):
    __tablename__ = "articles"

    id: model.Mapped[int] = model.mapped_column(autoincrement=True, primary_key=True)
    title: model.Mapped[str] = model.mapped_column(model.String(100), unique=True)
    documents: model.Mapped[t.List[model.typeDecorator.File]] = model.mapped_column(
        model.typeDecorator.FileField(multiple=True, upload_storage="documents")
    )
```
The `Article` model's `documents` column will store a list of files,
applying validators and processors to each file individually.
The returned model is a list of File objects.

#### Saving Multiple File Fields
Saving multiple files is as simple as passing a list of file contents to the file field column. For example:

```python
import typing as t
import ellar.common as ecm
from ellar_sql import model
from ..models import Article
from .schema import ArticleSchema

@ecm.Controller
class ArticlesController(ecm.ControllerBase):
    @ecm.post("/", response={201: ArticleSchema})
    def create_article(
        self,
        title: ecm.Body[str],
        documents: ecm.File[t.List[ecm.UploadFile]],
        session: ecm.Inject[model.Session],
    ):
        article = Article(
            title=title, documents=[
                model.typeDecorator.File(
                    content="Hello World",
                    filename="hello.txt",
                    content_type="text/plain",
                )
            ] + documents
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return article
```

## **See Also**
- [Validators](https://jowilf.github.io/sqlalchemy-file/tutorial/using-files-in-models/#validators)
- [Processors](https://jowilf.github.io/sqlalchemy-file/tutorial/using-files-in-models/#processors)

For a more comprehensive hands-on experience, check out the [file-field-example](https://github.com/python-ellar/ellar-sql/tree/main/samples/file-field-example) project.
