-- System accounts. Player accounts are created lazily on first posting;
-- these fixed accounts are seeded once so settlement can credit the pool.
INSERT INTO accounts (owner_type, owner_id, currency) VALUES
    ('POOL',             'common-pool',      'VND'),
    ('ACTIVITY_EXPENSE', 'activity-expense', 'VND'),
    ('CASH_RECEIVED',    'cash-received',    'VND');
