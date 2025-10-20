#!/usr/bin/env python3
"""Analyze metadata quality in Milvus collection"""

from pymilvus import connections, Collection

connections.connect(host='localhost', port='19530')

collection = Collection('test_comprehensive_detailed')
collection.flush()
collection.load()

print(f'\n✅ Collection: test_comprehensive_detailed')
print(f'✅ Total entities: {collection.num_entities}\n')

# Query all metadata fields
results = collection.query(
    expr='chunk_index >= 0',
    output_fields=['id', 'document_id', 'chunk_index', 'text', 'char_count', 'token_count',
                   'keywords', 'topics', 'questions', 'summary',
                   'semantic_keywords', 'entity_relationships', 'attributes'],
    limit=5
)

print('=' * 80)
print('🔍 METADATA QUALITY ANALYSIS (First 5 chunks)')
print('=' * 80)

for i, chunk in enumerate(results, 1):
    print(f'\n📄 Chunk {i}: {chunk["id"]}')
    print('-' * 78)
    print(f'Document ID: {chunk["document_id"]}')
    print(f'Chunk Index: {chunk["chunk_index"]}')
    print(f'Char Count: {chunk["char_count"]:,} | Token Count: {chunk["token_count"]:,}')
    print(f'Text: {chunk["text"][:120]}...')

    print(f'\n🏷️  Metadata Fields:')

    fields = {
        'keywords': 500,
        'topics': 500,
        'questions': 500,
        'summary': 1000,
        'semantic_keywords': 800,
        'entity_relationships': 1000,
        'attributes': 1000
    }

    for field, max_len in fields.items():
        value = chunk.get(field, '')
        is_empty = not value or value.strip() == ''

        if is_empty:
            print(f'   ❌ {field:<22} EMPTY')
        else:
            preview = value[:80] + '...' if len(value) > 80 else value
            print(f'   ✅ {field:<22} ({len(value)}/{max_len} chars)')
            print(f'      → {preview}')

# Count overall metadata quality
print(f'\n{"=" * 80}')
print('📊 OVERALL METADATA QUALITY')
print('=' * 80)

all_results = collection.query(
    expr='chunk_index >= 0',
    output_fields=['keywords', 'topics', 'questions', 'summary',
                   'semantic_keywords', 'entity_relationships', 'attributes'],
    limit=100
)

field_stats = {}
for field in ['keywords', 'topics', 'questions', 'summary', 'semantic_keywords', 'entity_relationships', 'attributes']:
    populated = sum(1 for r in all_results if r.get(field, '').strip() != '')
    total = len(all_results)
    percentage = (populated / total) * 100 if total > 0 else 0
    field_stats[field] = {
        'populated': populated,
        'total': total,
        'percentage': percentage
    }

    icon = '✅' if percentage == 100 else ('⚠️' if percentage > 50 else '❌')
    print(f'{icon} {field:<22} {populated}/{total} populated ({percentage:.1f}%)')

collection.release()
connections.disconnect('default')

print(f'\n{"=" * 80}')
print('✅ ANALYSIS COMPLETE - Check UI: http://localhost:3000')
print('=' * 80)
