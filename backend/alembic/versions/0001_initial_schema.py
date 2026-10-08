"""Initial database schema migration.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2024-10-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Exchanges
    op.create_table(
        'exchanges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=True, server_default='Asia/Kolkata'),
        sa.Column('mic_code', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # 2. Stocks
    op.create_table(
        'stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('isin', sa.String(), nullable=True),
        sa.Column('exchange_id', sa.Integer(), nullable=False),
        sa.Column('sector', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['exchange_id'], ['exchanges.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'exchange_id', name='_symbol_exchange_uc')
    )

    # 3. Symbol changes
    op.create_table(
        'symbol_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('old_symbol', sa.String(), nullable=False),
        sa.Column('new_symbol', sa.String(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Watchlists
    op.create_table(
        'watchlists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Watchlist Items
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('watchlist_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.ForeignKeyConstraint(['watchlist_id'], ['watchlists.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Daily Candles
    op.create_table(
        'daily_candles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('high', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('low', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('close', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('adjusted_close', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('is_adjusted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'date', 'is_adjusted', name='_stock_date_adj_uc')
    )

    # 7. Latest Quotes
    op.create_table(
        'latest_quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('change', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('change_percent', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('open', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('high', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('low', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('prev_close', sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('market_cap', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('data_quality', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id')
    )

    # 8. Price Alerts
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('threshold', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. Corporate Actions
    op.create_table(
        'corporate_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('ex_date', sa.Date(), nullable=False),
        sa.Column('record_date', sa.Date(), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=False),
        sa.Column('ratio_from', sa.Numeric(), nullable=True),
        sa.Column('ratio_to', sa.Numeric(), nullable=True),
        sa.Column('dividend_amount', sa.Numeric(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('fetch_timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. Financial Statements
    op.create_table(
        'financial_statements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('statement_type', sa.String(), nullable=False),
        sa.Column('period_type', sa.String(), nullable=False),
        sa.Column('reporting_type', sa.String(), nullable=False),
        sa.Column('period_end_date', sa.Date(), nullable=False),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('currency', sa.String(), nullable=False, server_default='INR'),
        sa.Column('unit', sa.String(), nullable=False, server_default='crores'),
        sa.Column('data_json', sa.JSON(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('fetch_timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_id', 'statement_type', 'period_type', 'reporting_type', 'period_end_date', name='_fs_unique')
    )

    # 11. Calculated Ratios
    op.create_table(
        'calculated_ratios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('period_end_date', sa.Date(), nullable=False),
        sa.Column('period_type', sa.String(), nullable=False),
        sa.Column('ratio_name', sa.String(), nullable=False),
        sa.Column('value', sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column('is_meaningful', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('formula_used', sa.String(), nullable=False),
        sa.Column('inputs_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. Shareholding Patterns
    op.create_table(
        'shareholding_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('quarter_end_date', sa.Date(), nullable=False),
        sa.Column('promoter_holding_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('promoter_pledged_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('fii_holding_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('dii_holding_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('public_holding_pct', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('fetch_timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. Research Reports
    op.create_table(
        'research_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('report_json', sa.JSON(), nullable=False),
        sa.Column('report_html', sa.Text(), nullable=True),
        sa.Column('generation_method', sa.String(), nullable=False),
        sa.Column('llm_model', sa.String(), nullable=True),
        sa.Column('data_freshness_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('research_reports')
    op.drop_table('shareholding_patterns')
    op.drop_table('calculated_ratios')
    op.drop_table('financial_statements')
    op.drop_table('corporate_actions')
    op.drop_table('price_alerts')
    op.drop_table('latest_quotes')
    op.drop_table('daily_candles')
    op.drop_table('watchlist_items')
    op.drop_table('watchlists')
    op.drop_table('symbol_changes')
    op.drop_table('stocks')
    op.drop_table('exchanges')
