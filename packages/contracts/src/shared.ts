// Shared A.22 types used by the contracts in this package (SPEC.md Appendix A.22 "Shared types").
import { z } from "zod";

export const UUID = z.string().uuid();

/** Integer cents, safe integer. May be signed (ledger amounts and balances). */
export const MoneyCents = z.number().int().refine(Number.isSafeInteger, "must be a safe integer");

export const LedgerTag = z.enum([
  "business_receipts",
  "inventory_purchase",
  "sales_tax",
  "platform_fee",
  "rent_utilities",
  "personal_loan_proceeds",
  "business_loan_proceeds",
  "loan_principal",
  "loan_interest",
  "debt_interest",
  "overdraft_fee",
  "starting_cash",
  "fresh_start_credit",
  "savings_deposit",
  "savings_withdrawal",
  "business_slot_purchase",
  "other_credits",
  "other_debits",
]);

export const ConsumerReasonCode = z.enum([
  "bought",
  "price_rejected",
  "over_budget",
  "out_of_stock",
  "service_capacity_full",
  "business_closed",
]);

export const CustomerArchetype = z.enum(["bargain_hunter", "loyal_regular", "premium_buyer"]);
