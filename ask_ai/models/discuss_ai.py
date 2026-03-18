from odoo import models, api
from datetime import datetime, timedelta
import logging
import json
import re

from markupsafe import Markup
from openai import OpenAI

_logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# BLOCKLIST — models the AI must never touch.
# Everything else that exists in self.env is allowed.
# ─────────────────────────────────────────────────────────────────────────────
BLOCKED_MODELS = {
    # Odoo module registry — install/uninstall via UI, not raw ORM
    "ir.module.module",
    "ir.module.module.dependency",
    # System / security
    "ir.config_parameter",
    "ir.rule",
    "ir.model.access",
    "res.users",
    "res.groups",
    "ir.ui.view",
    "ir.ui.menu",
    "ir.actions.act_window",
    "ir.actions.server",
    "base.automation",
    # Messaging internals
    "mail.message",
    "discuss.channel",
}

# READ-ONLY models — AI may search_read but never create/update/delete
READ_ONLY_MODELS = {
    "ir.model",
    "ir.model.fields",
    "ir.module.module",       # kept here too for belt-and-suspenders
}

# Fields always excluded from create / write (computed or Odoo-managed)
EXCLUDED_FIELDS = {
    "id", "create_uid", "create_date", "write_uid", "write_date",
    "__last_update", "display_name",
}

# In-memory staging for pending delete confirmations
# Key: channel id  |  Value: {model, ids, description}
_pending_deletes: dict = {}

# ─────────────────────────────────────────────────────────────────────────────
# Well-known model labels — injected into the system prompt as examples only.
# The AI is NOT limited to this list.
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_MODELS = {
    "sale.order":           "Sale Order",
    "sale.order.line":      "Sale Order Line",
    "purchase.order":       "Purchase Order",
    "purchase.order.line":  "Purchase Order Line",
    "stock.picking":        "Stock Picking / Delivery",
    "stock.move":           "Stock Move",
    "product.product":      "Product Variant",
    "product.template":     "Product Template",
    "account.move":         "Journal Entry / Invoice",
    "account.move.line":    "Invoice Line",
    "account.payment":      "Payment",
    "crm.lead":             "CRM Lead / Opportunity",
    "hr.employee":          "Employee",
    "project.project":      "Project",
    "project.task":         "Task",
    "res.partner":          "Contact / Customer / Supplier",
    # Read-only reference models
    "ir.model":             "Model Registry (read only)",
    "ir.model.fields":      "Model Fields (read only)",
}


