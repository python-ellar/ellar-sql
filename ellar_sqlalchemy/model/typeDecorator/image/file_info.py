import typing as t

from ..file import FileObject


class ImageFileObject(FileObject):
    def __init__(self, *, height: float, width: float, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self.height = height
        self.width = width

    def to_dict(self) -> t.Dict[str, t.Any]:
        data = super().to_dict()
        data.update(height=self.height, width=self.width)
        return data
