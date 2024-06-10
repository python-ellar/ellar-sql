import typing as t

import ellar.common as ecm

from ellar_sql import model, paginate

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
        article = Article(title=title, documents=documents)
        session.add(article)

        session.commit()
        session.refresh(article)

        return article

    @ecm.get("/")
    @paginate(model=Article, item_schema=ArticleSchema)
    def list_articles(self):
        return {}
