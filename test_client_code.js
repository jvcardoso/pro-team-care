// Test script to verify client code generation
import { suggestClientCode, generateClientCode } from './frontend/src/utils/clientCodeGenerator.js';

console.log('🧪 Testando geração de código de cliente...\n');

// Test 1: Direct generateClientCode
console.log('Test 1: generateClientCode function');
const establishment1 = { code: 'EST-057-002' };
const code1 = generateClientCode(establishment1, 1);
console.log(`Input: EST-057-002, Expected: CLI-057-001, Got: ${code1}`);
console.log(`✅ Test 1: ${code1 === 'CLI-057-001' ? 'PASS' : 'FAIL'}\n`);

// Test 2: suggestClientCode
console.log('Test 2: suggestClientCode function');
const establishment2 = { code: 'EST-057-002' };
const code2 = suggestClientCode(establishment2, []);
console.log(`Input: EST-057-002, Expected: CLI-057-001, Got: ${code2}`);
console.log(`✅ Test 2: ${code2 === 'CLI-057-001' ? 'PASS' : 'FAIL'}\n`);

// Test 3: Different company code
console.log('Test 3: Different company code');
const establishment3 = { code: 'EST-123-001' };
const code3 = generateClientCode(establishment3, 1);
console.log(`Input: EST-123-001, Expected: CLI-123-001, Got: ${code3}`);
console.log(`✅ Test 3: ${code3 === 'CLI-123-001' ? 'PASS' : 'FAIL'}\n`);

// Test 4: Edge case - invalid format
console.log('Test 4: Edge case handling');
const establishment4 = { code: 'INVALID-CODE' };
const code4 = generateClientCode(establishment4, 1);
console.log(`Input: INVALID-CODE, Expected: CLI-000-001, Got: ${code4}`);
console.log(`✅ Test 4: ${code4 === 'CLI-000-001' ? 'PASS' : 'FAIL'}\n`);

console.log('🎯 All tests completed!');
