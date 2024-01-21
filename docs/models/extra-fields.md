# **Extra Column Types**
EllarSQL comes with extra column type descriptor that will come in handy in your project. They include

- [GUID](#guid-column)
- [IPAddress](#ipaddress-column)

## **GUID Column**
GUID, Global Unique Identifier of 128-bit text string can be used as a unique identifier in a table.
For applications that require a GUID type of primary, this can be a use resource. 
It uses `UUID` type in Postgres and `CHAR(32)` in other SQL databases.

```python
import uuid
from ellar_sql import model

class Guid(model.Model):
    id: model.Mapped[uuid.uuid4] = model.mapped_column(
        "id",
        model.GUID(),
        nullable=False,
        unique=True,
        primary_key=True,
        default=uuid.uuid4,
    )
```

## **IPAddress Column**
`GenericIP` column type validates and converts column value to `ipaddress.IPv4Address` or `ipaddress.IPv6Address`.
It uses `INET` type in Postgres and `CHAR(45)` in other SQL databases.

```python
import typing as t
import ipaddress
from ellar_sql import model

class IPAddress(model.Model):
    id = model.Column(model.Integer, primary_key=True)
    ip: model.Mapped[t.Union[ipaddress.IPv4Address, ipaddress.IPv6Address]] = model.Column(model.GenericIP)
```
