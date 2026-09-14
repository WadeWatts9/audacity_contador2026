"""initial_schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-13 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("token_symbol", sa.String(length=10), nullable=True),
        sa.Column("token_color", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username")
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Games table
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("profile", sa.String(length=20), server_default="genially", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="configuracion", nullable=False),
        sa.Column("initial_team_balance", sa.BigInteger(), server_default="1000000", nullable=False),
        sa.Column("initial_bank_balance", sa.BigInteger(), server_default="10000000", nullable=False),
        sa.Column("current_turn_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_team_order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("turn_order", sa.JSON(), nullable=True),
        sa.Column("rules_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code")
    )
    op.create_index(op.f("ix_games_code"), "games", ["code"], unique=True)
    op.create_index(op.f("ix_games_id"), "games", ["id"], unique=False)

    # Accounts table
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("account_type", sa.String(length=30), nullable=False),
        sa.Column("account_name", sa.String(length=100), nullable=False),
        sa.Column("balance_available", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("balance_reserved", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("lost_turns", sa.Integer(), server_default="0", nullable=False),
        sa.Column("has_insurance_e11", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_closed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("turn_opportunities_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_accounts_game_id"), "accounts", ["game_id"], unique=False)
    op.create_index(op.f("ix_accounts_id"), "accounts", ["id"], unique=False)
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)

    # Ledger entries table
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.String(length=50), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("source_account_id", sa.Integer(), nullable=True),
        sa.Column("destination_account_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("operation_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("rule_version", sa.String(length=50), server_default="1.0", nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
        sa.Column("source_available_before", sa.BigInteger(), nullable=True),
        sa.Column("source_available_after", sa.BigInteger(), nullable=True),
        sa.Column("source_reserved_before", sa.BigInteger(), nullable=True),
        sa.Column("source_reserved_after", sa.BigInteger(), nullable=True),
        sa.Column("dest_available_before", sa.BigInteger(), nullable=True),
        sa.Column("dest_available_after", sa.BigInteger(), nullable=True),
        sa.Column("dest_reserved_before", sa.BigInteger(), nullable=True),
        sa.Column("dest_reserved_after", sa.BigInteger(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("is_reverted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("reverted_by_id", sa.Integer(), nullable=True),
        sa.Column("reverts_entry_id", sa.Integer(), nullable=True),
        sa.Column("state_snapshot", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["destination_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reverted_by_id"], ["ledger_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reverts_entry_id"], ["ledger_entries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key")
    )
    op.create_index(op.f("ix_ledger_entries_created_at"), "ledger_entries", ["created_at"], unique=False)
    op.create_index(op.f("ix_ledger_entries_game_id"), "ledger_entries", ["game_id"], unique=False)
    op.create_index(op.f("ix_ledger_entries_id"), "ledger_entries", ["id"], unique=False)
    op.create_index(op.f("ix_ledger_entries_transaction_id"), "ledger_entries", ["transaction_id"], unique=False)

    # Cards table
    op.create_table(
        "cards",
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("deck_type", sa.String(length=5), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("teacher_answer", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("engine_rule", sa.String(length=100), nullable=True),
        sa.Column("target_description", sa.String(length=200), nullable=True),
        sa.Column("image_path", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("code")
    )
    op.create_index(op.f("ix_cards_deck_type"), "cards", ["deck_type"], unique=False)

    # Card instances table
    op.create_table(
        "card_instances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("card_code", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="disponible", nullable=False),
        sa.Column("assigned_to_account_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_account_id"], ["accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["card_code"], ["cards.code"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_card_instances_card_code"), "card_instances", ["card_code"], unique=False)
    op.create_index(op.f("ix_card_instances_game_id"), "card_instances", ["game_id"], unique=False)
    op.create_index(op.f("ix_card_instances_id"), "card_instances", ["id"], unique=False)
    op.create_index(op.f("ix_card_instances_status"), "card_instances", ["status"], unique=False)

    # Contracts table
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("contract_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("creditor_account_id", sa.Integer(), nullable=True),
        sa.Column("debtor_account_id", sa.Integer(), nullable=False),
        sa.Column("principal_amount", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("fixed_repayment_amount", sa.BigInteger(), nullable=True),
        sa.Column("total_repaid", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at_opportunity", sa.Integer(), nullable=False),
        sa.Column("total_installments", sa.Integer(), server_default="1", nullable=False),
        sa.Column("installments_completed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="activo", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["creditor_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["debtor_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_contracts_creditor_account_id"), "contracts", ["creditor_account_id"], unique=False)
    op.create_index(op.f("ix_contracts_debtor_account_id"), "contracts", ["debtor_account_id"], unique=False)
    op.create_index(op.f("ix_contracts_game_id"), "contracts", ["game_id"], unique=False)
    op.create_index(op.f("ix_contracts_id"), "contracts", ["id"], unique=False)
    op.create_index(op.f("ix_contracts_status"), "contracts", ["status"], unique=False)

    # Scheduled events table
    op.create_table(
        "scheduled_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=True),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("target_account_id", sa.Integer(), nullable=False),
        sa.Column("due_opportunity_number", sa.Integer(), nullable=False),
        sa.Column("priority_step", sa.Integer(), nullable=False),
        sa.Column("installment_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pendiente", nullable=False),
        sa.Column("amount_expected", sa.BigInteger(), nullable=True),
        sa.Column("amount_executed", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_scheduled_events_contract_id"), "scheduled_events", ["contract_id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_due_opportunity_number"), "scheduled_events", ["due_opportunity_number"], unique=False)
    op.create_index(op.f("ix_scheduled_events_game_id"), "scheduled_events", ["game_id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_id"), "scheduled_events", ["id"], unique=False)
    op.create_index(op.f("ix_scheduled_events_status"), "scheduled_events", ["status"], unique=False)
    op.create_index(op.f("ix_scheduled_events_target_account_id"), "scheduled_events", ["target_account_id"], unique=False)

    # Turn records table
    op.create_table(
        "turn_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("team_account_id", sa.Integer(), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("opportunity_number", sa.Integer(), nullable=False),
        sa.Column("dice_roll", sa.Integer(), nullable=True),
        sa.Column("square_number", sa.Integer(), nullable=True),
        sa.Column("square_name", sa.String(length=100), nullable=True),
        sa.Column("card_code", sa.String(length=10), nullable=True),
        sa.Column("was_turn_lost", sa.Integer(), server_default="0", nullable=False),
        sa.Column("action_summary", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_turn_records_created_at"), "turn_records", ["created_at"], unique=False)
    op.create_index(op.f("ix_turn_records_game_id"), "turn_records", ["game_id"], unique=False)
    op.create_index(op.f("ix_turn_records_id"), "turn_records", ["id"], unique=False)
    op.create_index(op.f("ix_turn_records_team_account_id"), "turn_records", ["team_account_id"], unique=False)

def downgrade() -> None:
    op.drop_table("turn_records")
    op.drop_table("scheduled_events")
    op.drop_table("contracts")
    op.drop_table("card_instances")
    op.drop_table("cards")
    op.drop_table("ledger_entries")
    op.drop_table("accounts")
    op.drop_table("games")
    op.drop_table("users")
