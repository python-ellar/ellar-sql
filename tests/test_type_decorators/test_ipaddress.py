from ellar_sqlalchemy import model


def test_ipaddress_column_type(db_service, ignore_base):
    ip = "192.0.2.1"

    class IPAddress(model.Model):
        id = model.Column(model.Integer, primary_key=True)
        ip = model.Column(model.GenericIP)

    db_service.create_all()
    session = db_service.session_factory()
    session.add(IPAddress(ip=ip))
    session.commit()

    ip_address = session.execute(model.select(IPAddress)).scalar()
    assert str(ip_address.ip) == ip
