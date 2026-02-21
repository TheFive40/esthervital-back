"""add_consentimientos_costos_abonos

Revision ID: f3a1b2c4d5e6
Revises: 1ed9060c2089
Create Date: 2026-02-21 10:00:00.000000

Agrega:
  - Tabla consentimientos_paciente  (Incremento 1)
  - Tabla costos_tratamiento        (Incremento 2)
  - Tabla abonos_tratamiento        (Incremento 2)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a1b2c4d5e6'
down_revision: Union[str, None] = '1ed9060c2089'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Tabla: consentimientos_paciente ───────────────────────────────
    op.create_table(
        'consentimientos_paciente',
        sa.Column('id_consentimiento', sa.Integer(), nullable=False),
        sa.Column('id_paciente', sa.Integer(), nullable=False),
        sa.Column('tipo_consentimiento', sa.String(length=100), nullable=False),
        sa.Column('url_archivo', sa.String(length=500), nullable=False),
        sa.Column('nombre_archivo', sa.String(length=255), nullable=False),
        sa.Column('tipo_archivo', sa.String(length=50), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
        sa.Column(
            'fecha_subida',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column('subido_por', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id_paciente'], ['pacientes.id_paciente'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subido_por'], ['usuarios.id_usuario'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id_consentimiento'),
    )
    op.create_index(
        op.f('ix_consentimientos_paciente_id_paciente'),
        'consentimientos_paciente',
        ['id_paciente'],
    )

    # ─── Tabla: costos_tratamiento ─────────────────────────────────────
    op.create_table(
        'costos_tratamiento',
        sa.Column('id_costo', sa.Integer(), nullable=False),
        sa.Column('id_tratamiento', sa.Integer(), nullable=False),
        sa.Column('costo_total', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column(
            'fecha_registro',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column('registrado_por', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['id_tratamiento'], ['tratamientos.id_tratamiento'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['registrado_por'], ['usuarios.id_usuario'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id_costo'),
        sa.UniqueConstraint('id_tratamiento'),   # 1 costo por tratamiento
    )

    # ─── Tabla: abonos_tratamiento ─────────────────────────────────────
    op.create_table(
        'abonos_tratamiento',
        sa.Column('id_abono', sa.Integer(), nullable=False),
        sa.Column('id_costo', sa.Integer(), nullable=False),
        sa.Column('monto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('medio_pago', sa.String(length=50), nullable=True),
        sa.Column('referencia', sa.String(length=100), nullable=True),
        sa.Column('estado', sa.String(length=20), server_default='Confirmado', nullable=True),
        sa.Column(
            'fecha_pago',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column(
            'fecha_registro',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column('registrado_por', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['id_costo'], ['costos_tratamiento.id_costo'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['registrado_por'], ['usuarios.id_usuario'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id_abono'),
    )
    op.create_index(
        op.f('ix_abonos_tratamiento_id_costo'),
        'abonos_tratamiento',
        ['id_costo'],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_abonos_tratamiento_id_costo'), table_name='abonos_tratamiento')
    op.drop_table('abonos_tratamiento')
    op.drop_table('costos_tratamiento')
    op.drop_index(
        op.f('ix_consentimientos_paciente_id_paciente'),
        table_name='consentimientos_paciente',
    )
    op.drop_table('consentimientos_paciente')