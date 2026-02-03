#!/usr/bin/env python3
"""
Test various Anthropic model identifiers to determine valid options
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv('config/.env')
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Test models to try
models_to_test = [
    # Current working model
    'claude-3-haiku-20240307',

    # Sonnet 3.5 variants (tried in Criterion 2)
    'claude-3-5-sonnet-20240620',
    'claude-3-5-sonnet-20241022',

    # Sonnet 4 variants (newest)
    'claude-sonnet-4-20250514',
    'claude-sonnet-4-20250415',

    # Opus 4 (newest flagship)
    'claude-opus-4-20250514',

    # Legacy Sonnet 3
    'claude-3-sonnet-20240229',
]

print('Testing Anthropic API Model Identifiers')
print('='*80)
print()

results = []

for model in models_to_test:
    print(f'Testing: {model}...')
    try:
        message = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{
                'role': 'user',
                'content': 'Reply with just: OK'
            }]
        )
        status = 'SUCCESS'
        response = message.content[0].text.strip()
        tokens = f'{message.usage.input_tokens}in/{message.usage.output_tokens}out'
        results.append({
            'model': model,
            'status': status,
            'response': response,
            'tokens': tokens
        })
        print(f'  -> {status} - Response: {response} - Tokens: {tokens}')
    except Exception as e:
        status = 'FAILED'
        error = str(e)
        if 'model:' in error:
            # Extract just the error type
            error = error.split('model:')[0].strip()
        results.append({
            'model': model,
            'status': status,
            'error': error[:80]
        })
        print(f'  -> {status} - Error: {error[:80]}')
    print()

print('='*80)
print('SUMMARY')
print('='*80)
print()
print('Working Models:')
for r in results:
    if r['status'] == 'SUCCESS':
        print(f'  ✓ {r["model"]} (Tokens: {r["tokens"]})')

print()
print('Failed Models:')
for r in results:
    if r['status'] == 'FAILED':
        print(f'  X {r["model"]}')
        print(f'     Error: {r["error"]}')
