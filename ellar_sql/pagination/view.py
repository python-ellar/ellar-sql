import typing as t
from abc import ABC, abstractmethod
from collections import OrderedDict

import ellar.common as ecm
import ellar.core as ec
import sqlalchemy as sa
from pydantic import BaseModel, Field

from ellar_sql.model.base import ModelBase
from ellar_sql.schemas import BasicPaginationSchema, PageNumberPaginationSchema

from .base import Paginator
from .utils import remove_query_param, replace_query_param


class PaginationBase(ABC):
    InputSource = ecm.Query

    class Input(BaseModel):
        pass

    def get_annotation(self) -> t.Any:
        return self.InputSource[self.Input, self.InputSource.P(...)]

    @abstractmethod
    def get_output_schema(
        self, item_schema: t.Type[BaseModel]
    ) -> t.Type[BaseModel]:  # pragma: no cover
        """Return a Response Schema Type for item schema"""

    def validate_model(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]],
        fallback: t.Optional[t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]]],
    ) -> t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]]:
        if isinstance(model, sa.sql.Select) or (
            isinstance(model, type) and issubclass(model, ModelBase)
        ):
            working_model = model
        else:
            working_model = fallback  # type:ignore[assignment]
            assert working_model is not None, "Model Can not be None"
        return working_model

    @abstractmethod
    def api_paginate(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]],
        input_schema: t.Any,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Any:
        pass  # pragma: no cover

    @abstractmethod
    def pagination_context(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]],
        input_schema: t.Any,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Dict[str, t.Any]:
        pass  # pragma: no cover

    if t.TYPE_CHECKING:

        def __init__(self, **kwargs: t.Any) -> None: ...


class PageNumberPagination(PaginationBase):
    class Input(BaseModel):
        page: int = Field(1, gt=0)

    paginator_class: t.Type[Paginator] = Paginator
    page_query_param: str = "page"

    def __init__(
        self,
        *,
        model: t.Optional[t.Type[ModelBase]] = None,
        per_page: int = 20,
        max_per_page: int = 100,
        error_out: bool = True,
    ) -> None:
        super().__init__()
        self._model = model
        self._paginator_init_kwargs = {
            "per_page": per_page,
            "max_per_page": max_per_page,
            "error_out": error_out,
        }

    def get_output_schema(self, item_schema: t.Type[BaseModel]) -> t.Type[BaseModel]:
        return PageNumberPaginationSchema[item_schema]  # type:ignore[valid-type]

    def api_paginate(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select, t.Any],
        input_schema: Input,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Any:
        working_model = self.validate_model(model, self._model)

        paginator = self.paginator_class(
            model=working_model, page=input_schema.page, **self._paginator_init_kwargs
        )
        return self._get_paginated_response(
            base_url=str(request.url), paginator=paginator
        )

    def pagination_context(
        self,
        model: t.Union[t.Type, sa.sql.Select],
        input_schema: Input,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Dict[str, t.Any]:
        working_model = self.validate_model(model, self._model)

        paginator = self.paginator_class(
            model=working_model, page=input_schema.page, **self._paginator_init_kwargs
        )
        return {"paginator": paginator}

    def _get_paginated_response(
        self, *, base_url: str, paginator: Paginator
    ) -> t.Dict[str, t.Any]:
        is_query = self.InputSource.name == "Query"
        next_url = (
            self._get_next_link(base_url, paginator=paginator) if is_query else None
        )

        prev_url = (
            self._get_previous_link(base_url, paginator=paginator) if is_query else None
        )
        return OrderedDict(
            [
                ("count", paginator.total),
                ("next", next_url),
                ("previous", prev_url),
                ("items", list(paginator)),
            ]
        )

    def _get_next_link(self, url: str, paginator: Paginator) -> t.Optional[str]:
        if not paginator.has_next:
            return None
        page_number = paginator.page + 1
        return replace_query_param(url, self.page_query_param, page_number)

    def _get_previous_link(self, url: str, paginator: Paginator) -> t.Optional[str]:
        if not paginator.has_prev:
            return None
        page_number = paginator.page - 1
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)


class LimitOffsetPagination(PaginationBase):
    class Input(BaseModel):
        limit: int = Field(50, ge=1)
        offset: int = Field(0, ge=0)

    paginator_class: t.Type[Paginator] = Paginator

    def __init__(
        self,
        *,
        model: t.Optional[t.Type[ModelBase]] = None,
        limit: int = 50,
        max_limit: int = 100,
        error_out: bool = True,
    ) -> None:
        super().__init__()
        self._model = model
        self._max_limit = max_limit
        self._error_out = error_out

        self._paginator_init_kwargs = {
            "error_out": error_out,
            "max_per_page": max_limit,
        }
        self.Input = self.create_input(limit)  # type:ignore[misc]

    def create_input(self, limit: int) -> t.Type[Input]:
        _limit = int(limit)

        class DynamicInput(self.Input):
            limit: int = Field(_limit, ge=1)
            offset: int = Field(0, ge=0)

        return DynamicInput

    def get_output_schema(self, item_schema: t.Type[BaseModel]) -> t.Type[BaseModel]:
        return BasicPaginationSchema[item_schema]

    def api_paginate(
        self,
        model: t.Union[t.Type[ModelBase], sa.sql.Select[t.Any], t.Any],
        input_schema: Input,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Any:
        working_model = self.validate_model(model, self._model)

        page = input_schema.offset or 1
        per_page: int = min(input_schema.limit, self._max_limit)

        paginator = self.paginator_class(
            model=working_model,
            page=page,
            per_page=per_page,
            **self._paginator_init_kwargs,
        )
        return OrderedDict(
            [
                ("count", paginator.total),
                ("items", list(paginator)),
            ]
        )

    def pagination_context(
        self,
        model: t.Union[t.Type, sa.sql.Select[t.Any]],
        input_schema: Input,
        request: ec.Request,
        **params: t.Any,
    ) -> t.Dict[str, t.Any]:
        working_model = self.validate_model(model, self._model)

        page = input_schema.offset or 1
        per_page: int = min(input_schema.limit, self._max_limit)

        paginator = self.paginator_class(
            model=working_model,
            page=page,
            per_page=per_page,
            **self._paginator_init_kwargs,
        )
        return {"paginator": paginator}
