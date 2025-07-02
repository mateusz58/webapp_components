#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect('postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database')
cur = conn.cursor()

print('🔍 Investigating trigger execution issue...')

# Check replication role
cur.execute('SHOW session_replication_role')
replication_role = cur.fetchone()[0]
print(f'📊 Session replication role: {replication_role}')

if replication_role != 'origin':
    print('⚠️  Triggers may be disabled due to replication role')

# Test trigger execution in transaction
try:
    cur.execute('BEGIN')
    cur.execute("""
        INSERT INTO component_app.picture (component_id, variant_id, picture_order, url) 
        VALUES (199, 233, 998, 'test') 
        RETURNING id, picture_name
    """)
    
    result = cur.fetchone()
    print(f'🧪 Test insert: ID={result[0]}, name="{result[1]}"')
    
    cur.execute('ROLLBACK')
    
    if result[1]:
        print('✅ Trigger worked in direct connection')
    else:
        print('❌ Trigger failed even in direct connection - this indicates a deeper issue')

except Exception as e:
    print(f'❌ Test failed: {e}')
    cur.execute('ROLLBACK')

conn.close()