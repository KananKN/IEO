"""empty message

Revision ID: 3b54437f09ad
Revises: bd94a18d9a6c
Create Date: 2025-03-02 11:27:57.358627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b54437f09ad'
down_revision = 'bd94a18d9a6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('files', 'file_type',
               existing_type=sa.INTEGER(),
               comment='1:PS',
               existing_comment='1:PO,2:Quotation,3:ISO,4:Warranty',
               existing_nullable=True)
    op.add_column('product_for_sales', sa.Column('detail', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_for_sales', 'detail')
    op.alter_column('files', 'file_type',
               existing_type=sa.INTEGER(),
               comment='1:PO,2:Quotation,3:ISO,4:Warranty',
               existing_comment='1:PS',
               existing_nullable=True)
    # ### end Alembic commands ###
