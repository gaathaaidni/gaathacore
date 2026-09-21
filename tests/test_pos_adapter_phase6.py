import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POS_APP_ROOT = ROOT / "imported" / "gaathapos" / "gaathapos-main"
SUITE_APP_ROOT = ROOT / "imported" / "gaathasuite" / "gaathasuite-main" / "backend"
for shadowed in [str(SUITE_APP_ROOT), str(POS_APP_ROOT)]:
    if shadowed in sys.path:
        sys.path.remove(shadowed)
if str(POS_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(POS_APP_ROOT))

os.environ.setdefault("SECRET_KEY", "pos-test-secret")
os.environ["DATABASE_URL"] = "sqlite:///./pos_test_app.db"

import importlib.util

def _load_pos_app():
    for module_name in list(sys.modules):
        if module_name == "gaatha_pos_app" or module_name == "blueprints" or module_name.startswith("blueprints.") or module_name in {"extensions", "models", "config", "decorators", "routes"}:
            sys.modules.pop(module_name, None)
    _pos_app_spec = importlib.util.spec_from_file_location("gaatha_pos_app", POS_APP_ROOT / "app.py")
    _pos_app_module = importlib.util.module_from_spec(_pos_app_spec)
    assert _pos_app_spec is not None and _pos_app_spec.loader is not None
    sys.modules["gaatha_pos_app"] = _pos_app_module
    _pos_app_spec.loader.exec_module(_pos_app_module)
    return _pos_app_module.create_app

create_app = _load_pos_app()

from core.factory import create_core_service
from core.platform import GaathaCoreService
from core.pos_adapter import POSCoreAdapter, require_pos_core_scope


def _get_pos_db_models():
    import importlib
    db_module = importlib.import_module("extensions")
    models_module = importlib.import_module("models")
    return db_module.db, models_module.User, models_module.Restaurant, models_module.Product


@pytest.fixture
def pos_adapter(tmp_path):
    service = GaathaCoreService(database_path=str(tmp_path / "gaathacore-pos.sqlite3"))
    return POSCoreAdapter(service=service)


@pytest.fixture
def pos_app(tmp_path):
    db_dir = tmp_path / "pos-instance"
    db_dir.mkdir(exist_ok=True)
    db_uri = f"sqlite:///{db_dir / 'app.db'}"
    os.environ["GAATHACORE_DB_PATH"] = str(tmp_path / "gaathacore-pos-route.sqlite3")
    os.environ["DATABASE_URL"] = db_uri
    create_app_fn = _load_pos_app()
    app = create_app_fn()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    db, _, _, _ = _get_pos_db_models()
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def _make_core_scoped_pos(adapter, *, pos_user_id=101, pos_restaurant_id=11, org_name="POS Org", project_name="Restaurant One"):
    core_user = adapter.core.create_user(email=f"pos{pos_user_id}@example.com", username=f"pos_user_{pos_user_id}", display_name=f"POS User {pos_user_id}")
    adapter.map_pos_user(pos_user_id=pos_user_id, core_user_id=core_user["id"])
    org = adapter.core.create_organization(name=org_name, slug=f"{org_name.lower().replace(' ', '-')}-{pos_restaurant_id}")
    project = adapter.core.create_project(organization_id=org["id"], name=project_name, slug=f"{project_name.lower().replace(' ', '-')}-{pos_restaurant_id}", project_type="pos")
    adapter.map_pos_restaurant(pos_restaurant_id=pos_restaurant_id, core_organization_id=org["id"], core_project_id=project["id"])
    adapter.core.add_organization_membership(user_id=core_user["id"], organization_id=org["id"], role="manager", status="active")
    adapter.core.add_project_membership(project_id=project["id"], user_id=core_user["id"], role="manager", status="active")
    adapter.core.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="pos", enabled=True)
    return core_user, org, project


