INSERT INTO "User" (
    id,
    name,
    email,
    email_verified,
    image,
    wallet_address,
    created_at,
    updated_at
) VALUES (
    'clrnjv1p30000ml08jxev1q8h',
    'John Doe',
    'john.doe@example.com',
    true,
    'https://example.com/avatar.jpg',
    '0x1234567890abcdef1234567890abcdef12345678',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);



INSERT INTO "Organization" (
   id,
   name,
   api_key,
   owner_id,
   settlement_currencies,
   created_at,
   updated_at
) VALUES (
   'clrnjv1p30001ml08g3k5qp12',
   'Test Company LLC',
   'apikey',
   'clrnjv1p30000ml08jxev1q8h',
   ARRAY[jsonb_build_object('currency_id', '8453', 'address', '0x123'), 
         jsonb_build_object('currency_id', '8453-0x833589fcd6edb6e08f4c7c32d4f71b54bda02913', 'address', '0x456')],
   CURRENT_TIMESTAMP,
   CURRENT_TIMESTAMP
);


UPDATE "Organization"
SET settlement_currencies = ARRAY[
   jsonb_build_object('currency_id', '30000000000001', 'address', 'C19adg59TG2NgU9xYpDra7D73XJiA3GodQZpJshZfFUD')
]
WHERE id = 'clrnjv1p30001ml08g3k5qp12';
