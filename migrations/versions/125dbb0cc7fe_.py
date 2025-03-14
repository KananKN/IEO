"""empty message

Revision ID: 125dbb0cc7fe
Revises: 3740df33d9e0
Create Date: 2025-02-26 21:17:37.055753

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '125dbb0cc7fe'
down_revision = '3740df33d9e0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('term_of_payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('term_of_payment')
    # ### end Alembic commands ###
