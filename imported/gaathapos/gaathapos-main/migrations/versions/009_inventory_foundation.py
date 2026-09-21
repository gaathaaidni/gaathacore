"""Add tenant-safe Product recipes and inventory foundation tables.

Revision ID: 009_inventory_foundation
Revises: 008_add_payment_register_context
"""
from alembic import op
import sqlalchemy as sa


revision = "009_inventory_foundation"
down_revision = "008_add_payment_register_context"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("inventory_item"):
        negative_rows = list(bind.execute(
            sa.text("SELECT id, quantity FROM inventory_item WHERE quantity < 0")
        ).fetchall())
        if negative_rows:
            raise ValueError(
                "Negative inventory quantities detected; remediation required before "
                "enforcing the non-negative inventory invariant."
            )

    if inspector.has_table("inventory_item") and not any(
        column["name"] == "restaurant_id"
        for column in inspector.get_columns("inventory_item")
    ):
        with op.batch_alter_table("inventory_item") as batch_op:
            batch_op.add_column(sa.Column("restaurant_id", sa.Integer(), nullable=True))

    if inspector.has_table("inventory_item") and inspector.has_table("restaurant"):
        unresolved = list(bind.execute(
            sa.text("SELECT id FROM inventory_item WHERE restaurant_id IS NULL")
        ).fetchall())
        if unresolved:
            restaurant_ids = [row[0] for row in bind.execute(
                sa.text("SELECT id FROM restaurant ORDER BY id")
            )]
            if len(restaurant_ids) == 1:
                bind.execute(
                    sa.text(
                        "UPDATE inventory_item SET restaurant_id = :restaurant_id WHERE restaurant_id IS NULL"
                    ),
                    {"restaurant_id": restaurant_ids[0]},
                )
            else:
                raise ValueError(
                    "Unresolved inventory ownership exists for multiple restaurants; "
                    "preserve the row and remediate it before enforcing tenant ownership."
                )

    if inspector.has_table("inventory_item"):
        null_ids = list(bind.execute(
            sa.text("SELECT id FROM inventory_item WHERE restaurant_id IS NULL")
        ).fetchall())
        if null_ids:
            raise ValueError(
                "Inventory rows with null restaurant ownership remain; remediation required before "
                "enforcing the restaurant invariant."
            )

        with op.batch_alter_table("inventory_item") as batch_op:
            if not any(
                foreign_key.get("name") == "fk_inventory_item_restaurant"
                for foreign_key in inspector.get_foreign_keys("inventory_item")
            ):
                batch_op.create_foreign_key(
                    "fk_inventory_item_restaurant",
                    "restaurant",
                    ["restaurant_id"],
                    ["id"],
                )
            batch_op.alter_column("restaurant_id", existing_type=sa.Integer(), nullable=False)

        op.create_index(
            "uq_inventory_item_id_restaurant",
            "inventory_item",
            ["id", "restaurant_id"],
            unique=True,
        )

    if inspector.has_table("product"):
        if not any(column["name"] == "stock_mode" for column in inspector.get_columns("product")):
            with op.batch_alter_table("product") as batch_op:
                batch_op.add_column(sa.Column("stock_mode", sa.String(length=16), nullable=False, server_default="direct"))
        if not any(column["name"] == "inventory_item_id" for column in inspector.get_columns("product")):
            with op.batch_alter_table("product") as batch_op:
                batch_op.add_column(sa.Column("inventory_item_id", sa.Integer(), nullable=True))
        if not any(
            foreign_key.get("name") == "fk_product_stock_inventory_restaurant"
            for foreign_key in inspector.get_foreign_keys("product")
        ):
            with op.batch_alter_table("product") as batch_op:
                batch_op.create_foreign_key(
                    "fk_product_stock_inventory_restaurant",
                    "inventory_item",
                    ["inventory_item_id", "restaurant_id"],
                    ["id", "restaurant_id"],
                )
        op.create_index(
            "uq_product_id_restaurant",
            "product",
            ["id", "restaurant_id"],
            unique=True,
        )

    op.create_table(
        "product_recipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("inventory_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurant.id"]),
        sa.ForeignKeyConstraint(
            ["product_id", "restaurant_id"],
            ["product.id", "product.restaurant_id"],
            name="fk_product_recipe_product_restaurant",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_item_id", "restaurant_id"],
            ["inventory_item.id", "inventory_item.restaurant_id"],
            name="fk_product_recipe_inventory_restaurant",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_product_recipe_positive_quantity"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "restaurant_id", "product_id", "inventory_item_id",
            name="uq_product_recipe_ingredient",
        ),
    )

    op.create_table(
        "inventory_movement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("inventory_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity_delta", sa.Float(), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("reference_type", sa.String(32), nullable=True),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurant.id"]),
        sa.ForeignKeyConstraint(
            ["inventory_item_id", "restaurant_id"],
            ["inventory_item.id", "inventory_item.restaurant_id"],
            name="fk_inventory_movement_item_restaurant",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(movement_type <> 'sale') OR (reference_type IS NOT NULL AND reference_id IS NOT NULL)",
            name="ck_inventory_movement_sale_reference_required",
        ),
        sa.UniqueConstraint(
            "restaurant_id", "inventory_item_id", "movement_type",
            "reference_type", "reference_id",
            name="uq_inventory_movement_reference",
        ),
    )


def downgrade():
    op.drop_table("inventory_movement")
    op.drop_table("product_recipe")
    inspector = sa.inspect(op.get_bind())
    if any(column["name"] == "stock_mode" for column in inspector.get_columns("product")):
        raise RuntimeError(
            "Downgrade is intentionally conservative: stock_mode was introduced in this migration and cannot be safely reconstructed from pre-migration data."
        )
    if any(column["name"] == "inventory_item_id" for column in inspector.get_columns("product")):
        with op.batch_alter_table("product") as batch_op:
            if any(
                foreign_key.get("name") == "fk_product_stock_inventory_restaurant"
                for foreign_key in inspector.get_foreign_keys("product")
            ):
                batch_op.drop_constraint("fk_product_stock_inventory_restaurant", type_="foreignkey")
            batch_op.drop_column("inventory_item_id")
    if any(column["name"] == "restaurant_id" for column in inspector.get_columns("inventory_item")):
        with op.batch_alter_table("inventory_item") as batch_op:
            if any(
                foreign_key.get("name") == "fk_inventory_item_restaurant"
                for foreign_key in inspector.get_foreign_keys("inventory_item")
            ):
                batch_op.drop_constraint("fk_inventory_item_restaurant", type_="foreignkey")
            batch_op.drop_column("restaurant_id")
    op.drop_index("uq_product_id_restaurant", table_name="product")
    op.drop_index("uq_inventory_item_id_restaurant", table_name="inventory_item")