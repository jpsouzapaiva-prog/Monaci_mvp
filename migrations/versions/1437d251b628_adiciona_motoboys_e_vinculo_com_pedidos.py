"""adiciona motoboys e vinculo com pedidos

Revision ID: 1437d251b628
Revises: ffeb5287d008
Create Date: 2026-09-15 08:56:42.080924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1437d251b628"
down_revision = "ffeb5287d008"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # A primeira tentativa em SQLite pode ter criado a tabela motoboys
    # antes de falhar na FK de pedidos. Por isso, nao recriamos a tabela
    # se ela ja existir.
    if "motoboys" not in inspector.get_table_names():
        op.create_table(
            "motoboys",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=120), nullable=False),
            sa.Column("telefone", sa.String(length=30), nullable=False),
            sa.Column("login", sa.String(length=80), nullable=False),
            sa.Column("senha_hash", sa.String(length=255), nullable=False),
            sa.Column("ativo", sa.Boolean(), nullable=False),
            sa.Column("criado_em", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "empresa_id",
                "login",
                name="uq_motoboy_empresa_login",
            ),
        )

        with op.batch_alter_table("motoboys", schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f("ix_motoboys_empresa_id"),
                ["empresa_id"],
                unique=False,
            )

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("motoboy_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("hora_aceite_entrega", sa.DateTime(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_pedidos_motoboy_id"),
            ["motoboy_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_pedidos_motoboy_id_motoboys",
            "motoboys",
            ["motoboy_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_pedidos_motoboy_id_motoboys",
            type_="foreignkey",
        )
        batch_op.drop_index(
            batch_op.f("ix_pedidos_motoboy_id")
        )
        batch_op.drop_column("hora_aceite_entrega")
        batch_op.drop_column("motoboy_id")

    with op.batch_alter_table("motoboys", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_motoboys_empresa_id")
        )

    op.drop_table("motoboys")
