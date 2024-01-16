import typing as t

import pytest

from ellar_sqlalchemy.pagination import PaginatorBase


class RangePagination(PaginatorBase):
    def __init__(
        self, total: t.Optional[int] = 150, page: int = 1, per_page: int = 10
    ) -> None:
        if total is None:
            self._data = range(150)
        else:
            self._data = range(total)

        super().__init__(page=page, per_page=per_page)

        if total is None:
            self.total = None

    def _get_init_kwargs(self) -> t.Dict[str, t.Any]:
        return {"total": self.total}

    def _query_items(self) -> t.List[t.Any]:
        first = self._query_offset
        last = first + self.per_page + 1
        return list(self._data[first:last])

    def _query_count(self) -> int:
        return len(self._data)


def test_first_page():
    p = RangePagination()
    assert p.page == 1
    assert p.per_page == 10
    assert p.total == 150
    assert p.pages == 15
    assert not p.has_prev
    assert p.prev_num is None
    assert p.has_next
    assert p.next_num == 2


def test_last_page():
    p = RangePagination(page=15)
    assert p.page == 15
    assert p.has_prev
    assert p.prev_num == 14
    assert not p.has_next
    assert p.next_num is None


def test_item_numbers_first_page():
    p = RangePagination()
    p.items = list(range(10))
    assert p.first == 1
    assert p.last == 10


def test_item_numbers_last_page():
    p = RangePagination(page=15)
    p.items = list(range(5))
    assert p.first == 141
    assert p.last == 145


def test_item_numbers_0():
    p = RangePagination(total=0)
    assert p.first == 0
    assert p.last == 0


@pytest.mark.parametrize("total", [0, None])
def test_0_pages(total):
    p = RangePagination(total=total)
    assert p.pages == 0
    assert not p.has_prev
    assert not p.has_next


@pytest.mark.parametrize(
    ("page", "expect"),
    [
        (1, [1, 2, 3, 4, 5, None, 14, 15]),
        (2, [1, 2, 3, 4, 5, 6, None, 14, 15]),
        (3, [1, 2, 3, 4, 5, 6, 7, None, 14, 15]),
        (4, [1, 2, 3, 4, 5, 6, 7, 8, None, 14, 15]),
        (5, [1, 2, 3, 4, 5, 6, 7, 8, 9, None, 14, 15]),
        (6, [1, 2, None, 4, 5, 6, 7, 8, 9, 10, None, 14, 15]),
        (7, [1, 2, None, 5, 6, 7, 8, 9, 10, 11, None, 14, 15]),
        (8, [1, 2, None, 6, 7, 8, 9, 10, 11, 12, None, 14, 15]),
        (9, [1, 2, None, 7, 8, 9, 10, 11, 12, 13, 14, 15]),
        (10, [1, 2, None, 8, 9, 10, 11, 12, 13, 14, 15]),
        (11, [1, 2, None, 9, 10, 11, 12, 13, 14, 15]),
        (12, [1, 2, None, 10, 11, 12, 13, 14, 15]),
        (13, [1, 2, None, 11, 12, 13, 14, 15]),
        (14, [1, 2, None, 12, 13, 14, 15]),
        (15, [1, 2, None, 13, 14, 15]),
    ],
)
def test_iter_pages(page, expect):
    p = RangePagination(page=page)
    assert list(p.iter_pages()) == expect


def test_iter_0_pages():
    p = RangePagination(total=0)
    assert list(p.iter_pages()) == []


@pytest.mark.parametrize("page", [1, 2, 3, 4])
def test_iter_pages_short(page):
    p = RangePagination(page=page, total=40)
    assert list(p.iter_pages()) == [1, 2, 3, 4]
