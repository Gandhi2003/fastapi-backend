"""OAuth2 / OIDC client registry for social login (Google, Microsoft).

Authlib handles the OIDC dance. The router (app/modules/auth) calls
`oauth.<provider>.authorize_redirect(...)` then `authorize_access_token(...)`,
reads the verified userinfo, and either links to or provisions a local User with
``auth_provider`` set accordingly. Local password login stays independent.
"""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth = OAuth()

if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.MICROSOFT_CLIENT_ID:
    tenant = settings.MICROSOFT_TENANT_ID
    oauth.register(
        name="microsoft",
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        server_metadata_url=(
            f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )
