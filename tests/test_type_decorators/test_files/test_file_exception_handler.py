import ellar.common as ecm
from ellar.testing import Test

from ellar_sql.model.typeDecorator.file.exceptions import (
    FileExceptionHandler,
    SizeValidationError,
)

router = ecm.ModuleRouter()


@router.get("/home")
def home():
    raise SizeValidationError("size", "size must be less than 5kb.")


tm = Test.create_test_module(
    routers=[router], config_module={"EXCEPTION_HANDLERS": [FileExceptionHandler]}
)


def test_exception_handler_works():
    client = tm.get_test_client()
    res = client.get("/home")

    assert res.status_code == 400
    assert res.json() == {"key": "size", "message": "size must be less than 5kb."}
