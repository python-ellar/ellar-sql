# **Pagination**

Pagination is a common practice for large datasets, 
enhancing user experience by breaking content into manageable pages. 
It optimizes load times and navigation and allows users to explore extensive datasets with ease 
while maintaining system performance and responsiveness.

EllarSQL offers two styles of pagination:

- **PageNumberPagination**: This pagination internally configures items `per_page` and max item size (`max_size`) and, allows users to set the `page` property.
- **LimitOffsetPagination**: This pagination internally configures max item size (`max_limit`) and, allows users to set the `limit` and `offset` properties.

EllarSQL pagination is activated when a route function is decorated with `paginate` function.
The result of the route function is expected to be a `SQLAlchemy.sql.Select` instance or a `Model` type.

For example:

```python
import ellar.common as ec
from ellar_sql import model, paginate
from .models import User
from .schemas import UserSchema


@ec.get('/users')
@paginate(item_schema=UserSchema)
def list_users():
    return model.select(User)
```

### **paginate properties**

- **pagination_class**: _t.Optional[t.Type[PaginationBase]]=None_: specifies pagination style to use. if not set, it will be set to `PageNumberPagination`
- **model**: _t.Optional[t.Type[ModelBase]]=None_: specifies a `Model` type to get list of data. If set, route function can return `None` or override by returning a **select/filtered** statement
- **as_template_context**: _bool=False_: indicates that the paginator object be added to template context. See [Template Pagination](#template-pagination)
- **item_schema**: _t.Optional[t.Type[BaseModel]]=None_: This is required if `template_context` is False. It is used to **serialize** the SQLAlchemy model and create a **response-schema/docs**.
- **paginator_options**:_t.Any_: keyword argument for configuring `pagination_class` set to use for pagination.

## **API Pagination**
API pagination simply means pagination in an API route function.
This requires `item_schema` for the paginate decorator
to create a `200` response documentation for the decorated route and for the paginated result to be serialized to json.

```python
import ellar.common as ec
from ellar_sql import paginate
from .models import User


class UserSchema(ec.Serializer):
    id: str
    name: str
    fullname: str


@ec.get('/users')
@paginate(item_schema=UserSchema, per_page=100)
def list_users():
    return User
```
We can also rewrite the illustration above since we are not making any modification to the User query.

```python
...

@ec.get('/users')
@paginate(model=User, item_schema=UserSchema)
def list_users():
    pass
```

## **Template Pagination**
This is for route functions
decorated with [`render`](https://python-ellar.github.io/ellar/overview/custom_decorators/#render) function
that need to be paginated.
For this to happen, `paginate`
function need to return a context and this is achieved by setting `as_template_context=True`

```python
import ellar.common as ec
from ellar_sql import model, paginate
from .models import User


@ec.get('/users')
@ec.render('list.html')
@paginate(as_template_context=True)
def list_users():
    return model.select(User), {'name': 'Template Pagination'} # pagination model, template context
```
In the illustration above, a tuple of select statement and a template context was returned.
The template context will be updated with a [`paginator`](https://github.com/python-ellar/ellar-sql/blob/master/ellar_sql/pagination/base.py) as an extra key by the `paginate` function
before been processed by `render` function.

We can re-write the example above to return just the template context since there is no form of 
filter directly affecting the `User` model query.
```python
...

@ec.get('/users')
@ec.render('list.html')
@paginate(model=model.select(User), as_template_context=True)
def list_users():
    return {'name': 'Template Pagination'}
```
Also, in the `list.html` we have the following codes:
```html
<!DOCTYPE html>
<html lang="en">
<h3>{{ name }}</h3>
{% macro render_pagination(paginator, endpoint) %}
  <div>
    {{ paginator.first }} - {{ paginator.last }} of {{ paginator.total }}
  </div>
  <div>
    {% for page in paginator.iter_pages() %}
      {% if page %}
        {% if page != paginator.page %}
          <a href="{{ url_for(endpoint) }}?page={{page}}">{{ page }}</a>
        {% else %}
          <strong>{{ page }}</strong>
        {% endif %}
      {% else %}
        <span class=ellipsis>…</span>
      {% endif %}
    {% endfor %}
  </div>
{% endmacro %}

<ul>
  {% for user in paginator %}
    <li>{{ user.id }} @ {{ user.name }}
  {% endfor %}
</ul>
{{render_pagination(paginator=paginator, endpoint="list_users") }}
</html>
```

The `paginator` object in the template context has a `iter_pages()` method which produces up to three group of numbers,
seperated by `None`. 

It defaults to showing 2 page numbers at either edge, 
2 numbers before the current, the current, and 4 numbers after the current. 
For example, if there are 20 pages and the current page is 7, the following values are yielded.
```
paginator.iter_pages()
[1, 2, None, 5, 6, 7, 8, 9, 10, 11, None, 19, 20]
```
The `total` attribute showcases the total number of results, while `first` and `last` display the range of items on the current page. 

The accompanying Jinja macro renders a simple pagination widget.
```html
{% macro render_pagination(paginator, endpoint) %}
  <div>
    {{ paginator.first }} - {{ paginator.last }} of {{ paginator.total }}
  </div>
  <div>
    {% for page in paginator.iter_pages() %}
      {% if page %}
        {% if page != paginator.page %}
          <a href="{{ url_for(endpoint) }}?page={{page}}">{{ page }}</a>
        {% else %}
          <strong>{{ page }}</strong>
        {% endif %}
      {% else %}
        <span class=ellipsis>…</span>
      {% endif %}
    {% endfor %}
  </div>
{% endmacro %}
```
