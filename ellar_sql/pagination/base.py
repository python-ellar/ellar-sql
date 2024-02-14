import typing as t
from abc import abstractmethod
from math import ceil

import ellar.common as ecm
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from ellar.app import current_injector
from ellar.threading import run_as_async
from sqlalchemy.ext.asyncio import AsyncSession

from ellar_sql.model.base import ModelBase
from ellar_sql.services import EllarSQLService


class PaginatorBase:
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: t.Optional[int] = 100,
        error_out: bool = True,
        count: bool = True,
    ) -> None:
        page, per_page = self._prepare_page_args(
            page=page,
            per_page=per_page,
            max_per_page=max_per_page,
            error_out=error_out,
        )

        self.page: int = page
        """The current page."""

        self.per_page: int = per_page
        """The maximum number of items on a page."""

        self.max_per_page: t.Optional[int] = max_per_page
        """The maximum allowed value for ``per_page``."""

        items = self._query_items()

        if not items and page != 1 and error_out:
            raise ecm.NotFound()

        self.items: t.List[t.Any] = items
        """The items on the current page. Iterating over the pagination object is
        equivalent to iterating over the items.
        """

        if count:
            total = self._query_count()
        else:
            total = None

        self.total: t.Optional[int] = total
        """The total number of items across all pages."""

    def _prepare_page_args(
        self,
        *,
        page: int,
        per_page: int,
        max_per_page: t.Optional[int],
        error_out: bool,
    ) -> t.Tuple[int, int]:
        if max_per_page is not None:
            per_page = min(per_page, max_per_page)

        if page < 1:
            if error_out:
                raise ecm.NotFound()
            else:
                page = 1

        if per_page < 1:
            if error_out:
                raise ecm.NotFound()
            else:
                per_page = 20

        return page, per_page

    @property
    def _query_offset(self) -> int:
        """ """
        return (self.page - 1) * self.per_page

    @abstractmethod
    def _query_items(self) -> t.List[t.Any]:
        """Execute the query to get the items on the current page."""

    @abstractmethod
    def _get_init_kwargs(self) -> t.Dict[str, t.Any]:
        """Returns dictionary of other attributes a child class requires for initialization"""

    @abstractmethod
    def _query_count(self) -> int:
        """Execute the query to get the total number of items."""

    @property
    def first(self) -> int:
        """The number of the first item on the page, starting from 1, or 0 if there are
        no items.
        """
        if len(self.items) == 0:
            return 0

        return (self.page - 1) * self.per_page + 1

    @property
    def last(self) -> int:
        """The number of the last item on the page, starting from 1, inclusive, or 0 if
        there are no items.
        """
        first = self.first
        return max(first, first + len(self.items) - 1)

    @property
    def pages(self) -> int:
        """The total number of pages."""
        if self.total == 0 or self.total is None:
            return 0

        return ceil(self.total / self.per_page)

    @property
    def has_prev(self) -> bool:
        """`True` if this is not the first page."""
        return self.page > 1

    @property
    def prev_num(self) -> t.Optional[int]:
        """The previous page number, or `None` if this is the first page."""
        if not self.has_prev:
            return None

        return self.page - 1

    def prev(self, *, error_out: bool = False) -> "PaginatorBase":
        """Query the pagination object for the previous page.

        :param error_out: Raise `404 Not Found` error if no items are returned
            and `page` is not 1, or if `page` or `per_page` is less than 1.
        """
        init_kwargs = self._get_init_kwargs()
        init_kwargs.update(
            page=self.page - 1,
            per_page=self.per_page,
            error_out=error_out,
            count=False,
        )
        p = self.__class__(**init_kwargs)
        p.total = self.total
        return p

    @property
    def has_next(self) -> bool:
        """`True` if this is not the last page."""
        return self.page < self.pages

    @property
    def next_num(self) -> t.Optional[int]:
        """The next page number, or `None` if this is the last page."""
        if not self.has_next:
            return None

        return self.page + 1

    def next(self, *, error_out: bool = False) -> "PaginatorBase":
        """
        Query the Pagination object for the next page.

        :param error_out: Raise `404 Not Found` error if no items are returned
            and `page` is not 1, or if `page` or `per_page` is less than 1.
        """
        init_kwargs = self._get_init_kwargs()
        init_kwargs.update(
            page=self.page + 1,
            per_page=self.per_page,
            max_per_page=self.max_per_page,
            error_out=error_out,
            count=False,
        )
        p = self.__class__(**init_kwargs)
        p.total = self.total
        return p

    def iter_pages(
        self,
        *,
        left_edge: int = 2,
        left_current: int = 2,
        right_current: int = 4,
        right_edge: int = 2,
    ) -> t.Iterator[t.Optional[int]]:
        """
        Yield page numbers for a pagination widget.
        A None represents skipped pages between the edges and middle.

        For example, if there are 20 pages and the current page is 7, the following
        values are yielded.

        For example:
        1, 2, None, 5, 6, 7, 8, 9, 10, 11, None, 19, 20

        :param left_edge: How many pages to show from the first page.
        :param left_current: How many pages to show left of the current page.
        :param right_current: How many pages to show right of the current page.
        :param right_edge: How many pages to show from the last page.

        """
        pages_end = self.pages + 1

        if pages_end == 1:
            return

        left_end = min(1 + left_edge, pages_end)
        yield from range(1, left_end)

        if left_end == pages_end:
            return

        mid_start = max(left_end, self.page - left_current)
        mid_end = min(self.page + right_current + 1, pages_end)

        if mid_start - left_end > 0:
            yield None

        yield from range(mid_start, mid_end)

        if mid_end == pages_end:
            return

        right_start = max(mid_end, pages_end - right_edge)

        if right_start - mid_end > 0:
            yield None

        yield from range(right_start, pages_end)

    def __iter__(self) -> t.Iterator[t.Any]:
        yield from self.items


