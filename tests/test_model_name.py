import inspect

import pytest
import sqlalchemy.exc as sa_exc

from ellar_sqlalchemy import model


@pytest.mark.parametrize(
    ("name", "expect"),
    [
        ("CamelCase", "camel_case"),
        ("Snake_case", "snake_case"),
        ("HTMLLayout", "html_layout"),
        ("LayoutHTML", "layout_html"),
        ("HTTP2Request", "http2_request"),
        ("ShoppingCartSession", "shopping_cart_session"),
        ("ABC", "abc"),
        ("PreABC", "pre_abc"),
        ("ABCPost", "abc_post"),
        ("PreABCPost", "pre_abc_post"),
        ("HTTP2RequestSession", "http2_request_session"),
        ("UserST4", "user_st4"),
        (
            "HTTP2ClientType3EncoderParametersSSE",
            "http2_client_type3_encoder_parameters_sse",
        ),
        (
            "LONGName4TestingCamelCase2snake_caseXYZ",
            "long_name4_testing_camel_case2snake_case_xyz",
        ),
        ("FooBarSSE2", "foo_bar_sse2"),
        ("AlarmMessageSS2SignalTransformer", "alarm_message_ss2_signal_transformer"),
        ("AstV2Node", "ast_v2_node"),
        ("HTTPResponseCodeXYZ", "http_response_code_xyz"),
        ("get2HTTPResponse123Code", "get2_http_response123_code"),
        # ("getHTTPresponseCode", "get_htt_presponse_code"),
        # ("__test__Method", "test___method"),
    ],
)
def test_camel_to_snake_case(name, expect):
    assert model.utils.camel_to_snake_case(name) == expect


def test_name(ignore_base):
    class FOOBar(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class BazBar(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Ham(model.Model):
        __tablename__ = "spam"
        id = model.Column(model.Integer, primary_key=True)

    assert FOOBar.__tablename__ == "foo_bar"
    assert BazBar.__tablename__ == "baz_bar"
    assert Ham.__tablename__ == "spam"


def test_joined_name(ignore_base):
    """Model has a separate primary key; it should set a new name."""

    class Duck(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Donald(Duck):
        id = model.Column(model.Integer, model.ForeignKey(Duck.id), primary_key=True)

    assert Donald.__tablename__ == "donald"


def test_mixin_id(ignore_base):
    """Primary key provided by mixin should still allow model to set
    tablename.
    """

    class Base:
        id = model.Column(model.Integer, primary_key=True)

    class Duck(Base, model.Model):
        pass

    assert not hasattr(Base, "__tablename__")
    assert Duck.__tablename__ == "duck"


def test_mixin_attr(ignore_base):
    """A declared attr tablename will be used down multiple levels of
    inheritance.
    """

    class Mixin:
        @model.declared_attr  # type: ignore[arg-type]
        def __tablename__(cls) -> str:  # noqa: B902
            return cls.__name__.upper()  # type: ignore[attr-defined,no-any-return]

    class Bird(Mixin, model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class Duck(Bird):
        # object reference
        id = model.Column(model.Integer, model.ForeignKey(Bird.id), primary_key=True)

    class Mallard(Duck):
        # string reference
        id = model.Column(model.Integer, model.ForeignKey("DUCK.id"), primary_key=True)

    assert Bird.__tablename__ == "BIRD"
    assert Duck.__tablename__ == "DUCK"
    assert Mallard.__tablename__ == "MALLARD"


def test_abstract_name(ignore_base):
    """Abstract model should not set a name. Subclass should set a name."""

    class Base(model.Model):
        __abstract__ = True
        id = model.Column(model.Integer, primary_key=True)

    class Duck(Base):
        pass

    assert "__tablename__" not in Base.__dict__
    assert Duck.__tablename__ == "duck"


def test_complex_inheritance(ignore_base):
    """Joined table inheritance, but the new primary key is provided by a
    mixin, not directly on the class.
    """

    class Duck(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class IdMixin:
        @model.declared_attr
        def id(cls):  # type: ignore[no-untyped-def]  # noqa: B902
            return model.Column(
                model.Integer, model.ForeignKey(Duck.id), primary_key=True
            )

    class RubberDuck(IdMixin, Duck):  # type: ignore[misc]
        pass

    assert RubberDuck.__tablename__ == "rubber_duck"


def test_manual_name(ignore_base):
    """Setting a manual name prevents generation for the immediate model. A
    name is generated for joined but not single-table inheritance.
    """

    class Duck(model.Model):
        __tablename__ = "DUCK"
        id = model.Column(model.Integer, primary_key=True)
        type = model.Column(model.String)

        __mapper_args__ = {"polymorphic_on": type}

    class Daffy(Duck):
        id = model.Column(model.Integer, model.ForeignKey(Duck.id), primary_key=True)

        __mapper_args__ = {"polymorphic_identity": "Tower"}

    # class Donald(Duck):
    #     __mapper_args__ = {"polymorphic_identity": "Mouse"}  # type: ignore[dict-item]

    assert Duck.__tablename__ == "DUCK"
    assert Daffy.__tablename__ == "daffy"
    # assert "__tablename__" not in Donald.__dict__
    # assert Donald.__tablename__ == "DUCK"


def test_primary_constraint(ignore_base):
    """Primary key will be picked up from table args."""

    class Duck(model.Model):
        id = model.Column(model.Integer)

        __table_args__ = (model.PrimaryKeyConstraint(id),)

    assert Duck.__table__ is not None
    assert Duck.__tablename__ == "duck"


def test_no_access_to_class_property(ignore_base):
    """Ensure the implementation doesn't access class properties or declared
    attrs while inspecting the unmapped model.
    """

    class class_property:
        def __init__(self, f):
            self.f = f

        def __get__(self, instance, owner):
            return self.f(owner)

    class Duck(model.Model):
        id = model.Column(model.Integer, primary_key=True)

    class ns:
        is_duck = False
        floats = False

    class Witch(Duck):
        id = model.Column(model.Integer, model.ForeignKey(Duck.id), primary_key=True)

        @model.declared_attr
        def is_duck(self) -> None:
            # declared attrs will be accessed during mapper configuration,
            # but make sure they're not accessed before that
            info = inspect.getouterframes(inspect.currentframe())[2]
            assert info[3] != "_should_set_tablename"
            ns.is_duck = True

        @class_property
        def floats(self) -> None:
            ns.floats = True

    assert ns.is_duck
    assert not ns.floats


def test_metadata_has_table(ignore_base):
    user = model.Table("user", model.Column("id", model.Integer, primary_key=True))

    class User(model.Model):
        pass

    assert User.__table__ is user


def test_correct_error_for_no_primary_key(ignore_base):
    with pytest.raises(sa_exc.ArgumentError) as info:

        class User(model.Model):
            pass

    assert "could not assemble any primary key" in str(info.value)


# def test_single_has_parent_table() -> None:
#     class Duck(model.Model):
#         id = model.Column(model.Integer, primary_key=True)
#
#     class Call(Duck):
#         pass
#
#     assert Call.__table__ is Duck.__table__
#     assert "__table__" not in Call.__dict__