class DiscussAI(models.Model):
    _inherit = "discuss.channel"

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_openrouter_client(self):
        """Return (OpenAI client, model string) from Odoo system parameters."""
        ICP = self.env["ir.config_parameter"].sudo()
        api_key = ICP.get_param("ask_ai.openrouter_api_key")
        ai_model = ICP.get_param("ask_ai.model", default="openai/gpt-4o-mini")
        if not api_key:
            raise Exception(
                "OpenRouter API key not configured. "
                "Go to Settings → Technical → System Parameters → ask_ai.openrouter_api_key"
            )
        return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1"), ai_model

    def _is_model_allowed(self, model_name: str, intent: str) -> tuple[bool, str]:
        """
        Return (True, "") if the model + intent combination is permitted.
        Return (False, reason) otherwise.
        """
        if not model_name or not isinstance(model_name, str):
            return False, "No model name provided."

        if model_name in BLOCKED_MODELS:
            return False, (
                f"Model '{model_name}' is restricted and cannot be accessed via chat.\n"
                f"To manage modules, use Settings → Apps in the Odoo UI."
            )

        if model_name not in self.env:
            return False, (
                f"Model '{model_name}' does not exist in this Odoo instance.\n"
                f"Tip: ask 'list all models' to explore available models."
            )

        if intent in ("create", "update", "delete") and model_name in READ_ONLY_MODELS:
            return False, (
                f"Model '{model_name}' is read-only via chat.\n"
                f"Only read queries are allowed on this model."
            )

        return True, ""

    def _get_model_schema(self, model_name: str) -> dict:
        """
        Return {field_name: {label, type, required?, relation?}} for model_name.
        Binary and serialized fields are excluded.
        """
        field_defs = self.env[model_name].fields_get(
            attributes=["string", "type", "required", "relation"]
        )
        schema = {}
        for fname, fmeta in field_defs.items():
            if fname in EXCLUDED_FIELDS:
                continue
            ftype = fmeta.get("type", "")
            if ftype in ("binary", "serialized"):
                continue
            entry = {"label": fmeta.get("string", fname), "type": ftype}
            if fmeta.get("required"):
                entry["required"] = True
            if fmeta.get("relation"):
                entry["relation"] = fmeta["relation"]
            schema[fname] = entry
        return schema

    def _build_known_model_list(self) -> str:
        return "\n".join(
            f"  - {label} → {tech}"
            for tech, label in KNOWN_MODELS.items()
        )

    def _post_reply(self, text: str):
        """Post a <pre>-wrapped plain-text reply into this channel."""
        super().message_post(
            body=Markup(f"<pre>{text}</pre>"),
            message_type="comment",
            subtype_id=self.env.ref("mail.mt_comment").id,
        )

    def _safe_post_reply(self, text: str):
        """
        Post a reply after rolling back any aborted transaction.
        Use this inside except blocks where a DB error may have occurred.
        """
        try:
            self.env.cr.rollback()
            self._post_reply(text)
        except Exception:
            _logger.exception("Failed to post error reply after rollback")

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD executors
    # ──────────────────────────────────────────────────────────────────────────

    def _execute_read(self, model_name: str, domain: list,
                      fields: list, title: str):
        records = self.env[model_name].search_read(domain, fields, limit=50)
        if not records:
            self._post_reply("No records found.")
            return

        fmeta = self.env[model_name].fields_get(fields, attributes=["string"])
        header = " | ".join(fmeta.get(f, {}).get("string", f) for f in fields)
        divider = "─" * min(len(header) + 10, 80)
        rows = []

        for rec in records:
            cells = []
            for f in fields:
                val = rec.get(f, "")
                if isinstance(val, list) and len(val) == 2:
                    val = val[1]            # many2one → display name
                elif isinstance(val, bool):
                    val = "Yes" if val else "No"
                cells.append(str(val))
            rows.append(" | ".join(cells))

        body = (
            f"{title}\n"
            f"{header}\n"
            f"{divider}\n"
            + "\n".join(rows)
            + f"\n{divider}\n"
              f"Total: {len(records)} record(s)"
        )
        self._post_reply(body)

    def _execute_create(self, model_name: str, values: dict, title: str):
        safe = {k: v for k, v in values.items() if k not in EXCLUDED_FIELDS}
        record = self.env[model_name].create(safe)
        self._post_reply(
            f"✅ {title}\n"
            f"Record created successfully.\n"
            f"ID: {record.id}"
        )

    def _execute_update(self, model_name: str, domain: list,
                        values: dict, title: str):
        safe = {k: v for k, v in values.items() if k not in EXCLUDED_FIELDS}
        records = self.env[model_name].search(domain, limit=50)
        if not records:
            self._post_reply("⚠️ No records matched the filter. Nothing was updated.")
            return
        records.write(safe)
        self._post_reply(
            f"✅ {title}\n"
            f"{len(records)} record(s) updated successfully."
        )

    def _execute_delete(self, model_name: str, domain: list, title: str):
        """Stage the delete and ask for confirmation before touching any data."""
        records = self.env[model_name].search(domain, limit=50)
        if not records:
            self._post_reply("⚠️ No records matched the filter. Nothing to delete.")
            return

        _pending_deletes[self.id] = {
            "model": model_name,
            "ids": records.ids,
            "description": title,
        }

        id_preview = ", ".join(str(i) for i in records.ids[:10])
        if len(records) > 10:
            id_preview += f" … (+{len(records) - 10} more)"

        self._post_reply(
            f"⚠️  DELETE CONFIRMATION REQUIRED\n"
            f"{'─' * 40}\n"
            f"Operation : {title}\n"
            f"Model     : {model_name}\n"
            f"Records   : {len(records)} record(s)\n"
            f"IDs       : {id_preview}\n"
            f"{'─' * 40}\n"
            f"Type  yes delete  to confirm.\n"
            f"Type anything else to cancel."
        )

    def _confirm_delete(self):
        pending = _pending_deletes.pop(self.id, None)
        if not pending:
            self._post_reply("No pending delete operation found.")
            return
        records = self.env[pending["model"]].browse(pending["ids"])
        count = len(records)
        records.unlink()
        self._post_reply(
            f"🗑️  {pending['description']}\n"
            f"{count} record(s) deleted successfully."
        )

    def _cancel_delete(self):
        _pending_deletes.pop(self.id, None)
        self._post_reply("Delete operation cancelled.")

    # ──────────────────────────────────────────────────────────────────────────
    # Main Odoo hook
    # ──────────────────────────────────────────────────────────────────────────

    @api.model
    def message_post(self, **kwargs):

        message = super().message_post(**kwargs)

        # Strip HTML tags Odoo wraps around message bodies
        user_input = re.sub(r"<[^>]+>", "", (kwargs.get("body") or "")).strip()
        if not user_input:
            return message

        user_input_lower = user_input.lower()

        # ── 1. Greeting ───────────────────────────────────────────────────────
        if user_input_lower in ("hi", "hello", "hey", "hai"):
            self._post_reply(
                "Hello 👋  How can I help?\n\n"
                "You can ask me to:\n"
                "  • Read   – 'show me today sales'\n"
                "  • Read   – 'show all installed modules'\n"
                "  • Create – 'create a customer named Ahmed'\n"
                "  • Update – 'set all draft purchase orders notes to pending review'\n"
                "  • Delete – 'delete sale orders from January 2025'\n\n"
                "I can work with any model in your Odoo database.\n"
                "Just describe what you want to do!"
            )
            return message

        # ── 2. Delete confirmation flow ───────────────────────────────────────
        if user_input_lower == "yes delete":
            self._confirm_delete()
            return message

        if self.id in _pending_deletes:
            self._cancel_delete()
            return message

        # ── 3. AI intent detection ────────────────────────────────────────────
        raw_text = ""
        try:
            client, ai_model = self._get_openrouter_client()

            today     = datetime.today().strftime("%Y-%m-%d")
            yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

            system_prompt = f"""
You are an Odoo ERP assistant. Convert natural language into a structured JSON command.

Today     : {today}
Yesterday : {yesterday}

You can access ANY model that exists in the Odoo database.
The user will describe what they want in plain language.
Map it to the correct Odoo technical model name.

IMPORTANT RESTRICTIONS:
- To install or uninstall modules, tell the user to use the Odoo UI (Settings → Apps).
  Never use intent "create" or "update" on ir.module.module.
  For module queries, use intent "read" only.

WELL-KNOWN MODELS (not exhaustive — other models are also valid):
{self._build_known_model_list()}

INTENT OPTIONS:
  read    – search and display records
  create  – create a new record
  update  – modify existing records
  delete  – remove records (user will be asked to confirm)

STRICT OUTPUT FORMAT — return ONLY valid JSON, no markdown, no explanation:

{{
  "intent"  : "read" | "create" | "update" | "delete",
  "model"   : "<technical odoo model name e.g. sale.order>",
  "title"   : "<short human-readable description>",
  "domain"  : [],
  "fields"  : [],
  "values"  : {{}}
}}

FIELD RULES:
  domain  → Odoo-style filter list.  []  means no filter.
  fields  → field names to fetch     (read only). Use []  to auto-select.
  values  → field→value pairs        (create / update). {{}} for read / delete.

DATE FORMAT: always "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"

EXAMPLES:

User: show today sales
{{
  "intent":"read","model":"sale.order","title":"Today Sales",
  "domain":[["date_order",">=","{today} 00:00:00"],["state","in",["sale","done"]]],
  "fields":["name","partner_id","amount_total","state","date_order"],"values":{{}}
}}

User: show all installed modules
{{
  "intent":"read","model":"ir.module.module","title":"Installed Modules",
  "domain":[["state","=","installed"]],
  "fields":["name","shortdesc","state","installed_version"],"values":{{}}
}}

User: install student management module
{{"intent":"read","model":"ir.module.module","title":"Student Management Module Info",
  "domain":[["name","=","student_management"]],
  "fields":["name","shortdesc","state","installed_version"],"values":{{}}
}}

User: list all models in the system
{{
  "intent":"read","model":"ir.model","title":"All Odoo Models",
  "domain":[],"fields":["model","name","state"],"values":{{}}
}}

User: show open invoices
{{
  "intent":"read","model":"account.move","title":"Open Invoices",
  "domain":[["move_type","=","out_invoice"],["payment_state","!=","paid"]],
  "fields":["name","partner_id","amount_total","invoice_date_due","payment_state"],"values":{{}}
}}

User: create a customer named Ahmed
{{
  "intent":"create","model":"res.partner","title":"Create Customer: Ahmed",
  "domain":[],"fields":[],"values":{{"name":"Ahmed","customer_rank":1}}
}}

User: update all draft purchase orders set notes to pending review
{{
  "intent":"update","model":"purchase.order","title":"Update Draft Purchase Orders",
  "domain":[["state","=","draft"]],"fields":[],"values":{{"notes":"pending review"}}
}}

User: delete sale orders from January 2025
{{
  "intent":"delete","model":"sale.order","title":"Delete Sale Orders Jan 2025",
  "domain":[["date_order",">=","2025-01-01"],["date_order","<=","2025-01-31 23:59:59"]],
  "fields":[],"values":{{}}
}}

Return JSON only. No markdown. No explanation.
"""

            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_input},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            raw_text = response.choices[0].message.content or ""
            _logger.info("AI raw response: %r", raw_text)

            raw_text = re.sub(r"```json|```", "", raw_text).strip()

            # Guard: empty response
            if not raw_text:
                _logger.warning("AI empty response for: %r", user_input)
                self._post_reply(
                    "⚠️ AI returned an empty response. Please rephrase your query."
                )
                return message

            # Guard: not JSON
            if not raw_text.startswith("{"):
                _logger.warning("AI non-JSON response: %r", raw_text)
                self._post_reply(f"🤖 {raw_text}")
                return message

            data = json.loads(raw_text)

            intent     = data.get("intent", "read").lower()
            model_name = data.get("model", "")
            title      = data.get("title", "Result")
            domain     = data.get("domain", [])
            fields     = data.get("fields", [])
            values     = data.get("values", {})

            # ── Security: validate model + intent before any ORM call ─────────
            allowed, reason = self._is_model_allowed(model_name, intent)
            if not allowed:
                self._post_reply(f"⚠️ {reason}")
                return message

            # ── Auto-select fields for read when AI returned [] ───────────────
            if intent == "read" and not fields:
                schema = self._get_model_schema(model_name)
                fields = [
                    f for f, meta in schema.items()
                    if meta["type"] not in ("one2many", "many2many")
                ][:6]

            # ── Route to executor ─────────────────────────────────────────────
            if intent == "read":
                self._execute_read(model_name, domain, fields, title)

            elif intent == "create":
                self._execute_create(model_name, values, title)

            elif intent == "update":
                self._execute_update(model_name, domain, values, title)

            elif intent == "delete":
                self._execute_delete(model_name, domain, title)

            else:
                self._post_reply(f"⚠️ Unknown intent '{intent}' returned by AI.")

        except json.JSONDecodeError as e:
            _logger.error("JSON parse error: %s | raw: %r", e, raw_text)
            self._safe_post_reply(
                "⚠️ AI response could not be parsed. Please try again."
            )

        except Exception as e:
            _logger.exception("AI Error: %s", e)
            self._safe_post_reply(
                f"⚠️ Error: {str(e)[:200]}\n"
                f"The operation could not be completed. Check the server log for details."
            )

        return message