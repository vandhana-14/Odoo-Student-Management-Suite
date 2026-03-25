# -*- coding: utf-8 -*-
from odoo import models, api
import logging
import json
import re

from markupsafe import Markup
from openai import OpenAI

_logger = logging.getLogger(__name__)

# BLOCKED MODELS (UNCHANGED)
BLOCKED_MODELS = {
    "ir.module.module",
    "ir.module.module.dependency",
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
    "mail.message",
    "discuss.channel",
}

# ONLY STUDENT MODELS ALLOWED
ALLOWED_MODELS = {
    "student.student",
    "student.department",
    "student.attendance",
    "student.leave",
    "student.skills",
    "student.exam",
    "student.marks",
    "student.marks.line",
    "student.score.record",
    "student.subject",
    "student.bulk.password.reset",
}

READ_ONLY_MODELS = {
    "ir.model",
    "ir.model.fields",
    "ir.module.module",
}

EXCLUDED_FIELDS = {
    "id", "create_uid", "create_date", "write_uid", "write_date",
    "__last_update", "display_name",
}

_pending_deletes: dict = {}


class DiscussAI(models.Model):
    _inherit = "discuss.channel"

    def _get_openrouter_client(self):
        ICP = self.env["ir.config_parameter"].sudo()
        api_key = ICP.get_param("ask_ai.openrouter_api_key")
        ai_model = ICP.get_param("ask_ai.model", default="openai/gpt-4o-mini")

        if not api_key:
            raise Exception("OpenRouter API key not configured.")

        return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1"), ai_model

    def _is_model_allowed(self, model_name: str, intent: str):
        if not model_name:
            return False, "No model provided."

        if model_name in BLOCKED_MODELS:
            return False, f"Model '{model_name}' is restricted."

        if model_name not in ALLOWED_MODELS:
            return False, f"Only Student Module allowed. ({model_name} blocked)"

        if model_name not in self.env:
            return False, f"Model '{model_name}' does not exist."

        if intent in ("create", "update", "delete") and model_name in READ_ONLY_MODELS:
            return False, f"Model '{model_name}' is read-only."

        return True, ""

    def _get_model_schema(self, model_name):
        fields = self.env[model_name].fields_get()
        return {
            k: v for k, v in fields.items()
            if k not in EXCLUDED_FIELDS and v.get("type") not in ("binary", "serialized")
        }

    def _post_reply(self, text):
        super().message_post(
            body=Markup(f"<pre>{text}</pre>"),
            message_type="comment",
            subtype_id=self.env.ref("mail.mt_comment").id,
        )

    def _safe_post_reply(self, text):
        try:
            self.env.cr.rollback()
            self._post_reply(text)
        except Exception:
            _logger.exception("Reply failed")

    # CRUD (UNCHANGED LOGIC)
    def _execute_read(self, model_name, domain, fields, title):
        records = self.env[model_name].search_read(domain, fields, limit=50)

        if not records:
            self._post_reply("No records found.")
            return

        header = " | ".join(fields)
        divider = "-" * 60

        rows = []
        for rec in records:
            row = []
            for f in fields:
                val = rec.get(f, "")
                if isinstance(val, list):
                    val = val[1]
                row.append(str(val))
            rows.append(" | ".join(row))

        output = f"{title}\n{header}\n{divider}\n" + "\n".join(rows)
        self._post_reply(output)

    def _execute_create(self, model_name, values, title):
        rec = self.env[model_name].create(values)
        self._post_reply(f"Created successfully (ID: {rec.id})")

    def _execute_update(self, model_name, domain, values, title):
        recs = self.env[model_name].search(domain)
        if not recs:
            self._post_reply("No records found to update.")
            return
        recs.write(values)
        self._post_reply(f"{len(recs)} records updated.")

    def _execute_delete(self, model_name, domain, title):
        recs = self.env[model_name].search(domain)
        if not recs:
            self._post_reply("No records found to delete.")
            return
        recs.unlink()
        self._post_reply(f"{len(recs)} records deleted.")

    @api.model
    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)

        user_input = re.sub(r"<[^>]+>", "", (kwargs.get("body") or "")).strip()

        if not user_input:
            return message

        try:
            client, ai_model = self._get_openrouter_client()

            system_prompt = """
You are an Odoo Student Management AI.

You can ONLY use these models:
student.student
student.department
student.attendance
student.leave
student.skills
student.exam
student.marks
student.marks.line
student.score.record
student.subject

IMPORTANT:
Always use FULL model name:
student.student (not student)

Return JSON only:
{
  "intent":"read|create|update|delete",
  "model":"model.name",
  "title":"text",
  "domain":[],
  "fields":[],
  "values":{}
}
"""

            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"```json|```", "", raw)

            data = json.loads(raw)

            intent = data.get("intent")
            model_name = data.get("model")
            domain = data.get("domain", [])
            fields = data.get("fields", [])
            values = data.get("values", {})
            title = data.get("title", "Result")

            # SECURITY CHECK
            allowed, reason = self._is_model_allowed(model_name, intent)
            if not allowed:
                self._post_reply(reason)
                return message

            # AUTO FIELD FIX
            if intent == "read" and not fields:
                schema = self._get_model_schema(model_name)
                fields = [
                    f for f, meta in schema.items()
                    if meta["type"] not in ("one2many", "many2many")
                ][:6]

            # ROUTING
            if intent == "read":
                self._execute_read(model_name, domain, fields, title)

            elif intent == "create":
                self._execute_create(model_name, values, title)

            elif intent == "update":
                self._execute_update(model_name, domain, values, title)

            elif intent == "delete":
                self._execute_delete(model_name, domain, title)

        except Exception as e:
            _logger.exception("AI ERROR")
            self._safe_post_reply(f"Error: {str(e)}")

        return message
