-- Rooftop-solar registrations carry the installed capacity and whether a home battery is fitted
-- (FR-PS-10, AS-9): the energy-budget check and the battery limit read them. Both stay optional.
ALTER TABLE account_event ADD COLUMN IF NOT EXISTS capacity_kwp double precision;
ALTER TABLE account_event ADD COLUMN IF NOT EXISTS has_battery boolean;
