-- Telegram dispatch bot (SRS 5.1-5.2): messages with buttons, answers, and chat links.
-- Messages still carry a case ID and link only; the buttons act through the same case service.

ALTER TABLE notification ADD COLUMN IF NOT EXISTS buttons jsonb;          -- [{"action": "approve", "label": "Approve"}]
ALTER TABLE notification ADD COLUMN IF NOT EXISTS answered_by text;
ALTER TABLE notification ADD COLUMN IF NOT EXISTS answered_action text;
ALTER TABLE notification ADD COLUMN IF NOT EXISTS answered_at timestamptz;
ALTER TABLE notification ADD COLUMN IF NOT EXISTS telegram_messages jsonb;  -- [{"chat_id", "message_id"}] for edits after an answer
CREATE INDEX IF NOT EXISTS notification_recipient ON notification (recipient, notification_id);

-- One-time codes a signed-in user sends to the bot (/start CODE) to link their Telegram chat.
CREATE TABLE IF NOT EXISTS telegram_link_code (
  code text PRIMARY KEY,
  user_id text NOT NULL REFERENCES app_user (user_id),
  expires_at timestamptz NOT NULL
);

-- Long-polling offset of the bot, so a restart does not replay answered updates.
CREATE TABLE IF NOT EXISTS telegram_state (
  key text PRIMARY KEY,
  value text NOT NULL
);
