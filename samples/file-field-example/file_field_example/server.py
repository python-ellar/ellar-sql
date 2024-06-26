import os

from ellar.app import App, AppFactory
from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.core import LazyModuleImport as lazyLoad
from ellar.openapi import OpenAPIDocumentBuilder, OpenAPIDocumentModule, SwaggerUI


def bootstrap() -> App:
    application = AppFactory.create_from_app_module(
        lazyLoad("file_field_example.root_module:ApplicationModule"),
        config_module=os.environ.get(
            ELLAR_CONFIG_MODULE, "file_field_example.config:DevelopmentConfig"
        ),
        global_guards=[],
    )

    # uncomment this section if you want API documentation

    document_builder = OpenAPIDocumentBuilder()
    document_builder.set_title("Image & File Field Demonstration").set_version(
        "1.0.2"
    ).set_contact(
        name="Author Name",
        url="https://www.author-name.com",
        email="authorname@gmail.com",
    ).set_license("MIT Licence", url="https://www.google.com").add_server(
        "/", description="Development Server"
    )

    document = document_builder.build_document(application)
    OpenAPIDocumentModule.setup(
        app=application, document=document, docs_ui=SwaggerUI(), guards=[]
    )
    return application
