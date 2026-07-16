from __future__ import annotations

from app.modules.auth.models import RefreshToken, UserDevice  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.customers.models import Customer  # noqa: F401
from app.modules.dealers.models import Dealer  # noqa: F401
from app.modules.farmers.models import Farmer  # noqa: F401
from app.modules.permissions.models import Permission  # noqa: F401
from app.modules.products.models import Product  # noqa: F401
from app.modules.roles.models import Role, role_permissions  # noqa: F401
from app.modules.suppliers.models import Supplier  # noqa: F401
from app.modules.users.models import User, user_roles  # noqa: F401