def test_pos_adapter_resolves_enabled_scope(pos_adapter):
    core_user, org, project = _make_core_scoped_pos(pos_adapter, pos_user_id=101, pos_restaurant_id=11)

    identity = pos_adapter.resolve_authenticated_request(
        pos_user_id=101,
        pos_restaurant_id=11,
        module_key="pos",
        request_id="req-pos-1",
    )

    assert identity["current_user"] == core_user["id"]
    assert identity["current_organization"] == org["id"]
    assert identity["current_project"] == project["id"]
    assert identity["current_module"] == "pos"
    assert "module.read" in identity["permissions"]


def test_pos_adapter_rejects_restaurant_cross_tenant(pos_adapter):
    _make_core_scoped_pos(pos_adapter, pos_user_id=201, pos_restaurant_id=22)
    _make_core_scoped_pos(pos_adapter, pos_user_id=202, pos_restaurant_id=23, org_name="Other Org", project_name="Restaurant Two")

    with pytest.raises(PermissionError):
        pos_adapter.resolve_authenticated_request(
            pos_user_id=201,
            pos_restaurant_id=23,
            module_key="pos",
            request_id="req-pos-tenant-bad",
        )


def test_pos_adapter_rejects_disabled_module_and_inactive_membership(pos_adapter):
    core_user, org, project = _make_core_scoped_pos(pos_adapter, pos_user_id=301, pos_restaurant_id=31)
    pos_adapter.core.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="pos", enabled=False)
    with pytest.raises(PermissionError):
        pos_adapter.resolve_authenticated_request(pos_user_id=301, pos_restaurant_id=31, module_key="pos")

    pos_adapter.core.set_module_access(organization_id=org["id"], project_id=project["id"], module_key="pos", enabled=True)
    pos_adapter.core.add_organization_membership(user_id=core_user["id"], organization_id=org["id"], role="manager", status="inactive")
    with pytest.raises(PermissionError):
        pos_adapter.resolve_authenticated_request(pos_user_id=301, pos_restaurant_id=31, module_key="pos")


def test_real_pos_products_route_enforces_core_scope(pos_app):
    service = create_core_service(database_path=os.environ["GAATHACORE_DB_PATH"])
    adapter = POSCoreAdapter(service=service)
    core_user, org, project = _make_core_scoped_pos(adapter, pos_user_id=401, pos_restaurant_id=41)

    db, User, Restaurant, Product = _get_pos_db_models()
    with pos_app.app_context():
        restaurant = Restaurant(name="POS Route Resto", email=f"route-{uuid.uuid4()}@example.com", owner_id=1)
        db.session.add(restaurant)
        db.session.flush()

        user = User(
            username="route_user",
            password_hash="unused",
            role="manager",
            restaurant_id=restaurant.id,
            is_super_admin=False,
        )
        db.session.add(user)
        db.session.flush()

        restaurant.owner_id = user.id
        product = Product(
            restaurant_id=restaurant.id,
            name="Route Product",
            base_price=12.5,
            available=True,
            active=True,
        )
        db.session.add(product)
        db.session.commit()

        adapter.map_pos_user(pos_user_id=user.id, core_user_id=core_user["id"])
        adapter.map_pos_restaurant(pos_restaurant_id=restaurant.id, core_organization_id=org["id"], core_project_id=project["id"])

    with pos_app.test_request_context("/pos/products", headers={"X-Request-ID": "req-pos-route-1"}):
        from flask_login import login_user
        login_user(user)
        response = pos_app.view_functions["pos.list_products"]()
        assert response.status_code == 200, response.get_data(as_text=True)
        payload = response.get_json()
        assert payload and payload[0]["name"] == "Route Product"

    with pos_app.test_request_context("/pos/products", headers={"X-Request-ID": "req-pos-route-2"}):
        from flask_login import logout_user
        logout_user()
        response = pos_app.view_functions["pos.list_products"]()
        assert response.status_code in {302, 403}
