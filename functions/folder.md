Purpose:
- Centralize modular backend logic for the Flask app.
Main Files:
- Uses submodules rather than root level python files.
Sub Folders:
- ui: template controllers and blueprints.
- api: OpenAI integrations and API routing.
- data: configuration, repositories, validators.
- auth: authentication helpers plus CSRF tooling.
Dependent Folders:
- utils for logging, templates for rendering, static for assets.
