import ellar.common as ecm

from ellar_sql import model, paginate

from ..models import Attachment
from .schema import AttachmentSchema


@ecm.Controller
class AttachmentController(ecm.ControllerBase):
    @ecm.post("/", response={201: AttachmentSchema})
    def create_attachment(
        self,
        name: ecm.Body[str],
        content: ecm.File[ecm.UploadFile],
        session: ecm.Inject[model.Session],
    ):
        attachment = Attachment(name=name, content=content)
        session.add(attachment)

        session.commit()
        session.refresh(attachment)

        return attachment

    @ecm.get("/")
    @paginate(model=Attachment, item_schema=AttachmentSchema)
    def list_attachments(self):
        return {}
