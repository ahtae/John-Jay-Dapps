from flask import Flask
from dapp.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    from dapp.employer_form.routes import employer_form
    from dapp.result.routes import result
    from dapp.main.routes import main
    from dapp.errors.handlers import errors

    app.register_blueprint(employer_form)
    app.register_blueprint(result)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
