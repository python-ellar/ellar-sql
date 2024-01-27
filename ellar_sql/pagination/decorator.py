import asyncio
import functools
import typing as t
import uuid

import ellar.common as ecm
import sqlalchemy as sa
from ellar.common import set_metadata
from ellar.common.constants import EXTRA_ROUTE_ARGS_KEY, RESPONSE_OVERRIDE_KEY
from pydantic import BaseModel

from ellar_sql.model.base import ModelBase

from .view import PageNumberPagination, PaginationBase


def paginate(
    pagination_class: t.Optional[t.Type[PaginationBase]] = None,
    model: t.Optional[t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]]] = None,
    as_template_context: bool = False,
    item_schema: t.Optional[t.Type[BaseModel]] = None,
    **paginator_options: t.Any,
) -> t.Callable:
    """
    =========ROUTE FUNCTION DECORATOR ==============

    :param pagination_class: Pagination Class of type PaginationBase
    :param model: SQLAlchemy Model or SQLAlchemy Select Statement
    :param as_template_context: If True adds `paginator` object to templating context data
    :param item_schema: Pagination Object Schema for serializing object and creating response schema documentation
    :param paginator_options: Other keyword args for initializing `pagination_class`
    :return: TCallable
    """
    paginator_options.update(model=model)

    def _wraps(func: t.Callable) -> t.Callable:
        operation_class = (
            _AsyncPaginationOperation
            if asyncio.iscoroutinefunction(func)
            else _PaginationOperation
        )
        operation = operation_class(
            route_function=func,
            pagination_class=pagination_class or PageNumberPagination,
            as_template_context=as_template_context,
            item_schema=item_schema,
            paginator_options=paginator_options,
        )

        return operation.as_view

    return _wraps


class _PaginationOperation:
    def __init__(
        self,
        route_function: t.Callable,
        pagination_class: t.Type[PaginationBase],
        paginator_options: t.Dict[str, t.Any],
        as_template_context: bool = False,
        item_schema: t.Optional[t.Type[BaseModel]] = None,
    ) -> None:
        self._original_route_function = route_function
        self._pagination_view = pagination_class(**paginator_options)
        _, _, view = self._get_route_function_wrapper(as_template_context, item_schema)
        self.as_view = functools.wraps(route_function)(view)

    def _prepare_template_response(
        self, res: t.Any
    ) -> t.Tuple[
        t.Optional[t.Union[t.Type[ModelBase], sa.sql.Select[t.Any]]], t.Dict[str, t.Any]
    ]:
        if isinstance(res, tuple):
            filter_query, extra_context = res
            assert isinstance(
                extra_context, dict
            ), "When using as `template_context`, route function should return a tuple(select, {})"

        elif isinstance(res, dict):
            filter_query = None
            extra_context = res

        elif (
            isinstance(res, sa.sql.Select)
            or isinstance(res, type)
            and issubclass(res, ModelBase)
        ):
            filter_query = res
            extra_context = {}
        else:
            raise RuntimeError(
                f"Invalid datastructure returned from route function. - {res}"
            )

        return filter_query, extra_context

    def _get_route_function_wrapper(
        self, as_template_context: bool, item_schema: t.Type[BaseModel]
    ) -> t.Tuple[ecm.params.ExtraEndpointArg, ecm.params.ExtraEndpointArg, t.Callable]:
        unique_id = str(uuid.uuid4())
        # use unique_id to make the kwargs difficult to collide with any route function parameter
        _paginate_args = ecm.params.ExtraEndpointArg(
            name=f"paginate_{unique_id[:-6]}",
            annotation=self._pagination_view.get_annotation(),
        )
        # use unique_id to make the kwargs difficult to collide with any route function parameter
        execution_context = ecm.params.ExtraEndpointArg(
            name=f"context_{unique_id[:-6]}",
            annotation=ecm.Inject[ecm.IExecutionContext],
        )

        set_metadata(EXTRA_ROUTE_ARGS_KEY, [_paginate_args, execution_context])(
            self._original_route_function
        )

        if not as_template_context and not item_schema:
            raise ecm.exceptions.ImproperConfiguration(
                "Must supply value for either `template_context` or `item_schema`"
            )

        if not as_template_context:
            # if pagination is not for template context, then we create a response schema for the api response
            response_schema = self._pagination_view.get_output_schema(item_schema)
            ecm.set_metadata(RESPONSE_OVERRIDE_KEY, {200: response_schema})(
                self._original_route_function
            )

        def as_view(*args: t.Any, **kw: t.Any) -> t.Any:
            func_kwargs = dict(**kw)
            paginate_input = _paginate_args.resolve(func_kwargs)
            context: ecm.IExecutionContext = execution_context.resolve(func_kwargs)

            items = self._original_route_function(*args, **func_kwargs)

            if not as_template_context:
                return self._pagination_view.api_paginate(
                    items,
                    paginate_input,
                    context.switch_to_http_connection().get_request(),
                )

            filter_query, extra_context = self._prepare_template_response(items)

            pagination_context = self._pagination_view.pagination_context(
                filter_query,
                paginate_input,
                context.switch_to_http_connection().get_request(),
            )
            extra_context.update(pagination_context)

            return extra_context

        return _paginate_args, execution_context, as_view


class _AsyncPaginationOperation(_PaginationOperation):
    def _get_route_function_wrapper(
        self, as_template_context: bool, item_schema: t.Type[BaseModel]
    ) -> t.Tuple[ecm.params.ExtraEndpointArg, ecm.params.ExtraEndpointArg, t.Callable]:
        _paginate_args, execution_context, _ = super()._get_route_function_wrapper(
            as_template_context, item_schema
        )

        async def as_view(*args: t.Any, **kw: t.Any) -> t.Any:
            func_kwargs = dict(**kw)

            paginate_input = _paginate_args.resolve(func_kwargs)
            context: ecm.IExecutionContext = execution_context.resolve(func_kwargs)

            items = await self._original_route_function(*args, **func_kwargs)
            request = context.switch_to_http_connection().get_request()

            if not as_template_context:
                return self._pagination_view.api_paginate(
                    items,
                    paginate_input,
                    request,
                )

            filter_query, extra_context = self._prepare_template_response(items)

            pagination_context = self._pagination_view.pagination_context(
                filter_query,
                paginate_input,
                request,
            )
            extra_context.update(pagination_context)

            return extra_context

        return _paginate_args, execution_context, as_view
