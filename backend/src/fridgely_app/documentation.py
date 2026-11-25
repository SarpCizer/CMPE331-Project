"""Self-host API documentation without inline scripts or third-party CDNs."""
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles


DOCS_HTML = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fridgely API documentation</title>
<link rel="icon" href="/api/docs/assets/favicon-32x32.png">
<link rel="stylesheet" href="/api/docs/assets/swagger-ui.css"></head>
<body><div id="swagger-ui"></div>
<script src="/api/docs/assets/swagger-ui-bundle.js"></script>
<script src="/api/docs/init.js"></script></body></html>'''
DOCS_SCRIPT = '''window.ui = SwaggerUIBundle({
  url: "/api/openapi.json", dom_id: "#swagger-ui", deepLinking: true,
  persistAuthorization: false, validatorUrl: null,
  defaultModelsExpandDepth: 0, displayRequestDuration: true
});'''


def install_documentation(api, frontend_dir):
    assets = frontend_dir / 'api-docs'
    if assets.is_dir():
        api.mount('/docs/assets', StaticFiles(directory=assets), name='api-doc-assets')

    @api.get('/docs', include_in_schema=False)
    def documentation():
        if not assets.is_dir():
            return JSONResponse({'error':'Build the frontend to install the documentation assets',
                'openapi':'/api/openapi.json'}, status_code=503)
        return HTMLResponse(DOCS_HTML)

    @api.get('/docs/init.js', include_in_schema=False)
    def initialize_documentation():
        return Response(DOCS_SCRIPT, media_type='text/javascript')

    for route in api.routes:
        if isinstance(route, APIRoute) and route.path.startswith(('/shopping-items','/favorites','/history')):
            route.tags = [{'shopping-items':'Shopping','favorites':'Favorites','history':'History'}[
                route.path.split('/')[1]]]

    original_openapi = api.openapi

    def documented_errors():
        if api.openapi_schema:
            return api.openapi_schema
        schema = original_openapi()
        error_schema = {'type':'object','required':['error'],'properties':{
            'error':{'type':'string'},'retryable':{'type':'boolean'}}}
        for path, methods in schema['paths'].items():
            for operation in methods.values():
                responses = operation.get('responses',{})
                # The feature routers sanitize request validation into HTTP 400.
                responses.pop('422',None)
                statuses = {400:'Invalid request',503:'Storage or recipe provider temporarily unavailable'}
                if operation.get('security') or path == '/sessions':
                    statuses[401] = 'Bearer token missing, invalid or expired'
                if '{' in path:
                    statuses[404] = 'Owned resource not found'
                if path == '/accounts':
                    statuses[409] = 'Account already exists'
                if path == '/recipes/generate':
                    statuses[422] = 'Generated batch rejected by dietary or allergen validation'
                    statuses[502] = 'Invalid provider response'
                for status, description in statuses.items():
                    responses[str(status)] = {'description':description,
                        'content':{'application/json':{'schema':error_schema}}}
        api.openapi_schema = schema
        return schema

    api.openapi = documented_errors