class Paginator(PaginatorBase):
    def __init__(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]],
        session: t.Optional[t.Union[sa_orm.Session, AsyncSession]] = None,
        page: int = 1,
        per_page: int = 20,
        max_per_page: t.Optional[int] = 100,
        error_out: bool = True,
        count: bool = True,
    ) -> None:
        if isinstance(model, type) and issubclass(model, ModelBase):
            self._select = sa.select(model)
        else:
            self._select = t.cast(sa.sql.Select, model)

        self._created_session = False

        self._session: t.Union[sa_orm.Session, AsyncSession] = (
            session or self._get_session()
        )
        self._is_async = self._session.get_bind().dialect.is_async

        super().__init__(
            page=page,
            per_page=per_page,
            max_per_page=max_per_page,
            error_out=error_out,
            count=count,
        )

        if self._created_session:
            self._close_session()  # session usage is done but only if Paginator created the session

    @run_as_async
    async def _close_session(self) -> None:
        res = self._session.close()
        if isinstance(res, t.Coroutine):
            await res

    def _get_session(self) -> t.Union[sa_orm.Session, AsyncSession, t.Any]:
        self._created_session = True
        service = current_injector.get(EllarSQLService)
        return service.get_scoped_session()()

    def _query_items(self) -> t.List[t.Any]:
        if self._is_async:
            res = self._query_items_async()
            return list(res)
        return self._query_items_sync()

    def _query_items_sync(self) -> t.List[t.Any]:
        select = self._select.limit(self.per_page).offset(self._query_offset)
        return list(self._session.execute(select).unique().scalars())

    @run_as_async
    async def _query_items_async(self) -> t.List[t.Any]:
        session = t.cast(AsyncSession, self._session)

        select = self._select.limit(self.per_page).offset(self._query_offset)
        res = await session.execute(select)

        return list(res.unique().scalars())

    def _query_count(self) -> int:
        if self._is_async:
            res = self._query_count_async()
            return int(res)
        return self._query_count_sync()

    def _query_count_sync(self) -> int:
        sub = self._select.options(sa_orm.lazyload("*")).order_by(None).subquery()
        out = self._session.execute(
            sa.select(sa.func.count()).select_from(sub)
        ).scalar()
        return out  # type:ignore[return-value]

    @run_as_async
    async def _query_count_async(self) -> int:
        session = t.cast(AsyncSession, self._session)

        sub = self._select.options(sa_orm.lazyload("*")).order_by(None).subquery()

        out = await session.execute(sa.select(sa.func.count()).select_from(sub))
        return out.scalar()  # type:ignore[return-value]

    def _get_init_kwargs(self) -> t.Dict[str, t.Any]:
        return {"model": self._select}
